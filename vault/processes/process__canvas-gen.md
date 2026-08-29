---
kind: process
id: "process:canvas-gen"
title: "Canvas generation"
shape: "process"
source: "tools/orchestration/gen_canvas.py:1"
extractor: "process"
aliases:
  - "Canvas generation"
  - "canvas-gen"
generated: true
---

# Canvas generation

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `tools/orchestration/gen_canvas.py:1`

## Statement

python3 tools/orchestration/gen_canvas.py --check — topology (orchestration/topology.json) + palette (policy/node-palette.json) → HTML

## Fields

| Field | Value |
|---|---|
| `path` | tools/orchestration/gen_canvas.py |
