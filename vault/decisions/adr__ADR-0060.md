---
kind: adr
id: "adr:ADR-0060"
title: "ADR-0038 decided harden; what was built does not enforce it, names a script that does not exist, and has never scanned a real diff"
status: "accepted"
shape: "heading"
date: "2026-09-05"
source: "docs/tier1/adr-log.md:5878"
extractor: "adrs"
aliases:
  - "ADR-0038 decided harden; what was built does not enforce it, names a script that does not "
  - "ADR-0060"
generated: true
---

# ADR-0038 decided harden; what was built does not enforce it, names a script that does not exist, and has never scanned a real diff

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:5878`

## Statement

**Date:** 2026-09-05 · **Status:** Accepted · **Supersedes:** none · **Amends:** ADR-0038's enforcement description · **See also:** ADR-0038 (the harden decision this audits rather than re-litigates), ADR-0031 (the protected set), ADR-0007 (the vacuity class), D57, #4, #88 · **D28 waiver:** no

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- **amends** → [[adr__ADR-0038|bench Immutability: Convention → Git-Level Control]]
- **see_also** → [[adr__ADR-0007|Executor-premise assertions may pass vacuously, and that is a third outcome]]
- **see_also** → [[adr__ADR-0031|The protected set is one file, and the gate protects its own policy]]
- **see_also** → [[adr__ADR-0038|bench Immutability: Convention → Git-Level Control]]
