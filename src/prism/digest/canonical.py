"""Canonical serialization for content addressing.

:func:`canonical_bytes` is the *one true* serializer feeding every digest in Prism. Two
inputs hash equal iff they are semantically equal, so the rules here are load-bearing:

* object keys are sorted by Unicode code point (keys are required to be ASCII);
* ``None`` values are dropped from objects (absent ≡ null) so optional fields never
  perturb identity;
* tuples serialize as JSON arrays and enums as their value;
* finite ``float`` literals are allowed and serialized by ``json.dumps`` (shortest
  round-trip repr, deterministic and platform-independent since CPython 3.1) so authored
  reference values such as ``14.6`` kg round-trip stably; **NaN/Infinity are rejected**;
* **``Decimal``, ``datetime``/``date`` and ``bytes`` are rejected** inside an identity
  payload. The "no floats in numeric identity" guarantee for tokens/latency/cost is
  enforced by the *models* (those fields are typed ``int``), not by this serializer —
  computed values never reach identity. Price rates are carried as decimal *strings*.
  Volatile, non-identity fields (timestamps) are excluded by the caller *before* hashing.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel

from prism.digest.hashing import digest_str


class CanonicalizationError(TypeError):
    """Raised when a value cannot appear in a canonical identity payload."""


def _normalize(value: Any) -> Any:
    """Recursively coerce ``value`` into JSON-native, identity-safe primitives."""
    # Order matters: bool is a subclass of int; StrEnum members are subclasses of str.
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, Enum):
        return _normalize(value.value)
    if isinstance(value, str):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise CanonicalizationError(f"non-finite float is not allowed (got {value!r})")
        return value
    if isinstance(value, Decimal):
        raise CanonicalizationError(
            "Decimal is not allowed in an identity payload; serialize it as a string "
            f"(got {value!r})"
        )
    if isinstance(value, (datetime, date)):
        raise CanonicalizationError(
            "datetime/date is not allowed in an identity payload; timestamps must live "
            f"in volatile fields excluded before hashing (got {value!r})"
        )
    if isinstance(value, (bytes, bytearray)):
        raise CanonicalizationError("bytes are not allowed in an identity payload")
    if isinstance(value, BaseModel):
        return _normalize(value.model_dump(mode="python"))
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, val in value.items():
            if not isinstance(key, str):
                raise CanonicalizationError(f"object keys must be str, got {type(key).__name__}")
            if not key.isascii():
                raise CanonicalizationError(f"object keys must be ASCII, got {key!r}")
            if val is None:
                continue  # absent ≡ null
            out[key] = _normalize(val)
        return {k: out[k] for k in sorted(out)}
    if isinstance(value, Sequence):  # list / tuple (str & bytes handled above)
        return [_normalize(v) for v in value]
    raise CanonicalizationError(f"unsupported type in identity payload: {type(value).__name__}")


def canonical_bytes(obj: Any) -> bytes:
    """Serialize ``obj`` to canonical UTF-8 JSON bytes for hashing."""
    normalized = _normalize(obj)
    text = json.dumps(
        normalized,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    )
    return text.encode("utf-8")


def canonical_json(obj: Any) -> str:
    """Human-readable form of :func:`canonical_bytes` (debugging / golden tests)."""
    return canonical_bytes(obj).decode("utf-8")


def content_digest(obj: Any) -> str:
    """Return the ``sha256:…`` content digest of ``obj`` under canonical serialization."""
    return digest_str(canonical_bytes(obj))


__all__ = [
    "CanonicalizationError",
    "canonical_bytes",
    "canonical_json",
    "content_digest",
]
