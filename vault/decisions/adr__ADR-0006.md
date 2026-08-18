---
kind: adr
id: "adr:ADR-0006"
title: "The result stamp field set, its own version, and upstream toolchain provenance"
status: "accepted"
shape: "heading"
date: "2026-08-16"
source: "docs/tier1/adr-log.md:459"
extractor: "adrs"
aliases:
  - "ADR-0006"
  - "The result stamp field set, its own version, and upstream toolchain provenance"
generated: true
---

# The result stamp field set, its own version, and upstream toolchain provenance

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:459`

## Statement

**Date:** 2026-08-16 · **Status:** Accepted · **Supersedes:** none · **Forward pointers:** ADR-0001 (the tagged-union pattern gains a third use), ADR-0003 (the record type `alfred.result_stamp` gains a versioned field set; a second record type `alfred.upstream_config` is allocated)

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- **see_also** → [[adr__ADR-0001|Representation of undefined and infinite metric values]]
- **see_also** → [[adr__ADR-0003|Canonical serialization for hashed structures (ACS-1)]]
- [[adr__ADR-0001|Representation of undefined and infinite metric values]] **see_also** → this
- [[adr__ADR-0003|Canonical serialization for hashed structures (ACS-1)]] **see_also** → this

## Enforced by (code)

- **enforced_by** → [[module__migrations_product_versions_0001_product_base|product: scenarios, trajectories, metric results, result stamps.]] — # The ten keys, frozen by D55 / ADR-0006. `stamp_schema_version` is in the
