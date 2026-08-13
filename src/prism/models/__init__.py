"""Versioned Pydantic domain models — the five core interfaces plus their parts."""

from __future__ import annotations

from prism.models.enums import (
    SHOULD_ACT_CLASSES,
    BehaviorClass,
    ReviewLabel,
    ReviewScope,
    RunMode,
    TaskFamily,
    ValidationStatus,
)
from prism.models.manifest import (
    EvaluationManifest,
    ManifestEntry,
    RunnerRef,
    compute_manifest_digest,
)
from prism.models.metric_result import MetricResult, MetricScope
from prism.models.provenance import Provenance
from prism.models.run_record import (
    Measurements,
    RunnerIdentity,
    RunRecord,
    RunResult,
    ValidationOutcome,
    compute_record_id,
)
from prism.models.task_case import (
    CasePayload,
    GradingSpec,
    TaskCase,
    compute_case_digest,
)

__all__ = [
    "SHOULD_ACT_CLASSES",
    "BehaviorClass",
    "CasePayload",
    # manifest
    "EvaluationManifest",
    "GradingSpec",
    "ManifestEntry",
    "Measurements",
    # metric result
    "MetricResult",
    "MetricScope",
    # provenance
    "Provenance",
    "ReviewLabel",
    "ReviewScope",
    "RunMode",
    # run record
    "RunRecord",
    "RunResult",
    "RunnerIdentity",
    "RunnerRef",
    # task case
    "TaskCase",
    # enums
    "TaskFamily",
    "ValidationOutcome",
    "ValidationStatus",
    "compute_case_digest",
    "compute_manifest_digest",
    "compute_record_id",
]
