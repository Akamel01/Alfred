---
kind: process
id: "process:dispatch"
title: "Dispatch + patch gate"
shape: "process"
source: "harness/worker/port.py:1"
extractor: "process"
aliases:
  - "Dispatch + patch gate"
  - "dispatch"
generated: true
---

# Dispatch + patch gate

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/worker/port.py:1`

## Statement

Worker port + harness/patch/validate.py (A2/A10) — privileged-side diff read, protected-prefix refusal, A10 scan

## Fields

| Field | Value |
|---|---|
| `path` | harness/worker/port.py |
