# Stage S7 — Durability — CONTEXT.md

> Instantiated from `_templates/stage-contract.md` (ADR-0041). Never edit the template in place.

One job: WAL archiving + base backups off-machine, hash-chain re-walk (JS), restore drill.

## Inputs

- Working: `stages/08_s7_durability/input/` (empty unless this stage stages material)
- Reference: `docs/tier2/execution-order.md § S7 — Durability`, `harness/evidence/store.py`, `harness/scripts/verify_chain.mjs

## Process

1. Read `docs/tier2/execution-order.md § S7 — Durability` for blockers and exit criteria.
2. Perform the movement ADR-0041 defines for S7 — produce the canonical outputs, not a copy.
3. Draft `stages/08_s7_durability/output/exit.md` as a claim; human confirms at gate; vault cross-checks.

## Outputs

- `stages/08_s7_durability/output/exit.md` — what, commit, ADRs, register pointer, residue (real outputs stay in canonical homes and this file points).
- harness/evidence/store.py (+ related paths per execution order)

## Human check

Is `D-SYNTHETIC DONE 2026-08-17, archiving outstanding` observable — do the vault stage extractor and `execution-order.md` agree, and does the exit record resolve to a real commit/ADR/register entry?
