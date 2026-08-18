---
kind: decision
id: "decision:D48"
title: "Alfred's buyer is the AV developer's own simulation/V&V function, not a regulator and not an attester"
shape: "table-row"
number: "48"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:85"
extractor: "decisions"
aliases:
  - "Alfred's buyer is the AV developer's own simulation/V&V function, not a regulator and not "
  - "D48"
generated: true
---

# Alfred's buyer is the AV developer's own simulation/V&V function, not a regulator and not an attester

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:85`

## Statement

**Alfred's buyer is the AV developer's own simulation/V&V function, not a regulator and not an attester.** Alfred supplies provenance tooling the customer operates itself, delivered as a customer-run container on the customer's own data; Alfred never issues an opinion on anyone's evidence and never holds customer data. Approach order is fixed and load-bearing: **simulation/V&V tooling engineer first, homologation second.** **Falsifies if:** by **2026-10-07**, no Track-1 role at three organisations names an artifact, in their own words, containing a provenance or re-derivability element. *(Track 2's result does not rescue this — the V&V engineer is the declared primary buyer, so the primary framing falsifies on its own evidence. A Track-2 respondent reporting a completed or scheduled 2022/1426 approval determines only whether the homologation framing survives as a slower fallback.)* **Consequence on falsification — and it is not another AV wedge:** the D1/D2 product-selection logic is re-run against a named alternative domain, decided by **2026-10-21**. Domain-neutral assets carry (ACS-1 and its vector suite, result stamping, `MetricValue`/`MetricSeries` and the reason codebook, the evidence chain, the document register, the harness, the lane); AV-specific assets are written off (edge-case catalog, CriMe oracle, `phase1_tasks.json`).

## Falsifies if

> by

## Fields

**rationale**

> K5 established that no instrument compels independent attestation. What survives is a duty on the *manufacturer*: EU 2022/1426 Annex III Part 4's binding "shall" obligations — Simulation Handbook, storage of every toolchain version used to release certification data, traceability from M&S output back to setup — which create a tooling need, not an attestation market. Against the assessors (TÜV SÜD, SGS, DEKRA, national technical services) Alfred is a **complement**: part of the toolchain being assessed, not a party to the assessment. Approach order is decided on **feedback latency**, which this plan names as the constraint that starves the calibration loop: a V&V engineer answers in days from a tooling budget; a homologation function answers in quarters through procurement. The two framings sell the *same artifact* in different words — "traceability from M&S output back to setup" and "you can tell which change moved the number" are the same feature — so this is a sequencing call, not a product fork, and nothing in Phase 0 or Phase 1 differs between them. **Recorded as the destination on falsification because two independent legs of the AV domain choice weakened in the same week:** K5 removed the market rationale, and the 2026-08-13 task enumeration measured the "long, well-shaped task tail" at **10 strong tasks**, not the ~20 the Phase 1 exit assumed. The plan recorded both and connected neither.
