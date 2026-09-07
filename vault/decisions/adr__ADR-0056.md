---
kind: adr
id: "adr:ADR-0056"
title: "The requalification trigger covers the whole binding, and the five fields that would record it are all unset"
status: "accepted"
shape: "heading"
date: "2026-09-05"
source: "docs/tier1/adr-log.md:5316"
extractor: "adrs"
aliases:
  - "ADR-0056"
  - "The requalification trigger covers the whole binding, and the five fields that would recor"
generated: true
---

# The requalification trigger covers the whole binding, and the five fields that would record it are all unset

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:5316`

## Statement

**Date:** 2026-09-05 · **Status:** Accepted · **Supersedes:** none · **Amends:** `policy/role-bindings.json`'s third note · **See also:** `docs/tier7/ticket-43-role-bindings-decision.md` D7 (the ruling this restates and does not invent), `docs/tier0/autonomy-boundaries.md:123` (the tiering), `harness/fingerprint/factory.py` (which already named this hole), ADR-0007 (the vacuity class), #84, #85 · **D28 waiver:** no

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- **see_also** → [[adr__ADR-0007|Executor-premise assertions may pass vacuously, and that is a third outcome]]
