"""Prism — a reproducible workbench for evaluating task-specific model tradeoffs.

Prism is educational, synthetic and transparent. Every result in this release is a
deterministic *simulation* produced by fixture profiles; it is never a measurement of
any named model or provider. See ``docs/LIMITATIONS.md`` for the non-claims.
"""

from __future__ import annotations

__version__ = "0.1.0"
"""Single source of truth for the code version stamped into every RunRecord."""

__all__ = ["__version__"]
