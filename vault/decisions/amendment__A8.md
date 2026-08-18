---
kind: amendment
id: "amendment:A8"
title: "Organizing principle amended"
shape: "table-row"
number: "A8"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:182"
extractor: "amendments"
aliases:
  - "A8"
  - "Organizing principle amended"
generated: true
---

# Organizing principle amended

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:182`

## Statement

**Organizing principle amended**: ground truth the agent did not author **and cannot retrieve**. Reference values held out of agent context and network reach, injected by `CriterionRunner` at verdict time, plus held-out perturbations on resampled slices whose answers were never published.

## Fields

| Field | Value |
|---|---|
| `evidence` | NetArena committed all 5,000 ground-truth tuples to a public repo; GAIA's answers are readable at runtime. Phase 0 deliberately targets *published* values, and training-data contamination survives any network policy. |
