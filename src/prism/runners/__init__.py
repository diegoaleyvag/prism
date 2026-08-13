"""Runner adapters: deterministic fixture replay (default) + guarded provider scaffold."""

from __future__ import annotations

from prism.runners.base import BaseRunner, Runner, RunnerOutput
from prism.runners.fixture import FixtureReplayRunner, estimate_tokens
from prism.runners.profiles import (
    DefaultBehavior,
    FixtureProfile,
    ProfileResponse,
    TokenModel,
    build_profile,
    compute_profile_digest,
    load_profile,
    load_profiles,
)
from prism.runners.provider import (
    ProviderDisabledError,
    ProviderRunner,
    ci_detected,
    provider_enabled,
)

__all__ = [
    "BaseRunner",
    "DefaultBehavior",
    "FixtureProfile",
    "FixtureReplayRunner",
    "ProfileResponse",
    "ProviderDisabledError",
    "ProviderRunner",
    "Runner",
    "RunnerOutput",
    "TokenModel",
    "build_profile",
    "ci_detected",
    "compute_profile_digest",
    "estimate_tokens",
    "load_profile",
    "load_profiles",
    "provider_enabled",
]
