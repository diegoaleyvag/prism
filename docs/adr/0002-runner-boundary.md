# ADR 0002 — Runner boundary: fixtures by default, provider scaffold disabled

- Status: accepted
- Date: 2026‑08‑13

## Context

Prism must produce only deterministic, offline, simulated results for this release, while
leaving a credible path for a future live‑provider adapter. A live call firing accidentally —
especially in CI — would undermine both reproducibility and the "no fabricated provider
results" guarantee.

## Decision

A `Runner` is a small interface (`Protocol` + `BaseRunner`) returning a `RunnerOutput` that
always records its `RunMode` and a `provenance` dict. Two implementations:

1. **`FixtureReplayRunner`** (default, used everywhere) — replays a canned answer keyed by
   `case_digest`; "jitter" is a pure hash of `(profile_id, case_digest)`, never an RNG.
2. **`ProviderRunner`** — a **scaffold with no network code**. Construction requires clearing
   four independent locks: (a) no CI env detected, (b) `PRISM_ENABLE_PROVIDER=1`,
   (c) explicit `--enable-provider`, and even then (d) `run()` raises `NotImplementedError`.

Manifests declare runners; validation guards any `provider` ref behind the same gate. Every
record carries explicit `run_mode`; the explorer renders fixture/replay/live distinctly and
never conflates them.

## Consequences

- It is impossible to trigger a live call by accident, and provably impossible in CI
  (guardrail test asserts this and that no provider SDK is imported).
- The extension point is concrete and documented, without shipping any provider dependency.
- Cost/latency are simulated per profile; a real adapter would populate the same
  `RunnerOutput` shape, so downstream metrics/export are unchanged.

## Alternatives considered

- *No provider scaffold at all* — loses the extension‑point clarity the brief asks for.
- *A single env flag* — one accidental export in CI would enable it; four independent locks
  give defence in depth.
