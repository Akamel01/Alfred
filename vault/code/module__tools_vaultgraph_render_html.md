---
kind: module
id: "module:tools.vaultgraph.render.html"
title: "The published artifact: one self-contained file built from the same graph the vault is."
shape: "module"
present: "true"
protected: "false"
lint_gated: "false"
source: "tools/vaultgraph/render/html.py:1"
extractor: "code"
aliases:
  - "The published artifact: one self-contained file built from the same graph the vault is."
  - "tools.vaultgraph.render.html"
generated: true
---

# The published artifact: one self-contained file built from the same graph the vault is.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `tools/vaultgraph/render/html.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | tools/vaultgraph/render/html.py |
| `tree` | tools |

## Binds

- **imports** → [[module__tools_vaultgraph_model|The graph's type vocabulary: what a node is, what an edge is, and how ids are minted.]]
- **imports** → [[module__tools_vaultgraph_render_assets|The stylesheet, inlined at build time.]]
- **imports** → [[module__tools_vaultgraph_render_cluster|What clumps together, computed rather than declared.]]
- **imports** → [[module__tools_vaultgraph_render_script|The script, composed at build time from four modules and inlined into one page.]]
- [[module__tools_vaultgraph|tools.vaultgraph]] **contains** → this
- [[module__tools_tests_test_render|The renderers: the vault tree, and the published artifact.]] **imports** → this
- [[module__tools_vaultgraph_render_dataview|Dataview boards. Queries, not materialized tables.]] **imports** → this
- [[module__tools_vaultgraph_render_vault|The whole vault as a dict of path to content, built in memory before anything is written.]] **imports** → this
