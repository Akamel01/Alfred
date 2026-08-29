---
kind: process
id: "process:gate-run"
title: "Gate run (five jobs)"
shape: "process"
source: ".github/workflows/gates.yml:15"
extractor: "process"
aliases:
  - "Gate run (five jobs)"
  - "gate-run"
generated: true
---

# Gate run (five jobs)

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:15`

## Statement

push/PR → integrity → product/inspector/database/mutation — enforcement: ci-gate, review-cadence, schema

## Fields

| Field | Value |
|---|---|
| `path` | .github/workflows/gates.yml |
