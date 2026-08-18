---
kind: decision
id: "decision:D7"
title: "The adversary is **deterministic tooling, not a second LLM**: Hypothesis property tests primary, mutmut secondary"
shape: "table-row"
number: "7"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:51"
extractor: "decisions"
aliases:
  - "D7"
  - "The adversary is **deterministic tooling, not a second LLM**: Hypothesis property tests pr"
generated: true
---

# The adversary is **deterministic tooling, not a second LLM**: Hypothesis property tests primary, mutmut secondary

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:51`

## Statement

The adversary is **deterministic tooling, not a second LLM**: Hypothesis property tests primary, mutmut secondary.

## Fields

| Field | Value |
|---|---|
| `rationale` | Properties encode intent over generated inputs; the agent cannot special-case past inputs it never sees. Mutation score measures branch coverage only. An LLM adversary is reserved for what neither reaches: missing requirements. |

## Stated in prose — unverified

- [[amendment__A5|Property tests over COMPOSED operations become the load-bearing correctness control]] **amends** → this — D7 named in A5
