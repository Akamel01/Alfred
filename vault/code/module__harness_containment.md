---
kind: module
id: "module:harness.containment"
title: "harness.containment"
shape: "package"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/containment:1"
extractor: "code"
tags: [protected]
aliases:
  - "harness.containment"
generated: true
---

# harness.containment

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/containment:1`

## Fields

| Field | Value |
|---|---|
| `namespace_package` | false |
| `tree` | harness |

## Binds

- **contains** → [[module__harness_containment___init__|Containment assertions: what the sandbox must prove before a run starts.]]
- **contains** → [[module__harness_containment_assertions|Three outcomes for a containment assertion, and the third is the dangerous one.]]
- **contains** → [[module__harness_containment_denylist|Load the oracle denylist and give it a digest the fingerprint can carry.]]
- **contains** → [[module__harness_containment_egress|C6 — the egress canary, and the control that stops it being vacuous.]]
- **contains** → [[module__harness_containment_oracle_absence|C7 — the oracle is absent, asserted rather than assumed.]]
- **contains** → [[module__harness_containment_test_containment|Containment assertions, each paired with the control that stops it reading green.]]
