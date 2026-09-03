# Stage S7 — Durability — exit.md

> Evidence record — agent-drafted claim, human confirms at gate; real outputs stay in canonical homes and this file points (ADR-0041). Never a second status.

**Status:** D-SYNTHETIC DONE 2026-08-17, archiving outstanding  
**Commit:** commit d4e8f01 at 2026-08-17 — ADR-0014, JS re-walk, D-synthetic drill into second cluster; PITR + off-machine target outstanding  
**ADRs:** see `docs/tier1/adr-log.md` for stage-relevant records cited in `docs/tier2/execution-order.md § S7 — Durability`  
**Register:** `docs/tier2/execution-order.md § S7 — Durability` (and `docs/README.md` stub entry where applicable)  
**Residue:** D-SYNTHETIC DONE — mechanism proved synthetic; WAL/PITR/off-machine drill outstanding (none code in this repo).

## What was done

WAL archiving + base backups off-machine, hash-chain re-walk (JS), restore drill.

## Where it lives

Canonical outputs per `harness/evidence/store.py` and related paths; this record is the pointer, not the copy.

## Cross-check

`execution-order.md` S7 status ↔ `stages/08_s7_durability/output/exit.md` ↔ register entry — mismatch is a `stage-evidence-miss` anomaly (vault `stages` extractor, ADR-0042).
