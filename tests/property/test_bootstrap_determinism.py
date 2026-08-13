"""Bootstrap CIs are deterministic and honor the small-n guardrail tiers."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from prism.stats.bootstrap import BootstrapConfig, bootstrap_rate_ci

_CFG = BootstrapConfig()


@st.composite
def _k_n(draw: st.DrawFn) -> tuple[int, int]:
    n = draw(st.integers(min_value=1, max_value=200))
    k = draw(st.integers(min_value=0, max_value=n))
    return k, n


@given(_k_n())
def test_same_inputs_same_interval(kn: tuple[int, int]) -> None:
    k, n = kn
    a = bootstrap_rate_ci(k, n, seed_parts=("m", "p", "f"), config=_CFG)
    b = bootstrap_rate_ci(k, n, seed_parts=("m", "p", "f"), config=_CFG)
    assert (a.ci_low, a.ci_high, a.seed) == (b.ci_low, b.ci_high, b.seed)


@given(_k_n())
def test_denominator_and_rate_are_reported(kn: tuple[int, int]) -> None:
    k, n = kn
    r = bootstrap_rate_ci(k, n, seed_parts=("m", "p", "f"), config=_CFG)
    assert r.denominator == n
    assert r.rate == k / n


@given(_k_n())
def test_guardrail_tiers(kn: tuple[int, int]) -> None:
    k, n = kn
    r = bootstrap_rate_ci(k, n, seed_parts=("m", "p", "f"), config=_CFG)
    degenerate = k == 0 or k == n

    if degenerate:
        assert r.ci_low is None and r.ci_high is None
        assert "degenerate_proportion" in r.ci_flags
        assert r.rule_of_three  # a rule-of-three bound is provided
    elif n < _CFG.n_hard:
        assert r.ci_low is None and r.ci_high is None
        assert "n_below_hard_threshold" in r.ci_flags
    else:
        assert r.ci_low is not None and r.ci_high is not None
        assert r.ci_low <= r.rate <= r.ci_high  # type: ignore[operator]
        assert r.ci_reliable is (n >= _CFG.n_stable)


def test_reliable_only_at_or_above_stable_threshold() -> None:
    # A healthy proportion at n=30 is reliable; the same at n=29 is not.
    assert bootstrap_rate_ci(15, 30, seed_parts=("a", "b", "c")).ci_reliable is True
    assert bootstrap_rate_ci(15, 29, seed_parts=("a", "b", "c")).ci_reliable is False
