---
kind: module
id: "module:tools.vaultgraph"
title: "tools.vaultgraph"
shape: "package"
present: "true"
protected: "false"
lint_gated: "false"
source: "tools/vaultgraph:1"
extractor: "code"
aliases:
  - "tools.vaultgraph"
generated: true
---

# tools.vaultgraph

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `tools/vaultgraph:1`

## Fields

| Field | Value |
|---|---|
| `namespace_package` | false |
| `tree` | tools |

## Binds

- **contains** → [[module__tools_vaultgraph___init__|Alfred's vault and knowledge graph generator. One extraction, several renderers.]]
- **contains** → [[module__tools_vaultgraph_extract___init__|The one ordered registry. Adding an extractor means adding it here, with its floors.]]
- **contains** → [[module__tools_vaultgraph_extract_adrs|Every ADR in the log, and the relations stated on each entry's metadata line.]]
- **contains** → [[module__tools_vaultgraph_extract_amendments|A1-A12, and the edges from an amendment to the decision it amends.]]
- **contains** → [[module__tools_vaultgraph_extract_charter|K1-K6 and R1-R12, which live in Tier 0 and not, as the handoff assumed, in the plan.]]
- **contains** → [[module__tools_vaultgraph_extract_code|The engineered half of the graph: packages, modules, schemas, and what D20 protects.]]
- **contains** → [[module__tools_vaultgraph_extract_decisions|D1-D57, which the plan encodes four different ways, two of them traps.]]
- **contains** → [[module__tools_vaultgraph_extract_documents|The 63 documents under `docs/tier0`…`tier7`, and the eight tiers that hold them.]]
- **contains** → [[module__tools_vaultgraph_extract_imports|What depends on what: module -> module edges, read from import statements.]]
- **contains** → [[module__tools_vaultgraph_extract_references|Where decisions are enforced in code, read out of comments and docstrings.]]
- **contains** → [[module__tools_vaultgraph_extract_stages|S0-S9 and O1-O9, and the dependency clauses that make them a DAG.]]
- **contains** → [[module__tools_vaultgraph_extract_workflows|The gates: five jobs and every step they run, read out of `.github/workflows/gates.yml`.]]
- **contains** → [[module__tools_vaultgraph_fixtures|Planted fixture trees, kept apart from the assertions that use them.]]
- **contains** → [[module__tools_vaultgraph_mdscan|Line-oriented markdown primitives. The risky parsing, isolated from anything that uses it.]]
- **contains** → [[module__tools_vaultgraph_mirror|The plan file lives outside the repo. This mirrors it in, and makes drift mechanical.]]
- **contains** → [[module__tools_vaultgraph_model|The graph's type vocabulary: what a node is, what an edge is, and how ids are minted.]]
- **contains** → [[module__tools_vaultgraph_protocol|The extractor contract, shaped so a missing vacuity guard is impossible rather than unlike]]
- **contains** → [[module__tools_vaultgraph_render___init__|Renderers. Downstream of one extraction, and structurally unable to reach it.]]
- **contains** → [[module__tools_vaultgraph_render_assets|The stylesheet, inlined at build time.]]
- **contains** → [[module__tools_vaultgraph_render_camera|Where the page is looking. The only thing that knows how world coordinates become pixels.]]
- **contains** → [[module__tools_vaultgraph_render_canvas|Obsidian Canvas boards — the stage DAG, laid out deterministically.]]
- **contains** → [[module__tools_vaultgraph_render_cluster|What clumps together, computed rather than declared.]]
- **contains** → [[module__tools_vaultgraph_render_dataview|Dataview boards. Queries, not materialized tables.]]
- **contains** → [[module__tools_vaultgraph_render_html|The published artifact: one self-contained file built from the same graph the vault is.]]
- **contains** → [[module__tools_vaultgraph_render_layout|Where the nodes go. The force simulation, the isolate margin, and the container hulls.]]
- **contains** → [[module__tools_vaultgraph_render_note|One node, one note. Frontmatter mirroring the repo's own contract, and a source pointer.]]
- **contains** → [[module__tools_vaultgraph_render_script|The script, composed at build time from four modules and inlined into one page.]]
- **contains** → [[module__tools_vaultgraph_render_vault|The whole vault as a dict of path to content, built in memory before anything is written.]]
- **contains** → [[module__tools_vaultgraph_render_view|What is on screen. Five filter dimensions behind one predicate.]]
- **contains** → [[module__tools_vaultgraph_runner|Runs the registry and fails on every way an extraction can be quietly empty.]]
- **contains** → [[module__tools_vaultgraph_selftest|Planted fixtures that prove the guards fire, and a clean control that proves they are quie]]
- **contains** → [[module__tools_vaultgraph_serialize|Canonical JSON. The rules here are the whole of the determinism guarantee.]]
- **contains** → [[module__tools_vaultgraph_textio|Reading the repo the same way the repo already reads itself, and one path spelling.]]
- [[module__tools_vaultgraph_runner|Runs the registry and fails on every way an extraction can be quietly empty.]] **imports** → this
- [[module__tools_vaultgraph_selftest|Planted fixtures that prove the guards fire, and a clean control that proves they are quie]] **imports** → this
