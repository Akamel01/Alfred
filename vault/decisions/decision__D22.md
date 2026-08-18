---
kind: decision
id: "decision:D22"
title: "Review is criterion-first, diff on signal"
shape: "table-row"
number: "22"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:66"
extractor: "decisions"
aliases:
  - "D22"
  - "Review is criterion-first, diff on signal"
generated: true
---

# Review is criterion-first, diff on signal

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:66`

## Statement

**Review is criterion-first, diff on signal.** Reviewer reads intent → criterion → evidence bundle → diff summary; full diff only when something looks wrong. Review time is recorded as a task-size signal.

## Fields

**rationale**

> If the harness verified correctness, a human reading the diff for bugs duplicates the harness — and that duplication is where review fatigue comes from. The human checks what the harness structurally cannot: whether the criterion was the right criterion, whether the agent solved the stated problem or a nearby easier one, future coupling cost, and whether a metric's validity envelope is honestly stated.
