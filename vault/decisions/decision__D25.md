---
kind: decision
id: "decision:D25"
title: "Org-level hard spend ceiling; cost-per-merged-task is a first-class metric"
shape: "table-row"
number: "25"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:69"
extractor: "decisions"
aliases:
  - "D25"
  - "Org-level hard spend ceiling; cost-per-merged-task is a first-class metric"
generated: true
---

# Org-level hard spend ceiling; cost-per-merged-task is a first-class metric

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:69`

## Statement

**Org-level hard spend ceiling; cost-per-merged-task is a first-class metric.** No per-task ceiling. Dispatch halts at a monthly org limit, with real-time alarms. Cost recorded per run, per node, per capability from Phase 2.

## Fields

| Field | Value |
|---|---|
| `rationale` | Cost as a bill is bookkeeping; cost-per-merged-task is what makes capabilities and models comparable. Merge rate alone ranks a 90%/$50 capability above a 60%/$3 one, which is backwards. An autonomy grant must therefore read "X% merge, $Y per success, on fingerprint Z" — all three. Attribution cannot be applied retroactively, so it must exist before it is needed. |
