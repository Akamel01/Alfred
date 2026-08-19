---
kind: adr
id: "adr:ADR-0012"
title: "The verdict boundary is a lint, and the lint fails when it has nothing to check"
status: "accepted"
shape: "heading"
date: "2026-08-17"
source: "docs/tier1/adr-log.md:1149"
extractor: "adrs"
aliases:
  - "ADR-0012"
  - "The verdict boundary is a lint, and the lint fails when it has nothing to check"
generated: true
---

# The verdict boundary is a lint, and the lint fails when it has nothing to check

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:1149`

## Statement

**Date:** 2026-08-17 · **Status:** Accepted · **Supersedes:** none

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- [[adr__ADR-0027|An agent edited the inspector, and this record was drafted by the same agent]] **see_also** → this

## Enforced by (code)

- **enforced_by** → [[module___github_workflows_gates_yml|.github/workflows/gates.yml]] — would pass. That is the failure this project has paid for four times (ADR-0012,
