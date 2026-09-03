---
kind: process
id: "process:doc-gen"
title: "Doc generation"
shape: "process"
source: "scripts/gen_reading_map.py:1"
extractor: "process"
aliases:
  - "Doc generation"
  - "doc-gen"
generated: true
---

# Doc generation

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `scripts/gen_reading_map.py:1`

## Statement

python3 scripts/gen_reading_map.py --check + python3 scripts/lint_docs.py --check — reading map + register index

## Fields

| Field | Value |
|---|---|
| `path` | scripts/gen_reading_map.py |
