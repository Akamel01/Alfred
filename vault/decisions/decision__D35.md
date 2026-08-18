---
kind: decision
id: "decision:D35"
title: "hard constraint"
shape: "table-row"
number: "35"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:79"
extractor: "decisions"
aliases:
  - "D35"
  - "hard constraint"
generated: true
---

# hard constraint

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:79`

## Statement

**Alfred's agents run on local open-weights models exclusively — hard constraint.** Hardware: Mac Studio M4 Max, 128 GB unified memory, 40-core GPU. Current candidate: gpt-oss-120b (MLX 4-bit, ~60–65 GB resident).

## Fields

| Field | Value |
|---|---|
| `rationale` | Chosen for sovereignty and zero marginal token cost, accepting a real capability ceiling: frontier models score 15–18% on private commercial codebases and open weights trail frontier on agentic coding. Structural win: **local weights never get deprecated** — fingerprints stay valid indefinitely and re-qualification becomes chosen, not imposed. Consequences absorbed elsewhere: binding resource beco |
