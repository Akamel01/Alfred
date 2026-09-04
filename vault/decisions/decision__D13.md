---
kind: decision
id: "decision:D13"
title: "Python throughout"
shape: "table-row"
number: "13"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:57"
extractor: "decisions"
aliases:
  - "D13"
  - "Python throughout"
generated: true
---

# Python throughout

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:57`

## Statement

**Python throughout.** `uv`, `ruff`, `pytest` + `hypothesis`, `pyright --strict`, FastAPI + Pydantic, Alembic, Postgres, Docker.

## Fields

| Field | Value |
|---|---|
| `rationale` | Single toolchain. Pydantic gives executable contracts. Hypothesis is the strongest available adversary. numpy/scipy is correct for the domain. |

## Enforced by (code)

- **enforced_by** → [[module__scripts_lint_invariants|Cross-stage invariants (I1–I17), and the map of what actually enforces each one.]] — "no long-running endpoint exists yet; S8 under D13"
