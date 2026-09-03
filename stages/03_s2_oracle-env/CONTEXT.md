# Stage S2 — Oracle environment — CONTEXT.md

> Instantiated from `_templates/stage-contract.md` (ADR-0041). Never edit the template in place.

One job: Pinned offline CriMe container at 60bebed (linux/amd64, py3.11), no agent code crosses. Blocks S5 reference values.

## Inputs

- Working: `stages/03_s2_oracle-env/input/` (empty unless this stage stages material)
- Reference: `docs/tier2/execution-order.md § S2 — Oracle environment · blocks S5`, `harness/oracle/pins.py`, `harness/oracle/Dockerfile

## Process

1. Read `docs/tier2/execution-order.md § S2 — Oracle environment · blocks S5` for blockers and exit criteria.
2. Perform the movement ADR-0041 defines for S2 — produce the canonical outputs, not a copy.
3. Draft `stages/03_s2_oracle-env/output/exit.md` as a claim; human confirms at gate; vault cross-checks.

## Outputs

- `stages/03_s2_oracle-env/output/exit.md` — what, commit, ADRs, register pointer, residue (real outputs stay in canonical homes and this file points).
- harness/oracle/pins.py (+ related paths per execution order)

## Human check

Is `ENVIRONMENT DONE 2026-08-18` observable — do the vault stage extractor and `execution-order.md` agree, and does the exit record resolve to a real commit/ADR/register entry?
