"""Schema drift, digest tamper and name leaks fail closed."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from prism.export.redaction import ProviderNameLeak, assert_no_provider_names
from prism.models.run_record import RunRecord
from prism.models.task_case import TaskCase


def test_unknown_field_on_record_is_rejected(records: list[RunRecord]) -> None:
    data = json.loads(records[0].model_dump_json())
    data["surprise"] = True
    with pytest.raises(ValidationError):
        RunRecord.model_validate(data)


def test_case_digest_tamper_is_rejected(cases: dict[str, TaskCase]) -> None:
    data = json.loads(cases["se-001"].model_dump_json())
    data["case_digest"] = "sha256:" + "0" * 64
    with pytest.raises(ValidationError, match="case_digest drift"):
        TaskCase.model_validate(data)


def test_case_content_change_changes_digest(cases: dict[str, TaskCase]) -> None:
    data = json.loads(cases["se-001"].model_dump_json())
    data["payload"]["prompt"] = data["payload"]["prompt"] + " (edited)"
    # digest no longer matches the (unchanged) stored digest -> fails closed
    with pytest.raises(ValidationError, match="case_digest drift"):
        TaskCase.model_validate(data)


def test_provider_name_leak_is_blocked() -> None:
    with pytest.raises(ProviderNameLeak):
        assert_no_provider_names({"profile": "gpt-4o results", "value": 1})


def test_synthetic_ids_pass_the_guard() -> None:
    # Our profile ids and disclaimers must not trip the guard.
    assert_no_provider_names(
        {"profiles": ["swift-lite", "deep-thinker"], "note": "SIMULATED, not a named model"}
    )
