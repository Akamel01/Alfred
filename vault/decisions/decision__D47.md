---
kind: decision
id: "decision:D47"
title: "Read-only retrieval index, settled by measurement in Phase 2"
shape: "bold-paragraph"
number: "47"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:481"
extractor: "decisions"
aliases:
  - "D47"
  - "Read-only retrieval index, settled by measurement in Phase 2"
generated: true
---

# Read-only retrieval index, settled by measurement in Phase 2

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:481`

## Statement

**Decision 47 — Read-only retrieval index, settled by measurement in Phase 2.** D44's invariants all hold: no extraction pipeline, no memory framework, no new authority over agent context. Added: an embedding + full-text index over the repo and evidence store, built **Postgres-native** (pgvector / tsvector, hybrid RRF) so single-source-of-truth survives, and strictly **derived and read-only** — the index is a materialized view of content that already exists, never a place anything is authored. Injected results are appended **after** the immutable seed (D45's hash-chain rule), so prefix caching

## Restated at

- `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:502`

## Enforced by (code)

- **enforced_by** → [[module___github_workflows_gates_yml|.github/workflows/gates.yml]] — nowhere. That property is what admits them as a read model under D44/D47/D51 rather
