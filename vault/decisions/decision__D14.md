---
kind: decision
id: "decision:D14"
title: "Batch replay first; streaming later"
shape: "table-row"
number: "14"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:58"
extractor: "decisions"
aliases:
  - "Batch replay first; streaming later"
  - "D14"
generated: true
---

# Batch replay first; streaming later

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:58`

## Statement

**Batch replay first; streaming later.** Phase 0 ingests a scenario log and returns metrics deterministically.

## Fields

**rationale**

> The replay harness is permanent infrastructure — it is how streaming gets validated, how agent changes get scored, and how customer-reported discrepancies get reproduced. Building it first is not a detour.
