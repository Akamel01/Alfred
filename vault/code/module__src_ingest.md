---
kind: module
id: "module:src.ingest"
title: "src.ingest"
shape: "package"
present: "true"
protected: "false"
lint_gated: "true"
source: "src/ingest:1"
extractor: "code"
aliases:
  - "src.ingest"
generated: true
---

# src.ingest

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `src/ingest:1`

## Fields

| Field | Value |
|---|---|
| `namespace_package` | false |
| `tree` | src |

## Binds

- **contains** → [[module__src_ingest___init__|Dataset adapters. The port is here; every adapter behind it is domain work.]]
- **contains** → [[module__src_ingest_port|The `TrajectorySource` port — how observed motion enters the system, and in what frame.]]
