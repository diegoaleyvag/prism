"""Aggregates reconcile with case-level data (drill-down integrity)."""

from __future__ import annotations

from prism.metrics.compute import compute_report, verify_reconciliation


def test_report_reconciles(records, cases, price_table) -> None:
    report = compute_report(records, cases, price_table, generated_at="fixed")
    assert verify_reconciliation(report) == []


def test_family_denominators_sum_to_aggregate(records, cases, price_table) -> None:
    report = compute_report(records, cases, price_table, generated_at="fixed")
    for prof in report.profiles:
        fam_total = sum(f.task_success.denominator or 0 for f in prof.families)
        assert fam_total == prof.aggregate.task_success.denominator == 24


def test_passed_ids_subset_of_members_and_rate_matches(records, cases, price_table) -> None:
    report = compute_report(records, cases, price_table, generated_at="fixed")
    for prof in report.profiles:
        for grp in (prof.aggregate, *prof.families):
            m = grp.task_success
            passed = set(m.extra["passed_record_ids"])  # type: ignore[arg-type]
            assert passed <= set(m.computed_from)
            assert m.numerator == len(passed)
            assert abs(float(m.value) - m.numerator / m.denominator) < 1e-9  # type: ignore[arg-type]


def test_drill_down_ids_are_content_addresses(records, cases, price_table) -> None:
    report = compute_report(records, cases, price_table, generated_at="fixed")
    known = {r.record_id for r in records}
    for prof in report.profiles:
        assert set(prof.aggregate.member_record_ids) <= known
        assert len(prof.aggregate.member_record_ids) == 24
