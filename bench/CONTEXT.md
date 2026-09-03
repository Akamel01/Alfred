# bench/CONTEXT.md

One job: Phase −1 inference measurements — immutable per-seed evidence the plan cites, never mutated.

## Inputs

- Working: `bench/results/`, `bench/fingerprints/`, `bench/tasks/`, `bench/scripts/`
- Reference: `docs/tier1/adr-log.md` (ADR-0038 bench immutability), `policy/protected-paths.json` (`bench/results/` + `bench/fingerprints/` append-only), `harness/fingerprint/record.py` (RunFingerprint, 27 fields, ACS-1)

## Process

1. Append only — new files may be added under `bench/results/` and `bench/fingerprints/`; modifications/deletions fail CI (`git diff --name-only` + protected-path gate).
2. Capture fingerprints via `python3 scripts/capture_run_fingerprint.py` — hash derived via ACS-1, never supplied.
3. Cite evidence by per-seed file path, not by prose summary — the vault cites `bench/` and `bench/results/` is the evidence.

## Outputs

- `bench/results/*.json` + `bench/fingerprints/*.json` — content-addressed, ledger-backed, never rewritten.

## Human check

Does CI reject a modified file under `bench/results/` and does every fingerprint record hash via ACS-1 without a supplied `fingerprint_sha256`?
