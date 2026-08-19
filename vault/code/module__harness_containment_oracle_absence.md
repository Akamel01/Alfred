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

- **imports** → [[module__harness_containment_assertions|Three outcomes for a containment assertion, and the third is the dangerous one.]]
- **imports** → [[module__harness_containment_denylist|Load the oracle denylist and give it a digest the fingerprint can carry.]]
- [[module__harness_containment|harness.containment]] **contains** → this
- [[module__harness_containment_test_c_assertions|C1–C15 beyond the two probes, each paired with the control that stops it reading green.]] **imports** → this
- [[module__harness_containment_test_containment|Containment assertions, each paired with the control that stops it reading green.]] **imports** → this

## Enforced by (code)

- [[decision__D50|The oracle is absent from the execution plane by assertion, not by convention]] **enforced_by** → this — """C7 — the oracle is absent, asserted rather than assumed.

If `commonroad_crime` is importable where agent-authored co
