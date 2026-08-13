"""Duplicate case ids in a manifest fail closed."""

from __future__ import annotations

import pytest

from prism.models.enums import TaskFamily
from prism.models.manifest import EvaluationManifest, ManifestEntry, RunnerRef
from prism.models.task_case import TaskCase


def test_duplicate_case_id_rejected(cases: dict[str, TaskCase]) -> None:
    se = cases["se-001"]
    entries = (
        ManifestEntry(case_id="se-001", case_digest=se.case_digest),
        ManifestEntry(case_id="se-001", case_digest=se.case_digest),  # duplicate
    )
    with pytest.raises(ValueError, match="duplicate case_id"):
        EvaluationManifest.build(
            manifest_id="m", manifest_version="1.0.0", title="t",
            families=(TaskFamily.STRUCTURED_EXTRACTION,),
            runners=(RunnerRef(runner_kind="fixture_replay", profile="deep-thinker"),),
            cases=entries, metrics=("task_success_rate",), seed=1, created_by="t",
        )
