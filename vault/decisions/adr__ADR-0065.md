---
kind: adr
id: "adr:ADR-0065"
title: "The bench append-only guarantee gets the lint ADR-0038 said it already had, and the shallow checkout that would have made it vacuous is fixed with it"
status: "accepted"
shape: "heading"
date: "2026-09-07"
source: "docs/tier1/adr-log.md:6723"
extractor: "adrs"
aliases:
  - "ADR-0065"
  - "The bench append-only guarantee gets the lint ADR-0038 said it already had, and the shallo"
generated: true
---

# The bench append-only guarantee gets the lint ADR-0038 said it already had, and the shallow checkout that would have made it vacuous is fixed with it

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:6723`

## Statement

**Date:** 2026-09-07 · **Status:** Accepted · **Supersedes:** none · **Amends:** `.github/workflows/gates.yml` (replaces the inline step, adds `fetch-depth: 0` to `integrity`); corrects ADR-0038's enforcement paragraph, which cannot be edited in place · **See also:** ADR-0038 (the harden decision this finally implements), ADR-0060 (the audit that found this), ADR-0007 and D57 (the vacuity class), ADR-0017 (a hole never passes), #4, #88 · **D28 waiver:** no — no register document is amended; `gates.yml` and `scripts/` are code, not documents carrying a status header

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- **amends** → [[adr__ADR-0038|bench Immutability: Convention → Git-Level Control]]
- **see_also** → [[adr__ADR-0007|Executor-premise assertions may pass vacuously, and that is a third outcome]]
- **see_also** → [[adr__ADR-0017|A containment assertion with an unread premise is a hole, and a hole never passes]]
- **see_also** → [[adr__ADR-0038|bench Immutability: Convention → Git-Level Control]]
- **see_also** → [[adr__ADR-0060|ADR-0038 decided harden; what was built does not enforce it, names a script that does not ]]

## Enforced by (code)

- **enforced_by** → [[module___github_workflows_gates_yml|.github/workflows/gates.yml]] — the vacuous pass those checks exist to prevent (ADR-0065).
- **enforced_by** → [[module___github_workflows_gates_yml|.github/workflows/gates.yml]] — ADR-0065. That step did not filter by status, so it failed on the additions it
