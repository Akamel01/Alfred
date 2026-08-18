---
kind: decision
id: "decision:D5"
title: "The harness executes checks, never the agent"
shape: "table-row"
number: "5"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:49"
extractor: "decisions"
aliases:
  - "D5"
  - "The harness executes checks, never the agent"
generated: true
---

# The harness executes checks, never the agent

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:49`

## Statement

**The harness executes checks, never the agent.** Agent output is a *claim*; the harness produces the *fact*, on a clean checkout, written to an append-only evidence store.

## Fields

| Field | Value |
|---|---|
| `rationale` | If the agent self-reports results, the entire validation system is theatre. |

## Enforced by (code)

- **enforced_by** → [[module__bench_toy_tasks|Phase -1 toy tasks: is the narrow task class within reach of a local model?]] — """Phase -1 toy tasks: is the narrow task class within reach of a local model?

Each task is shaped like the real Phase 
- **enforced_by** → [[module__harness_criterion_runner|Compose one verdict, and keep the held-out half out of the environment that runs.]] — """Sole author of verdicts (D5, D39).

    Holds `alfred_criterion` — the only role with any privilege on `heldout`, and
- **enforced_by** → [[module__migrations_harness_evidence_versions_0001_evidence_base|evidence: run records, verdicts, operator actions, artifacts, defect escapes.]] — # Sole author is CriterionRunner (D5, D39), and that is a grant, not a check in
- **enforced_by** → [[module__migrations_roles_002_grants_sql|migrations/roles/002_grants.sql]] — Sole author of verdicts is CriterionRunner (D5, D39). The harness may
- **enforced_by** → [[module__migrations_roles_grants_yaml|migrations/roles/grants.yaml]] — sole author of verdicts (D5, D39)
