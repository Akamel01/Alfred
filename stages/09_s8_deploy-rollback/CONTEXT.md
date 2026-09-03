# Stage S8 — Deploy and rollback — CONTEXT.md

> Instantiated from `_templates/stage-contract.md` (ADR-0041). Never edit the template in place.

One job: docker compose up serves API; deploy and rollback both executed and verified via /version.

## Inputs

- Working: `stages/09_s8_deploy-rollback/input/` (empty unless this stage stages material)
- Reference: `docs/tier2/execution-order.md § S8 — Deploy and rollback`, `deploy/api.Dockerfile`, `deploy/docker-compose.yml`, `harness/deploy/

## Process

1. Read `docs/tier2/execution-order.md § S8 — Deploy and rollback` for blockers and exit criteria.
2. Perform the movement ADR-0041 defines for S8 — produce the canonical outputs, not a copy.
3. Draft `stages/09_s8_deploy-rollback/output/exit.md` as a claim; human confirms at gate; vault cross-checks.

## Outputs

- `stages/09_s8_deploy-rollback/output/exit.md` — what, commit, ADRs, register pointer, residue (real outputs stay in canonical homes and this file points).
- deploy/api.Dockerfile (+ related paths per execution order)

## Human check

Is `DONE 2026-08-18` observable — do the vault stage extractor and `execution-order.md` agree, and does the exit record resolve to a real commit/ADR/register entry?
