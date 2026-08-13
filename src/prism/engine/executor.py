"""The run loop: (case x runner) -> grade -> immutable RunRecord.

The executor validates the manifest first (fail-closed), then for each runner and each
pinned case produces a graded, content-addressed record. Fixture runs are pure, so the
records are reproducible; only the wall-clock timestamps differ between runs and they are
excluded from the record id.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime

from prism import __version__
from prism.dataset.grading import grade, grader_id
from prism.digest import content_digest
from prism.models.enums import ValidationStatus
from prism.models.manifest import EvaluationManifest, RunnerRef
from prism.models.run_record import (
    Measurements,
    RunRecord,
    RunResult,
    ValidationOutcome,
)
from prism.models.task_case import TaskCase
from prism.runners.base import BaseRunner
from prism.runners.fixture import FixtureReplayRunner
from prism.runners.profiles import FixtureProfile
from prism.runners.provider import ProviderRunner
from prism.storage.record_store import RecordStore
from prism.validation.manifest_validator import has_errors, validate_manifest

Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.now(UTC)


class ManifestInvalidError(RuntimeError):
    """Raised when a manifest fails validation before execution."""

    def __init__(self, problems: list[str]) -> None:
        self.problems = problems
        super().__init__("manifest failed validation:\n" + "\n".join(problems))


@dataclass
class RunSummary:
    run_dir: str | None
    records: list[RunRecord]
    written: int
    skipped: int


def _build_runner(
    ref: RunnerRef, profiles: Mapping[str, FixtureProfile], *, allow_provider: bool
) -> BaseRunner:
    if ref.runner_kind == "fixture_replay":
        assert ref.profile is not None
        return FixtureReplayRunner(profiles[ref.profile])
    assert ref.provider_ref is not None
    return ProviderRunner(ref.provider_ref, explicit_enable=allow_provider)


def _grade_to_record(
    manifest: EvaluationManifest,
    case: TaskCase,
    runner: BaseRunner,
    *,
    clock: Clock,
) -> RunRecord:
    started = clock()
    output = runner.run(case)
    finished = clock()
    result = grade(case, output.raw_output)

    validation = ValidationOutcome(
        status=ValidationStatus.PASSED if result.task_success else ValidationStatus.FAILED,
        grader=grader_id(case.payload.family),
        schema_valid=result.schema_valid,
        task_success=result.task_success,
        abstention_correct=result.abstention_correct,
        failed_metric=result.failed_metric,
        detail=result.reason,
    )
    measurements = Measurements(
        latency_ms=output.latency_ms,
        input_tokens=output.input_tokens,
        output_tokens=output.output_tokens,
        total_tokens=output.input_tokens + output.output_tokens,
    )
    return RunRecord.build(
        manifest_id=manifest.manifest_id,
        manifest_version=manifest.manifest_version,
        manifest_digest=manifest.manifest_digest,
        case_id=case.case_id,
        case_digest=case.case_digest,
        runner=runner.identity,
        run_mode=runner.mode,
        config_digest=runner.identity.config_digest,
        result=RunResult(output_digest=content_digest(output.raw_output), normalized=result.normalized),
        validation=validation,
        measurements=measurements,
        prism_version=__version__,
        started_at=started,
        finished_at=finished,
        seed=manifest.seed,
    )


def execute_run(
    manifest: EvaluationManifest,
    cases: Mapping[str, TaskCase],
    profiles: Mapping[str, FixtureProfile],
    store: RecordStore,
    *,
    dry_run: bool = False,
    allow_provider: bool = False,
    clock: Clock = _utc_now,
) -> RunSummary:
    """Validate then execute the manifest, writing immutable records unless ``dry_run``."""
    problems = validate_manifest(manifest, cases, profiles, allow_provider=allow_provider)
    if has_errors(problems):
        raise ManifestInvalidError([p.render() for p in problems if p.level == "error"])

    run_dir = None if dry_run else str(store.initialize_run(manifest, profiles))
    runners = [_build_runner(r, profiles, allow_provider=allow_provider) for r in manifest.runners]

    records: list[RunRecord] = []
    written = skipped = 0
    for runner in runners:
        for entry in manifest.cases:
            case = cases[entry.case_id]
            record = _grade_to_record(manifest, case, runner, clock=clock)
            records.append(record)
            if not dry_run:
                assert run_dir is not None
                _, was_written = store.write_record(store.run_dir(manifest), record)
                written += int(was_written)
                skipped += int(not was_written)
    return RunSummary(run_dir=run_dir, records=records, written=written, skipped=skipped)


__all__ = ["ManifestInvalidError", "RunSummary", "execute_run"]
