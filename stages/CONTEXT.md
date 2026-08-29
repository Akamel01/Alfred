# stages/CONTEXT.md

One job: numbered pipeline `01_s0` … `10_s9` — the build order materialized as folders, evidence in `output/exit.md`, cross-checked by the vault.

## Inputs

- Working: `stages/01_s0_backlog/` … `stages/10_s9_phase1-build/` (each: `CONTEXT.md` + `input/` + `output/exit.md`)
- Reference: `docs/tier2/execution-order.md` § Stages (status = DONE/provisional/blocked — single source of truth), `docs/tier1/adr-log.md` (ADR-0041 pipeline shape), `_templates/stage-contract.md` (instantiate-by-copy)

## Process

1. Create a stage by copying `_templates/stage-contract.md` → `stages/NN_sN_slug/CONTEXT.md` — one job, Inputs with exact paths, Process numbered, Outputs, exactly one human check.
2. Agent drafts `output/exit.md` (what, commit, ADRs, register pointer, residue) — human confirms at gate; real outputs stay in canonical homes, exit record points.
3. Never carry status in the folder — status is `execution-order.md` declaration + vault `stages` extractor cross-checks DONE vs `output/exit.md` + register pointer; mismatch → anomaly.

## Outputs

- `stages/*/output/exit.md` — evidence for DONE stages (S0–S4, S8 backfilled); `stages/06_s5_product-path/output/README.md` empty-in-progress marker.

## Human check

Can a cold agent derive stage status by listing `stages/` and reading `execution-order.md` with no disagreement, and does the vault see every DONE without evidence as `stage-evidence-miss`?
