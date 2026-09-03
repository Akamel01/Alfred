---
kind: module
id: "module:tools.vaultgraph.textio"
title: "Reading the repo the same way the repo already reads itself, and one path spelling."
shape: "module"
present: "true"
protected: "false"
lint_gated: "false"
source: "tools/vaultgraph/textio.py:1"
extractor: "code"
aliases:
  - "Reading the repo the same way the repo already reads itself, and one path spelling."
  - "tools.vaultgraph.textio"
generated: true
---

# Reading the repo the same way the repo already reads itself, and one path spelling.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `tools/vaultgraph/textio.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | tools/vaultgraph/textio.py |
| `tree` | tools |

## Binds

- [[module__tools_vaultgraph|tools.vaultgraph]] **contains** → this
- [[module__tools_vaultgraph_extract_adrs|Every ADR in the log, and the relations stated on each entry's metadata line.]] **imports** → this
- [[module__tools_vaultgraph_extract_amendments|A1-A12, and the edges from an amendment to the decision it amends.]] **imports** → this
- [[module__tools_vaultgraph_extract_charter|K1-K6 and R1-R12, which live in Tier 0 and not, as the handoff assumed, in the plan.]] **imports** → this
- [[module__tools_vaultgraph_extract_code|The engineered half of the graph: packages, modules, schemas, and what D20 protects.]] **imports** → this
- [[module__tools_vaultgraph_extract_decisions|D1-D57, which the plan encodes four different ways, two of them traps.]] **imports** → this
- [[module__tools_vaultgraph_extract_documents|The 63 documents under `docs/tier0`…`tier7`, and the eight tiers that hold them.]] **imports** → this
- [[module__tools_vaultgraph_extract_imports|What depends on what: module -> module edges, read from import statements.]] **imports** → this
- [[module__tools_vaultgraph_extract_layout|The top-level layout as declared in the coding-standards structure fence.]] **imports** → this
- [[module__tools_vaultgraph_extract_process|Verbs the repository runs — one node per runnable, with path:line provenance.]] **imports** → this
- [[module__tools_vaultgraph_extract_references|Where decisions are enforced in code, read out of comments and docstrings.]] **imports** → this
- [[module__tools_vaultgraph_extract_stages|S0-S9 and O1-O9, and the dependency clauses that make them a DAG.]] **imports** → this
- [[module__tools_vaultgraph_extract_workflows|The gates: five jobs and every step they run, read out of `.github/workflows/gates.yml`.]] **imports** → this
- [[module__tools_vaultgraph_mirror|The plan file lives outside the repo. This mirrors it in, and makes drift mechanical.]] **imports** → this
- [[module__tools_vaultgraph_stamp|A cheap fingerprint of the inputs, so a served page can tell it has gone stale.]] **imports** → this
