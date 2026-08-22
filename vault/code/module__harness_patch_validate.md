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
- [[module__harness_patch_test_import_hook_binding|The import-hook lists in `criterion.materialize` and `patch.validate` answer to each other]] **imports** → this
- [[module__harness_patch_test_protected_set|The protected set is policy configuration, and the policy is one home (ADR-0031).]] **imports** → this
- [[module__harness_patch_test_validate|Every refusal in the patch gate, planted and caught.]] **imports** → this

## Enforced by (code)

- [[adr__ADR-0031|The protected set is one file, and the gate protects its own policy]] **enforced_by** → this — """Validates a patch before anything touches a tree. Runs outside the container.

A2: the container holds no VCS credent
- [[adr__ADR-0031|The protected set is one file, and the gate protects its own policy]] **enforced_by** → this — # The protected set as policy configuration (ADR-0031). The file is under `policy/` —
- [[decision__D20|Agents may improve the factory, never the inspector]] **enforced_by** → this — """Validates a patch before anything touches a tree. Runs outside the container.

A2: the container holds no VCS credent
- [[decision__D20|Agents may improve the factory, never the inspector]] **enforced_by** → this — "configuration and never agent-writable (D20)"
- [[decision__D20|Agents may improve the factory, never the inspector]] **enforced_by** → this — "configuration and never agent-writable (D20)"
- [[decision__D32|All 55 documents written as stubs; full content only for the ~12–15 Phase 0 can falsify]] **enforced_by** → this — "content here is read as instructions by a later agent; it is the D32 "
- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — """Read the protected set, refusing every way it can be missing.

    Failing open is not an option for the file a gate 
- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — "and a gate that passes everything is a formality (D57)"
- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — """Read a unified diff and report every reason it must not be applied.

    Every finding is collected rather than raisi
