---
kind: adr
id: "adr:ADR-0015"
title: "An agent edited the inspector, and this record was drafted by the same agent"
status: "accepted"
shape: "heading"
date: "2026-08-18"
source: "docs/tier1/adr-log.md:1444"
extractor: "adrs"
aliases:
  - "ADR-0015"
  - "An agent edited the inspector, and this record was drafted by the same agent"
generated: true
---

# An agent edited the inspector, and this record was drafted by the same agent

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:1444`

## Statement

**Date:** 2026-08-18 · **Status:** Accepted · **Supersedes:** none · **See also:** ADR-0012 (the vacuity guard this ADR wires into CI), ADR-0013 (the control that stops a probe reading green)

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- **see_also** → [[adr__ADR-0012|The verdict boundary is a lint, and the lint fails when it has nothing to check]]
- **see_also** → [[adr__ADR-0013|Containment probes, and the control that stops each one reading green]]
- [[adr__ADR-0016|The review ADR-0015 said was owed has been done]] **see_also** → this
