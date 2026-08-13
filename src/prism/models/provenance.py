"""Provenance and ownership metadata attached to every case and fixture profile.

Provenance is an *annotation*: it is deliberately excluded from content identity so that
re-licensing or re-attributing a case does not change its digest. Prism is synthetic-only,
so ``synthetic`` defaults to ``True`` and is validated to stay that way.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class Provenance(BaseModel):
    """Where a synthetic artifact came from, who owns it, and under what license."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source: str
    """Origin tag, e.g. ``"synthetic:prism-generator"``."""
    generator: str | None = None
    """Generator name + version, when machine-produced."""
    synthetic: bool = True
    """Prism publishes only synthetic content; validated to be ``True``."""
    license: str
    """SPDX identifier or ``"proprietary-owned"``."""
    owner: str
    created_at: datetime
    """Authoring timestamp (annotation only; never hashed into identity)."""
    origin_note: str | None = None
    """Human note asserting the content is original and not exam-derived."""
    notes: str | None = None

    @field_validator("synthetic")
    @classmethod
    def _must_be_synthetic(cls, v: bool) -> bool:
        if v is not True:
            raise ValueError("Prism artifacts must be synthetic (synthetic=True)")
        return v


__all__ = ["Provenance"]
