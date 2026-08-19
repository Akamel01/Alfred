---
kind: module
id: "module:tools.vaultgraph.extract.__init__"
title: "The one ordered registry. Adding an extractor means adding it here, with its floors."
shape: "module"
present: "true"
protected: "false"
lint_gated: "false"
source: "tools/vaultgraph/extract/__init__.py:1"
extractor: "code"
aliases:
  - "The one ordered registry. Adding an extractor means adding it here, with its floors."
  - "tools.vaultgraph.extract.__init__"
generated: true
---

# The one ordered registry. Adding an extractor means adding it here, with its floors.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `tools/vaultgraph/extract/__init__.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | tools/vaultgraph/extract/__init__.py |
| `tree` | tools |

## Binds

- **imports** → [[module__tools_vaultgraph_extract_adrs|Every ADR in the log, and the relations stated on each entry's metadata line.]]
- **imports** → [[module__tools_vaultgraph_extract_amendments|A1-A12, and the edges from an amendment to the decision it amends.]]
- **imports** → [[module__tools_vaultgraph_extract_charter|K1-K6 and R1-R12, which live in Tier 0 and not, as the handoff assumed, in the plan.]]
- **imports** → [[module__tools_vaultgraph_extract_code|The engineered half of the graph: packages, modules, schemas, and what D20 protects.]]
- **imports** → [[module__tools_vaultgraph_extract_decisions|D1-D57, which the plan encodes four different ways, two of them traps.]]
- **imports** → [[module__tools_vaultgraph_extract_documents|The 63 documents under `docs/tier0`…`tier7`, and the eight tiers that hold them.]]
- **imports** → [[module__tools_vaultgraph_extract_imports|What depends on what: module -> module edges, read from import statements.]]
- **imports** → [[module__tools_vaultgraph_extract_references|Where decisions are enforced in code, read out of comments and docstrings.]]
- **imports** → [[module__tools_vaultgraph_extract_stages|S0-S9 and O1-O9, and the dependency clauses that make them a DAG.]]
- **imports** → [[module__tools_vaultgraph_extract_workflows|The gates: five jobs and every step they run, read out of `.github/workflows/gates.yml`.]]
- **imports** → [[module__tools_vaultgraph_protocol|The extractor contract, shaped so a missing vacuity guard is impossible rather than unlike]]
- [[module__tools_vaultgraph|tools.vaultgraph]] **contains** → this
