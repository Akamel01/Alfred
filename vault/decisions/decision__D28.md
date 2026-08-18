---
kind: decision
id: "decision:D28"
title: "Stage gates are executable where measurable; overriding one requires an immutable waiver ADR"
shape: "table-row"
number: "28"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:72"
extractor: "decisions"
aliases:
  - "D28"
  - "Stage gates are executable where measurable; overriding one requires an immutable waiver A"
generated: true
---

# Stage gates are executable where measurable; overriding one requires an immutable waiver ADR

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:72`

## Statement

**Stage gates are executable where measurable; overriding one requires an immutable waiver ADR** recording gate, threshold, actual value, reason, and the condition that would reverse it.

## Fields

| Field | Value |
|---|---|
| `rationale` | Every forbidden-advancement condition in this plan is a promise made to a future self who will be under pressure and will want to proceed. A gate that can be waived silently is a note, not a gate — but an unwaivable gate gets bypassed entirely rather than adjusted honestly. Making the override expensive and permanent is the realistic control. Waiver count becomes its own health metric. Note this i |
