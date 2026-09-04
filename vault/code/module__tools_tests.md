---
kind: module
id: "module:tools.tests"
title: "tools.tests"
shape: "package"
present: "true"
protected: "false"
lint_gated: "false"
source: "tools/tests:1"
extractor: "code"
aliases:
  - "tools.tests"
generated: true
---

# tools.tests

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `tools/tests:1`

## Fields

| Field | Value |
|---|---|
| `namespace_package` | true |
| `tree` | tools |

## Binds

- **contains** → [[module__tools_tests_test_orchestration|Orchestration palette binding + topology validation.]]
- **contains** → [[module__tools_tests_test_protected_binding|The vault's `protected` node flag answers to the policy file, not to a hand copy.]]
- **contains** → [[module__tools_tests_test_render|The renderers: the vault tree, and the published artifact.]]
- **contains** → [[module__tools_tests_test_serve|The local refresh surface, and the four controls that keep it from being a liability.]]
- **contains** → [[module__tools_tests_test_vaultgraph|The generator's own guards, asserted from outside the generator.]]
- [[gate-step__integrity_30|Vault generator suites]] **runs** → this
