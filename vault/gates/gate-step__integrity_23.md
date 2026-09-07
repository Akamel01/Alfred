---
kind: gate-step
id: "gate-step:integrity.23"
title: "Bench records are append-only (bench/results/, bench/fingerprints/)"
shape: "step"
job: "integrity"
source: ".github/workflows/gates.yml:223"
extractor: "workflows"
tags: [protected]
aliases:
  - "Bench records are append-only (bench/results/, bench/fingerprints/)"
  - "integrity.23"
generated: true
---

# Bench records are append-only (bench/results/, bench/fingerprints/)

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:223`

## Statement

python3 scripts/lint_bench_append_only.py

## Fields

| Field | Value |
|---|---|
| `command` | python3 scripts/lint_bench_append_only.py |
| `kind` | run |
| `ordinal` | 23 |

## Binds

- **runs** → [[module__scripts_lint_bench_append_only|`bench/results/` and `bench/fingerprints/` are append-only. This is what says so.]]
- [[gate__integrity|integrity (fixtures and register)]] **contains** → this
