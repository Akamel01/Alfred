# Stage S3 — Inspector core — CONTEXT.md

> Instantiated from `_templates/stage-contract.md` (ADR-0041). Never edit the template in place.

One job: EvidenceStore (hash-chained) + CriterionRunner (outside agent tree) + D16 lint. Blocks S4 and every verdict.

## Inputs

- Working: `stages/04_s3_inspector-core/input/` (empty unless this stage stages material)
- Reference: `docs/tier2/execution-order.md § S3 — Inspector core · blocks S4`, `harness/containment/`, `harness/acs/acs1.py`, `scripts/lint_verdict_boundary.py

## Process

1. Read `docs/tier2/execution-order.md § S3 — Inspector core · blocks S4` for blockers and exit criteria.
2. Perform the movement ADR-0041 defines for S3 — produce the canonical outputs, not a copy.
3. Draft `stages/04_s3_inspector-core/output/exit.md` as a claim; human confirms at gate; vault cross-checks.

## Outputs

- `stages/04_s3_inspector-core/output/exit.md` — what, commit, ADRs, register pointer, residue (real outputs stay in canonical homes and this file points).
- harness/containment/ (+ related paths per execution order)

## Human check

Is `DONE 2026-08-17` observable — do the vault stage extractor and `execution-order.md` agree, and does the exit record resolve to a real commit/ADR/register entry?
