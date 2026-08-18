---
kind: decision
id: "decision:D11"
title: "Protected paths are harness-enforced"
shape: "table-row"
number: "11"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:55"
extractor: "decisions"
aliases:
  - "D11"
  - "Protected paths are harness-enforced"
generated: true
---

# Protected paths are harness-enforced

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:55`

## Statement

**Protected paths are harness-enforced**, defined by ground-truth provenance (see below).

## Fields

| Field | Value |
|---|---|
| `rationale` | Otherwise the agent can make checks pass by deleting them — a standard reward-hacking outcome, not a hypothetical. |

## Stated in prose — unverified

- [[amendment__A1|`CriterionRunner` runs outside the agent's tree]] **amends** → this — D11 named in A1
