---
kind: decision
id: "decision:D2"
title: "Product is **backend/data-heavy** with thin UI"
shape: "table-row"
number: "2"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:46"
extractor: "decisions"
aliases:
  - "D2"
  - "Product is **backend/data-heavy** with thin UI"
generated: true
---

# Product is **backend/data-heavy** with thin UI

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:46`

## Statement

Product is **backend/data-heavy** with thin UI.

## Fields

| Field | Value |
|---|---|
| `rationale` | Correctness must be machine-checkable. UI-led products have no automated verdict, making evaluation and self-improvement structurally impossible. |
