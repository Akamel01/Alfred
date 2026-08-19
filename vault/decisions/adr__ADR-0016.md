---
kind: adr
id: "adr:ADR-0016"
title: "`StampedResult` takes its schema version from the stamp it contains"
status: "accepted"
shape: "heading"
date: "2026-08-18"
source: "docs/tier1/adr-log.md:1513"
extractor: "adrs"
aliases:
  - "ADR-0016"
  - "`StampedResult` takes its schema version from the stamp it contains"
generated: true
---

# `StampedResult` takes its schema version from the stamp it contains

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:1513`

## Statement

**Date:** 2026-08-18 · **Status:** Accepted · **Supersedes:** none · **Amends:** ADR-0006 (which versions the stamp and is silent on the record that wraps it) · **See also:** ADR-0001 (the tagged `MetricValue` encoding is inside this record's preimage), ADR-0003 (`alfred.stamped_result` is the third domain-separation record type)

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- **amends** → [[adr__ADR-0006|The result stamp field set, its own version, and upstream toolchain provenance]]
- **see_also** → [[adr__ADR-0001|Representation of undefined and infinite metric values]]
- **see_also** → [[adr__ADR-0003|Canonical serialization for hashed structures (ACS-1)]]

## Enforced by (code)

- **enforced_by** → [[module__harness_acs_gen_vectors|Generate the ACS-1 test-vector suite (ADR-0003).]] — "stamp_schema_version is inside this preimage (ADR-0016)"
- **enforced_by** → [[module__src_provenance_stamp|Result stamping — the shape in which a number leaves the system.]] — """A metric value that can be re-derived and, if necessary, recalled.

    The only shape in which a number leaves the s
