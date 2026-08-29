# policy/CONTEXT.md

One job: machine-readable Tier 4 — allowlists, denylists, and the single protected set.

## Inputs

- Working: `policy/*.json`, `policy/*.md` (tier4), `policy/node-palette.json` (21 entries, v1, ADR-0039)
- Reference: `docs/tier4/protected-paths-policy.md` (frozen, ADR-0031), `harness/patch/validate.py` (the gate reading this set), `docs/tier0/glossary.md`

## Process

1. Change `policy/protected-paths.json` only via ADR + line-by-line Gate D review (D20) — never a convenience edit.
2. Keep `harness/patch/test_protected_set.py` ROW_COVERAGE in sync — set ↔ doc equality in both directions per ADR-0009.
3. Keep `policy/node-palette.json` bijective with code-side node-kind spellings (`tools/tests/test_orchestration.py` enforces).

## Outputs

- `policy/` — protected by its own entry; any diff touching it is refused before it reaches a tree.

## Human check

Does `harness/patch/validate.py` still refuse a planted write to a protected prefix and does `test_protected_set.py` still fail on a doc↔set mismatch?
