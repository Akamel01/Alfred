---
kind: module
id: "module:tools.vaultgraph.render.note"
title: "One node, one note. Frontmatter mirroring the repo's own contract, and a source pointer."
shape: "module"
present: "true"
protected: "false"
lint_gated: "false"
source: "tools/vaultgraph/render/note.py:1"
extractor: "code"
aliases:
  - "One node, one note. Frontmatter mirroring the repo's own contract, and a source pointer."
  - "tools.vaultgraph.render.note"
generated: true
---

# One node, one note. Frontmatter mirroring the repo's own contract, and a source pointer.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `tools/vaultgraph/render/note.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | tools/vaultgraph/render/note.py |
| `tree` | tools |

## Binds

- **imports** → [[module__tools_vaultgraph_model|The graph's type vocabulary: what a node is, what an edge is, and how ids are minted.]]
- [[module__tools_vaultgraph|tools.vaultgraph]] **contains** → this
- [[module__tools_vaultgraph_render_canvas|Obsidian Canvas boards — the stage DAG, laid out deterministically.]] **imports** → this
- [[module__tools_vaultgraph_render_dataview|Dataview boards. Queries, not materialized tables.]] **imports** → this
- [[module__tools_vaultgraph_render_vault|The whole vault as a dict of path to content, built in memory before anything is written.]] **imports** → this
