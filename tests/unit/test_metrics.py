"""Metric report: headline numbers, denominators, cost/latency, and the guardrail."""

from __future__ import annotations

from prism.metrics.compute import compute_report
from prism.models.enums import TaskFamily


def _profile(report, pid):
    return next(p for p in report.profiles if p.profile_id == pid)


def test_headline_success_counts(records, cases, price_table) -> None:
    report = compute_report(records, cases, price_table, generated_at="fixed")
    deep = _profile(report, "deep-thinker").aggregate.task_success
    swift = _profile(report, "swift-lite").aggregate.task_success
    assert (deep.numerator, deep.denominator) == (22, 24)
    assert (swift.numerator, swift.denominator) == (15, 24)


def test_swift_is_weaker_on_safety(records, cases, price_table) -> None:
    report = compute_report(records, cases, price_table, generated_at="fixed")
    swift = _profile(report, "swift-lite")
    safety = next(f for f in swift.families if f.family == TaskFamily.SAFETY_ESCALATION)
    assert safety.task_success.numerator == 3
    assert safety.correct_escalation is not None
    assert safety.correct_escalation.denominator == 4  # should_refuse + should_escalate


def test_over_refusal_present_only_where_controls_exist(records, cases, price_table) -> None:
    report = compute_report(records, cases, price_table, generated_at="fixed")
    swift = _profile(report, "swift-lite")
    assert swift.aggregate.over_refusal is not None
    assert swift.aggregate.over_refusal.denominator == 2  # two benign safety controls
    extraction = next(f for f in swift.families if f.family == TaskFamily.STRUCTURED_EXTRACTION)
    assert extraction.over_refusal is None  # no safety controls in this family


def test_small_n_guardrail_suppresses_family_cis(records, cases, price_table) -> None:
    report = compute_report(records, cases, price_table, generated_at="fixed")
    for prof in report.profiles:
        # aggregate n=24 -> CI emitted but flagged low_n (not reliable)
        assert prof.aggregate.task_success.ci_reliable is False
        assert "low_n" in prof.aggregate.task_success.ci_flags
        for fam in prof.families:  # per-family n=6 -> suppressed
            assert fam.task_success.ci_low is None
            assert fam.task_success.ci_high is None


def test_cost_and_latency_tradeoff(records, cases, price_table) -> None:
    report = compute_report(records, cases, price_table, generated_at="fixed")
    deep = _profile(report, "deep-thinker").aggregate
    swift = _profile(report, "swift-lite").aggregate
    assert deep.cost.mean_usd > swift.cost.mean_usd
    assert deep.latency.p90_ms > swift.latency.p90_ms
    assert deep.cost.simulated is True


def test_pareto_frontier_is_a_real_tradeoff(records, cases, price_table) -> None:
    report = compute_report(records, cases, price_table, generated_at="fixed")
    # Neither dominates the other (higher quality costs more and is slower).
    assert all(p.on_frontier for p in report.pareto)
