# migrations/CONTEXT.md

One job: additive-only schema versions for the four stores the factory trusts — product, control, evidence, heldout — plus roles/grants.

## Inputs

- Working: `migrations/`, `migrations/harness/`, `migrations/roles/`
- Reference: `docs/tier1/data-architecture.md` (role split, hash chain), `harness/db/assert_grants.py` (set-equality grant check), `policy/protected-paths.json`

## Process

1. Add one Alembic version per change — never edit a landed version, never add a downgrade that mutates evidence rows.
2. Update `migrations/harness/` and `migrations/roles/` together; keep the grant matrix in `assert_grants.py` as exact set equality in both directions.
3. Run `python3 scripts/lint_migrations.py` — additive-only, one head per branch.

## Outputs

- `migrations/versions/*.py` — apply cleanly against a fresh cluster, grants asserted, evidence rows immutable.

## Human check

Does `scripts/lint_migrations.py` pass and does the migration apply against the throwaway cluster in `harness/db/` without widening a grant?
