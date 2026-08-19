---
kind: module
id: "module:harness.oracle.fingerprints"
title: "Runs INSIDE the oracle image. Emits digests and names, and never the source itself."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/oracle/fingerprints.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Runs INSIDE the oracle image. Emits digests and names, and never the source itself."
  - "harness.oracle.fingerprints"
generated: true
---

# Runs INSIDE the oracle image. Emits digests and names, and never the source itself.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/oracle/fingerprints.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/oracle/fingerprints.py |
| `tree` | harness |

## Binds

- [[module__harness_oracle|harness.oracle]] **contains** → this

## Enforced by (code)

- [[adr__ADR-0007|Executor-premise assertions may pass vacuously, and that is a third outcome]] **enforced_by** → this — """Runs INSIDE the oracle image. Emits digests and names, and never the source itself.

Two jobs, both of which need the
- [[decision__D54|D50 is enforced by an environment split, not by a check alone: the oracle's outputs cross ]] **enforced_by** → this — """Runs INSIDE the oracle image. Emits digests and names, and never the source itself.

Two jobs, both of which need the
- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — # D57. A register built from zero files would disable clause 3 while looking built.
