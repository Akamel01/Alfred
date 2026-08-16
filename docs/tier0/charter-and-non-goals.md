---
status:        provisional
owner:         human
enforcement:   review-cadence
evidence:      none — written pre-Phase-0. The engineering thesis rests on four adversarial research runs; the commercial thesis rests on nothing yet and is the subject of the Phase 0.75 demand gate.
falsifies_if:  No named buyer role at three AV organizations will describe, in their own words, an artifact they would pay for — or no design-partner engagement exists by the end of Phase 1. Either observation falsifies the wedge and forces D30 to be re-argued.
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
| K1 | No design-partner engagement by **2026-10-07** (Phase 1 exit) | The wedge is falsified. D30 is re-argued before any Phase 2 investment. |
| K2 | No signed LOI **and** no documented refusal reasons from three named buyer roles by **2026-10-07** | Phase 2 investment does not begin. |
| K3 | Per-task merge rate below ~50% at Phase 1 exit (**2026-10-07**), after the bounded retry budget | Narrow the task class. Never lower the bar, never add orchestration. |
| K4 | Factory wall-clock per merged task exceeds the measured human baseline by a stated factor, at Phase 2 exit (**2026-11-04**) | D35 (pure-local) is re-argued, with the frontier-API lane as the named alternative. |
| K5 | **FIRED 2026-08-13.** No instrument requires the attester to be independent of the simulation vendor: EU AI Act Art. 2(2) excludes ADS from substantive duties; EU 2022/1426 makes validation discretionary and document-based; NHTSA withdrew AV STEP (91 FR 38619); UK AV Act 2024 does not contain the word "independent". | The wedge has no forcing function. **D30 is re-argued before any Phase 2 investment.** What survives is a compliance-tooling product bought by OEMs, not attestation compelled by regulators. |

**The largest unaddressed risk is K1/K2.** Nothing in four research runs and ~1,450
fetched sources established that a metric-reproduction correctness harness can be sold to
anyone. This plan asserts it. The demand gate exists to find out cheaply, before the
investment that would make the answer expensive.

## Company-level constraints

Ring-fenced weekly hours for business development from Phase 0, so it cannot lose every
prioritization contest to engineering. Entity formation, a liability-capped pilot
agreement template, and an insurance quote all precede the first prospect-facing
conversation.
