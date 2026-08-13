# Threat model — evaluation integrity

Prism's value is trustworthy, reproducible evidence. This model enumerates threats to that
integrity and the mitigation each one has. Scope: the evaluation pipeline and its published
artifacts, not host/OS security.

| # | Threat | Mitigation |
| --- | --- | --- |
| 1 | **Overclaiming** — a fabricated result implies real‑model performance | Everything is labelled `simulated: true`; the explorer shows a non‑dismissible SIMULATED banner on every page; `docs/LIMITATIONS.md` states the non‑claims. |
| 2 | **Provider‑name leak** — a real provider name appears next to a number | `assert_no_provider_names` runs over every artifact before write and rejects a denylist of provider/model tokens (whole + hyphenated). Profile ids are synthetic. A frontend `check:names` scan re‑checks built HTML + data. |
| 3 | **Non‑determinism** — results drift between runs/machines | Canonical JSON digests (sorted ASCII keys, None‑drop, no floats/datetime in identity); `uv.lock` pins deps + Python; fixture runs are pure (hash‑derived "jitter", no RNG); bootstrap seeds are derived from stable identity. `prism run` twice → identical `record_id`s. |
| 4 | **Silent schema drift** — a record/case/artifact shape changes unnoticed | Every model pins `schema_version` with `Literal` and forbids extra fields (`extra="forbid"`), so drift fails at load. Guardrail tests assert rejection. |
| 5 | **Content/digest tamper** — a case or record is edited after the fact | Content addressing: `case_digest` / `record_id` / `manifest_digest` are recomputed and verified on load; records are chmod `0o444` and re‑checked by `prism verify`. Manifests pin `case_digest`, so a changed case fails validation (`digest-drift`). |
| 6 | **Fabricated confidence** — a misleadingly tight interval on tiny n | Small‑n guardrail suppresses CIs below n = 10, flags `low_n` below 30, and surfaces denominators + rule‑of‑three bounds. |
| 7 | **Aggregate/case mismatch** — headline numbers don't match the cases | Single `GROUPING SETS` rollup; `verify_reconciliation` asserts `rate == passed/denominator` and family sums == aggregate; the CLI fails closed if reconciliation breaks; the UI links every aggregate to its records. |
| 8 | **Accidental provider activation** — a live call fires in CI or by mistake | Provider adapter ships no network code and is behind four independent locks (CI‑env hard‑disable, `PRISM_ENABLE_PROVIDER=1`, explicit `--enable-provider`, and `run()` raises). Default runner is always `fixture_replay`; validation guards provider refs. |
| 9 | **Secret / raw‑prompt exposure** in public artifacts | `RunRecord` has *no field* for secrets or raw prompts (structural). Artifacts publish bounded, redacted excerpts and graded/normalized output only. |
| 10 | **Exam‑derived or private content entering Git** | Private banks live outside the repo and are ignored defensively (`CCAR-*`, `*preguntas*`, `Downloads/`). All cases are original synthetic content with provenance asserting so. |
| 11 | **"Offline" that secretly needs network** | An autouse socket guard blocks all outbound connections during the test suite; the e2e test runs the full evaluation with the guard active. (Dependency install via `uv sync` / `pnpm install` is the one documented online step.) |
| 12 | **Mode confusion** — fixture vs replay vs live conflated in the UI | Distinct colour + icon + text per mode; live rendered disabled; never colour‑alone. |

## Residual risks (accepted, documented)

- Local immutability is enforced by convention (hash‑addressing + read‑only + verify), not by
  WORM/object‑lock storage.
- The denylist in mitigation #2 is finite; a novel provider name not on the list would pass.
  It is maintained alongside the export module.
- Grading is structural, not semantic; a wrong‑but‑schema‑valid answer that happens to match
  the reference shape could be over‑credited.
