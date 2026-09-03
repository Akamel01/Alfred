# harness/CONTEXT.md

One job: deterministic inspector machinery that dispatches work, executes criteria, and writes evidence — outside the agent tree, never agent-writable.

## Inputs

- Working: `harness/db/`, `harness/lane/`, `harness/containment/`, `harness/worker/`, `harness/patch/`, `harness/deploy/`, `harness/selftest/`, `harness/fingerprint/`, `harness/acs/`
- Reference: `docs/tier1/adr-log.md` (ADRs 0009–0015, 0018, 0029), `policy/protected-paths.json` (this tree is protected — `harness/`), `docs/tier2/execution-order.md` § S1/S3/S4

## Process

1. Keep `harness/` outside the agent tree — no import path from any agent module to a verdict field (`scripts/lint_verdict_boundary.py` enforces).
2. Write evidence only via `EvidenceStore` (append-only, hash-chained, D43) — never directly.
3. Wrap external executors behind `harness/worker/port.py` (`Worker` protocol + `SandboxHandle` proof).

## Outputs

- Deterministic verdicts + evidence rows in the stores `migrations/` defines; `python3 -m pytest harness -q` green.

## Human check

Is every verdict field written only by code in this tree, under a separate DB role and process, with `lint_verdict_boundary.py` still red on a planted violation?
