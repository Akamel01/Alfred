# Stage S0 — Land the decided-but-unapplied text — CONTEXT.md

> Instantiated from `_templates/stage-contract.md` (ADR-0041). Never edit the template in place.

One job: Apply merge-ready text from H3/H4/H5/H8 that encodes decisions already made. No build work, decays if deferred.

## Inputs

- Working: `stages/01_s0_backlog/input/` (empty unless this stage stages material)
- Reference: `docs/tier2/execution-order.md § S0 — Land the decided-but-unapplied text · blocks nothing`, `docs/tier1/adr-log.md`, `docs/tier2/execution-order.md

## Process

1. Read `docs/tier2/execution-order.md § S0 — Land the decided-but-unapplied text · blocks nothing` for blockers and exit criteria.
2. Perform the movement ADR-0041 defines for S0 — produce the canonical outputs, not a copy.
3. Draft `stages/01_s0_backlog/output/exit.md` as a claim; human confirms at gate; vault cross-checks.

## Outputs

- `stages/01_s0_backlog/output/exit.md` — what, commit, ADRs, register pointer, residue (real outputs stay in canonical homes and this file points).
- docs/tier1/adr-log.md (+ related paths per execution order)

## Human check

Is `DONE 2026-08-17` observable — do the vault stage extractor and `execution-order.md` agree, and does the exit record resolve to a real commit/ADR/register entry?
