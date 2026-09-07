---
kind: adr
id: "adr:ADR-0067"
title: "Gate D's read is batched per pull request, and the comment-only exemption is rejected as unsafe here"
status: "accepted"
shape: "heading"
date: "2026-09-07"
source: "docs/tier1/adr-log.md:6922"
extractor: "adrs"
aliases:
  - "ADR-0067"
  - "Gate D's read is batched per pull request, and the comment-only exemption is rejected as u"
generated: true
---

# Gate D's read is batched per pull request, and the comment-only exemption is rejected as unsafe here

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:6922`

## Statement

**Date:** 2026-09-07 · **Status:** Accepted · **Supersedes:** none · **Amends:** `docs/tier4/protected-paths-policy.md` § *The inspector stays small* (frozen, `ci-gate`) · **See also:** ADR-0028 (an agent cannot supply this approval for itself), ADR-0035 (the first waiver against this document), `tools/vaultgraph/extract/references.py` (why comments are not inert), #93 · **D28 waiver:** yes

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- **see_also** → [[adr__ADR-0028|The review ADR-0027 said was owed has been done]]
- **see_also** → [[adr__ADR-0035|The protected set's single home names its fourth shape as a projection, not a second autho]]
