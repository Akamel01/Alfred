---
kind: module
id: "module:tools.vaultgraph.selftest"
title: "Planted fixtures that prove the guards fire, and a clean control that proves they are quiet."
shape: "module"
present: "true"
protected: "false"
lint_gated: "false"
source: "tools/vaultgraph/selftest.py:1"
extractor: "code"
aliases:
  - "Planted fixtures that prove the guards fire, and a clean control that proves they are quie"
  - "tools.vaultgraph.selftest"
generated: true
---

# Planted fixtures that prove the guards fire, and a clean control that proves they are quiet.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `tools/vaultgraph/selftest.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | tools/vaultgraph/selftest.py |
| `tree` | tools |

## Binds

- **imports** → [[module__tools_vaultgraph|tools.vaultgraph]]
- **imports** → [[module__tools_vaultgraph_extract_code|The engineered half of the graph: packages, modules, schemas, and what D20 protects.]]
- **imports** → [[module__tools_vaultgraph_extract_decisions|D1-D57, which the plan encodes four different ways, two of them traps.]]
- **imports** → [[module__tools_vaultgraph_extract_documents|The 63 documents under `docs/tier0`…`tier7`, and the eight tiers that hold them.]]
- **imports** → [[module__tools_vaultgraph_extract_imports|What depends on what: module -> module edges, read from import statements.]]
- **imports** → [[module__tools_vaultgraph_extract_references|Where decisions are enforced in code, read out of comments and docstrings.]]
- **imports** → [[module__tools_vaultgraph_extract_workflows|The gates: five jobs and every step they run, read out of `.github/workflows/gates.yml`.]]
- **imports** → [[module__tools_vaultgraph_fixtures|Planted fixture trees, kept apart from the assertions that use them.]]
- **imports** → [[module__tools_vaultgraph_model|The graph's type vocabulary: what a node is, what an edge is, and how ids are minted.]]
- **imports** → [[module__tools_vaultgraph_protocol|The extractor contract, shaped so a missing vacuity guard is impossible rather than unlike]]
- **imports** → [[module__tools_vaultgraph_render_vault|The whole vault as a dict of path to content, built in memory before anything is written.]]
- **imports** → [[module__tools_vaultgraph_runner|Runs the registry and fails on every way an extraction can be quietly empty.]]
- **imports** → [[module__tools_vaultgraph_serialize|Canonical JSON. The rules here are the whole of the determinism guarantee.]]
- [[module__tools_vaultgraph|tools.vaultgraph]] **contains** → this
- [[module__tools_tests_test_render|The renderers: the vault tree, and the published artifact.]] **imports** → this
- [[module__tools_tests_test_vaultgraph|The generator's own guards, asserted from outside the generator.]] **imports** → this
