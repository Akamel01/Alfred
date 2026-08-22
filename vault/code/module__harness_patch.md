---
kind: module
id: "module:harness.patch"
title: "harness.patch"
shape: "package"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/patch:1"
extractor: "code"
tags: [protected]
aliases:
  - "harness.patch"
generated: true
---

# harness.patch

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/patch:1`

## Fields

| Field | Value |
|---|---|
| `namespace_package` | false |
| `tree` | harness |

## Binds

- **contains** → [[module__harness_patch___init__|harness/patch/__init__.py]]
- **contains** → [[module__harness_patch_test_import_hook_binding|The import-hook lists in `criterion.materialize` and `patch.validate` answer to each other]]
- **contains** → [[module__harness_patch_test_protected_set|The protected set is policy configuration, and the policy is one home (ADR-0031).]]
- **contains** → [[module__harness_patch_test_validate|Every refusal in the patch gate, planted and caught.]]
- **contains** → [[module__harness_patch_validate|Validates a patch before anything touches a tree. Runs outside the container.]]
- [[gate-step__inspector_13|Patch gate (protected paths, A10 invisibles, import hooks)]] **runs** → this
