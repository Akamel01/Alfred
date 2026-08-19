---
kind: module
id: "module:tools.vaultgraph.fixtures"
title: "Planted fixture trees, kept apart from the assertions that use them."
shape: "module"
present: "true"
protected: "false"
lint_gated: "false"
source: "tools/vaultgraph/fixtures.py:1"
extractor: "code"
aliases:
  - "Planted fixture trees, kept apart from the assertions that use them."
  - "tools.vaultgraph.fixtures"
generated: true
---

# Planted fixture trees, kept apart from the assertions that use them.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `tools/vaultgraph/fixtures.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | tools/vaultgraph/fixtures.py |
| `tree` | tools |

## Binds

- **imports** → [[module__tools_vaultgraph_mirror|The plan file lives outside the repo. This mirrors it in, and makes drift mechanical.]]
- [[module__tools_vaultgraph|tools.vaultgraph]] **contains** → this
- [[module__tools_vaultgraph_selftest|Planted fixtures that prove the guards fire, and a clean control that proves they are quie]] **imports** → this
