# Stage S5 — Product path to a reproduced number — CONTEXT.md

> Instantiated from `_templates/stage-contract.md` (ADR-0041). Never edit the template in place.

One job: ingest→metrics→replay→stamping→api; reproduce CriMe asserted values on six scenarios within tolerance.

## Inputs

- Working: `stages/06_s5_product-path/input/` (empty unless this stage stages material)
- Reference: `docs/tier2/execution-order.md § S5 — Product path · blocked by S1,S2`, `src/ingest/`, `src/metrics/`, `src/replay/`, `src/provenance/

## Process

1. Read `docs/tier2/execution-order.md § S5 — Product path · blocked by S1,S2` for blockers and exit criteria.
2. Perform the movement ADR-0041 defines for S5 — produce the canonical outputs, not a copy.
3. Draft `stages/06_s5_product-path/output/exit.md` as a claim; human confirms at gate; vault cross-checks.

## Outputs

- `stages/06_s5_product-path/output/exit.md` — what, commit, ADRs, register pointer, residue (real outputs stay in canonical homes and this file points).
- src/ingest/ (+ related paths per execution order)

## Human check

Is `IN PROGRESS — blocked by S1,S2` observable — do the vault stage extractor and `execution-order.md` agree, and does the exit record resolve to a real commit/ADR/register entry?
