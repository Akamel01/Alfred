---
kind: module
id: "module:harness.patch.test_protected_set"
title: "The protected set is policy configuration, and the policy is one home (ADR-0031)."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/patch/test_protected_set.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "The protected set is policy configuration, and the policy is one home (ADR-0031)."
  - "harness.patch.test_protected_set"
generated: true
---

# The protected set is policy configuration, and the policy is one home (ADR-0031).

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/patch/test_protected_set.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | true |
| `path` | harness/patch/test_protected_set.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_patch_validate|Validates a patch before anything touches a tree. Runs outside the container.]]
- [[module__harness_patch|harness.patch]] **contains** → this

## Enforced by (code)

- [[adr__ADR-0009|The grant matrix is asserted by set equality, and converging by REVOKE strips ownership]] **enforced_by** → this — """The protected set is policy configuration, and the policy is one home (ADR-0031).

Three things must agree: `policy/p
- [[adr__ADR-0031|The protected set is one file, and the gate protects its own policy]] **enforced_by** → this — """The protected set is policy configuration, and the policy is one home (ADR-0031).

Three things must agree: `policy/p
- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — """D57. A set that enumerates nothing protects nothing, and passes everything."""
