---
kind: module
id: "module:tools.vaultgraph.extract.code"
title: "The engineered half of the graph: packages, modules, schemas, and what D20 protects."
shape: "module"
present: "true"
protected: "false"
lint_gated: "false"
source: "tools/vaultgraph/extract/code.py:1"
extractor: "code"
aliases:
  - "The engineered half of the graph: packages, modules, schemas, and what D20 protects."
  - "tools.vaultgraph.extract.code"
generated: true
---

# The engineered half of the graph: packages, modules, schemas, and what D20 protects.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `tools/vaultgraph/extract/code.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | tools/vaultgraph/extract/code.py |
| `tree` | tools |

## Binds

- **imports** → [[module__tools_vaultgraph_model|The graph's type vocabulary: what a node is, what an edge is, and how ids are minted.]]
- **imports** → [[module__tools_vaultgraph_protocol|The extractor contract, shaped so a missing vacuity guard is impossible rather than unlike]]
- **imports** → [[module__tools_vaultgraph_textio|Reading the repo the same way the repo already reads itself, and one path spelling.]]
- [[module__tools_vaultgraph|tools.vaultgraph]] **contains** → this
- [[module__tools_tests_test_vaultgraph|The generator's own guards, asserted from outside the generator.]] **imports** → this
- [[module__tools_vaultgraph_extract___init__|The one ordered registry. Adding an extractor means adding it here, with its floors.]] **imports** → this
- [[module__tools_vaultgraph_selftest|Planted fixtures that prove the guards fire, and a clean control that proves they are quie]] **imports** → this
