---
kind: decision
id: "decision:D24"
title: "One criterion = one task"
shape: "table-row"
number: "24"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:68"
extractor: "decisions"
aliases:
  - "D24"
  - "One criterion = one task"
generated: true
---

# One criterion = one task

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:68`

## Statement

**One criterion = one task.** Agents may create subtasks freely, each receiving its own budget allocation.

## Fields

| Field | Value |
|---|---|
| `rationale` | Chosen for throughput and to let decomposition scale without human involvement. **Known exposure, accepted:** budget ceilings become advisory, since an agent approaching its cap can split into subtasks that each receive fresh budget. No malice is required — it is the locally rational move under a constraint. A global tree cap would have preserved the same agent freedom while bounding total spend;  |
