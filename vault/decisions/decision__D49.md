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

## Fields

| Field | Value |
|---|---|
| `rationale` | The 2026-08-13 enumeration graded task admissibility by counting pinned constants, which is a proxy for what A3/D33 actually need: **a visible/held-out split where passing the visible half does not imply passing the held-out half.** The proxy is wrong in both directions. **Too loose** — of the 10 "strong" measures only **7** hold two independent literals; three derive their second value relational |

## Enforced by (code)

- **enforced_by** → [[module__harness_criterion_runner|Compose one verdict, and keep the held-out half out of the environment that runs.]] — """Compose one verdict, and keep the held-out half out of the environment that runs.

**The structural decision in this 
- **enforced_by** → [[module__harness_criterion_runner|Compose one verdict, and keep the held-out half out of the environment that runs.]] — # D49: every schedulable task carries at least one held-out grading point. A task
- **enforced_by** → [[module__harness_criterion_test_runner|Verdict composition, with the two collapses that would make the number meaningless.]] — """D49: a task the visible half alone would accept is not schedulable."""
- **enforced_by** → [[module__migrations_harness_control_versions_0001_control_base|control: work items, fingerprints, protected paths, thresholds.]] — # Set at authoring time, on the criterion rather than on the run. P1…P5 per D49.
- **enforced_by** → [[module__migrations_harness_heldout_versions_0001_heldout_base|heldout: reference values and perturbations.]] — # D49. Every schedulable task carries at least two grading points, at least one held
- **enforced_by** → [[module__migrations_harness_heldout_versions_0001_heldout_base|heldout: reference values and perturbations.]] — # clears a whole bucket, which is a two-sided squeeze D49 never states. Recording the
- **enforced_by** → [[module__migrations_harness_heldout_versions_0001_heldout_base|heldout: reference values and perturbations.]] — # D49 tier, and the oracle that produced it. `oracle_commit_sha` is NOT NULL

## Stated in prose — unverified

- [[stage__S2|Oracle environment]] **blocks** → this — S2 blocks D49
