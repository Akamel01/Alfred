---
kind: module
id: "module:harness.oracle.load"
title: "Carries oracle values across the boundary as data, and refuses when they are not clean."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/oracle/load.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Carries oracle values across the boundary as data, and refuses when they are not clean."
  - "harness.oracle.load"
generated: true
---

# Carries oracle values across the boundary as data, and refuses when they are not clean.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/oracle/load.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/oracle/load.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_acs_acs1|ACS-1 — Alfred Canonical Serialization, version 1 (ADR-0003, ADR-0004).]]
- **imports** → [[module__harness_oracle_pins|What the oracle environment is pinned to, and the platform finding that forced it.]]
- [[module__harness_oracle|harness.oracle]] **contains** → this
- [[module__harness_oracle_test_oracle|Tests for the oracle boundary. Most run without the image; the slow one needs it.]] **imports** → this

## Enforced by (code)

- [[adr__ADR-0007|Executor-premise assertions may pass vacuously, and that is a third outcome]] **enforced_by** → this — """Carries oracle values across the boundary as data, and refuses when they are not clean.

The oracle's code never cros
- [[decision__D49|A grading point is admitted by the provenance of its authorship, not by whether the oracle]] **enforced_by** → this — # D49. Every point produced by this stage is a constant pinned by the oracle itself, which
- [[decision__D49|A grading point is admitted by the provenance of its authorship, not by whether the oracle]] **enforced_by** → this — # Measures holding at least two non-degenerate points. D49's admissibility test: a
- [[decision__D54|D50 is enforced by an environment split, not by a check alone: the oracle's outputs cross ]] **enforced_by** → this — """Carries oracle values across the boundary as data, and refuses when they are not clean.

The oracle's code never cros
