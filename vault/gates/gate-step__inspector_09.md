---
kind: gate-step
id: "gate-step:inspector.09"
title: "Harness self-test (null-agent floor, seeded-defect ladder, controls)"
shape: "step"
job: "inspector"
source: ".github/workflows/gates.yml:314"
extractor: "workflows"
tags: [protected]
aliases:
  - "Harness self-test (null-agent floor, seeded-defect ladder, controls)"
  - "inspector.09"
generated: true
---

# Harness self-test (null-agent floor, seeded-defect ladder, controls)

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:314`

## Statement

uv run pytest harness/selftest

## Fields

| Field | Value |
|---|---|
| `command` | uv run pytest harness/selftest |
| `kind` | run |
| `ordinal` | 9 |

## Binds

- **runs** → [[module__harness_selftest|harness.selftest]]
- [[gate__inspector|inspector (ACS-1, lane, bench)]] **contains** → this
