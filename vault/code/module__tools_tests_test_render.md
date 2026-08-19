---
kind: module
id: "module:tools.tests.test_render"
title: "The renderers: the vault tree, and the published artifact."
shape: "module"
present: "true"
protected: "false"
lint_gated: "false"
source: "tools/tests/test_render.py:1"
extractor: "code"
aliases:
  - "The renderers: the vault tree, and the published artifact."
  - "tools.tests.test_render"
generated: true
---

# The renderers: the vault tree, and the published artifact.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `tools/tests/test_render.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | true |
| `path` | tools/tests/test_render.py |
| `tree` | tools |

## Binds

- **imports** → [[module__tools_vaultgraph_model|The graph's type vocabulary: what a node is, what an edge is, and how ids are minted.]]
- **imports** → [[module__tools_vaultgraph_render_assets|The stylesheet, inlined at build time.]]
- **imports** → [[module__tools_vaultgraph_render_cluster|What clumps together, computed rather than declared.]]
- **imports** → [[module__tools_vaultgraph_render_html|The published artifact: one self-contained file built from the same graph the vault is.]]
- **imports** → [[module__tools_vaultgraph_render_vault|The whole vault as a dict of path to content, built in memory before anything is written.]]
- **imports** → [[module__tools_vaultgraph_runner|Runs the registry and fails on every way an extraction can be quietly empty.]]
- **imports** → [[module__tools_vaultgraph_selftest|Planted fixtures that prove the guards fire, and a clean control that proves they are quie]]
- **imports** → [[module__tools_vaultgraph_serialize|Canonical JSON. The rules here are the whole of the determinism guarantee.]]
- [[module__tools_tests|tools.tests]] **contains** → this
