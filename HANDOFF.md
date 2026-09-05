# HANDOFF — Prism foundation vertical slice

**Status boundary (2026-09-05):** this document is a point-in-time snapshot of the
`feat/five-decisions-integration` foundation slice. `PR #1` referenced below has since merged
to `build/foundation`, and `portfolio.project.json`'s status has since advanced from `building`
to **`released`**, with `demo` and `methodology` links populated and a promoted production
deployment recorded as evidence — see [`README.md`](README.md) for the current state. Kept
verbatim below as historical record, not rewritten. Everything here remains true of that
foundation slice: it was, and remains, SIMULATED — no live provider.

---

Branch: `feat/five-decisions-integration`. Open PR #1 targets `build/foundation`. Status:
foundation slice complete and green offline. Everything is SIMULATED — no live provider.

## Commands

```bash
uv sync --frozen                                   # install locked deps
uv run prism version                               # version + schema tags
uv run prism validate manifests/example.manifest.json
uv run prism run      manifests/example.manifest.json --out runs   # seed is pinned in the manifest
uv run prism verify   runs/                         # recompute + check digests, read-only
uv run prism metrics  manifests/example.manifest.json --runs runs
uv run prism export   manifests/example.manifest.json --runs runs --out artifacts
uv run prism dataset build                          # regenerate cases + profiles + manifest
uv run pytest                                       # fully offline; see collected count in output
uv run ruff check src/ tests/ && uv run mypy        # lint + types

cd explorer && pnpm install && pnpm run build && pnpm test && pnpm run check:names
cd .. && node build-explorer.mjs                    # clean generated run/artifact/static build
```

## Architecture (Python, `src/prism/`)

| Module | Responsibility |
| --- | --- |
| `digest/` | Canonical JSON serialization + sha256 content addressing (the identity contract). |
| `models/` | Versioned Pydantic records: `TaskCase`, `EvaluationManifest`, `RunRecord`, `MetricResult`, `Provenance`, enums. |
| `runners/` | `Runner` protocol; `FixtureReplayRunner` (default); `ProviderRunner` (disabled scaffold); `FixtureProfile`. |
| `storage/` | Append‑only, content‑addressed, read‑only record store + integrity checks. |
| `dataset/` | 24 synthetic cases (`generate.py`), family graders (`grading.py`), profile generator, loaders. |
| `validation/` | Fail‑closed manifest validation with actionable problems. |
| `engine/` | Default manifest planner + the run loop (`execute_run`). |
| `metrics/` | Polars fact frame + DuckDB `GROUPING SETS` rollups, versioned price table, Pareto, reconciliation. |
| `stats/` | Seeded percentile bootstrap + small‑n guardrail. |
| `export/` | Redacted static artifacts + provider‑name guard. |
| `cli/` | Typer CLI (`validate/run/verify/metrics/export/digest/version/dataset build`). |

`explorer/` — SvelteKit static app consuming the redacted artifacts (see `docs/adr/0003`).
`build-explorer.mjs` is the reproducible clean-root bridge: it removes generated output, executes
the documented fixture pipeline, requires exactly eight export artifacts, then builds the explorer.
For remote static builds, `vercel.json` pins the project to Vite, bootstraps checksum-verified
`uv` 0.11.11 through `vercel-install.sh`, installs frozen dependencies, runs this root build
bridge, and exposes only `explorer/build`. It intentionally defines no Python Function entrypoint.

## Data flow

`manifest + cases + profiles → run → immutable RunRecords → metrics (fact frame → rollups →
bootstrap) → redacted artifacts → static explorer`. Aggregates reconcile to case‑level by
construction (`verify_reconciliation`).

## Key facts a reviewer should know

- `record_id` excludes wall‑clock timestamps → two runs give identical ids; `prism verify`
  proves it.
- CIs are **suppressed** below n = 10 (per‑family n = 6 → suppressed; per‑profile n = 24 →
  `low_n`). This is intended honesty, not a bug.
- deep‑thinker 22/24 (safety 6/6); swift‑lite 15/24 (safety 3/6, one schema‑invalid output).
  The safety gap is the "good enough?" narrative and is authored, not accidental.
- Cost is simulated (versioned price table), stored as integer micro‑USD; never billed.

## Tests

`tests/{unit,property,e2e,guardrails}`. Autouse socket guard blocks all network.
Property tests (Hypothesis) cover digest determinism, JSON round‑trips, bootstrap determinism
+ guardrail tiers, and subset reconciliation. Guardrails assert invalid manifests / duplicate
ids / schema drift / digest tamper / name‑leak fail, and that the provider adapter is
un‑triggerable (including in CI) and imports no provider SDK.

## Changed files

Everything in the repo is new (greenfield). Notable: `src/prism/**`, `data/cases/**` (24
JSON), `data/pricing/**`, `profiles/**` (2 JSON), `manifests/example.manifest.json`,
`tests/**`, `docs/**`, `explorer/**`, `portfolio.project.json`, `pyproject.toml`, `uv.lock`.
Generated (gitignored): `runs/`, `artifacts/`, `explorer/static/data/`, `explorer/build/`.
The explorer vendors a Five Decisions 1.0.0 contract snapshot under `static/five-decisions/`;
`CONTRACT.md` records the source version and portable source hashes. `portfolio.project.json` is
validated offline against the vendored portable schema by the guardrail suite.

## Known debt

- Explorer frontend tests are vitest + strict static build + a `check:names` scan; no
  Playwright browser smoke (avoids a browser download in this environment).
- Local record immutability is by convention (content‑address + read‑only + verify), not WORM.
- Provider adapter is a scaffold only; a real adapter is out of scope for this release.
- `portfolio.project.json` links the GitHub repository; demo and methodology stay `null` and
  status remains `building` until a canonical public preview is promoted (do not advance to
  `verified` before then).
- The name‑guard denylist is finite; extend it alongside the export module.

## Open review questions

1. Are the small‑n thresholds (`n_hard=10`, `n_stable=30`) the right honesty/utility balance,
   or should per‑family show wide‑but‑present intervals?
2. Should the provider scaffold be split into its own optional extra so the default install
   has zero provider surface?
3. Is per‑profile Pareto (2 points) enough, or should we also expose per‑(profile, family)?
4. Do the simulated price magnitudes read as clearly synthetic, or should they be more
   obviously fake?
