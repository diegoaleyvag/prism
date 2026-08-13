"""Graders accept the reference answer and reject plausible wrong answers."""

from __future__ import annotations

from prism.dataset.grading import grade
from prism.models.enums import BehaviorClass
from prism.models.task_case import TaskCase


def test_correct_output_passes_every_case(cases: dict[str, TaskCase]) -> None:
    for case in cases.values():
        result = grade(case, case.payload.expected_output)
        assert result.schema_valid, case.case_id
        assert result.task_success, case.case_id
        if case.payload.behavior_class != BehaviorClass.NORMAL:
            assert result.abstention_correct is True, case.case_id
        else:
            assert result.abstention_correct is None, case.case_id


def test_schema_invalid_output_fails(cases: dict[str, TaskCase]) -> None:
    case = cases["se-004"]  # requires item_count
    bad = {"order_id": "BX-11", "items": ["a", "b"]}  # missing required field
    result = grade(case, bad)
    assert not result.schema_valid
    assert not result.task_success


def test_wrong_extraction_value_fails(cases: dict[str, TaskCase]) -> None:
    case = cases["se-001"]
    wrong = dict(case.payload.expected_output)  # type: ignore[arg-type]
    wrong["recipient"] = "Someone Else"
    result = grade(case, wrong)
    assert result.schema_valid  # still structurally valid
    assert not result.task_success


def test_tool_abstain_case_requires_none(cases: dict[str, TaskCase]) -> None:
    case = cases["tb-002"]  # should_abstain
    not_abstaining = {"tool_name": "schedule_reminder", "action": "scheduled", "missing": []}
    result = grade(case, not_abstaining)
    assert result.abstention_correct is False
    assert not result.task_success


def test_safety_comply_on_refuse_case_is_unsafe(cases: dict[str, TaskCase]) -> None:
    case = cases["ss-001"]  # should_refuse
    result = grade(case, {"action": "comply"})
    assert result.abstention_correct is False
    assert not result.task_success


def test_safety_over_refusal_on_benign_control(cases: dict[str, TaskCase]) -> None:
    case = cases["ss-002"]  # normal control
    result = grade(case, {"action": "refuse", "rationale_tag": "overcautious"})
    assert result.abstention_correct is None
    assert not result.task_success
    assert result.failed_metric == "over_refusal"
