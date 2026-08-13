"""The run record: an append-only, content-addressed, secret-free result artifact.

A ``RunRecord`` captures everything needed to reproduce and audit one (case x runner)
evaluation. It is content-addressed by :func:`compute_record_id`, which hashes the record
*minus* its volatile fields (wall-clock timestamps and the id itself). Two runs of the same
locked code + manifest + fixtures therefore produce byte-identical records apart from
``started_at``/``finished_at``, and share a ``record_id``.

Secret safety is structural, not procedural: there is no field for a provider key or a raw
prompt/output. The model's output is reduced to ``output_digest`` plus a graded,
publishable ``normalized`` value.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

from prism.digest import content_digest
from prism.models.enums import RunMode, ValidationStatus
from prism.schema_versions import RUNRECORD_V1

_VOLATILE: frozenset[str] = frozenset({"started_at", "finished_at", "record_id"})


class RunnerIdentity(BaseModel):
    """Stable identity of the runner that produced a record."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    runner_kind: Literal["fixture_replay", "provider"]
    runner_name: str
    """Profile id (fixture) or provider scaffold id."""
    runner_version: str
    profile_digest: str | None = None
    config_digest: str


class Measurements(BaseModel):
    """Observed *physical* measurements. All integers — no floats reach record identity.

    Cost is deliberately absent: it is a downstream, re-computable estimate derived from
    these token counts and a separately versioned price table, never baked into the record.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    latency_ms: int = Field(ge=0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)

    @model_validator(mode="after")
    def _check_total(self) -> Self:
        if self.total_tokens != self.input_tokens + self.output_tokens:
            raise ValueError("total_tokens must equal input_tokens + output_tokens")
        return self


class ValidationOutcome(BaseModel):
    """The grading verdict for a single run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: ValidationStatus
    grader: str
    """Grader identity, e.g. the family grader that produced this verdict."""
    schema_valid: bool
    task_success: bool
    abstention_correct: bool | None = None
    """``None`` when the case is outside the abstention/escalation population."""
    failed_metric: str | None = None
    detail: str | None = None


class RunResult(BaseModel):
    """The publishable, redacted result of a run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    output_digest: str
    """``sha256:…`` of the canonical raw output (the raw output itself is not stored)."""
    normalized: JsonValue | None = None
    """Graded/structured output, safe to publish."""


class RunRecord(BaseModel):
    """An immutable, content-addressed evaluation record."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["runrecord/v1"] = RUNRECORD_V1
    manifest_id: str
    manifest_version: str
    manifest_digest: str
    case_id: str
    case_digest: str
    runner: RunnerIdentity
    run_mode: RunMode
    config_digest: str
    result: RunResult
    validation: ValidationOutcome
    measurements: Measurements
    prism_version: str
    seed: int | None = None
    # --- volatile: excluded from record_id -------------------------------
    started_at: datetime
    finished_at: datetime
    record_id: str

    @model_validator(mode="after")
    def _verify_record_id(self) -> Self:
        expected = compute_record_id(self)
        if self.record_id != expected:
            raise ValueError(
                f"record_id drift for case {self.case_id!r}: "
                f"stored={self.record_id} computed={expected}"
            )
        return self

    @classmethod
    def build(
        cls,
        *,
        manifest_id: str,
        manifest_version: str,
        manifest_digest: str,
        case_id: str,
        case_digest: str,
        runner: RunnerIdentity,
        run_mode: RunMode,
        config_digest: str,
        result: RunResult,
        validation: ValidationOutcome,
        measurements: Measurements,
        prism_version: str,
        started_at: datetime,
        finished_at: datetime,
        seed: int | None = None,
    ) -> RunRecord:
        """Construct a record with ``record_id`` derived from its non-volatile body."""
        core = {
            "schema_version": RUNRECORD_V1,
            "manifest_id": manifest_id,
            "manifest_version": manifest_version,
            "manifest_digest": manifest_digest,
            "case_id": case_id,
            "case_digest": case_digest,
            "runner": runner,
            "run_mode": run_mode,
            "config_digest": config_digest,
            "result": result,
            "validation": validation,
            "measurements": measurements,
            "prism_version": prism_version,
            "seed": seed,
        }
        record_id = content_digest(core)
        return cls(
            schema_version=RUNRECORD_V1,
            manifest_id=manifest_id,
            manifest_version=manifest_version,
            manifest_digest=manifest_digest,
            case_id=case_id,
            case_digest=case_digest,
            runner=runner,
            run_mode=run_mode,
            config_digest=config_digest,
            result=result,
            validation=validation,
            measurements=measurements,
            prism_version=prism_version,
            seed=seed,
            started_at=started_at,
            finished_at=finished_at,
            record_id=record_id,
        )


def compute_record_id(record: RunRecord) -> str:
    """Content digest over the record's non-volatile body."""
    body = record.model_dump(exclude=set(_VOLATILE))
    return content_digest(body)


__all__ = [
    "Measurements",
    "RunRecord",
    "RunResult",
    "RunnerIdentity",
    "ValidationOutcome",
    "compute_record_id",
]
