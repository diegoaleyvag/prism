"""On any subset of the run, aggregates still reconcile with case-level data."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from prism.dataset.generate import build_cases
from prism.metrics.compute import compute_report, verify_reconciliation

_CASE_IDS = sorted(c.case_id for c in build_cases())


@given(subset=st.sets(st.sampled_from(_CASE_IDS), min_size=1))
def test_any_case_subset_reconciles(records, cases, price_table, subset) -> None:
    recs = [r for r in records if r.case_id in subset]
    report = compute_report(recs, cases, price_table, generated_at="fixed")
    assert verify_reconciliation(report) == []
    for prof in report.profiles:
        fam_sum = sum(f.task_success.denominator or 0 for f in prof.families)
        assert fam_sum == prof.aggregate.task_success.denominator == len(subset)
