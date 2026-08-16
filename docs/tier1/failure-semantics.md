---
status:        frozen
owner:         executable
enforcement:   ci-gate
evidence:      Two documented cases of controls failing open silently: an eval sandbox left with live internet access under a deny-by-default configuration, and an SDK that treated an empty settings-source list as omitted and loaded user configuration anyway. Both failed without signalling.
falsifies_if:  A run reaches a verdict while any control that gates it could not be shown to have executed, or a harness fault is recorded as an agent failure.
review_after:  Phase 1
---

# Failure Semantics and Error Handling

What the system does when something does not work. The rules here are load-bearing
because the architecture's central claim — that the harness produces facts and the agent
produces claims — survives only if a harness that could not run says so instead of
returning something verdict-shaped.

## The distinction everything rests on

**A check that failed and a check that did not run are different outcomes.** Collapsing
them is the single most dangerous error-handling defect available here, and it is the
default behaviour of almost every test runner and CI system, which report a crash and a
failure through the same non-zero exit path.

Verdicts are therefore three-valued:

| Verdict | Meaning | Merge | Counted in merge rate |
|---|---|---|---|
| `pass` | every criterion executed and passed | eligible | numerator and denominator |
| `fail` | every criterion executed; at least one failed | blocked | denominator only |
| `indeterminate` | at least one criterion did not execute to completion | blocked | **neither** |

`indeterminate` is not a capability signal — nothing was learned about the agent — so it
is excluded from merge rate entirely and tracked separately as a **harness health
metric**. Folding harness flakiness into either side of the ratio corrupts the only
number the autonomy gates read.

An `indeterminate` verdict is never retried into a `pass` without both outcomes recorded
in the evidence chain.

## Fail-closed by default

Anything that cannot demonstrate its control executed **aborts the run**. It does not
proceed with the control disabled, and it does not log a warning and continue.

| Condition | Disposition |
|---|---|
| Sandbox will not provision | run does not start |
| Egress canary does not fire (non-allowlisted connection succeeded) | run does not start |
| Egress canary itself errors | run does not start — an unproven control is a failed control |
| Held-out schema unreachable at verdict time | `indeterminate`; never a `pass` on visible criteria alone |
| `CriterionRunner` crashes mid-execution | `indeterminate` |
| Evidence store unwritable | run halts; no work proceeds unrecorded |
| Hash-chain head cannot be read | run halts; the chain must not fork |
| Artifact store write fails | the referencing evidence row is not written |
| Model server unreachable or times out | run marked `indeterminate`, requeued once |
| Loaded context length differs from the fingerprint | run does not start — the lane silently reconfigured |
| Lane parallel slot count differs from the fingerprint | run does not start — slots above 1 disable KV reuse entirely |
| Patch validator cannot parse the diff | patch rejected — an unparseable diff is not a safe diff |
| Protected-path check errors | patch rejected |
| Policy configuration fails to load | nothing dispatches |
| Oracle-absence probe does not run, errors, or cannot enumerate the interpreter set | run does not start — an unproven control is a failed control |
| Oracle-absence probe finds a denied module importable, in the agent container or the criterion environment | run does not start; environment rebuilt; **never retried** as-is |
| Oracle denylist fails to load, or its version differs from the fingerprint | run does not start |
| End-of-run oracle-absence re-assertion finds what boot did not | claim rejected, `indeterminate`; the patch is not offered for merge |
| Executor's durable event count below the count the adaptor observed | `indeterminate` — the read log is a subset of unknown size |
| A condensation or summarization event present in the executor's stream | `indeterminate` — a summary sat upstream of the verdict (I16) |
| Executor's own frontend reachable, or an approval-class event present in its stream | run does not start; a stream-side hit rejects the claim |
| Loaded executor configuration hash differs from the harness-supplied configuration | run does not start |
| Mount set inside the container differs from the dispatch spec | run does not start |
| Runtime image digest differs from the fingerprint | run does not start |
| Any containment assertion recorded as `not_executed` | run does not start; `not_executed` is never read as passed |
| `Worker` returns a claim carrying a verdict-vocabulary field | contract violation; `indeterminate`; CI lint failure |
| Off-machine backup target unreachable | alarm; dispatch continues, escalation raised |

The single fail-open entry is backup unreachability, and it is deliberate: refusing to
work because an off-machine target is down trades a durability risk for a total outage.
It is the exception, it is named, and it escalates.

## Error taxonomy

Five classes. Every raised error is assigned one; an unclassified error is itself a
contract violation and halts the run.

| Class | Example | Owner | Disposition |
|---|---|---|---|
| **Infrastructure** | model server down, DB connection lost, disk full | harness | `indeterminate`, bounded requeue |
| **Policy violation** | protected-path write attempt, egress to a non-allowlisted host, held-out `SELECT` from the agent role | agent | terminate run, **never retried**, recorded as evidence of an attempt |
| **Criterion failure** | assertion failed, tolerance exceeded, type check red | agent | `fail`, retry against visible criteria within budget |
| **Exhaustion** | turn cap, wall-clock cap, iteration cap, no monotone progress | agent | escalate with the structured attempt bundle |
| **Contract violation** | schema-invalid tool call, agent node returned a verdict field, malformed patch | harness or agent, determined by origin | terminate run; if harness-origin, `indeterminate` |

**A tool call arriving in the content channel is a serving defect, not an agent failure.**
Measured on the selected lane: 3–5 calls per run — roughly 15–20% of all tool calls, and
disproportionately the *final* one — are rendered as prose instead of through the
tool-call channel, in at least two syntaxes (`name` followed by a JSON object, and
`name(value)` positional form). The JSON is valid; the channel is wrong.

The harness therefore parses tool calls from the content channel and counts them as a
serving-quality metric. Recovery is restricted to unambiguous cases — a named tool with a
parseable object, or a single-parameter tool called positionally — because anything wider
is guessing at intent, which is how a harness starts inventing agent actions.

Without this, the effect is not a visible error: the agent appears to stall with no
message. In the probe that established it, chain completion read **20%** without the
salvage and **100%** with it, on identical model behaviour.

A policy violation is never retried. Retrying it is indistinguishable from letting the
agent search for a formulation of the same action that the check does not catch.

## Timeouts

Every external call carries an explicit timeout. No unbounded wait exists anywhere in the
control plane.

Timeouts are set from **measured** distributions, not from library defaults. Prefill on
this machine costs roughly 45 s at a 28k context before a single token is generated, so
any default in the 30–60 s range would abort healthy work and be diagnosed as model
failure.

**A request timeout must not become a lane restart.** The inference lane is a long-lived
daemon whose in-process KV cache is worth 32–128× on prefill; a supervisor that restarts
it to recover from one slow request silently discards that saving on every subsequent
task. Lane restart is an operator action, or a response to a liveness failure, never to a
single timeout.

**The lane can also reconfigure itself.** The serving stack auto-unloads an idle model
and JIT-reloads it on the next request at its *default* context length, not the length it
was loaded with. Observed directly: a model loaded at 262,144 was found serving at 28,672
after an idle gap, and the probes that ran against it returned 0/10 on a tool-calling
suite the same model had just scored 10/10 on. Nothing errored, and the result read as a
capability regression.

So the loaded context length is asserted against the fingerprint at run start, not merely
recorded from it. A fingerprint field the server can change without notice is not a
fingerprint unless something checks it.

**The parallel slot count is the second field of that kind, and it is worse.** Cross-request
KV reuse is off entirely at more than one slot: measured 140.7× at `--parallel 1` and
**1.0×** at the default of 4, on the same model, same context, same prompt. Nothing in the
response distinguishes them — the same tokens come back, only slower — so a lane running
without reuse looks exactly like a lane running with it, and only a wall-clock comparison
against a prefix that should have been warm reveals the difference. Slot count is therefore
asserted, not recorded, and concurrency and prefix reuse are mutually exclusive on this
serving stack.

## Retry and idempotency

- Only idempotent operations retry. Every mutating operation carries an idempotency key,
  so a retry that partially succeeded cannot double-apply.
- Retries are bounded, and every attempt is recorded — attempt count is a task-difficulty
  signal, and turn count and token spend are among the strongest available failure
  predictors.
- **Retries select against visible criteria only.** Held-out criteria are evaluated once,
  at acceptance. A retry loop that could see held-out results would be a search process
  over the held-out set.
- Infrastructure retries preserve the fingerprint. If any fingerprint field would change
  between attempts — a server restart, a runtime upgrade — the retry is a new run against
  a new fingerprint, not a continuation.

## Ordering and atomicity

The **evidence write is the commit point.** An action is not considered to have happened
until its evidence row is appended, and side effects that cannot be undone are ordered
after that append.

The hash chain has exactly one writer and is written serially. A concurrent chain writer
would produce a fork, and a forked audit log in an audit product is the failure the whole
architecture exists to prevent.

Evidence migrations are additive-only. A migration that would `ALTER` or `UPDATE` an
existing evidence row fails CI rather than running and being reverted.

## Crash recovery

The checkpointer is execution memory, never the system of record. On restart:

- A run interrupted **before** verdict computation is recomputed from the task, not
  resumed from partial agent state. Resumption would carry forward state whose provenance
  cannot be reconstructed.
- A run interrupted **during** verdict computation is `indeterminate` and recomputed in
  full. A partially-executed criterion set has no meaning.
- Completed evidence rows are never rewritten on recovery. A duplicate attempt appends a
  new row referencing the first.
- An orchestrator restart that changes the orchestrator's commit SHA is an epoch
  boundary: in-flight runs are discarded rather than resumed across it.

## Errors as an attack surface

Error text from dependencies, tools and datasets is attacker-reachable and enters agent
context. It is treated as untrusted data on the same footing as issue text.

- Third-party error text injected into agent context passes the same deterministic scan
  as any diff — control, zero-width and bidi characters rejected — and is truncated to a
  declared length.
- Harness-authored errors surfaced to the agent are a stable code plus a
  harness-authored message. The agent is told *what class of thing went wrong*, never
  handed a verbatim string from an untrusted source as an instruction-shaped payload.
- Full raw error text is recorded in the evidence store regardless. Sanitization applies
  to what enters context, never to what is recorded.
- **Held-out failures emit a pass/fail class label only.** The trace, the failing input
  and the expected value never enter task context — a diagnostic channel that leaks
  held-out content is a channel that dissolves the boundary.

## Deliberately absent

- **No automatic remediation.** Every fix is a normal task with a criterion and a blast
  radius. A privileged repair path is an unaudited write path.
- **No catch-all exception handler** that logs and continues. An unclassified error halts.
- **No degraded mode** in which a control is skipped to keep throughput. The two
  documented instances of security controls failing in practice both failed by continuing
  without the control and without signalling.

## Enforcement

CI asserts: every port method declares its timeout; no bare `except:` or
`except Exception: pass` in `harness/`; every raised error type maps to a taxonomy class;
evidence migrations are additive-only; no verdict field is assigned outside the verdict
module. The seeded-defect suite includes fault injection — killed criterion runner,
unreachable held-out schema, unwritable evidence store — and asserts each produces
`indeterminate` rather than `pass`.
