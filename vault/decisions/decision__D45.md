---
kind: decision
id: "decision:D45"
title: "Caching: three layers, two adopted, one rejected"
shape: "bold-paragraph"
number: "45"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:445"
extractor: "decisions"
aliases:
  - "Caching: three layers, two adopted, one rejected"
  - "D45"
generated: true
---

# Caching: three layers, two adopted, one rejected

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:445`

## Statement

**Decision 45 — Caching: three layers, two adopted, one rejected.**

## Restated at

- `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:464`
- `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:497`

## Enforced by (code)

- **enforced_by** → [[module__bench_bench_infer|Phase -1 local-model benchmark.]] — """Phase -1 local-model benchmark.

Measures the three things that decide Alfred's inference lane:

  1. prefill through
- **enforced_by** → [[module__bench_bench_infer|Phase -1 local-model benchmark.]] — """Same prefix twice. If the serving stack reuses KV across separate
    requests, the second call is dramatically cheap
