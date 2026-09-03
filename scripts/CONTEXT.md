# scripts/CONTEXT.md

One job: register lints and generators — the inspector's own tooling — protected (D20), agent may read never write.

## Inputs

- Working: `scripts/*.py` (lints: `lint_docs.py`, `lint_migrations.py`, `lint_verdict_boundary.py`, `lint_topology.py`, `lint_stage_gates.py`; generators: `gen_reading_map.py`, `gen_doc_stubs.py`, `capture_run_fingerprint.py`)
- Reference: `docs/README.md` (register), `policy/protected-paths.json` (this directory is protected), `docs/tier2/coding-standards.md`

## Process

1. Lint before generate — every lint fails when it scans zero files (vacuity guard).
2. Keep generators pure (read register/source, write generated doc/fingerprint, no mutation of evidence).
3. Run `scripts/lint_protected_paths.py` on any change here — this tree validates itself.

## Outputs

- Lints gate CI (`gates.yml` five jobs); generators emit `docs/README.md`, `vault/`, `bench/fingerprints/` with byte-compared `--check`.

## Human check

Do all lints still fail on a planted violation and pass on the real tree, with this directory still in `policy/protected-paths.json`?
