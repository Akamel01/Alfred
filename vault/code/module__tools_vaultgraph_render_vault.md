---
kind: module
id: "module:tools.vaultgraph.render.vault"
title: "The whole vault as a dict of path to content, built in memory before anything is written."
shape: "module"
present: "true"
protected: "false"
lint_gated: "false"
source: "tools/vaultgraph/render/vault.py:1"
extractor: "code"
aliases:
  - "The whole vault as a dict of path to content, built in memory before anything is written."
  - "tools.vaultgraph.render.vault"
generated: true
---

# The whole vault as a dict of path to content, built in memory before anything is written.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `tools/vaultgraph/render/vault.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | tools/vaultgraph/render/vault.py |
| `tree` | tools |

## Binds

- **imports** → [[module__tools_vaultgraph_model|The graph's type vocabulary: what a node is, what an edge is, and how ids are minted.]]
- **imports** → [[module__tools_vaultgraph_render_canvas|Obsidian Canvas boards — the stage DAG, laid out deterministically.]]
- **imports** → [[module__tools_vaultgraph_render_dataview|Dataview boards. Queries, not materialized tables.]]
- **imports** → [[module__tools_vaultgraph_render_html|The published artifact: one self-contained file built from the same graph the vault is.]]
- **imports** → [[module__tools_vaultgraph_render_note|One node, one note. Frontmatter mirroring the repo's own contract, and a source pointer.]]
- [[module__tools_vaultgraph|tools.vaultgraph]] **contains** → this
- [[module__tools_tests_test_render|The renderers: the vault tree, and the published artifact.]] **imports** → this
- [[module__tools_vaultgraph_selftest|Planted fixtures that prove the guards fire, and a clean control that proves they are quie]] **imports** → this
