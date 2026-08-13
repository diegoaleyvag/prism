"""Seeded percentile-bootstrap confidence intervals for rate metrics, with a small-n guardrail.

The guardrail is the point: with 24 cases split by profile and family, most per-family
denominators are tiny. Rather than emit a misleadingly tight interval, Prism **suppresses**
the CI when ``n`` is small and always surfaces the denominator. For degenerate proportions
(0 or all successes) it reports a rule-of-three bound instead of a zero-width interval.

Bootstrap draws are exploited in closed form: resampling ``n`` Bernoulli outcomes with
replacement makes the resample success count ``~ Binomial(n, k/n)``. Seeding is derived from
the metric's stable identity, so every interval is independently reproducible and
order-independent.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

import numpy as np


@dataclass(frozen=True)
class BootstrapConfig:
    n_hard: int = 10
    """Below this denominator the CI is suppressed as unreliable."""
    n_stable: int = 30
    """At/above this denominator the CI is marked reliable."""
    resamples: int = 10_000
    level: float = 0.95
    base_seed: int = 0


@dataclass(frozen=True)
class RateCIResult:
    numerator: int
    denominator: int
    rate: float | None
    ci_low: float | None
    ci_high: float | None
    ci_reliable: bool
    ci_flags: tuple[str, ...]
    method: str
    resamples: int
    level: float
    seed: int | None
    rule_of_three: dict[str, float] = field(default_factory=dict)
    """Optional {'kind': 'upper'|'lower', 'bound': x} for degenerate proportions."""


def derive_seed(*parts: str, base_seed: int = 0) -> int:
    """Deterministically derive a 64-bit seed from stable string parts + base seed."""
    joined = "\x1f".join((*parts, str(base_seed))).encode("utf-8")
    return int.from_bytes(hashlib.blake2b(joined, digest_size=8).digest(), "big")


def _percentile_ci(numerator: int, denominator: int, seed: int, cfg: BootstrapConfig) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    p = numerator / denominator
    successes = rng.binomial(denominator, p, size=cfg.resamples)
    rates = successes / denominator
    alpha = 1.0 - cfg.level
    lo, hi = np.quantile(rates, [alpha / 2.0, 1.0 - alpha / 2.0], method="linear")
    return float(lo), float(hi)


def bootstrap_rate_ci(
    numerator: int,
    denominator: int,
    *,
    seed_parts: tuple[str, ...],
    config: BootstrapConfig | None = None,
) -> RateCIResult:
    """Compute a rate CI with the small-n guardrail applied. Deterministic given inputs."""
    cfg = config or BootstrapConfig()
    method = "percentile_bootstrap"

    if denominator == 0:
        return RateCIResult(
            numerator=0, denominator=0, rate=None, ci_low=None, ci_high=None,
            ci_reliable=False, ci_flags=("empty_denominator",), method=method,
            resamples=cfg.resamples, level=cfg.level, seed=None,
        )

    rate = numerator / denominator
    flags: list[str] = []
    low_n = denominator < cfg.n_stable
    if low_n:
        flags.append("low_n" if denominator >= cfg.n_hard else "n_below_hard_threshold")

    # Degenerate proportion: a bootstrap interval collapses to zero width — misleading.
    if numerator == 0 or numerator == denominator:
        rot: dict[str, float] = {}
        bound = 3.0 / denominator  # rule of three
        if numerator == 0:
            rot = {"kind_upper": round(bound, 6)}
        else:
            rot = {"kind_lower": round(1.0 - bound, 6)}
        return RateCIResult(
            numerator=numerator, denominator=denominator, rate=rate, ci_low=None, ci_high=None,
            ci_reliable=False, ci_flags=("degenerate_proportion", *flags), method=method,
            resamples=cfg.resamples, level=cfg.level, seed=None, rule_of_three=rot,
        )

    # Hard suppression below the hard threshold.
    if denominator < cfg.n_hard:
        return RateCIResult(
            numerator=numerator, denominator=denominator, rate=rate, ci_low=None, ci_high=None,
            ci_reliable=False, ci_flags=tuple(flags), method=method,
            resamples=cfg.resamples, level=cfg.level, seed=None,
        )

    seed = derive_seed(*seed_parts, base_seed=cfg.base_seed)
    lo, hi = _percentile_ci(numerator, denominator, seed, cfg)
    return RateCIResult(
        numerator=numerator, denominator=denominator, rate=rate, ci_low=lo, ci_high=hi,
        ci_reliable=denominator >= cfg.n_stable, ci_flags=tuple(flags), method=method,
        resamples=cfg.resamples, level=cfg.level, seed=seed,
    )


__all__ = ["BootstrapConfig", "RateCIResult", "bootstrap_rate_ci", "derive_seed"]
