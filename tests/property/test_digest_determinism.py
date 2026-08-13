"""Canonical digests are stable, key-order/None invariant, and reject unsafe types."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from prism.digest import CanonicalizationError, canonical_json, content_digest

_keys = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_",
    min_size=1,
    max_size=8,
)
_scalars = (
    st.none()
    | st.booleans()
    | st.integers(min_value=-(10**9), max_value=10**9)
    | st.floats(allow_nan=False, allow_infinity=False)
    | st.text(max_size=12)
)
_json = st.recursive(
    _scalars,
    lambda children: st.lists(children, max_size=4)
    | st.dictionaries(_keys, children, max_size=4),
    max_leaves=15,
)


@given(_json)
def test_digest_is_idempotent(value: object) -> None:
    assert content_digest(value) == content_digest(value)


@given(_json)
def test_parse_reserialize_is_stable(value: object) -> None:
    import json

    reparsed = json.loads(canonical_json(value))
    assert content_digest(value) == content_digest(reparsed)


@given(st.dictionaries(_keys, _json, min_size=1, max_size=6))
def test_key_order_invariance(mapping: dict[str, object]) -> None:
    reordered = dict(reversed(list(mapping.items())))
    assert content_digest(mapping) == content_digest(reordered)


@given(st.dictionaries(_keys, _json, max_size=6), _keys)
def test_none_valued_key_is_dropped(mapping: dict[str, object], key: str) -> None:
    assume(key not in mapping)
    with_none = {**mapping, key: None}
    assert content_digest(mapping) == content_digest(with_none)


@given(st.dictionaries(_keys, _json, min_size=2, max_size=6))
def test_distinct_content_distinct_digest(mapping: dict[str, object]) -> None:
    key = next(iter(mapping))
    mutated = {**mapping, key: [mapping[key], "prism-sentinel"]}
    if mutated[key] != mapping[key]:
        assert content_digest(mapping) != content_digest(mutated)


def test_datetime_is_rejected() -> None:
    with pytest.raises(CanonicalizationError):
        content_digest({"t": datetime(2026, 1, 1, tzinfo=UTC)})


def test_decimal_is_rejected() -> None:
    with pytest.raises(CanonicalizationError):
        content_digest({"d": Decimal("1.5")})


def test_non_ascii_key_is_rejected() -> None:
    with pytest.raises(CanonicalizationError):
        content_digest({"café": 1})
