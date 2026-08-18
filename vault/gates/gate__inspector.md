---
kind: gate
id: "gate:inspector"
title: "inspector (ACS-1, lane, bench)"
shape: "job"
job: "inspector"
source: ".github/workflows/gates.yml:175"
extractor: "workflows"
tags: [protected]
aliases:
  - "inspector"
  - "inspector (ACS-1, lane, bench)"
generated: true
---

# inspector (ACS-1, lane, bench)

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:175`

## Fields

| Field | Value |
|---|---|
| `ordinal` | 3 |

## Binds

- **contains** → [[gate-step__inspector_01|Install uv]]
- **contains** → [[gate-step__inspector_02|Set up Python]]
- **contains** → [[gate-step__inspector_03|Sync dependencies from the lockfile]]
- **contains** → [[gate-step__inspector_04|ACS-1 — Python conformance]]
- **contains** → [[gate-step__inspector_05|ACS-1 — JavaScript conformance]]
- **contains** → [[gate-step__inspector_06|bench harness self-tests]]
- **contains** → [[gate-step__inspector_07|Lane controls]]
- **contains** → [[gate-step__inspector_08|Containment probes (C6 egress canary, C7 oracle absence)]]
- **needs** → [[gate__integrity|integrity (fixtures and register)]]
- [[gate__mutation|mutation control (the suite's own negative control)]] **needs** → this
