"""The provider adapter is impossible to trigger by accident, and never in CI."""

from __future__ import annotations

import sys

import pytest

from prism.engine.executor import ManifestInvalidError, execute_run
from prism.models.enums import TaskFamily
from prism.models.manifest import EvaluationManifest, ManifestEntry, RunnerRef
from prism.runners.provider import ProviderDisabledError, ProviderRunner, ci_detected
from prism.storage.record_store import RecordStore


def test_provider_disabled_without_env_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PRISM_ENABLE_PROVIDER", raising=False)
    monkeypatch.delenv("CI", raising=False)
    with pytest.raises(ProviderDisabledError):
        ProviderRunner("acme-llm", explicit_enable=True)


def test_provider_hard_disabled_in_ci(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CI", "true")
    monkeypatch.setenv("PRISM_ENABLE_PROVIDER", "1")
    assert ci_detected() is True
    with pytest.raises(ProviderDisabledError):
        ProviderRunner("acme-llm", explicit_enable=True)


_CI_KEYS = ("CI", "PRISM_CI", "GITHUB_ACTIONS", "GITLAB_CI", "BUILDKITE")


def test_provider_run_raises_even_when_fully_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in _CI_KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("PRISM_ENABLE_PROVIDER", "1")
    runner = ProviderRunner("acme-llm", explicit_enable=True)
    with pytest.raises(NotImplementedError):
        runner.run(None)  # type: ignore[arg-type]


def test_provider_manifest_blocked_without_guard(cases, profiles) -> None:
    entries = tuple(
        ManifestEntry(case_id=cid, case_digest=cases[cid].case_digest) for cid in sorted(cases)
    )
    manifest = EvaluationManifest.build(
        manifest_id="m", manifest_version="1.0.0", title="t", families=tuple(TaskFamily),
        runners=(RunnerRef(runner_kind="provider", provider_ref="acme-llm"),),
        cases=entries, metrics=("task_success_rate",), seed=1, created_by="t",
    )
    with pytest.raises(ManifestInvalidError):
        execute_run(manifest, cases, profiles, RecordStore("."), dry_run=True, allow_provider=False)


def test_no_provider_sdk_imported() -> None:
    for banned in ("openai", "anthropic", "cohere", "google.generativeai"):
        assert banned not in sys.modules
