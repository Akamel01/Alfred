# Stage S4 — The two suites, together — CONTEXT.md

> Instantiated from `_templates/stage-contract.md` (ADR-0041). Never edit the template in place.

One job: Null-agent floor + seeded-defect ladder as one stage (mutual vacuity controls). Blocks Phase 0 exit.

## Inputs

- Working: `stages/05_s4_suites-together/input/` (empty unless this stage stages material)
- Reference: `docs/tier2/execution-order.md § S4 — The two suites, together`, `harness/selftest/`, `harness/selftest/stage_gate_register.json

## Process

1. Read `docs/tier2/execution-order.md § S4 — The two suites, together` for blockers and exit criteria.
2. Perform the movement ADR-0041 defines for S4 — produce the canonical outputs, not a copy.
3. Draft `stages/05_s4_suites-together/output/exit.md` as a claim; human confirms at gate; vault cross-checks.

## Outputs

- `stages/05_s4_suites-together/output/exit.md` — what, commit, ADRs, register pointer, residue (real outputs stay in canonical homes and this file points).
- harness/selftest/ (+ related paths per execution order)

## Human check

Is `DONE 2026-08-18` observable — do the vault stage extractor and `execution-order.md` agree, and does the exit record resolve to a real commit/ADR/register entry?
