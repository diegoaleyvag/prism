"""Build the default evaluation manifest that pins all seed cases + both profiles."""

from __future__ import annotations

from collections.abc import Mapping

from prism.models.enums import TaskFamily
from prism.models.manifest import EvaluationManifest, ManifestEntry, RunnerRef
from prism.models.task_case import TaskCase

DEFAULT_METRICS: tuple[str, ...] = (
    "task_success_rate",
    "schema_validity_rate",
    "correct_escalation_rate",
    "over_refusal_rate",
    "latency_ms",
    "tokens",
    "estimated_cost_usd",
    "pareto",
)

DEFAULT_SEED = 20260813


def build_default_manifest(
    cases: Mapping[str, TaskCase],
    profile_ids: list[str],
    *,
    manifest_id: str = "prism-foundation",
    manifest_version: str = "1.0.0",
    title: str = "Prism foundation evaluation (simulated)",
    seed: int = DEFAULT_SEED,
    created_by: str = "atomicz",
) -> EvaluationManifest:
    """Pin every case (sorted by id) and one fixture runner per profile id."""
    entries = tuple(
        ManifestEntry(case_id=cid, case_digest=cases[cid].case_digest)
        for cid in sorted(cases)
    )
    runners = tuple(
        RunnerRef(runner_kind="fixture_replay", profile=pid) for pid in sorted(profile_ids)
    )
    return EvaluationManifest.build(
        manifest_id=manifest_id,
        manifest_version=manifest_version,
        title=title,
        description="Deterministic fixture simulation across four task families. SIMULATED "
        "results — not a measurement of any named model or provider.",
        families=tuple(TaskFamily),
        runners=runners,
        cases=entries,
        metrics=DEFAULT_METRICS,
        seed=seed,
        created_by=created_by,
    )


__all__ = ["DEFAULT_METRICS", "DEFAULT_SEED", "build_default_manifest"]
