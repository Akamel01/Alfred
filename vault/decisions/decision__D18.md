---
kind: decision
id: "decision:D18"
title: "Agents are capability-scoped, never role-scoped"
shape: "table-row"
number: "18"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:62"
extractor: "decisions"
aliases:
  - "Agents are capability-scoped, never role-scoped"
  - "D18"
generated: true
---

# Agents are capability-scoped, never role-scoped

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:62`

## Statement

**Agents are capability-scoped, never role-scoped.** An agent is `(input contract, output contract, tools, permissions, criteria, escalation)` — never a job title.

## Fields

**rationale**

> A role has no input/output contract, therefore no golden tasks and no measurable merge rate. Role-based agents structurally break the Phase 4 autonomy mechanism. Agents also must justify themselves against a deterministic alternative: open input space and checkable output, or it is a node.
