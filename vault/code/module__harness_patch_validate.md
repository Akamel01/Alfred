---
kind: module
id: "module:harness.patch.validate"
title: "Validates a patch before anything touches a tree. Runs outside the container."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/patch/validate.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Validates a patch before anything touches a tree. Runs outside the container."
  - "harness.patch.validate"
generated: true
---

# Validates a patch before anything touches a tree. Runs outside the container.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/patch/validate.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/patch/validate.py |
| `tree` | harness |

## Binds

- [[module__harness_patch|harness.patch]] **contains** → this
- [[module__harness_patch_test_validate|Every refusal in the patch gate, planted and caught.]] **imports** → this

## Enforced by (code)

- [[decision__D20|Agents may improve the factory, never the inspector]] **enforced_by** → this — """Validates a patch before anything touches a tree. Runs outside the container.

A2: the container holds no VCS credent
- [[decision__D20|Agents may improve the factory, never the inspector]] **enforced_by** → this — # Inspector machinery (D20). Prefix match on a repo-relative POSIX path.
- [[decision__D32|All 55 documents written as stubs; full content only for the ~12–15 Phase 0 can falsify]] **enforced_by** → this — "content here is read as instructions by a later agent; it is the D32 "
