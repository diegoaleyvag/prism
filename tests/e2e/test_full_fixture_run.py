"""End-to-end, fully offline: fresh run -> immutable records -> reconciled artifacts."""

from __future__ import annotations

import os
from pathlib import Path

from tests.conftest import REPO_ROOT

from prism.dataset.loader import load_cases
from prism.engine.executor import execute_run
from prism.engine.plan import build_default_manifest
from prism.export.artifacts import build_artifacts, write_artifacts
from prism.metrics.compute import compute_report, verify_reconciliation
from prism.metrics.pricing import default_price_table
from prism.models.run_record import compute_record_id
from prism.runners.profiles import load_profiles
from prism.storage.record_store import RecordStore

EXPECTED_ARTIFACTS = {
    "index.json", "overview.json", "families.json", "cases.json",
    "failures.json", "uncertainty.json", "pareto.json", "pricing.json",
}


def _load_repo() -> tuple[dict, dict]:
    cases = load_cases(REPO_ROOT / "data" / "cases")
    profiles = load_profiles(REPO_ROOT / "profiles")
    return cases, profiles


def test_fresh_run_produces_reconciled_artifacts(tmp_path: Path) -> None:
    cases, profiles = _load_repo()
    manifest = build_default_manifest(cases, list(profiles))
    store = RecordStore(tmp_path / "runs")

    summary = execute_run(manifest, cases, profiles, store)
    assert len(summary.records) == 48  # 24 cases x 2 profiles
    assert summary.written == 48

    # Every stored record is content-addressed and read-only.
    run_dir = store.run_dir(manifest)
    stored = list(store.iter_records(run_dir))
    assert len(stored) == 48
    for path in store.iter_record_paths(run_dir):
        assert os.stat(path).st_mode & 0o222 == 0
    for rec in stored:
        assert compute_record_id(rec) == rec.record_id

    price_table = default_price_table()
    report = compute_report(summary.records, cases, price_table, generated_at="fixed")
    assert verify_reconciliation(report) == []

    artifacts = build_artifacts(report, summary.records, cases, price_table)
    written = write_artifacts(artifacts, tmp_path / "artifacts")
    assert {p.name for p in written} == EXPECTED_ARTIFACTS


def test_run_is_reproducible(tmp_path: Path) -> None:
    cases, profiles = _load_repo()
    manifest = build_default_manifest(cases, list(profiles))

    store_a = RecordStore(tmp_path / "a")
    store_b = RecordStore(tmp_path / "b")
    ids_a = sorted(r.record_id for r in execute_run(manifest, cases, profiles, store_a).records)
    ids_b = sorted(r.record_id for r in execute_run(manifest, cases, profiles, store_b).records)
    assert ids_a == ids_b  # deterministic across independent runs


def test_rerun_is_idempotent(tmp_path: Path) -> None:
    cases, profiles = _load_repo()
    manifest = build_default_manifest(cases, list(profiles))
    store = RecordStore(tmp_path / "runs")

    first = execute_run(manifest, cases, profiles, store)
    second = execute_run(manifest, cases, profiles, store)
    assert first.written == 48
    assert second.written == 0 and second.skipped == 48
