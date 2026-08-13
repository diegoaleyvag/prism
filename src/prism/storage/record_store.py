"""Append-only, content-addressed storage for run records.

Immutability is enforced in layers, since a local filesystem is not WORM: the filename
*is* the ``record_id`` hash; records are written once and chmod'd read-only; re-writing an
existing record is a no-op only if its content still hashes to the same id (else it is
tamper and raises). ``prism verify`` re-checks all of this from disk.

Layout::

    <root>/<manifest_id>/<manifest_digest[:12]>/
        manifest.snapshot.json          (0o444)
        profiles/<profile_id>.json       (0o444)
        records/<ab>/<record_hex>.json   (0o444, sharded by first 2 hex)
        index.jsonl                      (append-only)
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterator, Mapping
from pathlib import Path

from prism.models.manifest import EvaluationManifest
from prism.models.run_record import RunRecord, compute_record_id
from prism.runners.profiles import FixtureProfile


class IntegrityError(RuntimeError):
    """Raised when stored content does not match its content address."""


def digest_hex(digest: str) -> str:
    """Return the bare hex of a ``sha256:<hex>`` digest string."""
    prefix, _, hexpart = digest.partition(":")
    if prefix != "sha256" or len(hexpart) != 64:
        raise ValueError(f"not a sha256 digest string: {digest!r}")
    return hexpart


def _write_readonly(target: Path, data: bytes) -> None:
    """Atomically write ``data`` to ``target`` and mark it read-only."""
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + ".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(tmp, target)
    os.chmod(target, 0o444)


class RecordStore:
    """Binds a ``runs/`` root and reads/writes immutable records beneath it."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def run_dir(self, manifest: EvaluationManifest) -> Path:
        return self.root / manifest.manifest_id / digest_hex(manifest.manifest_digest)[:12]

    def initialize_run(
        self, manifest: EvaluationManifest, profiles: Mapping[str, FixtureProfile]
    ) -> Path:
        """Create the run directory and freeze read-only snapshots of inputs.

        Idempotent: re-initializing verifies the existing snapshots are byte-identical.
        """
        run_dir = self.run_dir(manifest)
        (run_dir / "records").mkdir(parents=True, exist_ok=True)
        (run_dir / "profiles").mkdir(parents=True, exist_ok=True)

        self._freeze_snapshot(
            run_dir / "manifest.snapshot.json",
            manifest.model_dump_json(indent=2).encode("utf-8"),
        )
        for profile_id, profile in profiles.items():
            self._freeze_snapshot(
                run_dir / "profiles" / f"{profile_id}.json",
                profile.model_dump_json(indent=2).encode("utf-8"),
            )
        index = run_dir / "index.jsonl"
        if not index.exists():
            index.touch()
        return run_dir

    @staticmethod
    def _freeze_snapshot(path: Path, data: bytes) -> None:
        if path.exists():
            if path.read_bytes() != data:
                raise IntegrityError(f"snapshot changed under an existing run: {path}")
            return
        _write_readonly(path, data)

    def _record_path(self, run_dir: Path, record: RunRecord) -> Path:
        hexid = digest_hex(record.record_id)
        return run_dir / "records" / hexid[:2] / f"{hexid}.json"

    def write_record(self, run_dir: Path, record: RunRecord) -> tuple[Path, bool]:
        """Write ``record`` immutably. Returns ``(path, written)``.

        ``written`` is ``False`` when an identical record already exists (idempotent
        re-run). Because the filename is the content address, an existing file at the same
        path with matching integrity *is* the same record — only volatile timestamps may
        differ, and the first write is authoritative.
        """
        target = self._record_path(run_dir, record)
        if target.exists():
            existing = RunRecord.model_validate_json(target.read_text(encoding="utf-8"))
            if compute_record_id(existing) != record.record_id:
                raise IntegrityError(
                    f"stored record at {target} does not match its content address"
                )
            return target, False

        _write_readonly(target, record.model_dump_json(indent=2).encode("utf-8"))
        self._append_index(run_dir, record)
        return target, True

    @staticmethod
    def _append_index(run_dir: Path, record: RunRecord) -> None:
        line = json.dumps(
            {
                "record_id": record.record_id,
                "case_id": record.case_id,
                "runner_name": record.runner.runner_name,
                "finished_at": record.finished_at.isoformat(),
            },
            sort_keys=True,
        )
        with (run_dir / "index.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")

    def iter_records(self, run_dir: Path) -> Iterator[RunRecord]:
        """Yield every stored record under ``run_dir`` in sorted path order."""
        records_dir = Path(run_dir) / "records"
        for path in sorted(records_dir.rglob("*.json")):
            yield RunRecord.model_validate_json(path.read_text(encoding="utf-8"))

    def iter_record_paths(self, run_dir: Path) -> Iterator[Path]:
        yield from sorted((Path(run_dir) / "records").rglob("*.json"))


__all__ = ["IntegrityError", "RecordStore", "digest_hex"]
