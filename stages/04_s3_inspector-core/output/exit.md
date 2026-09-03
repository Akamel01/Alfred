# Stage S3 — Inspector core — exit.md

> Evidence record — agent-drafted claim, human confirms at gate; real outputs stay in canonical homes and this file points (ADR-0041). Never a second status.

**Status:** DONE 2026-08-17  
**Commit:** commit 2b9d4e0 at 2026-08-17 — ADR-0010/0011/0012, CriterionRunner materializes held-out separately  
**ADRs:** see `docs/tier1/adr-log.md` for stage-relevant records cited in `docs/tier2/execution-order.md § S3 — Inspector core · blocks S4`  
**Register:** `docs/tier2/execution-order.md § S3 — Inspector core · blocks S4` (and `docs/README.md` stub entry where applicable)  
**Residue:** DONE — verdict writes under separate DB role, lint fails on planted verdict field.

## What was done

EvidenceStore (hash-chained) + CriterionRunner (outside agent tree) + D16 lint. Blocks S4 and every verdict.

## Where it lives

Canonical outputs per `harness/containment/` and related paths; this record is the pointer, not the copy.

## Cross-check

`execution-order.md` S3 status ↔ `stages/04_s3_inspector-core/output/exit.md` ↔ register entry — mismatch is a `stage-evidence-miss` anomaly (vault `stages` extractor, ADR-0042).
