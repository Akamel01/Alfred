---
kind: amendment
id: "amendment:A6"
title: "Extend the decision 19 fingerprint"
shape: "table-row"
number: "A6"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:180"
extractor: "amendments"
aliases:
  - "A6"
  - "Extend the decision 19 fingerprint"
generated: true
---

# Extend the decision 19 fingerprint

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:180`

## Statement

**Extend the decision 19 fingerprint** to add: resolved lockfile hash, hash of every tool *description* in context, criterion-set version **and expiry**, turn/cost budget.

## Fields

**evidence**

> MCP tool-poisoning changes behavior via descriptions without changing names. `langgraph-prebuilt` 1.0.2 broke `ToolNode.afunc` with an unconstrained dependency. Two professionally-maintained criterion sets rotted within six months. Terminal-Bench 2.0's top four differ by 2.5pp across harnesses — same order as the error bars.

## Stated in prose — unverified

- **amends** → [[decision__D19|Autonomy grants are keyed to a fingerprint]] — D19 named in A6
