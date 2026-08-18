---
kind: decision
id: "decision:D36"
title: "Acceptance requires held-out pass; retries select only against visible criteria; the agent never sees held-out results"
shape: "table-row"
number: "36"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:80"
extractor: "decisions"
aliases:
  - "Acceptance requires held-out pass; retries select only against visible criteria; the agent"
  - "D36"
generated: true
---

# Acceptance requires held-out pass; retries select only against visible criteria; the agent never sees held-out results

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:80`

## Statement

**Acceptance requires held-out pass; retries select only against visible criteria; the agent never sees held-out results.** Merge rate is measured **per task after a bounded retry budget**, not per attempt. Phase 1's ≥50% gate is kept and met by **narrowing the task class**, never by lowering the bar.

## Fields

| Field | Value |
|---|---|
| `rationale` | Free inference turns retry-until-green into a search process sampling the distribution of solutions that pass visible checks — some fraction of which fail held-out. Expensive inference accidentally capped that search via budget; local removes the accidental protection, which promotes A3 from hardening to load-bearing. Per-task-after-retries is the honest unit when attempts are free. The gate then  |

## Enforced by (code)

- **enforced_by** → [[module__bench_toy_tasks|Phase -1 toy tasks: is the narrow task class within reach of a local model?]] — """Phase -1 toy tasks: is the narrow task class within reach of a local model?

Each task is shaped like the real Phase 
