---
kind: index
title: "Anomalies"
generated: true
---

# Anomalies

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

Discrepancies the generator found and deliberately did not resolve. A generator that picked a side here would be asserting something it does not know.

## Surfaced

| Kind | Detail |
|---|---|
| `adr-numbering-gap` | the log is append-only and numbers are never reused; missing: ADR-0029, ADR-0030 |
| `discharge-target-absent` | ADR-0018 declares **Discharges:** O5, and no operator-item by that name is declared |
| `operator-item-count` | 8 operator items found, 9 declared in the execution order |
| `risk-register-order` | the risk register is not in numeric order: R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R12, R11 |

## Not parsed

Constructs matched by an extractor and left unresolved. The budget for these is committed per extractor, so this list shrinking is progress and it growing is a build failure.

| Source | Text | Reason |
|---|---|---|
| `docs/tier2/execution-order.md:132` | every verdict ever recorded | dependency names no target this graph can resolve |
