---
kind: module
id: "module:harness.patch.test_import_hook_binding"
title: "The import-hook lists in `criterion.materialize` and `patch.validate` answer to each other."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/patch/test_import_hook_binding.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "The import-hook lists in `criterion.materialize` and `patch.validate` answer to each other"
  - "harness.patch.test_import_hook_binding"
generated: true
---

# The import-hook lists in `criterion.materialize` and `patch.validate` answer to each other.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/patch/test_import_hook_binding.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | true |
| `path` | harness/patch/test_import_hook_binding.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_criterion_materialize|Build the criterion environment from an allowlist, never from the candidate tree.]]
- **imports** → [[module__harness_patch_validate|Validates a patch before anything touches a tree. Runs outside the container.]]
- [[module__harness_patch|harness.patch]] **contains** → this

## Enforced by (code)

- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — """Vacuity guard (D57): two empty copies agree perfectly and refuse nothing.

    Equality alone would pass on two sets 
