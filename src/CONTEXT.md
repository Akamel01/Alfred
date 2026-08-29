# src/CONTEXT.md

One job: product code the factory builds — trajectories, metrics, stamping, thresholds, ingest, replay, API — behind the Worker port, not the factory itself.

## Inputs

- Working: `src/domain/`, `src/metrics/`, `src/provenance/`, `src/thresholds/`, `src/ingest/`, `src/replay/`, `src/api/`
- Reference: `docs/tier1/domain-model.md`, `docs/tier1/data-architecture.md` (phases), `docs/tier0/glossary.md`, `policy/protected-paths.json` (read-only — `src/provenance/` + `src/thresholds/` are protected)

## Process

1. Read `docs/tier2/execution-order.md` § S5 for what product work is due and its blockers.
2. Implement behind the port contract in `harness/worker/port.py` (metrics behind `Metric`, ingest behind `TrajectorySource`).
3. Keep pure functions for metrics: trajectories in, values out, no I/O/clock/randomness without declared seed.

## Outputs

- `src/**/*.py` — typed (`pyright --strict`), tested (`tests/`), provenance-stamped where required.

## Human check

Does `pyright --strict` pass and do `tests/` + `harness/selftest` attest the change without touching a protected prefix?
