"""The evaluation case: a versioned, content-addressed unit of work.

Identity is isolated in :class:`CasePayload` (the semantic content). Annotations that may
legitimately change without altering *what the case tests* — the review label, provenance,
and the digest field itself — live on :class:`TaskCase` and are excluded from the hash.
Promoting a case from ``generated_unreviewed`` to ``owner_reviewed`` therefore leaves
``case_digest`` untouched, preserving referential stability across the manifest.
"""

from __future__ import annotations

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

from prism.digest import content_digest
from prism.models.enums import BehaviorClass, ReviewLabel, TaskFamily
from prism.models.provenance import Provenance
from prism.schema_versions import TASKCASE_V1


class GradingSpec(BaseModel):
    """How a case's output is judged.

    ``output_schema`` is a JSON Schema (Draft 2020-12) describing a *structurally valid*
    answer; it powers the schema-validity metric for every family. ``options`` holds
    per-family grader configuration (e.g. which keys are compared, normalization flags).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    output_schema: dict[str, JsonValue]
    options: dict[str, JsonValue] = Field(default_factory=dict)


class CasePayload(BaseModel):
    """The hashed, semantic content of a case. Only this determines ``case_digest``."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    family: TaskFamily
    prompt: str
    context: tuple[str, ...] = ()
    """Prior turns / setup material (used by context-retention cases)."""
    expected_output: JsonValue
    """The reference answer graded against."""
    grading: GradingSpec
    behavior_class: BehaviorClass = BehaviorClass.NORMAL
    tags: tuple[str, ...] = ()


class TaskCase(BaseModel):
    """A reviewed, content-addressed evaluation case."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["taskcase/v1"] = TASKCASE_V1
    case_id: str
    """Human-readable id, unique within a manifest (e.g. ``"se-001"``)."""
    payload: CasePayload
    review_label: ReviewLabel = ReviewLabel.GENERATED_UNREVIEWED
    provenance: Provenance
    case_digest: str
    """``sha256:…`` over the canonical form of ``payload`` only."""

    @model_validator(mode="after")
    def _verify_digest(self) -> Self:
        expected = compute_case_digest(self.payload)
        if self.case_digest != expected:
            raise ValueError(
                f"case_digest drift for {self.case_id!r}: "
                f"stored={self.case_digest} computed={expected}"
            )
        return self

    @classmethod
    def build(
        cls,
        *,
        case_id: str,
        payload: CasePayload,
        provenance: Provenance,
        review_label: ReviewLabel = ReviewLabel.GENERATED_UNREVIEWED,
    ) -> TaskCase:
        """Construct a case with its ``case_digest`` computed from ``payload``."""
        return cls(
            case_id=case_id,
            payload=payload,
            review_label=review_label,
            provenance=provenance,
            case_digest=compute_case_digest(payload),
        )


def compute_case_digest(payload: CasePayload) -> str:
    """Content digest over the semantic payload of a case."""
    return content_digest(payload)


__all__ = ["CasePayload", "GradingSpec", "TaskCase", "compute_case_digest"]
