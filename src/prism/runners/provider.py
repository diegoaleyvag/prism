"""Provider adapter scaffold — disabled by default, impossible to trigger in CI.

This module ships **no** network code. It exists to prove the runner boundary and to make
the "how a live provider would plug in" story concrete. Enabling it requires clearing four
independent locks; even fully enabled, :meth:`ProviderRunner.run` raises, because no live
provider I/O is shipped in this release. See ``docs/adr/0002-runner-boundary.md``.
"""

from __future__ import annotations

import os

from prism.models.enums import RunMode
from prism.models.run_record import RunnerIdentity
from prism.models.task_case import TaskCase
from prism.runners.base import BaseRunner, RunnerOutput

_CI_ENV_KEYS = ("CI", "PRISM_CI", "GITHUB_ACTIONS", "GITLAB_CI", "BUILDKITE")
_TRUTHY = frozenset({"1", "true", "yes", "on"})


class ProviderDisabledError(RuntimeError):
    """Raised when a provider runner is constructed without clearing every lock."""


def ci_detected() -> bool:
    """True if any well-known CI environment variable is set truthy."""
    return any(os.environ.get(k, "").strip().lower() in _TRUTHY for k in _CI_ENV_KEYS)


def provider_enabled(*, explicit_enable: bool) -> bool:
    """Whether *all* provider locks are cleared. Never true under CI."""
    if ci_detected():
        return False
    if os.environ.get("PRISM_ENABLE_PROVIDER") != "1":
        return False
    return explicit_enable


class ProviderRunner(BaseRunner):
    """Scaffold for a live provider adapter. Construction is guarded; :meth:`run` raises."""

    def __init__(self, provider_ref: str, *, explicit_enable: bool = False) -> None:
        if ci_detected():
            raise ProviderDisabledError(
                "Provider runners are hard-disabled under CI; unset CI env vars to run locally."
            )
        if os.environ.get("PRISM_ENABLE_PROVIDER") != "1":
            raise ProviderDisabledError(
                "Provider runners require the env gate PRISM_ENABLE_PROVIDER=1."
            )
        if not explicit_enable:
            raise ProviderDisabledError(
                "Provider runners require the explicit --enable-provider flag."
            )
        self.provider_ref = provider_ref
        self.mode = RunMode.PROVIDER_LIVE
        self.identity = RunnerIdentity(
            runner_kind="provider",
            runner_name=provider_ref,
            runner_version="scaffold",
            config_digest="sha256:provider-scaffold",
        )

    def run(self, case: TaskCase) -> RunnerOutput:
        raise NotImplementedError(
            "The provider adapter is a scaffold; no live provider calls are shipped in this "
            "release. Prism publishes only deterministic fixture simulations."
        )


__all__ = ["ProviderDisabledError", "ProviderRunner", "ci_detected", "provider_enabled"]
