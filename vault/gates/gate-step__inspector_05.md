---
kind: gate-step
id: "gate-step:inspector.05"
title: "ACS-1 — JavaScript conformance"
shape: "step"
job: "inspector"
source: ".github/workflows/gates.yml:309"
extractor: "workflows"
tags: [protected]
aliases:
  - "ACS-1 — JavaScript conformance"
  - "inspector.05"
generated: true
---

# ACS-1 — JavaScript conformance

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:309`

## Statement

node harness/acs/verify_js.mjs

## Fields

| Field | Value |
|---|---|
| `command` | node harness/acs/verify_js.mjs |
| `kind` | run |
| `ordinal` | 5 |

## Binds

- **runs** → [[module__harness_acs_verify_js_mjs|Verify the JavaScript implementation against the published ACS-1 vector suite.]]
- [[gate__inspector|inspector (ACS-1, lane, bench)]] **contains** → this
