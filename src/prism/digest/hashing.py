"""Hashing primitives.

Kept deliberately tiny and dependency-free so the digest contract is auditable. All
content addressing in Prism funnels through :func:`digest_str`.
"""

from __future__ import annotations

import hashlib

_UNIT_SEP = "\x1f"  # ASCII unit separator: cannot appear in our ASCII identifiers.


def sha256_hex(data: bytes) -> str:
    """Return the lowercase hex SHA-256 of ``data``."""
    return hashlib.sha256(data).hexdigest()


def digest_str(data: bytes) -> str:
    """Return the canonical Prism digest string, e.g. ``"sha256:ab12…"``.

    The algorithm prefix is explicit so records remain self-describing if the hash is
    ever migrated.
    """
    return "sha256:" + sha256_hex(data)


def stable_int(*parts: str) -> int:
    """Deterministically derive a non-negative integer from string ``parts``.

    Used by the fixture runner for reproducible "jitter" without an RNG: the same parts
    always yield the same integer, on any machine, forever. Parts are joined with the
    ASCII unit separator so ``("a", "bc")`` and ``("ab", "c")`` never collide.
    """
    joined = _UNIT_SEP.join(parts).encode("utf-8")
    return int(hashlib.sha256(joined).hexdigest()[:16], 16)
