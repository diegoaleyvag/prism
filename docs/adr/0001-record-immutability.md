# ADR 0001 — Immutable, content‑addressed run records

- Status: accepted
- Date: 2026‑08‑13

## Context

Prism's credibility rests on reproducibility: the same locked code + manifest + fixtures must
yield equivalent artifacts, and a stored result must be tamper‑evident. Run records also carry
wall‑clock timestamps, which are inherently nondeterministic.

## Decision

Run records are **append‑only and content‑addressed**. `record_id = "sha256:" +
sha256(canonical_json(record_without_volatile_fields))`, where the volatile fields
(`started_at`, `finished_at`, `record_id`) are excluded before hashing. The canonical
serializer sorts ASCII keys, drops `None`, forbids `Decimal`/`datetime`/`bytes` in identity,
and rejects non‑finite floats.

Records are stored write‑once, sharded by hash, chmod `0o444`, with an append‑only index. A
re‑run that produces the same non‑volatile content is an idempotent no‑op (only timestamps
would differ); differing content at the same address raises `IntegrityError`. `prism verify`
recomputes every digest from disk and checks the filename + read‑only bit.

## Consequences

- Two runs are byte‑identical except timestamps and share a `record_id`; determinism is
  testable and enforced (`prism verify`, e2e test).
- Secrets/raw prompts cannot leak via records — the model has no field for them.
- True immutability would need WORM/object‑lock storage; on a local filesystem we enforce by
  convention (content addressing + read‑only + verification). Documented as a residual risk.

## Alternatives considered

- *Hash the whole record including timestamps* — breaks re‑run idempotency and cross‑machine
  reproducibility. Rejected.
- *Mutable records with a separate checksum* — weaker tamper evidence; rejected in favour of
  the address **being** the hash.
