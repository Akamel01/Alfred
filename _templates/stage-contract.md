# Stage S_ — <Name> — CONTEXT.md

> Instantiate by copy: `cp _templates/stage-contract.md stages/NN_sN_slug/CONTEXT.md` — never edit this template in place.

One job: <one sentence — what this stage alone does, per `docs/tier2/execution-order.md`>

## Inputs

- Working: `stages/NN_sN_slug/input/` (empty unless this stage stages material)
- Reference: `docs/tier2/execution-order.md` § S_ — ..., `docs/tier1/____.md`, `harness/____`

## Process

1. <numbered, short — the movement that actually runs>
2. <next step — what it writes where>
3. <gate — what must be observed before advancing>

## Outputs

- `stages/NN_sN_slug/output/exit.md` — what, commit, ADRs, register pointer, residue (real outputs stay in canonical homes and this file points).
- <canonical output path(s) — e.g. `src/____`, `harness/____`>

## Human check

<Exactly one check that a human confirms at the stage gate — the observation that makes this stage DONE rather than merely executed.>
