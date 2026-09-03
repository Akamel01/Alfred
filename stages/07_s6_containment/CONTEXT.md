# Stage S6 — Containment — CONTEXT.md

> Instantiated from `_templates/stage-contract.md` (ADR-0041). Never edit the template in place.

One job: Egress canary (nftables) + oracle-absence probe (both containers). Blocks Phase 1 dispatch.

## Inputs

- Working: `stages/07_s6_containment/input/` (empty unless this stage stages material)
- Reference: `docs/tier2/execution-order.md § S6 — Containment`, `harness/containment/canary.py`, `policy/denylist.json

## Process

1. Read `docs/tier2/execution-order.md § S6 — Containment` for blockers and exit criteria.
2. Perform the movement ADR-0041 defines for S6 — produce the canonical outputs, not a copy.
3. Draft `stages/07_s6_containment/output/exit.md` as a claim; human confirms at gate; vault cross-checks.

## Outputs

- `stages/07_s6_containment/output/exit.md` — what, commit, ADRs, register pointer, residue (real outputs stay in canonical homes and this file points).
- harness/containment/canary.py (+ related paths per execution order)

## Human check

Is `PROBES DONE 2026-08-17, enforcement outstanding` observable — do the vault stage extractor and `execution-order.md` agree, and does the exit record resolve to a real commit/ADR/register entry?
