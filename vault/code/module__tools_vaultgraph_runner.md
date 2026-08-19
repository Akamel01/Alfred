---
kind: module
id: "module:tools.vaultgraph.runner"
title: "Runs the registry and fails on every way an extraction can be quietly empty."
shape: "module"
present: "true"
protected: "false"
lint_gated: "false"
source: "tools/vaultgraph/runner.py:1"
extractor: "code"
aliases:
  - "Runs the registry and fails on every way an extraction can be quietly empty."
  - "tools.vaultgraph.runner"
generated: true
---

# Runs the registry and fails on every way an extraction can be quietly empty.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `tools/vaultgraph/runner.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | tools/vaultgraph/runner.py |
| `tree` | tools |

## Binds

- **imports** → [[module__tools_vaultgraph|tools.vaultgraph]]
- **imports** → [[module__tools_vaultgraph_model|The graph's type vocabulary: what a node is, what an edge is, and how ids are minted.]]
- **imports** → [[module__tools_vaultgraph_protocol|The extractor contract, shaped so a missing vacuity guard is impossible rather than unlike]]
- [[module__tools_vaultgraph|tools.vaultgraph]] **contains** → this
- [[module__tools_tests_test_render|The renderers: the vault tree, and the published artifact.]] **imports** → this
- [[module__tools_tests_test_serve|The local refresh surface, and the four controls that keep it from being a liability.]] **imports** → this
- [[module__tools_tests_test_vaultgraph|The generator's own guards, asserted from outside the generator.]] **imports** → this
- [[module__tools_vaultgraph_selftest|Planted fixtures that prove the guards fire, and a clean control that proves they are quie]] **imports** → this
- [[module__tools_vaultgraph_serialize|Canonical JSON. The rules here are the whole of the determinism guarantee.]] **imports** → this
