---
status:        frozen
owner:         human
enforcement:   review-cadence
evidence:      Derived from four adversarial research runs (~63 agents, ~1,450 fetched sources) and from the documented failure of a prior attempt at this system. Each principle names the evidence or the failure it answers.
falsifies_if:  A principle is repeatedly waived under D28's ADR discipline — three waivers against the same principle means the principle is wrong, not the situations.
review_after:  Phase 2
---

# Operating Principles

Nine principles. Each exists because something specific went wrong, or would.

## 1. The harness produces facts; the agent produces claims

Agent output is a *claim*. The harness executes checks on a clean checkout and writes
the *fact* to an append-only evidence store. If the agent self-reports results, the
entire validation system is theatre.

The load-bearing consequence: **the evidence plane is never written by the agent.** That
single rule drives more of the architecture than any other decision here.

## 2. A task is only schedulable if it carries an executable acceptance criterion

Prose-only tasks are unschedulable and escalate to a human. This is the mechanism behind
every credible agent coding result; remove it and measured performance collapses.

## 3. Agents may improve the factory, never the inspector

Permanently protected: `CriterionRunner`, `EvidenceStore`, `PolicyEngine`, `AutonomyGate`,
protected-path configuration, sandbox specification, fingerprint tracker, and the
evidence/verdict/policy migrations.

This is documented, not hypothesized. CVE-2025-53773 is the exploit form: an agent wrote
`"chat.tools.autoApprove": true` into a settings file — it disabled its own approval gate
because the gate lived in a file it could write. The pressure is ordinary optimization,
not malice: "make the criterion runner faster" that quietly loosens a tolerance looks like
success at every layer of observation available.

Enforcement is **physical** — separate process, separate DB role with column-level grants,
no import path from any agent module. Never a runtime field-name check.

## 4. Agents are capability-scoped, never role-scoped

An agent is `(input contract, output contract, tools, permissions, criteria, escalation)`
— never a job title. A role has no input/output contract, therefore no golden tasks and no
measurable merge rate, which structurally breaks the autonomy mechanism.

Every agent must also justify itself against a deterministic alternative: open input space
and checkable output, or it is a node.

## 5. Structural triggers, never agent self-assessment

Escalation fires on iteration cap, budget exhaustion, criterion red after N attempts,
protected-path attempt, tool unavailability, turn count, token spend, or wall-clock. The
agent cannot write `blocked` or `complete`.

Agents almost never stop. The default behaviour under an unsatisfiable task is a plausible
partial solution, not an admission — so escalation cannot depend on the agent recognizing
it is stuck, since that is precisely the judgment the failure compromises. An agent that
can declare itself blocked can also declare itself done.

## 6. Measure the system, not the model

Every measurement describes a specific system. Autonomy grants are keyed to a **fingerprint**
covering capability, weights, quantization artifact, inference runtime, server, orchestrator
commit, harness identity, prompt version, tool descriptions, context strategy, lockfile,
criterion-set version and expiry, and budget. Any change suspends the grant until re-measured.

Identical weights have produced opposite tool-calling outcomes on different servers, and
harness identity alone moves scores by more than the spread between leading submissions.

## 7. Calibrate on held-out, never on visible

Graduation calibrates on **held-out** pass rate only. Calibrating on visible-criterion pass
rate would certify exactly the agents that reward-hack hardest, since hacking agents saturate
the visible suite by definition.

Held-out criteria compose operations end-to-end. Visible criteria test them in isolation. The
gap between the two is where honest agents, honest criteria and honest harnesses still produce
wrong code — a 43–48pp effect with no exploit involved.

## 8. Narrow the scope; never lower the bar

When a gate is not met, the response is to constrain the task class, not to weaken the
threshold. Free local inference turns retry-until-green into a search over solutions that pass
visible checks — so acceptance requires a held-out pass the agent never sees, and merge rate is
measured **per task after a bounded retry budget**, not per attempt.

## 9. Gates are executable; overriding one is expensive and permanent

Every forbidden-advancement condition is a promise to a future self who will be under pressure
and will want to proceed. A gate that can be waived silently is a note, not a gate — but an
unwaivable gate gets bypassed entirely rather than adjusted honestly.

So: overriding a gate requires an **immutable waiver ADR** recording the gate, threshold, actual
value, reason, and the condition that would reverse it. Waiver count is itself a health metric.

This is the only control in the architecture aimed at the human rather than the agents. It
addresses the failure that actually occurred last time.
