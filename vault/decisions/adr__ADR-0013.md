---
kind: adr
id: "adr:ADR-0013"
title: "Containment probes, and the control that stops each one reading green"
status: "accepted"
shape: "heading"
date: "2026-08-17"
source: "docs/tier1/adr-log.md:1235"
extractor: "adrs"
aliases:
  - "ADR-0013"
  - "Containment probes, and the control that stops each one reading green"
generated: true
---

# Containment probes, and the control that stops each one reading green

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:1235`

## Statement

**Date:** 2026-08-17 · **Status:** Accepted · **Supersedes:** none

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- [[adr__ADR-0015|An agent edited the inspector, and this record was drafted by the same agent]] **see_also** → this

## Enforced by (code)

- **enforced_by** → [[module___github_workflows_gates_yml|.github/workflows/gates.yml]] — ADR-0013), arriving through a new door.
