---
kind: module
id: "module:harness.containment.reassert"
title: "C14 — the end-of-run re-assertion, and why a boot-time pass is not enough."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/containment/reassert.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "C14 — the end-of-run re-assertion, and why a boot-time pass is not enough."
  - "harness.containment.reassert"
generated: true
---

# C14 — the end-of-run re-assertion, and why a boot-time pass is not enough.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/containment/reassert.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/containment/reassert.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_containment_assertions|Three outcomes for a containment assertion, and the third is the dangerous one.]]
- [[module__harness_containment|harness.containment]] **contains** → this
- [[module__harness_containment_test_c_assertions|C1–C15 beyond the two probes, each paired with the control that stops it reading green.]] **imports** → this

## Enforced by (code)

- [[adr__ADR-0007|Executor-premise assertions may pass vacuously, and that is a third outcome]] **enforced_by** → this — # ADR-0007 exists to keep visible.
- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — """C14 — the end-of-run re-assertion, and why a boot-time pass is not enough.

C7, C9, C12, C13 and C16 are asserted bef
- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — """Re-asserted ids present in both reports that **neither side gave any observation for**.

    D57, aimed at this compa
