---
kind: module
id: "module:tools.tests.test_vaultgraph"
title: "The generator's own guards, asserted from outside the generator."
shape: "module"
present: "true"
protected: "false"
lint_gated: "false"
source: "tools/tests/test_vaultgraph.py:1"
extractor: "code"
aliases:
  - "The generator's own guards, asserted from outside the generator."
  - "tools.tests.test_vaultgraph"
generated: true
---

# The generator's own guards, asserted from outside the generator.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `tools/tests/test_vaultgraph.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | true |
| `path` | tools/tests/test_vaultgraph.py |
| `tree` | tools |

## Binds

- **imports** → [[module__tools_vaultgraph_mirror|The plan file lives outside the repo. This mirrors it in, and makes drift mechanical.]]
- **imports** → [[module__tools_vaultgraph_model|The graph's type vocabulary: what a node is, what an edge is, and how ids are minted.]]
- **imports** → [[module__tools_vaultgraph_protocol|The extractor contract, shaped so a missing vacuity guard is impossible rather than unlike]]
- **imports** → [[module__tools_vaultgraph_runner|Runs the registry and fails on every way an extraction can be quietly empty.]]
- **imports** → [[module__tools_vaultgraph_selftest|Planted fixtures that prove the guards fire, and a clean control that proves they are quie]]
- **imports** → [[module__tools_vaultgraph_serialize|Canonical JSON. The rules here are the whole of the determinism guarantee.]]
- [[module__tools_tests|tools.tests]] **contains** → this
