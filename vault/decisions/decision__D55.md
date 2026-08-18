---
kind: decision
id: "decision:D55"
title: "SSP Layered Standard Traceability is declined — and its field set freezes at ten keys with a stamp schema version and a tagged upstream-toolchain field, before any stamp is written"
shape: "table-row"
number: "55"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:99"
extractor: "decisions"
aliases:
  - "D55"
  - "SSP Layered Standard Traceability is declined — and its field set freezes at ten keys with"
generated: true
---

# SSP Layered Standard Traceability is declined — and its field set freezes at ten keys with a stamp schema version and a tagged upstream-toolchain field, before any stamp is written

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:99`

## Statement

**The result stamp stays ACS-1-native — SSP Layered Standard Traceability is declined — and its field set freezes at ten keys with a stamp schema version and a tagged upstream-toolchain field, before any stamp is written.** SSP-LS-Traceability 1.0.0 defines **no canonical form for the SRMD record itself** (its SHA3-256 is over "the raw data of the data item"; the three occurrences of "canonical" in the 253 KB document all refer to a *canonical master source* URI), so it cannot carry a digest a third party recomputes — which is the property Alfred sells. It also has **no field for a tool version or a tool configuration**: `generatingTool` is defined as *"the name of the tool"*, and `fileversion` versions the file, not the tool. So it does not supply the upstream field this decision exists to add. Every provenance field in its Table 62 is Optional against `version`/`name` Mandatory; Alfred inverts that and keeps the version. Dual emission is rejected now and specified as a deferred export adapter: exactly one Alfred field (`stamp_schema_version` → SSP `version`) has a true correspondence, `input_hash` → `checksum` is a semantic mismatch, and the remaining eight have no slot at all — they would land in an opaque `Annotation type="org.alfred.stamp"`, so the SSP-shaped part of the export transmits none of the load-bearing information. **The stamp adds `stamp_schema_version: int` (=1, in the preimage, name and shape pinned for all time) and `upstream: Simulated | Corpus | Unknown` (no `null` arm; `unknown` carries a mandatory reason; "not applicable" is expressed as the positive `corpus` arm so the claim is checkable).** Verifier verdicts are three-valued — `VERIFIED` / `MISMATCH` / `UNVERIFIABLE`, the last mapping to `indeterminate` and never to either other — because "I cannot check this schema version" reported as "tampering" is an incident-grade misreport. ADR-0006. **One thing this does not buy, and it must not be overclaimed:** Alfred's container never observes the simulator, so `tool_name`, `tool_version` and `config_digest` are **declared by whoever ran the run**. The stamp makes the declaration tamper-evident and binds it to a specific number rather than to a file — a real difference from Ansys Minerva's user-declared solver field, whose unit of provenance is a file. It does not make the declaration true, and no assessment conversation may say otherwise. **Falsifies if:** a stamp is found persisted under any shape without `stamp_schema_version`; or a verifier is found reporting `MISMATCH` for an unrecognised schema version; or ≥2 of 3 Phase 0.75 conversations name a toolchain that reads SRMD, which reopens the export adapter.

## Falsifies if

> a stamp is found persisted under any shape without `stamp_schema_version`; or a verifier is found reporting `MISMATCH` for an unrecognised schema version; or ≥2 of 3 Phase 0.75 conversations name a toolchain that reads SRMD, which reopens the export adapter.

## Fields

| Field | Value |
|---|---|
| `rationale` | The change is free today and hash-breaking tomorrow — **verified, not assumed:** all four `migrations/*/versions/` directories contain only `.gitkeep`, no Alembic revision exists, no table holds a stamp, and the only `ResultStamp` constructions in the tree are two test fixtures. Zero stamps have ever been persisted. Without a schema version, adding the upstream field later changes the digest of ev |

## Enforced by (code)

- **enforced_by** → [[module__migrations_product_versions_0001_product_base|product: scenarios, trajectories, metric results, result stamps.]] — """product: scenarios, trajectories, metric results, result stamps.

Revision ID: 0001_product_base
Revises:
Create Date
- **enforced_by** → [[module__migrations_product_versions_0001_product_base|product: scenarios, trajectories, metric results, result stamps.]] — # The ten keys, frozen by D55 / ADR-0006. `stamp_schema_version` is in the
