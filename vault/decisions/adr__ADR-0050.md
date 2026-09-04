---
kind: adr
id: "adr:ADR-0050"
title: "Mission Control is hosted off-host, and the loopback bind is replaced rather than relaxed"
status: "accepted"
shape: "heading"
date: "2026-09-03"
source: "docs/tier1/adr-log.md:4700"
extractor: "adrs"
aliases:
  - "ADR-0050"
  - "Mission Control is hosted off-host, and the loopback bind is replaced rather than relaxed"
generated: true
---

# Mission Control is hosted off-host, and the loopback bind is replaced rather than relaxed

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:4700`

## Statement

**Date:** 2026-09-03 · **Status:** Accepted · **Supersedes:** none · **Amends:** `docs/tier1/mission-control-specification.md` § *Authentication and exposure*; `docs/tier2/coding-standards.md` § *Structure* (frozen, `ci-gate`) · **See also:** ADR-0049, `docs/tier4/threat-model.md`, `docs/tier4/permission-and-identity-model.md` · **D28 waiver:** no

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- **see_also** → [[adr__ADR-0049|Agent-stated intent is rendered on the live view and nowhere a decision is taken]]
- [[adr__ADR-0051|The live view is pulled forward ahead of its trigger, and the trigger's reasoning is not d]] **see_also** → this
