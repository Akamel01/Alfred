# Stage S9 — Phase 1 build — CONTEXT.md

> Instantiated from `_templates/stage-contract.md` (ADR-0041). Never edit the template in place.

One job: Worker port + OpenHands adaptor (d460d1a0) + 15 boot assertions + patch validation (A2/A10); mission-control is operator-built (D51).

## Inputs

- Working: `stages/10_s9_phase1-build/input/` (empty unless this stage stages material)
- Reference: `docs/tier2/execution-order.md § S9 — Phase 1 build · blocked by S1–S8 and O1`, `harness/worker/port.py`, `harness/patch/validate.py`, `harness/containment/dispatch_mount.py

## Process

1. Read `docs/tier2/execution-order.md § S9 — Phase 1 build · blocked by S1–S8 and O1` for blockers and exit criteria.
2. Perform the movement ADR-0041 defines for S9 — produce the canonical outputs, not a copy.
3. Draft `stages/10_s9_phase1-build/output/exit.md` as a claim; human confirms at gate; vault cross-checks.

## Outputs

- `stages/10_s9_phase1-build/output/exit.md` — what, commit, ADRs, register pointer, residue (real outputs stay in canonical homes and this file points).
- harness/worker/port.py (+ related paths per execution order)

## Human check

Is `PORT AND PATCH GATE DONE 2026-08-18, mission-control outstanding` observable — do the vault stage extractor and `execution-order.md` agree, and does the exit record resolve to a real commit/ADR/register entry?
