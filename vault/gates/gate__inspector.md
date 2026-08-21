---
kind: gate
id: "gate:inspector"
title: "inspector (ACS-1, lane, bench)"
shape: "job"
job: "inspector"
source: ".github/workflows/gates.yml:219"
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

**Source** · `.github/workflows/gates.yml:219`

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
- **contains** → [[gate-step__inspector_08|Containment (C6, C7 probes; C8-C15; and the O5 shells that must not pass)]]
- **contains** → [[gate-step__inspector_09|Harness self-test (null-agent floor, seeded-defect ladder, controls)]]
- **contains** → [[gate-step__inspector_10|Oracle boundary (pins, refusals, admissibility)]]
- **contains** → [[gate-step__inspector_11|Deploy and rollback (ledger, identity, refusals)]]
- **contains** → [[gate-step__inspector_12|Worker port (claim/fault split, containment refusals)]]
- **contains** → [[gate-step__inspector_13|Patch gate (protected paths, A10 invisibles, import hooks)]]
- **contains** → [[gate-step__inspector_14|Stamp (version, upstream union, total verifier)]]
- **contains** → [[gate-step__inspector_15|Run fingerprint record (field set, derived digest, register agreement)]]
- **needs** → [[gate__integrity|integrity (fixtures and register)]]
- [[gate__mutation|mutation control (the suite's own negative control)]] **needs** → this
