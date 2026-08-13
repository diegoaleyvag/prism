# Dataset card — Prism foundation cases

## Summary

24 original, synthetic evaluation cases — six in each of four task families — authored for
Prism. Every case is content‑addressed and owner‑reviewed. The dataset exists to demonstrate
a reproducible evaluation workbench, not to benchmark any real model.

| Field | Value |
| --- | --- |
| Size | 24 cases (6 × 4 families) |
| Families | `structured_extraction`, `tool_selection`, `context_retention`, `safety_escalation` |
| Review status | All `owner_reviewed` (foundation release) |
| Source | `synthetic:prism-generator` (`src/prism/dataset/generate.py`) |
| License | CC‑BY‑4.0 (provenance metadata on every case) |
| Owner | atomicz |
| PII | None. No personal, employer‑confidential or exam‑derived content. |

## Source & generation

Cases are defined in code (`src/prism/dataset/generate.py`) and materialized to
`data/cases/<family>/<case_id>.json` by `prism dataset build`. Defining them in code
guarantees the stored `case_digest` always matches the payload. Each case carries
`provenance` with `origin_note`: *"Original invented content; not derived from any exam or
third‑party source."*

The content is deliberately invented (fictional depots, orders, tickets, bookings). It was
inspired only by broad *categories* of AI‑system tasks — never by any specific certification
practice question. Private question banks are kept outside the repository and are ignored
defensively (`.gitignore`: `CCAR-*`, `*preguntas*`, `Downloads/`).

## Structure of a case

```
family, prompt, context[]           # the task
expected_output                     # the reference answer
grading.output_schema               # JSON Schema for schema-validity
behavior_class                      # normal | should_abstain | should_escalate | should_refuse
review_label, provenance, case_digest
```

`behavior_class` drives the abstention/escalation denominators. Distribution: 18 `normal`,
1 `should_abstain`, 3 `should_escalate`, 2 `should_refuse` (6 `should_*` in total), plus
2 benign safety **controls** used to measure over‑refusal.

## Grading

Graders (`src/prism/dataset/grading.py`) dispatch by family. Every grader checks schema
validity (jsonschema Draft 2020‑12) then family‑specific correctness, and reports
`abstention_correct` for `should_*` cases. Grading is pure and deterministic.

## Fixture profiles (not part of the case dataset)

Two profiles provide the *simulated answers*. They are synthetic, owner‑authored, and each
deliberate miss uses an explicit hand‑written wrong answer (`src/prism/dataset/profiles_gen.py`).
No profile represents, or is named after, any real provider.

## Intended use

Educational demonstration of task‑specific evaluation, reproducibility and honest uncertainty.
Suitable for teaching how to define "good enough" per task and constraint.

## Out‑of‑scope / limitations

- **Not** a measurement of any named model or provider.
- **Not** a general‑purpose benchmark; 24 cases is intentionally small.
- Simulated latency and cost — not real timings or billed cost.
- Small samples: most per‑family confidence intervals are suppressed by design.
- English‑only, narrow domain; not representative of production traffic.

## Maintenance

New or expanded cases enter as `generated_unreviewed` and are excluded from release metrics
(counted in `excluded_count`) until an owner promotes them to `owner_reviewed`. Promotion does
not change a case's `case_digest` (the label is not part of content identity).
