---
kind: module
id: "module:tools.vaultgraph.mirror"
title: "The plan file lives outside the repo. This mirrors it in, and makes drift mechanical."
shape: "module"
present: "true"
protected: "false"
lint_gated: "false"
source: "tools/vaultgraph/mirror.py:1"
extractor: "code"
aliases:
  - "The plan file lives outside the repo. This mirrors it in, and makes drift mechanical."
  - "tools.vaultgraph.mirror"
generated: true
---

# The plan file lives outside the repo. This mirrors it in, and makes drift mechanical.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `tools/vaultgraph/mirror.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | tools/vaultgraph/mirror.py |
| `tree` | tools |

## Binds

- **imports** → [[module__tools_vaultgraph_textio|Reading the repo the same way the repo already reads itself, and one path spelling.]]
- [[module__tools_vaultgraph|tools.vaultgraph]] **contains** → this
- [[module__tools_tests_test_vaultgraph|The generator's own guards, asserted from outside the generator.]] **imports** → this
- [[module__tools_vaultgraph_extract_amendments|A1-A12, and the edges from an amendment to the decision it amends.]] **imports** → this
- [[module__tools_vaultgraph_extract_decisions|D1-D57, which the plan encodes four different ways, two of them traps.]] **imports** → this
- [[module__tools_vaultgraph_fixtures|Planted fixture trees, kept apart from the assertions that use them.]] **imports** → this
