# tests/CONTEXT.md

One job: product tests proving product code — properties, references, held-out scaffolding (but not the held-out values themselves).

## Inputs

- Working: `tests/properties/`, `tests/reference/`, `tests/heldout/` (scaffold only — `tests/heldout/` is protected, values materialized at verdict time from `migrations/harness/`)
- Reference: `docs/tier2/testing-strategy.md` (visible/held-out split), `src/` (code under test), `docs/tier0/glossary.md`

## Process

1. Read the criterion's interface signature and threshold provenance before writing the test.
2. Cover composed operations via Hypothesis properties; keep reference fixtures in `tests/reference/` oracle-free unless explicitly pinned.
3. Never import or read `tests/heldout/` values in a visible test or agent tree — they are held-out by DB role.

## Outputs

- `tests/**/*.py` — `pytest` green, held-out integrity preserved.

## Human check

Does the test fail when the code is wrong and pass when it is right, without reading held-out answers into the agent tree?
