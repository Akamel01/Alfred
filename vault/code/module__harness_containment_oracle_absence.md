---
kind: module
id: "module:harness.containment.oracle_absence"
title: "C7 — the oracle is absent, asserted rather than assumed."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/containment/oracle_absence.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "C7 — the oracle is absent, asserted rather than assumed."
  - "harness.containment.oracle_absence"
generated: true
---

# C7 — the oracle is absent, asserted rather than assumed.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/containment/oracle_absence.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/containment/oracle_absence.py |
| `tree` | harness |

## Binds

- [[module__harness_containment|harness.containment]] **contains** → this

## Enforced by (code)

- [[decision__D50|The oracle is absent from the execution plane by assertion, not by convention]] **enforced_by** → this — """C7 — the oracle is absent, asserted rather than assumed.

If `commonroad_crime` is importable where agent-authored co
