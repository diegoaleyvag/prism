# Methodology & metric definitions

All results are **simulated**: a fixture profile is a canned oracle that returns a fixed
answer per case. Metrics describe the *workbench*, not any real model.

## Pipeline

```
manifest + cases + profiles
        │  prism run
        ▼
immutable RunRecords (content-addressed)
        │  prism metrics / export
        ▼
Polars fact frame ──DuckDB GROUPING SETS──▶ per-family + aggregate rollups
        │                                        │ seeded bootstrap CIs
        ▼                                        ▼
redacted static artifacts ◀──────────────── MetricReport (reconciled)
```

The **fact frame** has one tidy row per record. Every published number is a pure function of
that frame, so aggregates reconcile with case‑level data by re‑running the group‑by
(`verify_reconciliation` asserts this).

## Metrics

Each rate is reported with its **numerator, denominator and a `display` string** (`"4 / 6"`).
No rate is ever shown without the sample it came from.

- **Task success rate** — fraction of cases graded correct for the family. Requires a
  schema‑valid output *and* family‑specific correctness (exact/normalized field match for
  extraction and tool selection; correct current‑value + contradiction flag for context;
  the required protective action for safety).
- **Schema‑validity rate** — fraction of outputs conforming to the case's JSON Schema
  (Draft 2020‑12). Independent of task correctness.
- **Correct abstention / escalation rate** — over the `should_*` subpopulation only
  (`should_abstain` + `should_escalate` + `should_refuse`). Denominator is surfaced.
- **Over‑refusal rate** — over benign safety *controls* (`normal` cases in the safety
  family). Reported separately so both error directions (under‑ and over‑action) are visible,
  each with its own denominator.
- **Latency distribution** — p50/p90/p95/p99, min/max/mean (ms). Latency is *simulated*
  (a deterministic per‑case value from the profile), not measured wall‑clock.
- **Tokens** — input/output/total sums and means. Estimated deterministically from text
  length (`chars_per_token`) unless the profile overrides.
- **Estimated cost** — see below.
- **Pareto** — quality (task‑success, max) vs cost (mean per case, min) vs latency (p90, min).

## Cost model

Cost is **not** stored on records. It is derived downstream from token counts and an
explicit, versioned, **simulated** price table (`data/pricing/price_table_prism-sim-2026.08.json`):

```
cost = input_tokens/1000 * input_price + output_tokens/1000 * output_price
```

computed with `Decimal` and stored as integer **micro‑USD** so no float nondeterminism ever
enters identity. Each cost carries the price table's id + content hash. This is an educational
estimate for comparing profiles — **never real provider pricing and never billed cost**.

## Uncertainty (and why we suppress it)

CIs use a **seeded percentile bootstrap**. For a rate with `k` successes out of `n`,
resampling with replacement makes the resample success count `~ Binomial(n, k/n)`, so:

```
seed  = blake2b(metric_id, profile, family, scope, record_set_hash, B, level, base_seed)
draws = Binomial(n, k/n) over B = 10000 resamples
CI    = [quantile(draws/n, 0.025), quantile(draws/n, 0.975)]   # 95%
```

The seed is derived from the metric's stable identity, so each interval is independently
reproducible and order‑independent.

**The guardrail is the point.** With 24 cases split by profile and family, denominators are
tiny and a tight interval would be misleading. So:

| Condition | Behavior |
| --- | --- |
| `k == 0` or `k == n` (degenerate) | Suppress CI; report a rule‑of‑three bound (`≈ 3/n`) instead of a zero‑width interval. Flag `degenerate_proportion`. |
| `n < 10` (`n_hard`) | **Suppress** CI; show `k / n`. Flag `n_below_hard_threshold`. |
| `10 ≤ n < 30` (`n_stable`) | Emit CI but mark `ci_reliable = false`. Flag `low_n`. |
| `n ≥ 30` | Emit CI, `ci_reliable = true`. |

Consequence for this release: essentially every **per‑family** CI (n = 6) is suppressed, and
even **per‑profile** aggregates (n = 24) are `low_n`. That is the honest answer to
"when is a model good enough?" at this scale — the workbench shows denominators instead of
fabricating confidence. Thresholds are configurable (`BootstrapConfig`).

## Reconciliation & drill‑down

Per‑family and per‑profile‑aggregate rows come from a single DuckDB `GROUPING SETS` pass, so
they are consistent by construction. Each rate carries its `denominator_record_ids` and
`passed_record_ids`; `verify_reconciliation` checks `rate == passed/denominator`,
`passed ⊆ denominator ⊆ members`, and `Σ_family denominator == aggregate`. The explorer links
every aggregate to exactly those records.

## Review scope

Cases are labelled `generated_unreviewed` → `owner_reviewed`. Release metrics use
`review_scope = release` (owner‑reviewed only); the excluded count is surfaced, never
silently dropped. Labels are snapshotted into the report so a later label change does not
retroactively alter a computed report.
