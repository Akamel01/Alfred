---
kind: adr
id: "adr:ADR-0069"
title: "Unset D19 version fields report `indeterminate`, and TOP014 makes a silent `pass` impossible"
status: "accepted"
shape: "heading"
date: "2026-10-18"
source: "docs/tier1/adr-log.md:7036"
extractor: "adrs"
aliases:
  - "ADR-0069"
  - "Unset D19 version fields report `indeterminate`, and TOP014 makes a silent `pass` impossib"
generated: true
---

# Unset D19 version fields report `indeterminate`, and TOP014 makes a silent `pass` impossible

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:7036`

## Statement

**Date:** 2026-10-18 · **Status:** Accepted · **Supersedes:** none · **Amends:** `policy/role-bindings.json` (top-level `requalification` key), `scripts/lint_topology.py` (TOP014), `docs/tier3/agent-definition-standard.md` (evidence, falsifies_if, Enforcement) · **See also:** ADR-0007 (the vacuity class), ADR-0056 (the requalification trigger), ADR-0067 (the batched Gate D read), #86 · **D28 waiver:** no

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- **see_also** → [[adr__ADR-0007|Executor-premise assertions may pass vacuously, and that is a third outcome]]
- **see_also** → [[adr__ADR-0056|The requalification trigger covers the whole binding, and the five fields that would recor]]
- **see_also** → [[adr__ADR-0067|Gate D's read is batched per pull request, and the comment-only exemption is rejected as u]]
