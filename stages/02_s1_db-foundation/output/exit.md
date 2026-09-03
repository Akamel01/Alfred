# Stage S1 — Database foundation — exit.md

> Evidence record — agent-drafted claim, human confirms at gate; real outputs stay in canonical homes and this file points (ADR-0041). Never a second status.

**Status:** DONE 2026-08-17  
**Commit:** commit 71a96c4 at 2026-08-17 — 14 tables, ADR-0009, lint_migrations additive-only  
**ADRs:** see `docs/tier1/adr-log.md` for stage-relevant records cited in `docs/tier2/execution-order.md § S1 — Database foundation · blocks S3, S4, S6`  
**Register:** `docs/tier2/execution-order.md § S1 — Database foundation · blocks S3, S4, S6` (and `docs/README.md` stub entry where applicable)  
**Residue:** DONE — four schemas versioned, grants asserted both directions.

## What was done

Alembic versions for product/control/evidence/heldout + assert_grants set-equality. Blocks S3,S4,S6, all Phase 1.

## Where it lives

Canonical outputs per `migrations/versions/` and related paths; this record is the pointer, not the copy.

## Cross-check

`execution-order.md` S1 status ↔ `stages/02_s1_db-foundation/output/exit.md` ↔ register entry — mismatch is a `stage-evidence-miss` anomaly (vault `stages` extractor, ADR-0042).
