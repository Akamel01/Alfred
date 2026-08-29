# Stage S1 — Database foundation — CONTEXT.md

> Instantiated from `_templates/stage-contract.md` (ADR-0041). Never edit the template in place.

One job: Alembic versions for product/control/evidence/heldout + assert_grants set-equality. Blocks S3,S4,S6, all Phase 1.

## Inputs

- Working: `stages/02_s1_db-foundation/input/` (empty unless this stage stages material)
- Reference: `docs/tier2/execution-order.md § S1 — Database foundation · blocks S3, S4, S6`, `migrations/versions/`, `harness/db/assert_grants.py

## Process

1. Read `docs/tier2/execution-order.md § S1 — Database foundation · blocks S3, S4, S6` for blockers and exit criteria.
2. Perform the movement ADR-0041 defines for S1 — produce the canonical outputs, not a copy.
3. Draft `stages/02_s1_db-foundation/output/exit.md` as a claim; human confirms at gate; vault cross-checks.

## Outputs

- `stages/02_s1_db-foundation/output/exit.md` — what, commit, ADRs, register pointer, residue (real outputs stay in canonical homes and this file points).
- migrations/versions/ (+ related paths per execution order)

## Human check

Is `DONE 2026-08-17` observable — do the vault stage extractor and `execution-order.md` agree, and does the exit record resolve to a real commit/ADR/register entry?
