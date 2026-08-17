---
status:        provisional
owner:         human
enforcement:   review-cadence
evidence:      none — written pre-Phase-0. The engineering thesis rests on four adversarial research runs; the commercial thesis rests on nothing yet and is the subject of the Phase 0.75 demand gate.
falsifies_if:  No named buyer role at three AV organizations will describe, in their own words, an artifact they would pay for — or no design-partner engagement exists by the end of Phase 1. Either observation falsifies the AV wedge, which is parked under K1 while the factory continues; demand is retested at K6.
review_after:  Phase 0.75
---

# Charter and Non-Goals

## What Alfred is

Alfred is a **supervised software factory with shrinking human gates**: a platform in
which LLM agents are replaceable, sandboxed, permissioned workers producing validated
artifacts under deterministic orchestration. Truth lives in a control plane — never in
prompts, never in agent-to-agent conversation.

Autonomy is not declared at the end of a stage list. It is **granted per task-class,
against measured merge rate and defect-escape rate, on a recorded fingerprint** — and
it is revocable.

## What Alfred builds first

A **reproducibility and audit layer for collision-risk quantification in autonomous
vehicles**. It computes, reproduces and audits *defined* criticality metrics. Every
number carries its formula, citation, code version and input hash, and is independently
re-derivable.

The product is the factory's first customer and its source of ground truth. The factory
is a byproduct of building it, not the other way round.

## The organizing principle

> **Agent autonomy tracks the availability of ground truth the agent did not author and
> cannot retrieve.**

This single rule generates the task model, the protected-path rules, the criterion
provenance ladder, and the autonomy gates. It is also a mechanical test applicable to
any new task: *what independent thing says this is right?* No answer means it is not
agent work yet.

## Non-goals

These are refusals, not deferrals. Each is a thing Alfred could plausibly do and will
not.

**Not a risk oracle.** Alfred does not tell anyone how dangerous a scenario is. Surrogate
safety metrics cannot deliver absolute risk: TTC and PET produce contradictory conclusions
on identical data, and no threshold standard exists. Risk classification ships only as a
configurable overlay with visible provenance, never as a fact.

**Not a threshold authority.** Threshold *selection* is a contested judgment with no
standard; only threshold *application* is checkable. Thresholds are declared, cited,
versioned configuration inputs — never agent-authored, never presented as facts.

**Not a coverage or scenario-generation tool.** That market is held: Applied Intuition
sells the aggregation-and-validation layer to most of the top OEMs, and Foretellix
authors the relevant standard. Alfred does not compete there.

**Not a platform product.** Alfred designs multi-product and builds single-product. No
second product until the first has paying users, and the platform itself is never sold.
The gate is revenue, not readiness — because "the platform is ready for a second product"
is a judgment the platform will always make in its own favour.

**Not a frontier-API product.** Alfred's agents run on local open-weights models
exclusively. This is a sovereignty choice with an accepted capability cost, not a claim
that local models are as capable.

**Not a general-purpose autonomous SaaS generator.** No production system today
autonomously produces enterprise SaaS. Alfred does not claim to be the first.

**Not certified for safety-case reliance.** Until and unless certification exists, every
pilot agreement disclaims fitness for safety-case reliance, and the disclaimer is
contractual, not a footnote.

## Kill and pivot criteria

Falsifiable, dated, and subject to the waiver-ADR discipline. Waiving one requires an
immutable ADR recording the gate, the threshold, the actual value, the reason, and the
condition that would reverse it.

| # | Criterion | Consequence if hit |
|---|---|---|
| K1 | No design-partner engagement by **2026-10-07** (Phase 1 exit) | **The AV wedge is parked; the factory continues.** Not a third re-argument — K1 and K5 both previously read "D30 is re-argued", D30 *was* re-argued on 2026-08-14, and a kill criterion whose consequence is to re-argue the decision just re-argued is a rescheduling, not a kill. **Parking means:** no further AV-specific investment (K2), the business-development ring-fence is lifted and those hours go to the factory, and the existing CriMe task class is retained as the factory's substrate. **A domain re-run is deliberately not triggered.** The arithmetic forbids it: a re-run decided 2026-10-21 has 71 days to the anchor, against the 57 days the AV track needed to get from a *verified oracle* to K1's own answer — with four research runs and ~1,450 fetched sources already behind it, and a contact list a new domain would not have. A pivot therefore arrives at the anchor holding exactly the evidence that K1 firing represents. Demand returns at **K6**, not before. |
| K2 | No signed LOI **and** no documented refusal reasons from three named buyer roles by **2026-10-07** | **AV-specific investment does not begin** — metric implementation beyond the Phase 1 class, the customer-run container, pilot work, and anything whose value depends on the AV wedge being real. **Factory phases 2–4 proceed regardless.** Phase 2 is the evidence store, the golden set and the failure taxonomy; none of it is product work, and all of it is what the 2026-12-31 anchor tests. Halting the factory on a demand signal would make the anchor unpassable by construction, which is what this row did before 2026-08-17. |
| K3 | Per-task merge rate below ~50% at Phase 1 exit (**2026-10-07**) after the bounded retry budget, **read as a Wilson 95% interval rather than a point estimate — the criterion fires when the interval's lower bound sits below 0.50** (at n=20 that means fewer than 15/20; at n=10, fewer than 9/10) | Narrow the task class. Never lower the bar, never add orchestration. |
| K4 | Factory wall-clock per merged task exceeds the measured human baseline by a stated factor, at Phase 2 exit (**2026-11-04**) | D35 (pure-local) is re-argued, with the frontier-API lane as the named alternative. |
| K5 | **FIRED 2026-08-13.** No instrument requires the attester to be independent of the simulation vendor: EU AI Act Art. 2(2) excludes ADS from substantive duties; EU 2022/1426 makes validation discretionary and document-based; NHTSA withdrew AV STEP (91 FR 38619); UK AV Act 2024 does not contain the word "independent". | The wedge has no forcing function. **D30 is re-argued before any Phase 2 investment.** What survives is a compliance-tooling product bought by OEMs, not attestation compelled by regulators. **DISCHARGED 2026-08-14** by the D30/D48 split: D30 retains the artifact shape, D48 carries the market position. A fired criterion whose consequence has been executed is not executed again. |
| K6 | No dated demand answer on the **live domain** when the **2026-12-31** anchor is reached — a named buyer role at three organisations, the artifact they would pay for in their own words, or documented refusal reasons | **Build halts until that answer exists.** Passing the anchor is a *factory* verdict and authorizes nothing beyond a decision. The business-development ring-fence returns at the anchor. Recorded because a factory-shaped anchor leaves demand untested at every date — precisely the R10 exposure the calendar was installed to prevent, which must be reassigned rather than allowed to lapse. |

**The largest unaddressed risk is K1/K2.** Nothing in four research runs and ~1,450
fetched sources established that a metric-reproduction correctness harness can be sold to
anyone. This plan asserts it. The demand gate exists to find out cheaply, before the
investment that would make the answer expensive.

## Company-level constraints

Ring-fenced weekly hours for business development from Phase 0, so it cannot lose every
prioritization contest to engineering. **The ring-fence is lifted if K1 fires**, because
parking the wedge closes the demand question until K6: those hours go to the factory, which
is what makes the anchor arithmetically reachable — `F` is the binding term in the capacity
ledger `5·n·m + F ≤ C` and it is the one term with no instrument. The ring-fence returns at
the anchor. Entity formation, a liability-capped pilot
agreement template, and an insurance quote all precede the first prospect-facing
conversation.
