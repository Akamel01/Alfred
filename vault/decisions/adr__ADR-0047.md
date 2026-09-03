---
kind: adr
id: "adr:ADR-0047"
title: "The ownership router gains the factory's facts, and runtime state is never evidence"
status: "accepted"
shape: "heading"
date: "2026-09-03"
source: "docs/tier1/adr-log.md:4439"
extractor: "adrs"
aliases:
  - "ADR-0047"
  - "The ownership router gains the factory's facts, and runtime state is never evidence"
generated: true
---

# The ownership router gains the factory's facts, and runtime state is never evidence

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:4439`

## Statement

**Date:** 2026-09-03 · **Status:** Accepted · **Supersedes:** none · **Amends:** `docs/tier1/data-architecture.md` § *Ownership, stated once so it is not restated inconsistently* (frozen), and `docs/tier3/run-instrumentation-specification.md`'s record-type enum · **See also:** ADR-0003 (ACS-1 domain separation), I2 and I6, `docs/tier7/ticket-45-state-authority-decision.md`, ADR-0039 (the type graph) · **D28 waiver:** no

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- **see_also** → [[adr__ADR-0003|Canonical serialization for hashed structures (ACS-1)]]
- **see_also** → [[adr__ADR-0039|Orchestration Canvas: Protected Topology Source & Palette Binding]]

## Enforced by (code)

- **enforced_by** → [[module__scripts_lint_state_authority|SA001-SA003: the ownership router's mechanical half, checked.]] — """SA001-SA003: the ownership router's mechanical half, checked.

ADR-0047 extends `docs/tier1/data-architecture.md`'s o
- **enforced_by** → [[module__scripts_lint_state_authority|SA001-SA003: the ownership router's mechanical half, checked.]] — #: Runtime state, named once. ADR-0047 decision 3.
