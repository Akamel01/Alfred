---
kind: adr
id: "adr:ADR-0038"
title: "bench Immutability: Convention → Git-Level Control"
status: "accepted"
shape: "heading"
date: "2026-08-24"
source: "docs/tier1/adr-log.md:3933"
extractor: "adrs"
aliases:
  - "ADR-0038"
  - "bench Immutability: Convention → Git-Level Control"
generated: true
---

# bench Immutability: Convention → Git-Level Control

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:3933`

## Statement

**Date:** 2026-08-24 · **Status:** Accepted · **Supersedes:** none · **See also:** Issue #4 (review output)

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- [[adr__ADR-0060|ADR-0038 decided harden; what was built does not enforce it, names a script that does not ]] **amends** → this
- [[adr__ADR-0065|The bench append-only guarantee gets the lint ADR-0038 said it already had, and the shallo]] **amends** → this
- [[adr__ADR-0060|ADR-0038 decided harden; what was built does not enforce it, names a script that does not ]] **see_also** → this
- [[adr__ADR-0065|The bench append-only guarantee gets the lint ADR-0038 said it already had, and the shallo]] **see_also** → this

## Enforced by (code)

- **enforced_by** → [[module__scripts_lint_bench_append_only|`bench/results/` and `bench/fingerprints/` are append-only. This is what says so.]] — """`bench/results/` and `bench/fingerprints/` are append-only. This is what says so.

ADR-0038 decided *harden* and name
