---
kind: decision
id: "decision:D23"
title: "Escalation triggers are structural, not agent-judged"
shape: "table-row"
number: "23"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:67"
extractor: "decisions"
aliases:
  - "D23"
  - "Escalation triggers are structural, not agent-judged"
generated: true
---

# Escalation triggers are structural, not agent-judged

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:67`

## Statement

**Escalation triggers are structural, not agent-judged.** Iteration cap, budget exhaustion, criterion red after N attempts, protected-path attempt, tool unavailable. Agent-initiated escalation is permitted as a budget optimization but never load-bearing. Agent cannot write `blocked` or `complete`. Every escalation carries a structured attempt bundle.

## Fields

| Field | Value |
|---|---|
| `rationale` | Agents almost never stop — default behavior under an unsatisfiable task is a plausible partial solution, not an admission. Escalation therefore cannot depend on the agent recognizing it is stuck, since that is precisely the judgment the failure compromises. An agent that can declare itself blocked can also declare itself done. |

## Enforced by (code)

- **enforced_by** → [[module__migrations_harness_control_versions_0001_control_base|control: work items, fingerprints, protected paths, thresholds.]] — # The caps the attempt inherits (D23). A task with no retry budget is not
