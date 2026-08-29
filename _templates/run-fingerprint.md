# Run Fingerprint — <seed / run id>

> Capture via `python3 scripts/capture_run_fingerprint.py` — hash derived via ACS-1, never hand-written.

## D19 — Requalification

- capability:
- weights:
- quantization_artifact_hash:

## D40 — Measurement comparability

- inference_runtime:
- runtime_version:
- server_version:
- orchestrator_commit:

## Lane — Serving

- harness_identity:
- runtime_image_digest:
- prompt_version:

## Worker — Executor / provisioning

- worker:
- context_strategy_version:
- resolved_lockfile_hash:

## Hash

- `fingerprint_sha256`: derived via `harness/acs/acs1.py` — never supplied (ADR-0036).
