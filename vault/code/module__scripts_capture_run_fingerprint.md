---
kind: module
id: "module:scripts.capture_run_fingerprint"
title: "Factory-owned script that collects all RunFingerprint fields from live sources,"
shape: "file"
present: "true"
protected: "true"
lint_gated: "false"
source: "scripts/capture_run_fingerprint.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Factory-owned script that collects all RunFingerprint fields from live sources,"
  - "scripts.capture_run_fingerprint"
generated: true
---

# Factory-owned script that collects all RunFingerprint fields from live sources,

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `scripts/capture_run_fingerprint.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | scripts/capture_run_fingerprint.py |
| `tree` | scripts |

## Binds

- **imports** → [[module__harness_acs_acs1|ACS-1 — Alfred Canonical Serialization, version 1 (ADR-0003, ADR-0004).]]
- **imports** → [[module__harness_fingerprint_record|The run fingerprint record: what a run was measured on, stated once and hashed.]]

## Enforced by (code)

- [[decision__D19|Autonomy grants are keyed to a fingerprint]] **enforced_by** → this — # D19
- [[decision__D40|fingerprint extension (final form)]] **enforced_by** → this — # D40
