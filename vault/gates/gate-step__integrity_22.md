---
kind: gate-step
id: "gate-step:integrity.22"
title: "Bench append-only lint checks its own vacuity"
shape: "step"
job: "integrity"
source: ".github/workflows/gates.yml:220"
extractor: "workflows"
tags: [protected]
aliases:
  - "Bench append-only lint checks its own vacuity"
  - "integrity.22"
generated: true
---

# Bench append-only lint checks its own vacuity

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:220`

## Statement

python3 scripts/lint_bench_append_only.py --self-test

## Fields

| Field | Value |
|---|---|
| `command` | python3 scripts/lint_bench_append_only.py --self-test |
| `kind` | run |
| `ordinal` | 22 |

## Binds

- **runs** → [[module__scripts_lint_bench_append_only|`bench/results/` and `bench/fingerprints/` are append-only. This is what says so.]]
- [[gate__integrity|integrity (fixtures and register)]] **contains** → this
