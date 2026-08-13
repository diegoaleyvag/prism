"""Models round-trip through JSON without changing their content identity."""

from __future__ import annotations

from prism.models.manifest import EvaluationManifest
from prism.models.run_record import RunRecord
from prism.models.task_case import TaskCase


def test_cases_roundtrip_preserve_digest(cases: dict[str, TaskCase]) -> None:
    for case in cases.values():
        again = TaskCase.model_validate_json(case.model_dump_json())
        assert again.case_digest == case.case_digest
        assert again == case


def test_manifest_roundtrips(manifest: EvaluationManifest) -> None:
    again = EvaluationManifest.model_validate_json(manifest.model_dump_json())
    assert again.manifest_digest == manifest.manifest_digest
    assert again == manifest


def test_records_roundtrip_preserve_record_id(records: list[RunRecord]) -> None:
    for record in records:
        again = RunRecord.model_validate_json(record.model_dump_json())
        assert again.record_id == record.record_id
        assert again == record
