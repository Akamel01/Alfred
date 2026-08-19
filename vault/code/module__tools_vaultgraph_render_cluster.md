---
kind: module
id: "module:tools.vaultgraph.render.cluster"
title: "What clumps together, computed rather than declared."
shape: "module"
present: "true"
protected: "false"
lint_gated: "false"
source: "tools/vaultgraph/render/cluster.py:1"
extractor: "code"
aliases:
  - "What clumps together, computed rather than declared."
  - "tools.vaultgraph.render.cluster"
generated: true
---

# What clumps together, computed rather than declared.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `tools/vaultgraph/render/cluster.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | tools/vaultgraph/render/cluster.py |
| `tree` | tools |

## Binds

- **imports** → [[module__tools_vaultgraph_model|The graph's type vocabulary: what a node is, what an edge is, and how ids are minted.]]
- [[module__tools_vaultgraph|tools.vaultgraph]] **contains** → this
- [[module__tools_tests_test_render|The renderers: the vault tree, and the published artifact.]] **imports** → this
- [[module__tools_vaultgraph_render_html|The published artifact: one self-contained file built from the same graph the vault is.]] **imports** → this
