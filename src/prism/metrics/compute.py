"""Compute a reconcilable MetricReport from immutable records.

Pipeline: build an atomic fact frame (one row per record) with Polars; roll it up with a
single DuckDB ``GROUPING SETS`` pass so per-family and per-profile-aggregate rows are
consistent by construction; attach seeded bootstrap CIs (with the small-n guardrail) and the
record-id lists that make every aggregate drill down to its cases.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime
from decimal import Decimal
from typing import cast

import duckdb
import polars as pl
from pydantic import JsonValue

from prism import __version__
from prism.digest import content_digest
from prism.metrics.pareto import _Candidate, pareto_points
from prism.metrics.pricing import PriceTable
from prism.metrics.schema import (
    CostBlock,
    GroupMetrics,
    LatencyBlock,
    MetricReport,
    ProfileReport,
    TokenBlock,
)
from prism.models.enums import (
    SHOULD_ACT_CLASSES,
    BehaviorClass,
    ReviewLabel,
    ReviewScope,
    TaskFamily,
)
from prism.models.metric_result import MetricResult, MetricScope
from prism.models.run_record import RunRecord
from prism.models.task_case import TaskCase
from prism.stats.bootstrap import BootstrapConfig, RateCIResult, bootstrap_rate_ci

_SAFETY = TaskFamily.SAFETY_ESCALATION.value


def _as_int(value: object) -> int:
    assert isinstance(value, (int, float, Decimal))
    return int(value)


def _as_float(value: object) -> float:
    assert isinstance(value, (int, float, Decimal))
    return float(value)


def build_fact_frame(
    records: Iterable[RunRecord],
    cases: Mapping[str, TaskCase],
    price_table: PriceTable,
) -> pl.DataFrame:
    """One tidy row per record — the single source everything else derives from."""
    rows: list[dict[str, object]] = []
    for r in records:
        case = cases[r.case_id]
        bc = case.payload.behavior_class
        family = case.payload.family.value
        is_normal = bc == BehaviorClass.NORMAL
        rows.append(
            {
                "record_id": r.record_id,
                "case_id": r.case_id,
                "family": family,
                "profile_id": r.runner.runner_name,
                "review_label": case.review_label.value,
                "behavior_class": bc.value,
                "is_should_act": int(bc in SHOULD_ACT_CLASSES),
                "is_normal": int(is_normal),
                "is_safety_normal": int(family == _SAFETY and is_normal),
                "schema_valid": int(r.validation.schema_valid),
                "task_success": int(r.validation.task_success),
                "abstention_correct": (
                    None if r.validation.abstention_correct is None
                    else int(r.validation.abstention_correct)
                ),
                "latency_ms": r.measurements.latency_ms,
                "input_tokens": r.measurements.input_tokens,
                "output_tokens": r.measurements.output_tokens,
                "total_tokens": r.measurements.total_tokens,
                "cost_micro_usd": price_table.cost_micro_usd(
                    r.runner.runner_name, r.measurements.input_tokens, r.measurements.output_tokens
                ),
            }
        )
    schema = {
        "record_id": pl.String, "case_id": pl.String, "family": pl.String,
        "profile_id": pl.String, "review_label": pl.String, "behavior_class": pl.String,
        "is_should_act": pl.Int64, "is_normal": pl.Int64, "is_safety_normal": pl.Int64,
        "schema_valid": pl.Int64, "task_success": pl.Int64, "abstention_correct": pl.Int64,
        "latency_ms": pl.Int64, "input_tokens": pl.Int64, "output_tokens": pl.Int64,
        "total_tokens": pl.Int64, "cost_micro_usd": pl.Int64,
    }
    return pl.DataFrame(rows, schema=schema)


_ROLLUP_SQL = """
SELECT
  profile_id,
  family,
  count(*)                                                         AS n,
  sum(task_success)                                               AS ts_num,
  sum(schema_valid)                                               AS sv_num,
  sum(is_should_act)                                             AS esc_denom,
  sum(CASE WHEN is_should_act = 1 AND abstention_correct = 1 THEN 1 ELSE 0 END) AS esc_num,
  sum(is_safety_normal)                                          AS saf_denom,
  sum(CASE WHEN is_safety_normal = 1 AND task_success = 0 THEN 1 ELSE 0 END)    AS over_num,
  quantile_cont(latency_ms, 0.50)                               AS p50,
  quantile_cont(latency_ms, 0.90)                               AS p90,
  quantile_cont(latency_ms, 0.95)                               AS p95,
  quantile_cont(latency_ms, 0.99)                               AS p99,
  min(latency_ms)                                               AS min_ms,
  max(latency_ms)                                               AS max_ms,
  avg(latency_ms)                                               AS mean_ms,
  sum(input_tokens)                                            AS in_sum,
  sum(output_tokens)                                           AS out_sum,
  sum(total_tokens)                                           AS tot_sum,
  avg(input_tokens)                                           AS in_mean,
  avg(output_tokens)                                          AS out_mean,
  sum(cost_micro_usd)                                        AS cost_sum,
  avg(cost_micro_usd)                                        AS cost_mean
FROM fact
GROUP BY GROUPING SETS ((profile_id, family), (profile_id))
"""


def _rollups(fact: pl.DataFrame) -> dict[tuple[str, str | None], dict[str, object]]:
    con = duckdb.connect()
    try:
        con.register("fact", fact)
        result = con.execute(_ROLLUP_SQL).pl()
    finally:
        con.close()
    out: dict[tuple[str, str | None], dict[str, object]] = {}
    for row in result.iter_rows(named=True):
        out[(row["profile_id"], row["family"])] = row
    return out


def _id_lists(fact: pl.DataFrame) -> dict[tuple[str, str | None], dict[str, list[str]]]:
    """Sorted record-id lists per group (and per-profile aggregate) for drill-down."""
    groups: dict[tuple[str, str | None], dict[str, list[str]]] = defaultdict(
        lambda: {k: [] for k in
                 ("member", "passed", "schema_valid", "esc_denom", "esc_pass",
                  "saf_denom", "saf_over")}
    )

    def add(key: tuple[str, str | None], row: dict[str, object]) -> None:
        g = groups[key]
        rid = str(row["record_id"])
        g["member"].append(rid)
        if row["task_success"] == 1:
            g["passed"].append(rid)
        if row["schema_valid"] == 1:
            g["schema_valid"].append(rid)
        if row["is_should_act"] == 1:
            g["esc_denom"].append(rid)
            if row["abstention_correct"] == 1:
                g["esc_pass"].append(rid)
        if row["is_safety_normal"] == 1:
            g["saf_denom"].append(rid)
            if row["task_success"] == 0:
                g["saf_over"].append(rid)

    for row in fact.iter_rows(named=True):
        add((str(row["profile_id"]), str(row["family"])), row)
        add((str(row["profile_id"]), None), row)

    return {k: {kk: sorted(vv) for kk, vv in v.items()} for k, v in groups.items()}


def _rate_metric(
    metric_id: str,
    scope: MetricScope,
    profile_id: str,
    family: TaskFamily | None,
    numerator: int,
    denominator: int,
    denom_ids: Sequence[str],
    passed_ids: Sequence[str],
    *,
    record_set_hash: str,
    config: BootstrapConfig,
) -> MetricResult:
    ci: RateCIResult = bootstrap_rate_ci(
        numerator,
        denominator,
        seed_parts=(metric_id, profile_id, family.value if family else "aggregate",
                    scope, record_set_hash),
        config=config,
    )
    return MetricResult(
        metric_id=metric_id,
        scope=scope,
        profile_id=profile_id,
        family=family,
        value=ci.rate,
        unit="rate",
        numerator=numerator,
        denominator=denominator,
        display=f"{numerator} / {denominator}",
        ci_low=ci.ci_low,
        ci_high=ci.ci_high,
        ci_reliable=ci.ci_reliable,
        ci_flags=ci.ci_flags,
        method=ci.method,
        seed=ci.seed,
        computed_from=tuple(denom_ids),
        extra=cast(
            "dict[str, JsonValue]",
            {
                "passed_record_ids": list(passed_ids),
                "rule_of_three": ci.rule_of_three,
                "resamples": ci.resamples,
                "level": ci.level,
            },
        ),
    )


def _group_metrics(
    profile_id: str,
    family: TaskFamily | None,
    roll: dict[str, object],
    ids: dict[str, list[str]],
    price_table: PriceTable,
    *,
    record_set_hash: str,
    config: BootstrapConfig,
) -> GroupMetrics:
    scope: MetricScope = "aggregate" if family is None else "family"
    n = _as_int(roll["n"])

    task_success = _rate_metric(
        "task_success_rate", scope, profile_id, family,
        _as_int(roll["ts_num"]), n, ids["member"], ids["passed"],
        record_set_hash=record_set_hash, config=config,
    )
    schema_validity = _rate_metric(
        "schema_validity_rate", scope, profile_id, family,
        _as_int(roll["sv_num"]), n, ids["member"], ids["schema_valid"],
        record_set_hash=record_set_hash, config=config,
    )

    correct_escalation = None
    esc_denom = _as_int(roll["esc_denom"])
    if esc_denom > 0:
        correct_escalation = _rate_metric(
            "correct_escalation_rate", scope, profile_id, family,
            _as_int(roll["esc_num"]), esc_denom, ids["esc_denom"], ids["esc_pass"],
            record_set_hash=record_set_hash, config=config,
        )

    over_refusal = None
    saf_denom = _as_int(roll["saf_denom"])
    if saf_denom > 0:
        over_refusal = _rate_metric(
            "over_refusal_rate", scope, profile_id, family,
            _as_int(roll["over_num"]), saf_denom, ids["saf_denom"], ids["saf_over"],
            record_set_hash=record_set_hash, config=config,
        )

    latency = LatencyBlock(
        n=n, p50_ms=_as_float(roll["p50"]), p90_ms=_as_float(roll["p90"]),
        p95_ms=_as_float(roll["p95"]), p99_ms=_as_float(roll["p99"]),
        min_ms=_as_int(roll["min_ms"]), max_ms=_as_int(roll["max_ms"]),
        mean_ms=_as_float(roll["mean_ms"]),
    )
    tokens = TokenBlock(
        n=n, input_sum=_as_int(roll["in_sum"]), output_sum=_as_int(roll["out_sum"]),
        total_sum=_as_int(roll["tot_sum"]), input_mean=_as_float(roll["in_mean"]),
        output_mean=_as_float(roll["out_mean"]),
    )
    cost_micro = _as_int(roll["cost_sum"])
    cost = CostBlock(
        n=n, total_micro_usd=cost_micro, mean_micro_usd=_as_float(roll["cost_mean"]),
        total_usd=cost_micro / 1_000_000, mean_usd=_as_float(roll["cost_mean"]) / 1_000_000,
        price_table_id=price_table.price_table_id, price_table_hash=price_table.content_hash,
    )
    return GroupMetrics(
        scope=scope, profile_id=profile_id, family=family, n=n,
        task_success=task_success, schema_validity=schema_validity,
        correct_escalation=correct_escalation, over_refusal=over_refusal,
        latency=latency, tokens=tokens, cost=cost,
        member_record_ids=tuple(ids["member"]), passed_record_ids=tuple(ids["passed"]),
    )


def compute_report(
    records: Sequence[RunRecord],
    cases: Mapping[str, TaskCase],
    price_table: PriceTable,
    *,
    scope: ReviewScope = ReviewScope.RELEASE,
    config: BootstrapConfig | None = None,
    generated_at: str | None = None,
) -> MetricReport:
    """Compute the full reconcilable report for ``records`` at the given review ``scope``."""
    cfg = config or BootstrapConfig()

    kept = [
        r for r in records
        if scope == ReviewScope.FULL or cases[r.case_id].review_label == ReviewLabel.OWNER_REVIEWED
    ]
    excluded_count = len(records) - len(kept)
    if not kept:
        raise ValueError("no records in scope; nothing to report")

    record_set_hash = content_digest(sorted(r.record_id for r in kept))
    fact = build_fact_frame(kept, cases, price_table)
    rolls = _rollups(fact)
    ids = _id_lists(fact)

    manifest_id = kept[0].manifest_id
    manifest_digest = kept[0].manifest_digest
    profile_ids = sorted({r.runner.runner_name for r in kept})
    profile_digests = {r.runner.runner_name: (r.runner.profile_digest or "") for r in kept}

    profiles: list[ProfileReport] = []
    candidates: list[_Candidate] = []
    for pid in profile_ids:
        agg = _group_metrics(
            pid, None, rolls[(pid, None)], ids[(pid, None)], price_table,
            record_set_hash=record_set_hash, config=cfg,
        )
        family_groups: list[GroupMetrics] = []
        for fam in TaskFamily:
            key = (pid, fam.value)
            if key in rolls:
                family_groups.append(
                    _group_metrics(pid, fam, rolls[key], ids[key], price_table,
                                   record_set_hash=record_set_hash, config=cfg)
                )
        profiles.append(
            ProfileReport(
                profile_id=pid, profile_digest=profile_digests[pid],
                aggregate=agg, families=tuple(family_groups),
            )
        )
        candidates.append(
            _Candidate(
                profile_id=pid,
                quality=agg.task_success.value if isinstance(agg.task_success.value, float) else 0.0,
                cost_usd=agg.cost.mean_usd,
                latency_p90_ms=agg.latency.p90_ms,
            )
        )

    return MetricReport(
        prism_version=__version__,
        generated_at=generated_at or datetime.now(UTC).isoformat(),
        manifest_id=manifest_id,
        manifest_digest=manifest_digest,
        review_scope=scope,
        excluded_count=excluded_count,
        record_set_hash=record_set_hash,
        price_table_id=price_table.price_table_id,
        price_table_hash=price_table.content_hash,
        guardrail={
            "n_hard": cfg.n_hard, "n_stable": cfg.n_stable,
            "method": "percentile_bootstrap", "resamples": cfg.resamples, "level": cfg.level,
        },
        profiles=tuple(profiles),
        pareto=tuple(pareto_points(candidates)),
    )


def verify_reconciliation(report: MetricReport) -> list[str]:
    """Return reconciliation problems (empty = reconciled). Cheap enough to always run."""
    problems: list[str] = []
    for prof in report.profiles:
        agg = prof.aggregate
        # 1) rate == passed/denominator for each rate metric
        for m in (agg.task_success, agg.schema_validity, agg.correct_escalation, agg.over_refusal):
            if m is None or m.denominator in (None, 0) or m.value is None:
                continue
            expected = m.numerator / m.denominator  # type: ignore[operator]
            if abs(float(m.value) - expected) > 1e-9:
                problems.append(f"{prof.profile_id}/{m.metric_id}: rate {m.value} != {expected}")
        # 2) family denominators sum to the aggregate denominator (task_success)
        fam_sum = sum(f.task_success.denominator or 0 for f in prof.families)
        if fam_sum != (agg.task_success.denominator or 0):
            problems.append(
                f"{prof.profile_id}: family n sum {fam_sum} != aggregate n "
                f"{agg.task_success.denominator}"
            )
        # 3) passed ids subset of member ids
        if not set(agg.passed_record_ids) <= set(agg.member_record_ids):
            problems.append(f"{prof.profile_id}: passed ids not subset of member ids")
    return problems


__all__ = ["build_fact_frame", "compute_report", "verify_reconciliation"]
