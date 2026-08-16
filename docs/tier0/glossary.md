---
status:        frozen
owner:         human
enforcement:   review-cadence
evidence:      Terms are drawn from the architecture decisions and from the domain literature. Domain metric definitions follow Westhofen et al. (arXiv 2108.02403).
falsifies_if:  Two documents in the register use the same term for different things, or different terms for the same thing — the condition this glossary exists to prevent.
review_after:  Phase 2
---

# Glossary

Definitions are binding across the register. Where a term has a common looser meaning, the
Alfred meaning is the one that applies.

## Architecture

**Control plane** — Postgres. The only source of truth for work items, acceptance criteria,
protected paths, permissions and run history. Deterministic.

**Execution plane** — the isolated, disposable, untrusted environment where an agent runs.
Alfred-owned container. Emits a patch file; holds no credential.

**Evidence plane** — append-only storage written **only** by the harness, never by an agent:
artifacts, check results, traces, diffs, wall-clock, latency, verdicts.

**Harness** — the deterministic machinery that dispatches work, executes criteria, and writes
evidence. Distinct from the agent in process, permission and import graph.

**Claim** — structured output from an agent. Never a fact until the harness verifies it.

**Verdict** — a fact produced by `CriterionRunner`. Agent nodes are schema-forbidden from
writing verdict fields, and a CI lint enforces it because LangGraph raises only on *concurrent*
unreducered writes.

**Node / edge / state** — units of work, transitions between them, and the typed object
travelling the edges. One owning writer per state field; fan-in on a shared field requires an
explicit reducer or it is an error at graph-definition time.

**Refs travel, payloads do not** — edges carry typed scalars, IDs, verdicts and status.
Drafts, diffs, logs and traces live in the content-addressed artifact store.

**Port** — an interface behind which an external system sits (LLM provider, sandbox, VCS,
artifact store, dataset source). The premise that agents are replaceable workers is only true
if they sit behind one.

## Agents and autonomy

**Capability** — `(input contract, output contract, tools, permissions, criteria, escalation)`.
The unit an agent is scoped to. Never a job title.

**Fingerprint** — the full identity a measurement describes: capability, weights, quantization
artifact hash, inference runtime and version, server version, orchestrator commit, harness
identity, runtime image digest, prompt version, tool-description hash, context strategy version,
resolved lockfile hash, criterion-set version and expiry, and budget.

**Autonomy grant** — permission for a task-class to run unattended. Reads *"X% merge, Y
wall-clock per success, on fingerprint Z."* Suspended by any fingerprint change; expires.

**Criterion** — *(assertion + interface signature + threshold provenance)*. The interface
signature component exists because valid solutions otherwise fail as false negatives against
under-determined executable criteria.

**Visible criterion** — tests a metric in isolation. The agent sees it and may retry against it.

**Held-out criterion** — composes operations end-to-end across scenario families. The agent
never sees it, and it is materialized at verdict time from a separate DB role.

**Merge rate** — measured **per task after a bounded retry budget**, never per attempt. Free
inference makes per-attempt rates meaningless.

**Defect-escape rate** — defects reaching merge despite passing every gate.

**Null-agent floor test** — a run taking no actions. Its score is the harness's floor. Above
zero means the harness is measuring itself.

**Golden set** — stratified accumulating task set pinned to **parent commits**, including
successes, failures, near-misses and escalations. At n≈20 it supports a failure taxonomy and
~25pp regression detection; resolving ~5pp needs roughly 150–400 tasks.

**Waiver ADR** — the immutable record required to override a stage gate: gate, threshold, actual
value, reason, and the condition that would reverse it.

## Domain

**Surrogate safety metric** — a computable proxy for collision risk derived from trajectories.
Alfred computes and audits these; it does not treat them as absolute risk.

**TTC** — time to collision. Time until collision if current kinematics persist.

**THW** — time headway. Time for the ego to reach the lead vehicle's current position at present
speed.

**PET** — post-encroachment time. Gap between one road user leaving a conflict area and the next
entering it.

**DRAC** — deceleration rate to avoid a crash.

**MSD** — minimum safe distance under a constant-deceleration model, including reaction distance.

**TET / TIT** — time exposed and time integrated, relative to a TTC threshold.

**TTB / TTK / TTS / TTR / TTZ / WTTC / WTTR / TTCE / ET** — the remaining time-domain measures
carrying shipped reference assertions. See the Metric Catalog for formulas, units and citations.

**Validity envelope** — the stated conditions under which a metric's output is meaningful.
Published per metric in its model card.

**Result stamp** — metric version, code commit, assumption set, input hash and tolerance, attached
to every emitted result. Cannot be retrofitted.

**Advisory** — a versioned notice naming affected result versions and date ranges after a defect is
found. The recall mechanism for a product that may not hold customer data.

**Oracle** — an external implementation treated as ground truth for a reimplementation.
CommonRoad-CriMe is Alfred's Phase 0 oracle; its shipped values are its own **self-consistency**
regression tests, not independently published reference values, and documentation must say so.

## Phases

**Phase −2** licence verification · **Phase −1** local-model benchmark gate · **Phase 0** hand-built
product skeleton · **Phase 0.5** data-licensing gate · **Phase 0.75** demand gate · **Phase 1** one
agent, one task, human gate · **Phase 2** evidence and measurement · **Phase 3** throughput ·
**Phase 4** earned autonomy · **Phase 5** planning · **Phase 6** specialization · **Phase 7**
streaming and operations autonomy.
