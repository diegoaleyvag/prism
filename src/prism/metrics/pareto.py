"""Pareto frontier over quality (max), cost (min) and latency (min).

Pure Python — the point set is tiny (one per profile). Every point is emitted with whether
it sits on the frontier and, if dominated, by whom, so the explorer can show the full trade
space rather than just the winners.
"""

from __future__ import annotations

from dataclasses import dataclass

from prism.metrics.schema import ParetoPoint


@dataclass(frozen=True)
class _Candidate:
    profile_id: str
    quality: float
    cost_usd: float
    latency_p90_ms: float


def _dominates(a: _Candidate, b: _Candidate) -> bool:
    """True if ``a`` is at least as good as ``b`` on all axes and strictly better on one."""
    at_least = a.quality >= b.quality and a.cost_usd <= b.cost_usd and a.latency_p90_ms <= b.latency_p90_ms
    strictly = a.quality > b.quality or a.cost_usd < b.cost_usd or a.latency_p90_ms < b.latency_p90_ms
    return at_least and strictly


def pareto_points(candidates: list[_Candidate]) -> list[ParetoPoint]:
    """Return Pareto points (sorted by profile_id) with frontier membership + dominators."""
    points: list[ParetoPoint] = []
    for c in candidates:
        dominators = sorted(o.profile_id for o in candidates if o is not c and _dominates(o, c))
        points.append(
            ParetoPoint(
                profile_id=c.profile_id,
                quality=c.quality,
                cost_usd=c.cost_usd,
                latency_p90_ms=c.latency_p90_ms,
                on_frontier=not dominators,
                dominated_by=tuple(dominators),
            )
        )
    return sorted(points, key=lambda p: p.profile_id)


__all__ = ["_Candidate", "pareto_points"]
