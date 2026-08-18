---
kind: decision
id: "decision:D16"
title: "Verdict fields are owned by deterministic nodes"
shape: "table-row"
number: "16"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:60"
extractor: "decisions"
aliases:
  - "D16"
  - "Verdict fields are owned by deterministic nodes"
generated: true
---

# Verdict fields are owned by deterministic nodes

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:60`

## Statement

**Verdict fields are owned by deterministic nodes.** Agent nodes are schema-forbidden from writing them. Evidence lives in Postgres tables, not in graph state.

## Fields

| Field | Value |
|---|---|
| `rationale` | Resolves the conflict between LangGraph's node-returns-state-update model and decision 5, inside LangGraph's own ownership model rather than fighting it. |

## Enforced by (code)

- **enforced_by** → [[module___github_workflows_gates_yml|.github/workflows/gates.yml]] — D16/D39. LangGraph raises only on *concurrent* unreducered writes, so a
- **enforced_by** → [[module__scripts_lint_verdict_boundary|D16/D39: the verdict boundary, enforced structurally rather than by convention.]] — """D16/D39: the verdict boundary, enforced structurally rather than by convention.

**Why this exists as a lint and not 
- **enforced_by** → [[module__scripts_lint_verdict_boundary|D16/D39: the verdict boundary, enforced structurally rather than by convention.]] — # The vocabulary D16 forbids an agent-invoking node from naming. Deliberately short:
