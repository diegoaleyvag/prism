"""Grading result types shared by the graders and the execution engine."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, JsonValue


class GradeResult(BaseModel):
    """The verdict for one (case, output) pair.

    ``abstention_correct`` is ``None`` for ``normal`` cases (outside the
    abstention/escalation population) and a bool for ``should_*`` cases.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_valid: bool
    task_success: bool
    abstention_correct: bool | None
    reason: str
    failed_metric: str | None = None
    normalized: JsonValue | None = None


__all__ = ["GradeResult"]
