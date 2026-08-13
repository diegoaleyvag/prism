"""Build the redacted static artifact set consumed by the SvelteKit explorer.

Pure and deterministic: given the same report + records the artifact bytes are identical
(``content_hash`` per file excludes only the volatile ``generated_at``). Every file carries
``simulated: true`` and passes the provider-name guard before it is written.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from prism.digest import content_digest
from prism.export.redaction import assert_no_provider_names, redact_text
from prism.metrics.pricing import PriceTable
from prism.metrics.schema import GroupMetrics, MetricReport
from prism.models.enums import ReviewLabel, ReviewScope, TaskFamily
from prism.models.metric_result import MetricResult
from prism.models.run_record import RunRecord
from prism.models.task_case import TaskCase
from prism.schema_versions import ARTIFACT_V1

_DISCLAIMER = (
    "SIMULATED — deterministic fixture results. Not a measurement of any named model or "
    "provider, and not billed cost."
)


def _rate_dict(m: MetricResult | None) -> dict[str, Any] | None:
    if m is None:
        return None
    extra = m.extra
    return {
        "metric_id": m.metric_id,
        "scope": m.scope,
        "profile_id": m.profile_id,
        "family": m.family.value if m.family else None,
        "numerator": m.numerator,
        "denominator": m.denominator,
        "rate": m.value,
        "display": m.display,
        "ci_low": m.ci_low,
        "ci_high": m.ci_high,
        "ci_reliable": m.ci_reliable,
        "ci_flags": list(m.ci_flags),
        "method": m.method,
        "seed": m.seed,
        "rule_of_three": extra.get("rule_of_three", {}),
        "denominator_record_ids": list(m.computed_from),
        "passed_record_ids": extra.get("passed_record_ids", []),
    }


def _group_dict(g: GroupMetrics) -> dict[str, Any]:
    return {
        "scope": g.scope,
        "profile_id": g.profile_id,
        "family": g.family.value if g.family else None,
        "n": g.n,
        "task_success": _rate_dict(g.task_success),
        "schema_validity": _rate_dict(g.schema_validity),
        "correct_escalation": _rate_dict(g.correct_escalation),
        "over_refusal": _rate_dict(g.over_refusal),
        "latency": g.latency.model_dump(),
        "tokens": g.tokens.model_dump(),
        "cost": g.cost.model_dump(),
        "member_record_ids": list(g.member_record_ids),
        "passed_record_ids": list(g.passed_record_ids),
    }


def _case_rows(
    report: MetricReport,
    records: Sequence[RunRecord],
    cases: Mapping[str, TaskCase],
    price_table: PriceTable,
) -> list[dict[str, Any]]:
    kept = [
        r for r in records
        if report.review_scope == ReviewScope.FULL
        or cases[r.case_id].review_label == ReviewLabel.OWNER_REVIEWED
    ]
    rows: list[dict[str, Any]] = []
    for r in sorted(kept, key=lambda x: (x.runner.runner_name, x.case_id)):
        case = cases[r.case_id]
        cost_micro = price_table.cost_micro_usd(
            r.runner.runner_name, r.measurements.input_tokens, r.measurements.output_tokens
        )
        rows.append(
            {
                "record_id": r.record_id,
                "case_id": r.case_id,
                "family": case.payload.family.value,
                "profile_id": r.runner.runner_name,
                "behavior_class": case.payload.behavior_class.value,
                "review_label": case.review_label.value,
                "schema_valid": r.validation.schema_valid,
                "task_success": r.validation.task_success,
                "abstention_correct": r.validation.abstention_correct,
                "failed_metric": r.validation.failed_metric,
                "reason": r.validation.detail,
                "latency_ms": r.measurements.latency_ms,
                "input_tokens": r.measurements.input_tokens,
                "output_tokens": r.measurements.output_tokens,
                "total_tokens": r.measurements.total_tokens,
                "cost_micro_usd": cost_micro,
                "cost_usd": cost_micro / 1_000_000,
                "input_excerpt": redact_text(case.payload.prompt),
                "expected_summary": redact_text(json.dumps(case.payload.expected_output, sort_keys=True)),
                "output_summary": redact_text(json.dumps(r.result.normalized, sort_keys=True)),
            }
        )
    return rows


def build_artifacts(
    report: MetricReport,
    records: Sequence[RunRecord],
    cases: Mapping[str, TaskCase],
    price_table: PriceTable,
) -> dict[str, dict[str, Any]]:
    """Return ``{filename: artifact_dict}``. Deterministic given the same inputs."""

    def env(name: str) -> dict[str, Any]:
        return {
            "artifact": name,
            "schema_version": ARTIFACT_V1,
            "simulated": True,
            "disclaimer": _DISCLAIMER,
            "generated_at": report.generated_at,
        }

    overview = env("overview")
    overview["review_scope"] = report.review_scope.value
    overview["excluded_count"] = report.excluded_count
    overview["guardrail"] = report.guardrail
    overview["price_table_id"] = report.price_table_id
    overview["record_set_hash"] = report.record_set_hash
    overview["profiles"] = [
        {"profile_id": p.profile_id, "profile_digest": p.profile_digest,
         "aggregate": _group_dict(p.aggregate)}
        for p in report.profiles
    ]

    families = env("families")
    families["profiles"] = [
        {"profile_id": p.profile_id,
         "families": [_group_dict(g) for g in p.families]}
        for p in report.profiles
    ]

    uncertainty = env("uncertainty")
    uncertainty["guardrail"] = report.guardrail
    unc_metrics: list[dict[str, Any]] = []
    for p in report.profiles:
        for grp in (p.aggregate, *p.families):
            for m in (grp.task_success, grp.schema_validity, grp.correct_escalation,
                      grp.over_refusal):
                d = _rate_dict(m)
                if d is not None:
                    unc_metrics.append(d)
    uncertainty["metrics"] = unc_metrics

    case_rows = _case_rows(report, records, cases, price_table)
    cases_art = env("cases")
    cases_art["rows"] = case_rows

    failures = env("failures")
    failures["rows"] = [r for r in case_rows if not r["task_success"]]

    pareto = env("pareto")
    pareto["axes"] = {"quality": "task_success_rate (max)", "cost_usd": "mean per case (min)",
                      "latency_p90_ms": "p90 latency (min)"}
    pareto["points"] = [p.model_dump() for p in report.pareto]

    pricing = env("pricing")
    pricing["price_table"] = json.loads(price_table.model_dump_json())

    artifacts: dict[str, dict[str, Any]] = {
        "overview.json": overview,
        "families.json": families,
        "uncertainty.json": uncertainty,
        "cases.json": cases_art,
        "failures.json": failures,
        "pareto.json": pareto,
        "pricing.json": pricing,
    }

    index = env("index")
    index["run"] = {
        "manifest_id": report.manifest_id,
        "manifest_digest": report.manifest_digest,
        "record_set_hash": report.record_set_hash,
        "prism_version": report.prism_version,
        "review_scope": report.review_scope.value,
    }
    index["profiles"] = [
        {"profile_id": p.profile_id, "profile_digest": p.profile_digest} for p in report.profiles
    ]
    index["families"] = [f.value for f in TaskFamily]
    index["case_ids"] = sorted({r["case_id"] for r in case_rows})
    index["artifacts"] = {
        name: {"file": name, "content_hash": _artifact_hash(art)}
        for name, art in artifacts.items()
    }
    artifacts["index.json"] = index
    return artifacts


def _artifact_hash(artifact: dict[str, Any]) -> str:
    """Content hash of an artifact, excluding the volatile ``generated_at``."""
    body = {k: v for k, v in artifact.items() if k != "generated_at"}
    return content_digest(body)


def write_artifacts(artifacts: Mapping[str, dict[str, Any]], out_dir: Path) -> list[Path]:
    """Guard against name leaks, then write each artifact as sorted, pretty JSON."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, artifact in artifacts.items():
        assert_no_provider_names(artifact)
        path = out / name
        path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written.append(path)
    return sorted(written)


__all__ = ["build_artifacts", "write_artifacts"]
