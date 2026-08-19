---
kind: module
id: "module:tools.vaultgraph.render.dataview"
title: "Dataview boards. Queries, not materialized tables."
shape: "module"
present: "true"
protected: "false"
lint_gated: "false"
source: "tools/vaultgraph/render/dataview.py:1"
extractor: "code"
aliases:
  - "Dataview boards. Queries, not materialized tables."
  - "tools.vaultgraph.render.dataview"
generated: true
---

# Dataview boards. Queries, not materialized tables.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `tools/vaultgraph/render/dataview.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | tools/vaultgraph/render/dataview.py |
| `tree` | tools |

## Binds

- **imports** → [[module__tools_vaultgraph_model|The graph's type vocabulary: what a node is, what an edge is, and how ids are minted.]]
- **imports** → [[module__tools_vaultgraph_render_html|The published artifact: one self-contained file built from the same graph the vault is.]]
- **imports** → [[module__tools_vaultgraph_render_note|One node, one note. Frontmatter mirroring the repo's own contract, and a source pointer.]]
- [[module__tools_vaultgraph|tools.vaultgraph]] **contains** → this
- [[module__tools_vaultgraph_render_vault|The whole vault as a dict of path to content, built in memory before anything is written.]] **imports** → this
