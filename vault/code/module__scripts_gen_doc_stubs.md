---
kind: module
id: "module:scripts.gen_doc_stubs"
title: "Generate the Alfred documentation register as stubs (D32)."
shape: "file"
present: "true"
protected: "true"
lint_gated: "false"
source: "scripts/gen_doc_stubs.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Generate the Alfred documentation register as stubs (D32)."
  - "scripts.gen_doc_stubs"
generated: true
---

# Generate the Alfred documentation register as stubs (D32).

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `scripts/gen_doc_stubs.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | scripts/gen_doc_stubs.py |
| `tree` | scripts |

## Enforced by (code)

- [[adr__ADR-0063|The structure fence is split out and reclassified provisional, discharging the falsificati]] **enforced_by** → this — "coding standards by ADR-0063: it is provisional because a list tracking a directory tree must "
- [[decision__D28|Stage gates are executable where measurable; overriding one requires an immutable waiver A]] **enforced_by** → this — "move when the tree does, and freezing it cost three D28 waivers."
- [[decision__D32|All 55 documents written as stubs; full content only for the ~12–15 Phase 0 can falsify]] **enforced_by** → this — """Generate the Alfred documentation register as stubs (D32).

A stub is header contract + two-sentence purpose + enforc
- [[decision__D32|All 55 documents written as stubs; full content only for the ~12–15 Phase 0 can falsify]] **enforced_by** → this — """---
status:        {status}
owner:         {owner}
enforcement:   {enforcement}
evidence:      none — written pre-Pha
