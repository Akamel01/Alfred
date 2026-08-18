---
kind: decision
id: "decision:D33"
title: "Graduation calibrates on held-out pass rate only"
shape: "table-row"
number: "33"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:77"
extractor: "decisions"
aliases:
  - "D33"
  - "Graduation calibrates on held-out pass rate only"
generated: true
---

# Graduation calibrates on held-out pass rate only

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:77`

## Statement

**Graduation calibrates on held-out pass rate only.** A criterion is redefined as *(assertion + interface signature + threshold provenance)*.

## Fields

**rationale**

> Calibrating on visible-criterion pass rate would certify exactly the agents that reward-hack hardest, since hacking agents saturate the visible suite by definition — SpecBench shows validation scores near-identical across scaffolds while held-out scores diverge 43–48pp. The interface-signature component is required because SWE-bench Pro had to bolt human-authored interface specs onto every task: valid solutions were failing as false negatives against under-determined executable criteria. That component cannot fully graduate to agents, since it is the thing preventing those false negatives.

## Enforced by (code)

- **enforced_by** → [[module__harness_criterion_runner|Compose one verdict, and keep the held-out half out of the environment that runs.]] — # decide acceptance — which is the calibration failure D33 exists to prevent.
