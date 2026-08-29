---
status:        provisional
owner:         human
enforcement:   review-cadence
evidence:      Risks R1-R4 and R7-R9 are drawn from measured external results or from this project's own prior failure. R5, R6, R10 and R11 are structural exposures accepted deliberately, each with a named revisit trigger.
falsifies_if:  A material incident occurs whose cause appears nowhere in this register — meaning the register is enumerating the wrong hazards.
review_after:  Phase 1
---

# Risk Register

Each entry carries a trigger that forces revisit. A risk without a trigger is an
observation, not a control.

## R1 — Nobody buys it

**The largest risk in the project.** Four research runs and ~1,450 fetched sources
established nothing about whether a metric-reproduction correctness harness can be sold.
The plan asserts it; no evidence supports it.

- **Exposure:** the entire commercial thesis.
- **Control:** Phase 0.75 demand gate. Requires zero code and zero data licence, so it can
  run in parallel with everything.
- **Trigger:** no design-partner engagement by **2026-10-07** → the AV wedge is parked and the factory continues (K1). Demand is retested at the post-anchor gate (K6), not by a domain re-run.

## R2 — Single machine is a single point of total loss

Hardware loss and total evidence loss are currently the same event. Append-only is an
integrity property against the agent; it does nothing against SSD failure on a 24/7 consumer
machine, kernel-panic corruption, or a bad migration.

- **Control:** continuous WAL archiving plus periodic base backups to an **off-machine**
  target; a **restore drill** as an executable check; evidence rows **hash-chained** with the
  chain head anchored off-machine daily. Without the chain, an audit-layer product's own audit
  log is silently rewritable by anyone with one login.
- **Trigger:** first paying customer or first autonomy grant → move the control plane off the
  inference host.

## R3 — Plausible-but-wrong numbers do not announce themselves

A wrong risk metric does not throw, spike latency, or fail a healthcheck. Every observability
mechanism detects a different class of failure, and none detects this one.

- **Control:** result stamping (metric version, commit, assumption set, input hash, tolerance)
  on every emitted result; versioned advisories naming affected versions and date ranges;
  published validity envelopes per metric. **Stamping cannot be retrofitted** — results computed
  before it exists are permanently unrecallable.
- **Trigger:** the first correctness advisory issued to any customer.

## R4 — Held-out criteria leak

A8's defence assumes reference values the agent cannot retrieve. Published values are plausibly
in training data, and no network policy removes that.

- **Control:** held-out values in a **separate table behind a separate DB role**, materialized by
  `CriterionRunner` at verdict time only — enforced by SQL grant, never by channel visibility.
  LangGraph `private` schemas do not hide channels from stream, and `output_keys` is caller-side.
  Held-out failure diagnosis emits only a pass/fail class label into task context, never the trace.
  Held-out perturbations on resampled slices whose answers were never published.
- **Trigger:** any held-out pass rate that matches visible pass rate across a full golden set —
  the signature of a leak.

## R5 — Budget ceilings are advisory (accepted)

Agents create subtasks with fresh budget allocations, so an agent approaching its cap can split
to obtain more. Under local inference the currency is wall-clock and hack amplification rather
than money.

- **Accepted for:** throughput, and decomposition that scales without human involvement.
- **Control:** hard ceiling on lane wall-clock per task tree and on tasks dispatched per day.
- **Trigger:** first observed decomposition tree exceeding expected spend by 5×.

## R6 — Pure-local capability ceiling (accepted)

Open-weights models on 128 GB trail frontier capability, and private commercial codebases score
far below public benchmarks (15–18% vs 41.8–43.6%, a 2.66× within-model drop). Alfred's codebase
is private and commercial by construction, so the lower figure is the relevant prior.

- **Accepted for:** sovereignty, zero marginal token cost, and the structural win that **local
  weights never get deprecated** — fingerprints stay valid indefinitely.
- **Control:** D36 narrows the task class rather than lowering the bar. gpt-oss-120b retained on
  disk as a fallback lane.
- **Trigger:** factory wall-clock per merged task exceeds the measured human baseline by a stated
  factor (K4) → D35 re-argued with the frontier-API lane as the named alternative.

## R7 — Prompt injection via everything the agent reads

Issue text, dependency READMEs, error messages and web content are all attacker-reachable and all
enter agent context. Zero-width and bidi-encoded instructions have been planted in `CLAUDE.md` and
`.cursorrules` files in pull requests against major agent repositories; GitHub flags bidi but not
zero-width.

- **Control:** deterministic pre-review gate rejecting non-ASCII control, zero-width or bidi
  characters outside declared string literals, with particular force on agent-instruction files;
  hash-locked dependency closure; scans for `.pth`, `sitecustomize` and instruction-file additions.
  CI runs before any human sees a pull request, so review is not the first gate.
- **Trigger:** first detected injection attempt, however unsuccessful.

## R8 — The harness measures itself

A ~7-line `conftest.py` has forced 100% resolve on all 500 SWE-bench Verified instances without
touching a single test file.

- **Control:** `CriterionRunner` runs **outside** the agent's tree and materializes the test
  environment itself from trusted provenance, ignoring everything outside declared source paths;
  a **null-agent floor test** — a run taking no actions — asserts the harness's floor permanently;
  a **seeded-defect suite** of deliberately wrong implementations at known deltas must red.
- **Trigger:** null-agent floor score above zero.

## R9 — Review capacity, not compute, is the bottleneck

One operator. Human minutes per task (authorship, review, escalation) × projected tasks/day plus
fixed weekly obligations is a real ceiling, and throughput work makes it worse.

- **Control:** capacity ledger with "projected human-minutes ≤ capacity" as an executable stage
  gate from Phase 3; dispatch backpressure when open-PR or pending-escalation count exceeds a
  ceiling; explicit drain mode for operator absence.
- **Trigger:** review-backlog depth exceeding the configured ceiling twice in one month.

## R10 — No forcing function (managed since 2026-08-12)

Originally recorded as "no calendar and no runway". Step 0 supplied both, and in doing so
changed what the risk is.

**Runway is not the constraint: the project is not capital-constrained.** Capacity is
20+ hrs/week and the cash line is under $5k. That removes the pressure the plan's gate
discipline was designed against — and replaces it with the opposite failure. A project
that cannot run out of money can run indefinitely without ever testing whether anyone
wants what it builds, executing every phase flawlessly and never learning the one thing
that would stop it. That is the prior attempt's failure one layer up, with better
instrumentation.

**The calendar is therefore the only forcing function, and it is treated as hard.**
Anchor: **2026-12-31**, roughly 20 weeks from Step 0.

| Milestone | Date | What it gates |
|---|---|---|
| Phase 0 exit | **2026-09-09** | no platform code before it |
| Company formation (entity, liability-capped pilot template, insurance quote) | **2026-09-09** | precedes the first prospect conversation |
| Phase 0.75 demand gate exit | **2026-10-07** | Phase 2 investment |
| Phase 1 exit | **2026-10-07** | K1 and K3 resolve here |
| Phase 2 exit | **2026-11-04** | K4 resolves here |
| Anchor | **2026-12-31** | the **factory** verdict: one task class is granted unattended operation, or defensibly refused it, from measurement |

**What the anchor tests, settled 2026-08-17.** It tests the factory, not demand. The AV
domain is substitutable and the factory is not, and under a demand reading the anchor carried
no information: K1 resolves on 2026-10-07, no pivot can produce a K1-equivalent demand answer
in the 71 days that remain, so the anchor's verdict would already be fixed twelve weeks
earlier. An anchor whose answer is determined by an earlier gate is a restatement, not a
forcing function.

**Pass condition.** The `AutonomyGate` reaches a decision on at least one task class, from
measurement rather than category, on a recorded fingerprint — reading per-task merge rate as
a Wilson interval, held-out pass rate stratified by provenance tier, and defect-escape rate
against a denominator of merged tasks under observation for a stated window. **A refusal
passes.** The thesis is *shrinking* human gates; a mechanism producing a defensible "no
grant, and here is the evidence" has demonstrated the thing nobody else has. Silence fails.

**Stated degradation, in D49's form.** If `n` at the anchor gives a Wilson interval too wide
to decide, the anchor is met by reporting `n`, the interval, the strata, and the `n` that
would settle it — never by widening the interval or lowering the bar. Written now because the
arithmetic already says a fully powered grant is out of reach: 8 weeks from Phase 2 exit at
2–3 dispatched tasks/day is 80–120 dispatched and roughly 40–60 merged, against D29's 150–400
for fine-grained comparison. An anchor implying a powered grant would be unpassable as
written — the same defect as the superseded Phase 1 exit criterion, one phase later.

**Open input, and the anchor is not evaluable without it:** the defect-escape *observation
window*. `data-architecture.md` correctly requires the gate to read a denominator of "merged
tasks under observation for a stated window", and states that an empty escape table is not a
zero rate — but no document states the window. Owed by the operator before Phase 2 exit.

- **Control:** dated milestones above; K1–K6 carry dates rather than phase names; a
  missed milestone requires a waiver ADR under D28, and the waiver count is the health
  metric that makes drift visible.
- **Trigger:** any milestone missed by more than two weeks without a waiver ADR, or the
  anchor arriving with K1 unresolved.

**Amended 2026-08-17.** The anchor was carrying two jobs — testing the factory and testing
demand — and now carries one. Making it factory-shaped is correct, because the factory is
what cannot be substituted, but it leaves demand with no dated test once K1 parks the wedge.
That is this risk's exact failure mode: a project that cannot run out of money running
indefinitely without learning whether anyone wants what it builds. The job is reassigned to
**K6** rather than deleted. If K6 is ever waived, this risk is live again and the waiver ADR
must say so.

## R11 — Documentation as a corruption vector

Agents read documentation as context, so a stale document is a corrupted instruction propagating
into every task that reads it. Three of 49 studied agent skills *degraded* performance by up to
−10% through version-mismatched guidance.

- **Control:** header contract with declared evidence basis and required falsification condition;
  stubs by default; CI doc lint; Tier 0 permanently human-authored.
- **Trigger:** any document found stale during a phase review whose `review_after` had not yet
  elapsed — meaning the review cadence itself is mis-set.

## R12 — The data licence is unaffordable, so the wedge must not require one

The cash line is under $5k. Entity formation, a liability-capped pilot template and an
insurance quote consume most of it; a **commercial dataset licence does not fit**. Phase
0.5 as written — "obtain a commercial data licence before any pilot" — cannot complete
as specified.

This is survivable and possibly clarifying. CommonRoad is BSD-3 and verified, Zenseact is
CC BY-SA, and the plan already favours a customer-deployed container for independent
reasons. A buyer who says "demonstrate it on our data" is answered by the container, not
by a licence Alfred holds — which resolves Q18 toward container-first on a second,
independent argument.

- **Control:** Phase 0.5 is restated as *confirm the open-data path satisfies the demand
  gate, or the wedge changes*. The permanent regression path stays on BSD-3 CommonRoad.
- **Trigger:** any Phase 0.75 conversation in which the buyer's stated blocker is that
  results are not demonstrated on licensed commercial data. Two such answers falsify the
  open-data path and force either capital or a different wedge.
