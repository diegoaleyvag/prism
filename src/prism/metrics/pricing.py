"""Versioned, SIMULATED price table and cost arithmetic.

Prices here are invented for educational cost *estimation*. They are **not** real provider
pricing and **not** billed cost. Cost is computed with :class:`decimal.Decimal` and stored as
integer micro-USD so it never introduces float nondeterminism. Every emitted cost records the
price table's id + content hash so the estimate is reproducible and auditable.
"""

from __future__ import annotations

import json
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, JsonValue, model_validator

from prism.digest import content_digest
from prism.schema_versions import PRICETABLE_V1

_MICRO = Decimal(1_000_000)
_PER_1K = Decimal(1000)


class PriceEntry(BaseModel):
    """Per-profile token pricing (decimal strings — never floats in identity)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    unit: Literal["per_1k_tokens"] = "per_1k_tokens"
    input_price: str
    output_price: str
    notes: str | None = None


class PriceTable(BaseModel):
    """A named, versioned, content-hashed table of simulated prices."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["pricetable/v1"] = PRICETABLE_V1
    price_table_id: str
    currency: Literal["USD"] = "USD"
    simulated: Literal[True] = True
    disclaimer: str
    effective_date: str
    entries: dict[str, PriceEntry]
    content_hash: str

    @model_validator(mode="after")
    def _verify_hash(self) -> Self:
        expected = compute_price_table_hash(self)
        if self.content_hash != expected:
            raise ValueError(
                f"price table content_hash drift: stored={self.content_hash} computed={expected}"
            )
        return self

    def cost_micro_usd(self, profile_id: str, input_tokens: int, output_tokens: int) -> int:
        """Estimated cost for one run, in integer micro-USD."""
        entry = self.entries.get(profile_id)
        if entry is None:
            raise KeyError(f"no price entry for profile {profile_id!r}")
        cost = (
            Decimal(input_tokens) / _PER_1K * Decimal(entry.input_price)
            + Decimal(output_tokens) / _PER_1K * Decimal(entry.output_price)
        ) * _MICRO
        return int(cost.quantize(Decimal(1), rounding=ROUND_HALF_EVEN))


_NON_IDENTITY: frozenset[str] = frozenset({"content_hash"})


def compute_price_table_hash(table: PriceTable) -> str:
    """Content hash over the table body, excluding the hash field itself."""
    return content_digest(table.model_dump(exclude=set(_NON_IDENTITY)))


def build_price_table(body: dict[str, JsonValue]) -> PriceTable:
    """Construct a price table from a body dict, computing ``content_hash``."""
    identity = {k: v for k, v in body.items() if k not in _NON_IDENTITY}
    return PriceTable.model_validate({**body, "content_hash": content_digest(identity)})


def load_price_table(path: Path) -> PriceTable:
    """Load and validate a price table JSON file (fails closed on hash drift)."""
    return PriceTable.model_validate_json(Path(path).read_text(encoding="utf-8"))


def default_price_table() -> PriceTable:
    """The foundation-release simulated price table (id ``prism-sim-2026.08``)."""
    return build_price_table(
        {
            "schema_version": PRICETABLE_V1,
            "price_table_id": "prism-sim-2026.08",
            "currency": "USD",
            "simulated": True,
            "disclaimer": "SIMULATED prices for educational cost estimation only. NOT real "
            "provider pricing. NOT billed cost.",
            "effective_date": "2026-08-01",
            "entries": {
                "swift-lite": {
                    "unit": "per_1k_tokens",
                    "input_price": "0.0002",
                    "output_price": "0.0006",
                    "notes": "synthetic fast/cheap profile",
                },
                "deep-thinker": {
                    "unit": "per_1k_tokens",
                    "input_price": "0.0030",
                    "output_price": "0.0120",
                    "notes": "synthetic slow/high-quality profile",
                },
            },
        }
    )


def write_price_table(table: PriceTable, path: Path) -> Path:
    """Write a price table to ``path`` as sorted, pretty JSON."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(
        json.dumps(json.loads(table.model_dump_json()), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return Path(path)


__all__ = [
    "PriceEntry",
    "PriceTable",
    "build_price_table",
    "compute_price_table_hash",
    "default_price_table",
    "load_price_table",
    "write_price_table",
]
