---
kind: process
id: "process:vault-regen"
title: "Vault regeneration"
shape: "process"
source: "tools/gen_vault.py:1"
extractor: "process"
aliases:
  - "Vault regeneration"
  - "vault-regen"
generated: true
---

# Vault regeneration

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `tools/gen_vault.py:1`

## Statement

python3 tools/gen_vault.py && python3 tools/gen_vault.py --check — build graph.json + vault/ (one extraction, several renderers)

## Fields

| Field | Value |
|---|---|
| `path` | tools/gen_vault.py |
