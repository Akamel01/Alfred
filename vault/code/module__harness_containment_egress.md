---
kind: module
id: "module:harness.containment.egress"
title: "C6 — the egress canary, and the control that stops it being vacuous."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/containment/egress.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "C6 — the egress canary, and the control that stops it being vacuous."
  - "harness.containment.egress"
generated: true
---

# C6 — the egress canary, and the control that stops it being vacuous.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/containment/egress.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/containment/egress.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_containment_assertions|Three outcomes for a containment assertion, and the third is the dangerous one.]]
- [[module__harness_containment|harness.containment]] **contains** → this
- [[module__harness_containment_test_containment|Containment assertions, each paired with the control that stops it reading green.]] **imports** → this
