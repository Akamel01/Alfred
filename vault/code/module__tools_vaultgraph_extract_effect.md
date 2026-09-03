---
kind: module
id: "module:tools.vaultgraph.extract.effect"
title: "Change-impact index — \"if you change X, open these cards\" — derived from in-edges."
shape: "module"
present: "true"
protected: "false"
lint_gated: "false"
source: "tools/vaultgraph/extract/effect.py:1"
extractor: "code"
aliases:
  - "Change-impact index — \"if you change X, open these cards\" — derived from in-edges."
  - "tools.vaultgraph.extract.effect"
generated: true
---

# Change-impact index — "if you change X, open these cards" — derived from in-edges.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `tools/vaultgraph/extract/effect.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | tools/vaultgraph/extract/effect.py |
| `tree` | tools |

## Binds

- **imports** → [[module__tools_vaultgraph_model|The graph's type vocabulary: what a node is, what an edge is, and how ids are minted.]]
- **imports** → [[module__tools_vaultgraph_protocol|The extractor contract, shaped so a missing vacuity guard is impossible rather than unlike]]
- [[module__tools_vaultgraph|tools.vaultgraph]] **contains** → this
- [[module__tools_vaultgraph_extract___init__|The one ordered registry. Adding an extractor means adding it here, with its floors.]] **imports** → this
