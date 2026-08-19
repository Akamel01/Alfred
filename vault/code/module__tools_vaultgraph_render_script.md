---
kind: module
id: "module:tools.vaultgraph.render.script"
title: "The script, composed at build time from four modules and inlined into one page."
shape: "module"
present: "true"
protected: "false"
lint_gated: "false"
source: "tools/vaultgraph/render/script.py:1"
extractor: "code"
aliases:
  - "The script, composed at build time from four modules and inlined into one page."
  - "tools.vaultgraph.render.script"
generated: true
---

# The script, composed at build time from four modules and inlined into one page.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `tools/vaultgraph/render/script.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | tools/vaultgraph/render/script.py |
| `tree` | tools |

## Binds

- **imports** → [[module__tools_vaultgraph_render_camera|Where the page is looking. The only thing that knows how world coordinates become pixels.]]
- **imports** → [[module__tools_vaultgraph_render_layout|Where the nodes go. The force simulation, the isolate margin, and the container hulls.]]
- **imports** → [[module__tools_vaultgraph_render_view|What is on screen. Five filter dimensions behind one predicate.]]
- [[module__tools_vaultgraph|tools.vaultgraph]] **contains** → this
- [[module__tools_tests_test_render|The renderers: the vault tree, and the published artifact.]] **imports** → this
- [[module__tools_vaultgraph_render_html|The published artifact: one self-contained file built from the same graph the vault is.]] **imports** → this
