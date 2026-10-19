---
kind: adr
id: "adr:ADR-0070"
title: "The #70 measurement gets a pre-run design: N against the interval, an honest fingerprint pair, and an empty trivial class until a run exists"
status: "accepted"
shape: "heading"
date: "2026-10-18"
source: "docs/tier1/adr-log.md:7003"
extractor: "adrs"
aliases:
  - "ADR-0070"
  - "The #70 measurement gets a pre-run design: N against the interval, an honest fingerprint p"
generated: true
---

# The #70 measurement gets a pre-run design: N against the interval, an honest fingerprint pair, and an empty trivial class until a run exists

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:7003`

## Statement

**Date:** 2026-10-18 · **Status:** Accepted · **Supersedes:** none · **Amends:** `scripts/gen_doc_stubs.py` (NOT_GENERATED bookkeeping) and `scripts/gen_reading_map.py` (a reading position) · **See also:** ADR-0054 (check A, dormant behind the same missing dispatcher), ADR-0065 (the vacuity class this design keeps out of its own numbers), ADR-0066 (why appending here is not a waiver), #70, #86 (the 24 unset version fields), `docs/tier7/ticket-46-model-routing-decision.md` (the policy this measurement would inform), `docs/tier0/charter-and-non-goals.md` K3, `docs/tier2/execution-order.md:424` · **D28 waiver:** no — `scripts/` and `tests/` are code, the ADR log is append-only by construction, and no register document carrying a status header is amended

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- **see_also** → [[adr__ADR-0054|Check A lands: the model that answers is asserted against the fingerprint before an attemp]]
- **see_also** → [[adr__ADR-0065|The bench append-only guarantee gets the lint ADR-0038 said it already had, and the shallo]]
- **see_also** → [[adr__ADR-0066|A D28 waiver declaration becomes correctable in the same append-only channel as its ordina]]
