# tools/CONTEXT.md

One job: vaultgraph and generators — CI-gated, not the protected set — the machinery that builds the system map.

## Inputs

- Working: `tools/vaultgraph/`, `tools/orchestration/`, `tools/gen_vault.py`, `tools/tests/`
- Reference: `tools/vaultgraph/README.md` (vocabulary), `vault/_anomalies.md` (findings), `docs/tier2/coding-standards.md` § Structure (fence)

## Process

1. Extract, then render — `tools/vaultgraph/extract/` mints nodes/edges/anomalies; `tools/vaultgraph/render/` builds `vault/`, `graph.json`, `docs-graph.html` in memory before writing (orphan detection).
2. Keep `render/` downstream of `extract/` — layering check in `--self-test` asserts no transitive import from render to extract.
3. Run `python3 tools/gen_vault.py --self-test && python3 tools/gen_vault.py --check` — floors, `FOLDERS` dict, and byte-compare.

## Outputs

- `vault/` + `graph.json` + `docs-graph.html` — one extraction, several renderers, cannot drift.

## Human check

Does `gen_vault.py --self-test` + `--check` pass and does the published page render from the same nodes/edges as the vault?
