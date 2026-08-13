# Limitations & non‑claims

Prism is an educational, synthetic, transparent workbench. Read these before drawing any
conclusion from its output.

## Explicit non‑claims

- **Prism does not measure any named model or provider.** Every result is produced by a
  deterministic fixture profile — a canned oracle. Profile ids (`swift-lite`, `deep-thinker`)
  are synthetic and represent no real system.
- **Prism does not publish provider performance.** It never associates a result with a real
  provider name; a name‑guard blocks that at export time.
- **Estimated cost is not billed cost.** Cost is a downstream estimate from a *simulated*,
  versioned price table. Latency is *simulated*, not measured.
- **This is not a leaderboard.** The point is the opposite: "good enough" is defined per task,
  constraint and failure budget, with denominators and uncertainty shown.

## Limitations

- **Tiny samples.** 24 cases (6 per family). Per‑family denominators are 6; per‑profile
  aggregates are 24. Most confidence intervals are therefore suppressed or flagged `low_n`
  by design — see [`METHODOLOGY.md`](METHODOLOGY.md). Do not read a single point estimate as
  a stable measurement.
- **Synthetic, narrow content.** Invented, English‑only, single‑domain cases. Not
  representative of production distributions or adversarial inputs.
- **Deterministic simulation.** There is no sampling variance, no real model behavior, no
  prompt sensitivity — the fixtures answer the same way every time on purpose.
- **Grading is exact/structural.** Graders use schema validation + normalized field matching,
  not semantic judgement. They reward the reference answer's shape.
- **Safety cases are tame, policy‑style stand‑ins.** They exercise the escalation/refusal
  *mechanism*, not real‑world harm.
- **Local immutability is by convention.** Records are content‑addressed, written once and
  marked read‑only, and re‑verified — but a local filesystem is not WORM storage.

## Appropriate use

Use Prism to learn and demonstrate *how* to evaluate task‑specific tradeoffs reproducibly:
manifests, immutable records, per‑family metrics, honest uncertainty, and a Pareto view of
quality/cost/latency. Do not cite its numbers as evidence about any real model.
