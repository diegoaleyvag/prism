"""Report models: per-group metrics, Pareto points, and the top-level MetricReport.

Every rate is a :class:`~prism.models.metric_result.MetricResult` carrying its numerator,
denominator, ``display`` string and (guardrailed) CI, plus the record ids that formed its
denominator and the passing subset — so every aggregate links to its underlying cases.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue

from prism.models.enums import ReviewScope, TaskFamily
from prism.models.metric_result import MetricResult
from prism.schema_versions import METRICREPORT_V1


class LatencyBlock(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    n: int
    p50_ms: float
    p90_ms: float
    p95_ms: float
    p99_ms: float
    min_ms: int
    max_ms: int
    mean_ms: float


class TokenBlock(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    n: int
    input_sum: int
    output_sum: int
    total_sum: int
    input_mean: float
    output_mean: float


class CostBlock(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    n: int
    total_micro_usd: int
    mean_micro_usd: float
    total_usd: float
    mean_usd: float
    price_table_id: str
    price_table_hash: str
    simulated: Literal[True] = True


class GroupMetrics(BaseModel):
    """Metrics for one (profile, family) group, or one (profile) aggregate (family=None)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    scope: Literal["family", "aggregate"]
    profile_id: str
    family: TaskFamily | None = None
    n: int
    task_success: MetricResult
    schema_validity: MetricResult
    correct_escalation: MetricResult | None = None
    over_refusal: MetricResult | None = None
    latency: LatencyBlock
    tokens: TokenBlock
    cost: CostBlock
    member_record_ids: tuple[str, ...]
    passed_record_ids: tuple[str, ...]


class ProfileReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    profile_id: str
    profile_digest: str
    aggregate: GroupMetrics
    families: tuple[GroupMetrics, ...]


class ParetoPoint(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    profile_id: str
    quality: float
    """Task-success rate (higher is better)."""
    cost_usd: float
    """Mean estimated cost per case (lower is better)."""
    latency_p90_ms: float
    """p90 latency (lower is better)."""
    on_frontier: bool
    dominated_by: tuple[str, ...]


class MetricReport(BaseModel):
    """The full, reconcilable metric report for a run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["metricreport/v1"] = METRICREPORT_V1
    prism_version: str
    generated_at: str
    manifest_id: str
    manifest_digest: str
    review_scope: ReviewScope
    excluded_count: int
    record_set_hash: str
    price_table_id: str
    price_table_hash: str
    simulated: Literal[True] = True
    guardrail: dict[str, JsonValue] = Field(default_factory=dict)
    profiles: tuple[ProfileReport, ...]
    pareto: tuple[ParetoPoint, ...]


__all__ = [
    "CostBlock",
    "GroupMetrics",
    "LatencyBlock",
    "MetricReport",
    "ParetoPoint",
    "ProfileReport",
    "TokenBlock",
]
