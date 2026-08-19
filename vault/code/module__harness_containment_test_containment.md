---
kind: module
id: "module:harness.containment.test_containment"
title: "Containment assertions, each paired with the control that stops it reading green."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/containment/test_containment.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Containment assertions, each paired with the control that stops it reading green."
  - "harness.containment.test_containment"
generated: true
---

# Containment assertions, each paired with the control that stops it reading green.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/containment/test_containment.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | true |
| `path` | harness/containment/test_containment.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_containment_assertions|Three outcomes for a containment assertion, and the third is the dangerous one.]]
- **imports** → [[module__harness_containment_denylist|Load the oracle denylist and give it a digest the fingerprint can carry.]]
- **imports** → [[module__harness_containment_egress|C6 — the egress canary, and the control that stops it being vacuous.]]
- **imports** → [[module__harness_containment_oracle_absence|C7 — the oracle is absent, asserted rather than assumed.]]
- [[module__harness_containment|harness.containment]] **contains** → this

## Enforced by (code)

- [[adr__ADR-0007|Executor-premise assertions may pass vacuously, and that is a third outcome]] **enforced_by** → this — """ADR-0007: an assertion may be executed, passed, and vacuous.

    Not representable in the three-valued outcome, so i
- [[decision__D54|D50 is enforced by an environment split, not by a check alone: the oracle's outputs cross ]] **enforced_by** → this — """A silent reclassification changes the fingerprint.

    The reasons are the recorded human judgement D54 asks for. If
- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — """Containment assertions, each paired with the control that stops it reading green.

**How this suite would be shown va
