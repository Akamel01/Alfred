---
kind: decision
id: "decision:D30"
title: "The product is a re-derivability layer for computed criticality metrics"
shape: "table-row"
number: "30"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:74"
extractor: "decisions"
aliases:
  - "D30"
  - "The product is a re-derivability layer for computed criticality metrics"
generated: true
---

# The product is a re-derivability layer for computed criticality metrics

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:74`

## Statement

**The product is a re-derivability layer for computed criticality metrics** — not a risk oracle, and not an attestation service. It computes and reproduces *defined* metrics; every number carries formula, citation, code version, input hash, **upstream toolchain identity as declared** (tool, version, and a digest of the run configuration — tamper-evident and bound to the number, not attested by Alfred, which never observes the simulator) and tolerance, and is independently re-derivable by anyone holding the stamp, the inputs and the code. Risk classification ships only as a configurable overlay with visible provenance, never as a fact. **Amended 2026-08-14 (K5):** the rationale's go-to-market clause — that this is "the audit need behind independent evidence for the system safety case" — is **withdrawn as falsified**. The market position it assumed now lives separately in D48 and is separately falsifiable. **Falsifies if:** (a) by Phase 0 exit (2026-09-09) byte-identical replay cannot be achieved across environments, so "independently re-derivable" is not technically deliverable; or (b) by 2026-10-07, in ≥2 of the 3 recorded demand-gate conversations, the artifact the buyer names contains no provenance or reproduction element.

## Falsifies if

> (a) by Phase 0 exit (2026-09-09) byte-identical replay cannot be achieved across environments, so "independently re-derivable" is not technically deliverable; or (b) by 2026-10-07, in ≥2 of the 3 recorded demand-gate conversations, the artifact the buyer names contains no provenance or reproduction element.

## Fields

| Field | Value |
|---|---|
| `rationale` | The product-shape argument never depended on regulation and is untouched. What K5 removed was the claim that someone is *compelled* to procure an independent opinion — a market claim fused into a product decision and therefore never separately tested. The word "audit" carried the fusion: re-derivability is a property of the artifact and needs no buyer's compulsion; attestation is a service needing |
