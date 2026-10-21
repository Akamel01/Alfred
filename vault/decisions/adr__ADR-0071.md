---
kind: adr
id: "adr:ADR-0071"
title: "A conditional roster member: `applies_when`, the named `pathlib-match` dialect, and TOP015 against the vacuous selector"
status: "accepted"
shape: "heading"
date: "2026-10-21"
source: "docs/tier1/adr-log.md:7121"
extractor: "adrs"
aliases:
  - "A conditional roster member: `applies_when`, the named `pathlib-match` dialect, and TOP015"
  - "ADR-0071"
generated: true
---

# A conditional roster member: `applies_when`, the named `pathlib-match` dialect, and TOP015 against the vacuous selector

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:7121`

## Statement

**Date:** 2026-10-21 · **Status:** Accepted · **Supersedes:** none · **Amends:** `policy/role-bindings.json` (the `reviewer` roster), `scripts/lint_topology.py` (TOP015), `docs/tier3/agent-definition-standard.md` (the `applies_when` field) · **See also:** ADR-0007 (the vacuity class), ADR-0056 (a binding edit is a requalification event), ADR-0069 (the unset D19 fields), ADR-0067 (the batched Gate D read), #43 (D6, D7), #85 · **D28 waiver:** no

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- **see_also** → [[adr__ADR-0007|Executor-premise assertions may pass vacuously, and that is a third outcome]]
- **see_also** → [[adr__ADR-0056|The requalification trigger covers the whole binding, and the five fields that would recor]]
- **see_also** → [[adr__ADR-0067|Gate D's read is batched per pull request, and the comment-only exemption is rejected as u]]
- **see_also** → [[adr__ADR-0069|Unset D19 version fields report `indeterminate`, and TOP014 makes a silent `pass` impossib]]
