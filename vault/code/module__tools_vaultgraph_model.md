---
kind: module
id: "module:tools.vaultgraph.model"
title: "The graph's type vocabulary: what a node is, what an edge is, and how ids are minted."
shape: "module"
present: "true"
protected: "false"
lint_gated: "false"
source: "tools/vaultgraph/model.py:1"
extractor: "code"
aliases:
  - "The graph's type vocabulary: what a node is, what an edge is, and how ids are minted."
  - "tools.vaultgraph.model"
generated: true
---

# The graph's type vocabulary: what a node is, what an edge is, and how ids are minted.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `tools/vaultgraph/model.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | tools/vaultgraph/model.py |
| `tree` | tools |

## Binds

- [[module__tools_vaultgraph|tools.vaultgraph]] **contains** → this
- [[module__tools_tests_test_render|The renderers: the vault tree, and the published artifact.]] **imports** → this
- [[module__tools_tests_test_vaultgraph|The generator's own guards, asserted from outside the generator.]] **imports** → this
- [[module__tools_vaultgraph_extract_adrs|Every ADR in the log, and the relations stated on each entry's metadata line.]] **imports** → this
- [[module__tools_vaultgraph_extract_amendments|A1-A12, and the edges from an amendment to the decision it amends.]] **imports** → this
- [[module__tools_vaultgraph_extract_charter|K1-K6 and R1-R12, which live in Tier 0 and not, as the handoff assumed, in the plan.]] **imports** → this
- [[module__tools_vaultgraph_extract_code|The engineered half of the graph: packages, modules, schemas, and what D20 protects.]] **imports** → this
- [[module__tools_vaultgraph_extract_decisions|D1-D57, which the plan encodes four different ways, two of them traps.]] **imports** → this
- [[module__tools_vaultgraph_extract_documents|The 63 documents under `docs/tier0`…`tier7`, and the eight tiers that hold them.]] **imports** → this
- [[module__tools_vaultgraph_extract_imports|What depends on what: module -> module edges, read from import statements.]] **imports** → this
- [[module__tools_vaultgraph_extract_references|Where decisions are enforced in code, read out of comments and docstrings.]] **imports** → this
- [[module__tools_vaultgraph_extract_stages|S0-S9 and O1-O9, and the dependency clauses that make them a DAG.]] **imports** → this
- [[module__tools_vaultgraph_extract_workflows|The gates: five jobs and every step they run, read out of `.github/workflows/gates.yml`.]] **imports** → this
- [[module__tools_vaultgraph_protocol|The extractor contract, shaped so a missing vacuity guard is impossible rather than unlike]] **imports** → this
- [[module__tools_vaultgraph_render_canvas|Obsidian Canvas boards — the stage DAG, laid out deterministically.]] **imports** → this
- [[module__tools_vaultgraph_render_cluster|What clumps together, computed rather than declared.]] **imports** → this
- [[module__tools_vaultgraph_render_dataview|Dataview boards. Queries, not materialized tables.]] **imports** → this
- [[module__tools_vaultgraph_render_html|The published artifact: one self-contained file built from the same graph the vault is.]] **imports** → this
- [[module__tools_vaultgraph_render_note|One node, one note. Frontmatter mirroring the repo's own contract, and a source pointer.]] **imports** → this
- [[module__tools_vaultgraph_render_vault|The whole vault as a dict of path to content, built in memory before anything is written.]] **imports** → this
- [[module__tools_vaultgraph_runner|Runs the registry and fails on every way an extraction can be quietly empty.]] **imports** → this
- [[module__tools_vaultgraph_selftest|Planted fixtures that prove the guards fire, and a clean control that proves they are quie]] **imports** → this
- [[module__tools_vaultgraph_serialize|Canonical JSON. The rules here are the whole of the determinism guarantee.]] **imports** → this
