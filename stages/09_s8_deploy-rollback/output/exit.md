# Stage S8 — Deploy and rollback — exit.md

> Evidence record — agent-drafted claim, human confirms at gate; real outputs stay in canonical homes and this file points (ADR-0041). Never a second status.

**Status:** DONE 2026-08-18  
**Commit:** commit 9b3a2d1 at 2026-08-18 — two releases built/deployed/rolled back, /version read-back, docs/tier2/branch-release-deploy-protocol.md promoted  
**ADRs:** see `docs/tier1/adr-log.md` for stage-relevant records cited in `docs/tier2/execution-order.md § S8 — Deploy and rollback`  
**Register:** `docs/tier2/execution-order.md § S8 — Deploy and rollback` (and `docs/README.md` stub entry where applicable)  
**Residue:** DONE — identity baked into artifact, ledger written after observation, rollback scans for different release_id.

## What was done

docker compose up serves API; deploy and rollback both executed and verified via /version.

## Where it lives

Canonical outputs per `deploy/api.Dockerfile` and related paths; this record is the pointer, not the copy.

## Cross-check

`execution-order.md` S8 status ↔ `stages/09_s8_deploy-rollback/output/exit.md` ↔ register entry — mismatch is a `stage-evidence-miss` anomaly (vault `stages` extractor, ADR-0042).
