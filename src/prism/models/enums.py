"""Enumerations shared across the domain model.

``StrEnum`` gives clean JSON values and exhaustiveness checking. Every enum value is a
stable part of the on-disk contract: renaming one is a breaking schema change.
"""

from __future__ import annotations

from enum import StrEnum


class TaskFamily(StrEnum):
    """The four task families evaluated by the foundation release."""

    STRUCTURED_EXTRACTION = "structured_extraction"
    TOOL_SELECTION = "tool_selection"
    CONTEXT_RETENTION = "context_retention"
    SAFETY_ESCALATION = "safety_escalation"


class ReviewLabel(StrEnum):
    """Owner-review status of a case. Release metrics include only ``owner_reviewed``."""

    GENERATED_UNREVIEWED = "generated_unreviewed"
    OWNER_REVIEWED = "owner_reviewed"


class BehaviorClass(StrEnum):
    """What the *correct* behavior for a case is — drives abstention denominators.

    ``normal`` cases must produce a substantive answer; refusing one is over-refusal.
    The ``should_*`` classes form the population over which correct-escalation is scored.
    """

    NORMAL = "normal"
    SHOULD_ABSTAIN = "should_abstain"
    SHOULD_ESCALATE = "should_escalate"
    SHOULD_REFUSE = "should_refuse"


class RunMode(StrEnum):
    """Execution mode recorded on every run. Fixture and live are never conflated."""

    FIXTURE_REPLAY = "fixture_replay"
    PROVIDER_LIVE = "provider_live"


class ValidationStatus(StrEnum):
    """Outcome of grading a single run."""

    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


class ReviewScope(StrEnum):
    """Which cases a metric report covers."""

    RELEASE = "release"  # owner_reviewed only
    FULL = "full"  # every case, including generated_unreviewed


SHOULD_ACT_CLASSES: frozenset[BehaviorClass] = frozenset(
    {BehaviorClass.SHOULD_ABSTAIN, BehaviorClass.SHOULD_ESCALATE, BehaviorClass.SHOULD_REFUSE}
)
"""Behavior classes that belong to the correct-abstention/escalation denominator."""


__all__ = [
    "SHOULD_ACT_CLASSES",
    "BehaviorClass",
    "ReviewLabel",
    "ReviewScope",
    "RunMode",
    "TaskFamily",
    "ValidationStatus",
]
