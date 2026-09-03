# Stage S6 — Containment — exit.md

> Evidence record — agent-drafted claim, human confirms at gate; real outputs stay in canonical homes and this file points (ADR-0041). Never a second status.

**Status:** PROBES DONE 2026-08-17, enforcement outstanding  
**Commit:** commit a71c9e3 at 2026-08-17 — ADR-0013, C6 loopback control, C7 find_spec layers 1–3; enforcement host-namespace outstanding  
**ADRs:** see `docs/tier1/adr-log.md` for stage-relevant records cited in `docs/tier2/execution-order.md § S6 — Containment`  
**Register:** `docs/tier2/execution-order.md § S6 — Containment` (and `docs/README.md` stub entry where applicable)  
**Residue:** PROBES DONE — assertions vocabulary + versioned denylist; host nftables and image closure check outstanding.

## What was done

Egress canary (nftables) + oracle-absence probe (both containers). Blocks Phase 1 dispatch.

## Where it lives

Canonical outputs per `harness/containment/canary.py` and related paths; this record is the pointer, not the copy.

## Cross-check

`execution-order.md` S6 status ↔ `stages/07_s6_containment/output/exit.md` ↔ register entry — mismatch is a `stage-evidence-miss` anomaly (vault `stages` extractor, ADR-0042).
