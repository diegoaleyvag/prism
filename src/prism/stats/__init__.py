"""Statistics: seeded bootstrap confidence intervals with a small-n guardrail."""

from __future__ import annotations

from prism.stats.bootstrap import (
    BootstrapConfig,
    RateCIResult,
    bootstrap_rate_ci,
    derive_seed,
)

__all__ = ["BootstrapConfig", "RateCIResult", "bootstrap_rate_ci", "derive_seed"]
