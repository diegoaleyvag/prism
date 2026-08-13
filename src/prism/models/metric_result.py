"""The metric result: a single versioned metric value with its uncertainty and denominator.

``MetricResult`` is the core interface for one computed number. It always carries the
denominator (and, for rates, numerator + ``display`` like ``"4 / 6"``) so no value is ever
shown without the sample it came from. Confidence-interval fields follow the small-n
guardrail: when ``n`` is too small the interval is suppressed (``ci_low``/``ci_high`` are
``None``) and ``ci_reliable`` is ``False`` with explanatory ``ci_flags``.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue

from prism.models.enums import TaskFamily
from prism.schema_versions import METRICRESULT_V1

MetricScope = Literal["family", "aggregate"]


class MetricResult(BaseModel):
    """One metric value, scoped to a profile and (optionally) a family."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["metricresult/v1"] = METRICRESULT_V1
    metric_id: str
    """Stable id, e.g. ``"task_success_rate"``, ``"p90_latency_ms"``, ``"cost_usd_mean"``."""
    metric_version: str = "1"
    scope: MetricScope
    profile_id: str
    family: TaskFamily | None = None
    """``None`` marks a per-profile aggregate across families."""

    value: float | int | bool | str | None = None
    unit: str | None = None

    # Rate/denominator context (present for rate metrics).
    numerator: int | None = None
    denominator: int | None = None
    display: str | None = None

    # Uncertainty (bootstrap). Suppressed when the small-n guardrail fires.
    ci_low: float | None = None
    ci_high: float | None = None
    ci_reliable: bool | None = None
    ci_flags: tuple[str, ...] = ()
    method: str | None = None
    seed: int | None = None

    # Provenance + any auxiliary numbers (thresholds, B, level, rule-of-three bound).
    computed_from: tuple[str, ...] = ()
    """Record ids that fed this metric (drill-down / reconciliation)."""
    extra: dict[str, JsonValue] = Field(default_factory=dict)


__all__ = ["MetricResult", "MetricScope"]
