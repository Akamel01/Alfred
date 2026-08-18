---
kind: decision
id: "decision:D31"
title: "LLM judge admitted as an advisory signal only"
shape: "table-row"
number: "31"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:75"
extractor: "decisions"
aliases:
  - "D31"
  - "LLM judge admitted as an advisory signal only"
generated: true
---

# LLM judge admitted as an advisory signal only

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:75`

## Statement

**LLM judge admitted as an advisory signal only.** It may raise escalation and flag suspected reward hacking; it is schema-forbidden from writing any verdict field. It is treated as a capability with golden tasks, a measured false-escalation rate, and its own fingerprint.

## Fields

| Field | Value |
|---|---|
| `rationale` | EvilGenie found LLM judges outperformed held-out tests at reward-hack detection (0 FP / 0 FN across three models) with "only minimal improvement from the use of held out test cases" — so decision 7's original exclusion was a determinism preference presented as an efficacy claim. The evidence is real but weakly powered (27-problem accuracy set; false negatives are uncountable without exhaustive rev |
