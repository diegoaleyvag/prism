"""Invalid manifests and missing cases fail closed."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from prism.engine.executor import ManifestInvalidError, execute_run
from prism.models.manifest import EvaluationManifest
from prism.storage.record_store import RecordStore


def test_unknown_field_is_rejected() -> None:
    with pytest.raises(ValidationError):
        EvaluationManifest.model_validate_json('{"schema_version": "manifest/v1", "nope": 1}')


def test_manifest_digest_drift_is_rejected(manifest: EvaluationManifest) -> None:
    data = manifest.model_dump()
    data["title"] = "tampered without recomputing the digest"
    with pytest.raises(ValidationError, match="manifest_digest drift"):
        EvaluationManifest.model_validate(data)


def test_execute_run_fails_on_missing_case(manifest, cases, profiles) -> None:
    partial = {cid: c for cid, c in cases.items() if cid != "se-001"}
    with pytest.raises(ManifestInvalidError):
        execute_run(manifest, partial, profiles, RecordStore("."), dry_run=True)
