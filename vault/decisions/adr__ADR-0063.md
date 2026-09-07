---
kind: adr
id: "adr:ADR-0063"
title: "The structure fence is split out and reclassified provisional, discharging the falsification ADR-0062 recorded"
status: "accepted"
shape: "heading"
date: "2026-09-06"
source: "docs/tier1/adr-log.md:6530"
extractor: "adrs"
aliases:
  - "ADR-0063"
  - "The structure fence is split out and reclassified provisional, discharging the falsificati"
generated: true
---

# The structure fence is split out and reclassified provisional, discharging the falsification ADR-0062 recorded

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:6530`

## Statement

**Date:** 2026-09-06 · **Status:** Accepted · **Supersedes:** none · **Amends:** `docs/tier2/coding-standards.md` (removes § Structure), `docs/README.md` (register row), `scripts/gen_doc_stubs.py` (stub register), `tools/vaultgraph/extract/layout.py` and `extract/effect.py` (repointed) · **See also:** ADR-0062 (the falsification this discharges), ADR-0033, ADR-0040 and ADR-0050 (the three waivers), ADR-0005 (the constitution is human-authored), `docs/tier0/operating-principles.md:6`, #78, #79 · **D28 waiver:** yes — the fifth by the log's derivation and the sixth in fact (ADR-0050's header is not yet corrected; see the Decision), and the fourth and terminal one against this fence

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- **see_also** → [[adr__ADR-0005|The Tier 0 authorship boundary is split by population, and enforced by an append-only log]]
- **see_also** → [[adr__ADR-0033|The structure fence names every top-level directory, and the vault floors it]]
- **see_also** → [[adr__ADR-0040|The structure fence grows to eighteen]]
- **see_also** → [[adr__ADR-0050|Mission Control is hosted off-host, and the loopback bind is replaced rather than relaxed]]
- **see_also** → [[adr__ADR-0062|Amending a frozen ci-gate document is a D28 waiver; ADR-0050 is retroactively the third ag]]
- [[adr__ADR-0064|The cross-stage invariants are reclassified provisional and stop re-listing what the lint ]] **see_also** → this

## Enforced by (code)

- **enforced_by** → [[module__scripts_gen_doc_stubs|Generate the Alfred documentation register as stubs (D32).]] — "coding standards by ADR-0063: it is provisional because a list tracking a directory tree must "
