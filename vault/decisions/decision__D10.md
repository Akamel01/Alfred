---
kind: decision
id: "decision:D10"
title: "Hard blast-radius separation"
shape: "table-row"
number: "10"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:54"
extractor: "decisions"
aliases:
  - "D10"
  - "Hard blast-radius separation"
generated: true
---

# Hard blast-radius separation

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:54`

## Statement

**Hard blast-radius separation.** Ephemeral container, throwaway DB from migrations, no production credentials in context, output is a PR only. Deploy stays CI-triggered on merge.

## Fields

| Field | Value |
|---|---|
| `rationale` | Worst case from a fully compromised agent is a pull request that gets declined. |

## Enforced by (code)

- **enforced_by** → [[module__bench_toy_tasks|Phase -1 toy tasks: is the narrow task class within reach of a local model?]] — """Phase -1 toy tasks: is the narrow task class within reach of a local model?

Each task is shaped like the real Phase 
