# docs/CONTEXT.md

One job: the register — what exists, what binds, what is generated — human-authored, frozen where it says frozen.

## Inputs

- Working: `docs/tier0/`, `docs/tier1/`, `docs/tier2/`, `docs/tier4/`, `docs/README.md`, `docs/READING-MAP.md`
- Reference: `vault/Overview.md` (generated map), `policy/protected-paths.json` (tier0 is protected), stage gates in `harness/selftest/stage_gate_register.json`

## Process

1. Edit the source, not the vault — `vault/` is generated via `python3 tools/gen_vault.py`.
2. Keep one home per fact (fence in `coding-standards.md` § Structure, glossary split per ADR-0033/0044, plan mirror in `plan/` sealed).
3. Run `python3 scripts/lint_docs.py --check && python3 scripts/gen_reading_map.py --check` before merge.

## Outputs

- `docs/**/*.md` — header-contract green (`status/owner/enforcement/evidence/falsifies_if/review_after`), reading map current.

## Human check

Does `lint_docs.py` still see every document and does the register still route a newcomer to the right tier in ≤2 reads?
