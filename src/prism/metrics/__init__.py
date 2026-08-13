"""Metrics: reconcilable rate/latency/token/cost computation with bootstrap CIs."""

from __future__ import annotations

from prism.metrics.compute import build_fact_frame, compute_report, verify_reconciliation
from prism.metrics.pareto import pareto_points
from prism.metrics.pricing import (
    PriceTable,
    default_price_table,
    load_price_table,
    write_price_table,
)
from prism.metrics.schema import (
    CostBlock,
    GroupMetrics,
    LatencyBlock,
    MetricReport,
    ParetoPoint,
    ProfileReport,
    TokenBlock,
)

__all__ = [
    "CostBlock",
    "GroupMetrics",
    "LatencyBlock",
    "MetricReport",
    "ParetoPoint",
    "PriceTable",
    "ProfileReport",
    "TokenBlock",
    "build_fact_frame",
    "compute_report",
    "default_price_table",
    "load_price_table",
    "pareto_points",
    "verify_reconciliation",
    "write_price_table",
]
