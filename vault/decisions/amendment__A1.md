---
kind: amendment
id: "amendment:A1"
title: "`CriterionRunner` runs outside the agent's tree"
shape: "table-row"
number: "A1"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:175"
extractor: "amendments"
aliases:
  - "A1"
  - "`CriterionRunner` runs outside the agent's tree"
generated: true
---

# `CriterionRunner` runs outside the agent's tree

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:175`

## Statement

**`CriterionRunner` runs outside the agent's tree** and materializes the test environment itself from trusted provenance, ignoring everything outside declared source paths. Add a **null-agent floor test** — a run taking no actions, whose score is the harness's floor — as a standing Phase 0 criterion.

## Fields

**evidence**

> BenchJack forced 100% resolve on all 500 SWE-bench Verified instances with a ~7-line `conftest.py`. No test file touched. Closes the entire class (`conftest.py`, `.pth`, `sitecustomize`, binary trojans) architecturally rather than by enumeration. Supersedes decision 11's enumerate-the-bad primitive.

## Stated in prose — unverified

- **amends** → [[decision__D11|Protected paths are harness-enforced]] — D11 named in A1
