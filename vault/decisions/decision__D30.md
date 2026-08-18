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

**rationale**

> The product-shape argument never depended on regulation and is untouched. What K5 removed was the claim that someone is *compelled* to procure an independent opinion — a market claim fused into a product decision and therefore never separately tested. The word "audit" carried the fusion: re-derivability is a property of the artifact and needs no buyer's compulsion; attestation is a service needing both compulsion and an attester with standing. Alfred builds the first. Original rationale, still standing on its product half: incumbents already own coverage and dashboards — Applied Intuition sells the aggregation-and-validation layer to 18 of the top 20 OEMs; Foretellix authors the ASAM standard; Streetscope has a published method and an ISO 26262 application. Meanwhile the differentiator Alfred was counting on — absolute risk quantification — is exactly what surrogate metrics cannot deliver: TTC and PET produce contradictory conclusions on identical data, and no threshold standard exists. Reproducibility is ~~unclaimed, is the audit need behind "independent evidence for the system safety case", and~~ **[clause withdrawn 2026-08-14; replaced 2026-08-15 after research — reproducibility is not "unclaimed": SSP-LS-Traceability 1.0.0 already specifies the record (SHA3-256 checksum, generating tool, derivation chain) and prostep ivip is funded to pursue it. What is unclaimed is **shipping it at the metric level with re-derivation and a recall path** — every provenance attribute in that spec is marked Optional, no vendor implements it, and Ansys Minerva, the closest thing that exists, is file-level with no recall. Restated: *specified but not shipped, and not re-derivable or recallable by anyone*]** the one thing Alfred's provenance architecture is already built to do.
