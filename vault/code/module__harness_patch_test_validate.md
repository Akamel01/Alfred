---
kind: module
id: "module:harness.patch.test_validate"
title: "Every refusal in the patch gate, planted and caught."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/patch/test_validate.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Every refusal in the patch gate, planted and caught."
  - "harness.patch.test_validate"
generated: true
---

# Every refusal in the patch gate, planted and caught.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/patch/test_validate.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | true |
| `path` | harness/patch/test_validate.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_patch_validate|Validates a patch before anything touches a tree. Runs outside the container.]]
- [[module__harness_patch|harness.patch]] **contains** → this
