"""Redaction + the provider-name guard for public artifacts.

Two jobs: keep raw material out of published artifacts (bounded excerpts only), and make it
structurally impossible to associate a fabricated result with a real provider. The name guard
runs over every artifact before it is written; profile ids are synthetic (``swift-lite`` /
``deep-thinker``) and no named model/provider token may appear anywhere.
"""

from __future__ import annotations

import re
from typing import Any

# Distinctive provider/model tokens. Matched against whole tokens (not substrings) so
# ordinary words like "metadata" are never false positives.
BANNED_NAME_TOKENS: frozenset[str] = frozenset(
    {
        "openai", "gpt", "chatgpt", "anthropic", "claude", "sonnet", "opus", "haiku",
        "gemini", "bard", "palm", "llama", "mistral", "mixtral", "cohere", "grok",
        "deepseek", "qwen", "phi", "command-r",
    }
)

_WORD_RE = re.compile(r"[a-z0-9]+")
_COMPOUND_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)+")

EXCERPT_MAX = 240


class ProviderNameLeak(ValueError):
    """Raised when a banned provider/model name appears in an artifact."""


def redact_text(text: str, max_len: int = EXCERPT_MAX) -> str:
    """Return a bounded, single-line excerpt suitable for publication."""
    collapsed = " ".join(text.split())
    if len(collapsed) <= max_len:
        return collapsed
    return collapsed[: max_len - 1].rstrip() + "…"


def _tokens(text: str) -> set[str]:
    """Whole words plus hyphenated compounds, so both ``gpt`` and ``command-r`` are caught."""
    lowered = text.lower()
    parts: set[str] = set(_WORD_RE.findall(lowered))
    parts.update(_COMPOUND_RE.findall(lowered))
    return parts


def find_provider_names(obj: Any) -> list[str]:
    """Return any banned name tokens found anywhere in ``obj`` (strings, keys, values)."""
    hits: set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, str):
            for tok in _tokens(node):
                if tok in BANNED_NAME_TOKENS:
                    hits.add(tok)
        elif isinstance(node, dict):
            for k, v in node.items():
                walk(k)
                walk(v)
        elif isinstance(node, (list, tuple)):
            for v in node:
                walk(v)

    walk(obj)
    return sorted(hits)


def assert_no_provider_names(obj: Any) -> None:
    """Raise :class:`ProviderNameLeak` if any banned provider/model name is present."""
    hits = find_provider_names(obj)
    if hits:
        raise ProviderNameLeak(f"artifact contains banned provider/model name(s): {hits}")


__all__ = [
    "BANNED_NAME_TOKENS",
    "EXCERPT_MAX",
    "ProviderNameLeak",
    "assert_no_provider_names",
    "find_provider_names",
    "redact_text",
]
