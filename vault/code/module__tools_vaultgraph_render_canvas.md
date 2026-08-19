---
kind: module
id: "module:tools.vaultgraph.render.canvas"
title: "Obsidian Canvas boards — the stage DAG, laid out deterministically."
shape: "module"
present: "true"
protected: "false"
lint_gated: "false"
source: "tools/vaultgraph/render/canvas.py:1"
extractor: "code"
aliases:
  - "Obsidian Canvas boards — the stage DAG, laid out deterministically."
  - "tools.vaultgraph.render.canvas"
generated: true
---

# Obsidian Canvas boards — the stage DAG, laid out deterministically.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `tools/vaultgraph/render/canvas.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | tools/vaultgraph/render/canvas.py |
| `tree` | tools |

## Binds

- **imports** → [[module__tools_vaultgraph_model|The graph's type vocabulary: what a node is, what an edge is, and how ids are minted.]]
- **imports** → [[module__tools_vaultgraph_render_note|One node, one note. Frontmatter mirroring the repo's own contract, and a source pointer.]]
- [[module__tools_vaultgraph|tools.vaultgraph]] **contains** → this
- [[module__tools_vaultgraph_render_vault|The whole vault as a dict of path to content, built in memory before anything is written.]] **imports** → this
