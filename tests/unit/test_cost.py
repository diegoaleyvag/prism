"""Price table: deterministic integer-micro-USD cost, hash integrity, no billed claim."""

from __future__ import annotations

import pytest

from prism.metrics.pricing import (
    PriceTable,
    build_price_table,
    default_price_table,
)


def test_cost_is_deterministic_integer_micro_usd() -> None:
    table = default_price_table()
    a = table.cost_micro_usd("deep-thinker", 100, 50)
    b = table.cost_micro_usd("deep-thinker", 100, 50)
    assert a == b
    assert isinstance(a, int)


def test_cost_matches_hand_computation() -> None:
    table = default_price_table()
    # deep-thinker: input 0.0030 / 1k, output 0.0120 / 1k
    # 1000 in + 1000 out => (1*0.0030 + 1*0.0120) usd = 0.015 usd = 15000 micro-USD
    assert table.cost_micro_usd("deep-thinker", 1000, 1000) == 15000


def test_cheaper_profile_costs_less() -> None:
    table = default_price_table()
    assert table.cost_micro_usd("swift-lite", 500, 500) < table.cost_micro_usd(
        "deep-thinker", 500, 500
    )


def test_unknown_profile_raises() -> None:
    with pytest.raises(KeyError):
        default_price_table().cost_micro_usd("mystery", 10, 10)


def test_content_hash_drift_fails() -> None:
    table = default_price_table()
    data = table.model_dump()
    data["disclaimer"] = "tampered"  # identity changed, hash not recomputed
    with pytest.raises(ValueError, match="content_hash drift"):
        PriceTable.model_validate(data)


def test_table_is_marked_simulated() -> None:
    table = default_price_table()
    assert table.simulated is True
    assert "NOT billed cost" in table.disclaimer


def test_build_roundtrip_reconciles() -> None:
    table = default_price_table()
    rebuilt = build_price_table(
        {k: v for k, v in table.model_dump().items() if k != "content_hash"}
    )
    assert rebuilt.content_hash == table.content_hash
