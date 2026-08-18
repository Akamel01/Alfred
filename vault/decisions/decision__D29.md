---
kind: decision
id: "decision:D29"
title: "Golden tasks pin the parent commit; the set is stratified and accumulates continuously"
shape: "table-row"
number: "29"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:73"
extractor: "decisions"
aliases:
  - "D29"
  - "Golden tasks pin the parent commit; the set is stratified and accumulates continuously"
generated: true
---

# Golden tasks pin the parent commit; the set is stratified and accumulates continuously

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:73`

## Statement

**Golden tasks pin the parent commit; the set is stratified and accumulates continuously.** Successes, failures, near-misses and escalations all enter. Every comparison reports its detectable effect size.

## Fields

| Field | Value |
|---|---|
| `rationale` | Three traps. (a) A set built from successes reads ~100% forever and goes green through changes that break everything else — the failures are the informative half. (b) Once a fix is merged the task is trivial, so tasks must run against the parent tree, not HEAD; this is why SWE-bench is constructed that way. (c) At n=20 and p≈0.6 the standard error is roughly 11pp, so an observed 10pp gain is noise |
