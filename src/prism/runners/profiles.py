"""Fixture profiles: the data behind deterministic simulated runners.

A profile is a canned oracle. For each case (keyed by ``case_digest``) it stores the exact
output the simulated model returns, plus optional token/latency overrides. Two profiles with
intentionally different accuracy/latency tradeoffs let the workbench demonstrate the
"good enough" question without any live provider. Profiles carry *no* pricing — cost is a
downstream estimate from a versioned price table.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

from prism.digest import content_digest
from prism.models.provenance import Provenance
from prism.schema_versions import PROFILE_V1


class TokenModel(BaseModel):
    """How token counts are estimated from text when a response gives no override."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    chars_per_token: int = Field(default=4, ge=1)


class ProfileResponse(BaseModel):
    """The canned answer this profile returns for one case."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    output: JsonValue
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    latency_ms: int | None = Field(default=None, ge=0)
    note: str | None = None
    """Optional human note, e.g. why this profile answers this case wrongly."""


class DefaultBehavior(BaseModel):
    """Fallback used for a case absent from ``responses`` (kept minimal and explicit)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    strategy: Literal["empty", "canned_refusal"] = "empty"
    canned_output: JsonValue = None


class FixtureProfile(BaseModel):
    """A deterministic simulated runner, expressed as data."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["profile/v1"] = PROFILE_V1
    profile_id: str
    profile_version: str
    title: str
    description: str
    base_latency_ms: int = Field(ge=0)
    latency_jitter_ms: int = Field(ge=0)
    token_model: TokenModel = Field(default_factory=TokenModel)
    responses: dict[str, ProfileResponse]
    default_behavior: DefaultBehavior = Field(default_factory=DefaultBehavior)
    provenance: Provenance
    profile_digest: str

    @model_validator(mode="after")
    def _verify_digest(self) -> Self:
        expected = compute_profile_digest(self)
        if self.profile_digest != expected:
            raise ValueError(
                f"profile_digest drift for {self.profile_id!r}: "
                f"stored={self.profile_digest} computed={expected}"
            )
        return self


# Fields excluded from a profile's identity: the digest itself, and provenance (an
# annotation — like case provenance — so re-attributing a profile does not change its id,
# and its authoring timestamp never reaches the datetime-free canonical form).
_PROFILE_NON_IDENTITY: frozenset[str] = frozenset({"profile_digest", "provenance"})


def compute_profile_digest(profile: FixtureProfile) -> str:
    """Content digest over the profile's behavioral identity (excludes annotations)."""
    body = profile.model_dump(exclude=set(_PROFILE_NON_IDENTITY))
    return content_digest(body)


def build_profile(body: dict[str, JsonValue]) -> FixtureProfile:
    """Construct a profile from a body dict, computing ``profile_digest``.

    ``body`` must contain every field except ``profile_digest``. The digest is computed over
    the identity fields only (provenance excluded) so a round-trip through
    :func:`compute_profile_digest` reconciles.
    """
    identity = {k: v for k, v in body.items() if k not in _PROFILE_NON_IDENTITY}
    digest = content_digest(identity)
    return FixtureProfile.model_validate({**body, "profile_digest": digest})


def load_profile(path: Path) -> FixtureProfile:
    """Load and validate a single profile JSON file (fails closed on drift)."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return FixtureProfile.model_validate(data)


def load_profiles(directory: Path) -> dict[str, FixtureProfile]:
    """Load every ``*.profile.json`` in ``directory``, keyed by ``profile_id``."""
    out: dict[str, FixtureProfile] = {}
    for path in sorted(Path(directory).glob("*.profile.json")):
        profile = load_profile(path)
        if profile.profile_id in out:
            raise ValueError(f"duplicate profile_id {profile.profile_id!r} in {directory}")
        out[profile.profile_id] = profile
    return out


__all__ = [
    "DefaultBehavior",
    "FixtureProfile",
    "ProfileResponse",
    "TokenModel",
    "build_profile",
    "compute_profile_digest",
    "load_profile",
    "load_profiles",
]
