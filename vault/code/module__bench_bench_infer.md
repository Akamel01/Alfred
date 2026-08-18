---
kind: module
id: "module:bench.bench_infer"
title: "Phase -1 local-model benchmark."
shape: "file"
present: "true"
protected: "false"
lint_gated: "false"
source: "bench/bench_infer.py:1"
extractor: "code"
aliases:
  - "Phase -1 local-model benchmark."
  - "bench.bench_infer"
generated: true
---

# Phase -1 local-model benchmark.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `bench/bench_infer.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | bench/bench_infer.py |
| `tree` | bench |

## Enforced by (code)

- [[decision__D19|Autonomy grants are keyed to a fingerprint]] **enforced_by** → this — """Phase -1 local-model benchmark.

Measures the three things that decide Alfred's inference lane:

  1. prefill through
- [[decision__D19|Autonomy grants are keyed to a fingerprint]] **enforced_by** → this — """D19/D40 fields obtainable without loading the weights ourselves."""
- [[decision__D19|Autonomy grants are keyed to a fingerprint]] **enforced_by** → this — # into a fingerprint that autonomy grants are keyed on (D19/D40).
- [[decision__D40|fingerprint extension (final form)]] **enforced_by** → this — """Phase -1 local-model benchmark.

Measures the three things that decide Alfred's inference lane:

  1. prefill through
- [[decision__D40|fingerprint extension (final form)]] **enforced_by** → this — """D19/D40 fields obtainable without loading the weights ourselves."""
- [[decision__D40|fingerprint extension (final form)]] **enforced_by** → this — # into a fingerprint that autonomy grants are keyed on (D19/D40).
- [[decision__D40|fingerprint extension (final form)]] **enforced_by** → this — """Reliability, not capability. A schema-capable model still emits invalid
    JSON through a bad serving layer (D40) — 
- [[decision__D45|Caching: three layers, two adopted, one rejected]] **enforced_by** → this — """Phase -1 local-model benchmark.

Measures the three things that decide Alfred's inference lane:

  1. prefill through
- [[decision__D45|Caching: three layers, two adopted, one rejected]] **enforced_by** → this — """Same prefix twice. If the serving stack reuses KV across separate
    requests, the second call is dramatically cheap
