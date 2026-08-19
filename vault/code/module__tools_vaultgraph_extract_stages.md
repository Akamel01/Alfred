---
kind: module
id: "module:tools.vaultgraph.extract.stages"
title: "S0-S9 and O1-O9, and the dependency clauses that make them a DAG."
shape: "module"
present: "true"
protected: "false"
lint_gated: "false"
source: "tools/vaultgraph/extract/stages.py:1"
extractor: "code"
aliases:
  - "S0-S9 and O1-O9, and the dependency clauses that make them a DAG."
  - "tools.vaultgraph.extract.stages"
generated: true
---

# S0-S9 and O1-O9, and the dependency clauses that make them a DAG.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `tools/vaultgraph/extract/stages.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | tools/vaultgraph/extract/stages.py |
| `tree` | tools |

## Binds

- **imports** → [[module__tools_vaultgraph_mdscan|Line-oriented markdown primitives. The risky parsing, isolated from anything that uses it.]]
- **imports** → [[module__tools_vaultgraph_model|The graph's type vocabulary: what a node is, what an edge is, and how ids are minted.]]
- **imports** → [[module__tools_vaultgraph_protocol|The extractor contract, shaped so a missing vacuity guard is impossible rather than unlike]]
- **imports** → [[module__tools_vaultgraph_textio|Reading the repo the same way the repo already reads itself, and one path spelling.]]
- [[module__tools_vaultgraph|tools.vaultgraph]] **contains** → this
- [[module__tools_vaultgraph_extract___init__|The one ordered registry. Adding an extractor means adding it here, with its floors.]] **imports** → this
