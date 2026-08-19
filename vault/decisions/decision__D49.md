---
kind: decision
id: "decision:D49"
title: "A grading point is admitted by the provenance of its authorship, not by whether the oracle happened to ship a second constant"
shape: "table-row"
number: "49"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:87"
extractor: "decisions"
aliases:
  - "A grading point is admitted by the provenance of its authorship, not by whether the oracle"
  - "D49"
generated: true
---

# A grading point is admitted by the provenance of its authorship, not by whether the oracle happened to ship a second constant

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:87`

## Statement

**A grading point is admitted by the provenance of its authorship, not by whether the oracle happened to ship a second constant.** Five tiers: **P1** second pinned oracle constant · **P2** oracle-pinned equivariance relation · **P3** oracle recomputation on a seeded resampled slice (= A8's existing mechanism) · **P4** invariance property over inputs generated at verdict time · **P5** held-out degeneracy case from the edge-case catalog. Every schedulable task carries **≥2 grading points, ≥1 held out**, and **≥1 level-fixing point from P1–P3**. P4 alone is invalid — invariance fixes a result's *shape*, never its *level*, so a uniformly scaled wrong answer satisfies it. The held-out point's tier is recorded with every verdict and merge rate is reported stratified by it.

## Falsifies if

> by Phase 0 exit (2026-09-09) the seeded resampler plus pinned oracle does not yield a second non-degenerate value for ≥10 of the 19 borderline measures, in which case P3 does not carry the load and the exit degrades to "exhaust what qualifies, state n and the strata."

## Fields

**rationale**

> The 2026-08-13 enumeration graded task admissibility by counting pinned constants, which is a proxy for what A3/D33 actually need: **a visible/held-out split where passing the visible half does not imply passing the held-out half.** The proxy is wrong in both directions. **Too loose** — of the 10 "strong" measures only **7** hold two independent literals; three derive their second value relationally from the first *computed* value (`thw - 10*dt`, `wttr + 1.0`, `ttce2 - 10*dt`), so a stub that gets the first value wrong gets the second consistently wrong and the pair tests one thing. **Too strict, and this is the larger error** — invariance under rigid transforms and time shifts, and the 30 degeneracy cases, are held-out points **authored by mathematics**: external, unretrievable, and unmemorisable from any constant. The edge-case specification already names degenerate cases "the highest-value held-out material in the product." The audit counted only P1 because it was auditing CriMe's test file rather than the space of available ground truth. Reclassifying yields a schedulable class of **29** and restores "20+" without lowering any bar — D36-compliant, since it narrows and labels rather than loosening. **Falsifies if:** by Phase 0 exit (2026-09-09) the seeded resampler plus pinned oracle does not yield a second non-degenerate value for ≥10 of the 19 borderline measures, in which case P3 does not carry the load and the exit degrades to "exhaust what qualifies, state n and the strata."

## Enforced by (code)

- **enforced_by** → [[module__harness_criterion_runner|Compose one verdict, and keep the held-out half out of the environment that runs.]] — """Compose one verdict, and keep the held-out half out of the environment that runs.

**The structural decision in this 
- **enforced_by** → [[module__harness_criterion_runner|Compose one verdict, and keep the held-out half out of the environment that runs.]] — # D49: every schedulable task carries at least one held-out grading point. A task
- **enforced_by** → [[module__harness_criterion_test_runner|Verdict composition, with the two collapses that would make the number meaningless.]] — """D49: a task the visible half alone would accept is not schedulable."""
- **enforced_by** → [[module__harness_oracle_load|Carries oracle values across the boundary as data, and refuses when they are not clean.]] — # D49. Every point produced by this stage is a constant pinned by the oracle itself, which
- **enforced_by** → [[module__harness_oracle_load|Carries oracle values across the boundary as data, and refuses when they are not clean.]] — # Measures holding at least two non-degenerate points. D49's admissibility test: a
- **enforced_by** → [[module__harness_oracle_points|The questions put to the oracle, and where each one came from.]] — """The questions put to the oracle, and where each one came from.

Every point here was transcribed from CriMe's own tes
- **enforced_by** → [[module__harness_oracle_points|The questions put to the oracle, and where each one came from.]] — # computation is D49's "too loose" case. Recorded, and tiered P2 rather than P1.
- **enforced_by** → [[module__harness_oracle_test_oracle|Tests for the oracle boundary. Most run without the image; the slow one needs it.]] — # --------------------------------------------------------------- D49 admissibility
- **enforced_by** → [[module__migrations_harness_control_versions_0001_control_base|control: work items, fingerprints, protected paths, thresholds.]] — # Set at authoring time, on the criterion rather than on the run. P1…P5 per D49.
- **enforced_by** → [[module__migrations_harness_heldout_versions_0001_heldout_base|heldout: reference values and perturbations.]] — # D49. Every schedulable task carries at least two grading points, at least one held
- **enforced_by** → [[module__migrations_harness_heldout_versions_0001_heldout_base|heldout: reference values and perturbations.]] — # clears a whole bucket, which is a two-sided squeeze D49 never states. Recording the
- **enforced_by** → [[module__migrations_harness_heldout_versions_0001_heldout_base|heldout: reference values and perturbations.]] — # D49 tier, and the oracle that produced it. `oracle_commit_sha` is NOT NULL

## Stated in prose — unverified

- [[stage__S2|Oracle environment]] **blocks** → this — S2 blocks D49
