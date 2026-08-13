"""Shared test fixtures + an offline guarantee.

An autouse fixture blocks all outbound network so any accidental live call fails loudly —
the whole suite must run on a fresh checkout with no network. A Hypothesis ``ci`` profile
disables deadlines so property tests stay deterministic under load.
"""

from __future__ import annotations

import socket
from collections.abc import Iterator
from pathlib import Path

import pytest
from hypothesis import HealthCheck, settings

from prism.dataset.generate import build_cases
from prism.dataset.profiles_gen import build_profiles
from prism.engine.plan import build_default_manifest
from prism.metrics.pricing import default_price_table
from prism.models.task_case import TaskCase
from prism.runners.profiles import FixtureProfile

settings.register_profile(
    "ci",
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
settings.load_profile("ci")

REPO_ROOT = Path(__file__).resolve().parents[1]


class NetworkBlockedError(RuntimeError):
    """Raised if any test attempts an outbound network connection."""


@pytest.fixture(autouse=True)
def _block_network(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    def guard(*_args: object, **_kwargs: object) -> None:
        raise NetworkBlockedError("network is disabled during tests")

    monkeypatch.setattr(socket.socket, "connect", guard)
    monkeypatch.setattr(socket.socket, "connect_ex", guard)
    monkeypatch.setattr(socket, "create_connection", guard)
    yield


@pytest.fixture(scope="session")
def cases() -> dict[str, TaskCase]:
    return {c.case_id: c for c in build_cases()}


@pytest.fixture(scope="session")
def profiles() -> dict[str, FixtureProfile]:
    return build_profiles()


@pytest.fixture
def manifest(cases: dict[str, TaskCase], profiles: dict[str, FixtureProfile]):
    return build_default_manifest(cases, list(profiles))


@pytest.fixture(scope="session")
def price_table():
    return default_price_table()


@pytest.fixture
def records(manifest, cases, profiles):
    """Graded records for the full foundation run (dry-run, not persisted)."""
    from prism.engine.executor import execute_run
    from prism.storage.record_store import RecordStore

    summary = execute_run(manifest, cases, profiles, RecordStore(Path(".")), dry_run=True)
    return summary.records
