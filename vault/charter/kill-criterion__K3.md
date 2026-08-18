---
kind: kill-criterion
id: "kill-criterion:K3"
title: "Per-task merge rate below ~50% at Phase 1 exit (**2026-10-07**) after the bounded retry budget, **read as a Wilson 95% interval rather than a point estimate — the criterion fires when the interval's l"
status: "armed"
shape: "table-row"
number: "K3"
source: "docs/tier0/charter-and-non-goals.md:87"
extractor: "charter"
aliases:
  - "K3"
  - "Per-task merge rate below ~50% at Phase 1 exit (**2026-10-07**) after the bounded retry bu"
generated: true
---

# Per-task merge rate below ~50% at Phase 1 exit (**2026-10-07**) after the bounded retry budget, **read as a Wilson 95% interval rather than a point estimate — the criterion fires when the interval's l

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier0/charter-and-non-goals.md:87`

## Statement

Per-task merge rate below ~50% at Phase 1 exit (**2026-10-07**) after the bounded retry budget, **read as a Wilson 95% interval rather than a point estimate — the criterion fires when the interval's lower bound sits below 0.50** (at n=20 that means fewer than 15/20; at n=10, fewer than 9/10)

## Fields

| Field | Value |
|---|---|
| `consequence` | Narrow the task class. Never lower the bar, never add orchestration. |
