---
kind: module
id: "module:tools.vaultgraph.stamp"
title: "A cheap fingerprint of the inputs, so a served page can tell it has gone stale."
shape: "module"
present: "true"
protected: "false"
lint_gated: "false"
source: "tools/vaultgraph/stamp.py:1"
extractor: "code"
aliases:
  - "A cheap fingerprint of the inputs, so a served page can tell it has gone stale."
  - "tools.vaultgraph.stamp"
generated: true
---

# A cheap fingerprint of the inputs, so a served page can tell it has gone stale.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `tools/vaultgraph/stamp.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | tools/vaultgraph/stamp.py |
| `tree` | tools |

## Binds

- **imports** → [[module__tools_vaultgraph_textio|Reading the repo the same way the repo already reads itself, and one path spelling.]]
- [[module__tools_vaultgraph|tools.vaultgraph]] **contains** → this
- [[module__tools_tests_test_serve|The local refresh surface, and the four controls that keep it from being a liability.]] **imports** → this
