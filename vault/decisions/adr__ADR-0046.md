---
kind: adr
id: "adr:ADR-0046"
title: "Registry additions to the register generators are inspector patches, and carry this ADR"
status: "accepted"
shape: "heading"
date: "2026-09-03"
source: "docs/tier1/adr-log.md:4346"
extractor: "adrs"
aliases:
  - "ADR-0046"
  - "Registry additions to the register generators are inspector patches, and carry this ADR"
generated: true
---

# Registry additions to the register generators are inspector patches, and carry this ADR

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:4346`

## Statement

**Date:** 2026-09-03 · **Status:** Accepted · **Supersedes:** none · **Amends:** nothing; this record supplies an obligation that was owed and initially misread · **See also:** ADR-0031 (the machine-readable protected set), D20, `docs/tier4/protected-paths-policy.md` § *The inspector stays small*, ADR-0045 (the effort this work belongs to) · **D28 waiver:** no

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- **see_also** → [[adr__ADR-0031|The protected set is one file, and the gate protects its own policy]]
- **see_also** → [[adr__ADR-0045|The ECC coupling is factory scope, ring-fenced, and overrides no gate]]
- [[adr__ADR-0048|The palette gains seven `hands-off-to` ports so the lifecycle chain becomes expressible]] **see_also** → this
