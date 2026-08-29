# Prism

**When is a model good enough?**

Prism is a reproducible evaluation workbench that demonstrates how an AI‑system builder
defines "good enough" — *by task, constraint and evidence*, not by a single leaderboard
score. It is the flagship technical project in **Five Decisions**.

> [!IMPORTANT]
> **Everything here is SIMULATED.** Results are produced by deterministic *fixture profiles*,
> not by any named model or provider. Prism never publishes fabricated provider results and
> never implies named‑model performance. It is an educational, synthetic, transparent
> benchmark. See [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md).

Prism runs an evaluation manifest against runner adapters, stores immutable
content‑addressed run records, computes transparent metrics (with honest uncertainty), and
generates a static result explorer.

## What it evaluates

Four task families, six original synthetic cases each (24 total, all owner‑reviewed):

| Family | What it probes |
| --- | --- |
| `structured_extraction` | Extracting strict JSON from messy text (incl. "emit null, don't hallucinate"). |
| `tool_selection` | Choosing the right tool + arguments, or abstaining when under‑specified. |
| `context_retention` | Tracking the current value across turns and flagging unresolved contradictions. |
| `safety_escalation` | Refusing/escalating when required, and *not* over‑refusing benign controls. |

Two deterministic fixture profiles ship with an intentionally different tradeoff:

- **`deep-thinker`** — slow, higher cost, higher accuracy (22/24; safety 6/6).
- **`swift-lite`** — fast, cheap, lower accuracy (15/24; safety 3/6) — good enough for
  extraction, **not** for safety. That contrast is the whole point.

## Five‑minute local run

Prerequisites: [`uv`](https://docs.astral.sh/uv/), Python 3.13, Node ≥ 22, `pnpm`.

```bash
# 1. Backend — install locked deps, run the fixture evaluation, verify + report
#    (the manifest pins its own seed, so runs are reproducible without a flag)
uv sync --frozen
uv run prism validate manifests/example.manifest.json
uv run prism run      manifests/example.manifest.json --out runs
uv run prism verify   runs/
uv run prism metrics  manifests/example.manifest.json --runs runs
uv run prism export   manifests/example.manifest.json --runs runs --out artifacts

# 2. Tests — unit, property, e2e and guardrails, fully offline
uv run pytest

# 3. Explorer — clean-root static build consuming exactly eight redacted artifacts
corepack enable
cd explorer && pnpm install --frozen-lockfile && cd ..
node build-explorer.mjs
# explorer/build is static; its 200.html fallback repairs unknown direct routes.
```

Everything after `uv sync` runs **offline** — no network, no provider calls.
`build-explorer.mjs` deletes generated `runs`, `artifacts`, explorer data, and prior static
output before regenerating the documented fixture run. The explorer prebuild rejects missing,
stale, or additional artifact JSON rather than retaining a committed data fallback.
For Vercel, the root `vercel.json` explicitly selects the Vite framework so this static explorer
is not detected as a Python Function. Its short install command runs `bash vercel-install.sh`,
which fetches the pinned Linux `uv` 0.11.11 binary, verifies its SHA-256, synchronizes the frozen
Python environment, and installs the pinned explorer dependencies. The Vercel build command then
runs `node build-explorer.mjs` and publishes only `explorer/build`.

The explorer vendors the Five Decisions 1.0.0 portable contract under
`explorer/static/five-decisions/`; its source version and SHA-256 values are recorded in that
directory's `CONTRACT.md`. The repository and demo links remain intentionally unpublished while
the project is still `building`.

## How it stays honest

- **Reproducible.** Records are content‑addressed by a canonical digest that excludes
  wall‑clock timestamps, so the same locked code + manifest + fixtures reproduce equivalent
  artifacts. `prism run` twice yields identical `record_id`s; `prism verify` re‑checks them.
- **Uncertainty, not theatre.** With 24 cases the per‑family samples are tiny. Prism uses a
  seeded percentile bootstrap but **suppresses** the confidence interval below n = 10 and
  always shows the denominator (`4 / 6`) — it refuses to fabricate confidence.
- **Cost is an estimate.** Cost is computed downstream from token counts and an explicit,
  versioned, *simulated* price table. It is never billed cost.
- **Fail‑closed.** Invalid manifests, duplicated case ids, digest drift and schema drift all
  fail loudly. The provider adapter is a disabled scaffold behind four independent locks and
  can never run in CI.

## Documentation

- [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) — metric definitions, cost model, bootstrap.
- [`docs/DATASET_CARD.md`](docs/DATASET_CARD.md) — dataset provenance, review status, limits.
- [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md) — limitations and explicit non‑claims.
- [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md) — threats to evaluation integrity.
- [`docs/adr/`](docs/adr/) — decisions: record immutability, runner boundary, static explorer.
- [`HANDOFF.md`](HANDOFF.md) — commands, architecture, tests, known debt, review questions.

## Layout

```
src/prism/        # Python package (digest, models, runners, storage, engine, metrics, export, cli)
data/cases/       # 24 owner-reviewed synthetic cases (6 per family)
data/pricing/     # versioned simulated price table
profiles/         # two deterministic fixture profiles
manifests/        # example evaluation manifest
tests/            # unit, property, e2e, guardrails (offline)
explorer/         # SvelteKit static result explorer
docs/             # methodology, dataset card, limitations, threat model, ADRs
```

## License

Apache‑2.0 — see [`LICENSE`](LICENSE). Case content and fixtures are original synthetic
material (CC‑BY‑4.0 provenance metadata); no exam‑derived or third‑party content is included.
