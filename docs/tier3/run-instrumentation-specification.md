---
status:        provisional
owner:         executable
enforcement:   schema
evidence:      The agentic probe (4 seeds × 5 tasks, 20/20; mean 4.1 turns, 4.75 tool calls) fixes the shape of a short run and supplies the repeat/recovery ambiguity this schema disambiguates; the content-channel defect (15–20% of calls, chain completion reading 20% or 100% on identical model behaviour) and the silent lane reload to defaultContextLength are both measured on the selected lane. The long-horizon and goal-seeking fields rest on nothing observed — Phase 1 is their first measurement, which is why they must be emitted before it starts.
falsifies_if:  A Phase 1 run completes and a question in "What this must answer" cannot be answered from the emitted records without re-running anything; or the instrument-verification suite passes against an instrument that a deliberately injected defect does not move; or a run record stream is chained without having passed the validator specified under Enforcement, which as of 2026-08-15 is specified and unwritten.
review_after:  Phase 1
---

# Run Instrumentation Specification

What every Phase 1 run emits, field by field, so that long-horizon execution and goal
seeking become measurable **after the fact**.

Two capability axes were audited and left unmeasured: item 3, long-horizon execution, and
item 4, goal seeking. The decision was that Phase 1 *is* that measurement. That decision
is only valid if the emission exists first. Instrumentation added afterwards measures
nothing about the runs already completed, and Phase 1 runs are the scarce artifact — 20
of them, three weeks, against a class enumerated in advance. There is no second pass.

This document is the contract between the harness and that measurement. It specifies
records, not dashboards. The Observability Standard covers how they are viewed.

## What this must answer

Phase 1 exits on a written failure taxonomy *derived from observed failures*. Each
question below must be answerable from the emitted records alone, without re-running a
task and without reading agent prose.

| # | Question | Axis |
|---|---|---|
| Q1 | How deep did chains actually go — turns and tool calls per attempt, distribution not mean? | long-horizon |
| Q2 | Where did wall-clock go, per merged task and per discarded attempt? | long-horizon |
| Q3 | Which tool failures were recovered from, by error class, and which ended the attempt? | long-horizon |
| Q4 | Did the run make monotone progress, stall, or regress — and when? | goal seeking |
| Q5 | How much of the trajectory was repeated work rather than new work? | goal seeking |
| Q6 | How often did stated intent and emitted action diverge? | goal seeking |
| Q7 | What caused each escalation, and what else was simultaneously true? | both |
| Q8 | Did the run stop before the required work occurred? | goal seeking |

Q1–Q3 are counting problems and are cheap. Q4–Q8 are the ones that need a definition
before they need code, because each of them is a judgment unless it is pinned to a
mechanically decidable rule. The rules are in this document; the point of writing it
before Phase 1 is that a rule chosen after seeing the data is a rule chosen to flatter it.

## Units, and the one that keeps being wrong

- **Task** — one work item, one criterion.
- **Attempt** — one dispatch of the agent against that task. A task has one or more
  attempts under its bounded retry budget.
- **Turn** — one model round trip within an attempt.
- **Tool call** — one invocation, whichever channel it arrived on.

**Merge rate is per task after the retry budget. Everything else is per attempt.** Turn
count and token spend are among the strongest available failure predictors — Spearman
ρ ≈ −0.67 and −0.73 against score — and both are agent-unwriteable, which is exactly what
makes them worth having. A predictor summed over a task's attempts is a different variable
from the same predictor on an attempt, and mixing them destroys the correlation. Both
levels are emitted; neither is derived from the other by the consumer's guesswork.

## Common envelope

Every record is a JSON object carrying these fields, appended to the run record stream in
emission order, one record per line. The stream is evidence: append-only (I2), written
only by the harness, hashed over ACS-1 into the chain (ADR-0003) with `record_type` as the
domain separator.

| Field | Type | Notes |
|---|---|---|
| `record_type` | enum | `attempt_start` · `phase_start` · `turn` · `tool_call` · `progress` · `phase_end` · `escalation` · `attempt_end` · `task_end` · `operator_action` |
| `schema_version` | int | I6. This document is version 1. |
| `event_id` | uuid7 | I4, typed distinctly. |
| `org_id`, `project_id` | uuid7 | I1. Present with one tenant. |
| `task_id`, `attempt_id` | uuid7 | `attempt_id` null on `task_end`, and on an `operator_action` that is about a task rather than an attempt. |
| `trace_id`, `span_id` | str | OpenTelemetry semantics, I8. |
| `caused_by` | uuid7 \| null | The `event_id` this record is a consequence of (I10). Null only on `attempt_start`. |
| `actor_kind` | enum | `harness` · `operator`. Closed set today. Every record states who wrote it rather than leaving it to be inferred from `record_type`. |
| `actor_id` | str | Constant on a single-operator machine, and present anyway: adding it later changes the digest of every prior record with no marker distinguishing old shape from new. |
| `emitted_at` | RFC 3339 UTC | Human-facing timestamp. Never used for durations. |
| `monotonic_ns` | int | Monotonic-clock reading. **All durations are computed from this field**, because a wall clock that steps during a four-minute prefill produces a negative duration and a plausible-looking one is worse. |

**`monotonic_ns` is differenced only between records sharing an `actor_kind`.** The reading
is system-wide since boot on this platform, so two processes agree — until a reboot, which
nothing in the stream marks. Harness durations all sit inside one attempt and one process,
so the restriction costs nothing there. An interval spanning the harness and the operator —
dispatch to approval — is measured by the operator surface's own `timing` object, never by
subtracting a harness record's reading from an operator record's.

Durations are integers in milliseconds unless named `_ns`. Token counts are integers.
Hashes are lowercase hex sha256. Artifact references are hashes, never paths (I3).

## `attempt_start`

| Field | Type | Notes |
|---|---|---|
| `attempt_index` | int | 0-based within the task. |
| `fingerprint_sha256` | str | The full D19/D40 identity this measurement describes. |
| `loaded_context_length` | int | **Asserted against the fingerprint, not read from it.** The lane auto-unloads when idle and JIT-reloads at its default context; a model loaded at 262,144 was found serving at 28,672 with nothing errored, and the probes against it read as a capability collapse. Mismatch is fail-closed: the attempt does not start. |
| `budget` | object | `turn_cap`, `token_cap`, `wallclock_cap_ms`, `iteration_cap`. All four are escalation triggers. |
| `tree_sha256` | str | Content hash of the checked-out tree before the agent acts. |
| `criterion_ref` | str | Visible criterion identity. Held-out criteria are referenced by the task, never by this stream. |
| `progress_scale` | object | `assertions_total: int`, `assertion_ids: [str]`. See Progress. |
| `seed` | int | I11. |
| `context_strategy_version` | str | Hash over the retrieval function source, FTS configuration and seed. |
| `prompt_version` | str | |

A task whose visible criterion cannot yield a stable, enumerable assertion set has no
progress scale and is **not schedulable under this specification**. That is a real
restriction on the Phase 1 class and it is deliberate: a loop contract requires a monotone
progress measure, and a task that cannot supply one cannot be run under a loop contract.

## `turn`

| Field | Type | Notes |
|---|---|---|
| `turn_index` | int | 0-based within the attempt. |
| `prompt_tokens`, `completion_tokens` | int | |
| `cached_prefix_tokens` | int | Recorded **separately** from `prompt_tokens`. Folding cache hits into token spend contaminates the strongest failure predictor with a serving property. |
| `prefill_ms`, `decode_ms`, `total_ms` | int | Split, because a 64k uncached turn costs ~76 s of prefill before one token, and a lane whose prefix cache has been silently zeroed looks identical to a hard task in an undifferentiated total. |
| `served_context_length` | int \| null | Per-turn, where the server reports it. |
| `stop_reason` | enum | `tool_call` · `content` · `length` · `stop` · `error` |
| `tool_calls_emitted` | int | Arriving on the tool channel. |
| `content_channel_calls_parsed` | int | Parseable calls found in the content channel. |
| `content_channel_calls_salvaged` | int | Of those, the ones recovered. `parsed − salvaged` is the ambiguous remainder, deliberately not acted on. |
| `content_sha256` | str | Artifact reference to the raw content channel, verbatim. Required — the classifiers below are lower bounds, and Phase 2 must be able to reclassify without re-running. |
| `mismatch_flags` | [enum] | See Reasoning–action divergence. |

## `tool_call`

| Field | Type | Notes |
|---|---|---|
| `turn_index`, `call_index` | int | `call_index` is 0-based across the whole attempt, giving total order. |
| `tool_name` | str | |
| `args_sha256` | str | Over the ACS-1 canonical form of the arguments. |
| `signature_sha256` | str | Over `tool_name ‖ 0x00 ‖ args_sha256`. This is what repetition is defined against. |
| `channel` | enum | `tool` · `content` |
| `salvage` | enum \| null | `named_object` · `positional_single`. Null when `channel = tool`. No other salvage form exists; anything wider is the harness guessing at intent. |
| `outcome` | enum | `ok` · `error` · `rejected` |
| `error_class` | enum \| null | The five-class taxonomy: `infrastructure` · `policy_violation` · `criterion_failure` · `exhaustion` · `contract_violation`. |
| `error_code` | str \| null | Stable harness-authored code. The raw third-party text goes to the artifact store, never into this field. |
| `duration_ms` | int | |
| `mutating`, `idempotent` | bool | Copied from the tool's declared specification, not inferred. |
| `repeat_of` | int \| null | `call_index` of the **earliest** prior call in this attempt with the same `signature_sha256`. |
| `repeat_kind` | enum \| null | `recovery_retry` · `correction` · `sterile`. |

### Repetition and recovery are the same event until you look at the predecessor

A call whose signature matches an earlier one is syntactically a repeat. Whether it is a
defect depends entirely on what happened to the earlier call, and collapsing the two is a
live hazard rather than a hypothetical: in the agentic probe, the one repeated call per
run was the model's *correct* retry of a deliberately injected transient failure, and the
naive metric counted it as repetition. That reading must not be inverted into a defect.

| `repeat_kind` | Rule | Reading |
|---|---|---|
| `recovery_retry` | The referenced prior call has `outcome = error` and `error_class = infrastructure`. | Correct behaviour. Counts toward recovery, never toward repetition. |
| `correction` | No signature match, but a prior call in this attempt has the same `tool_name`, `outcome = error`, and no successful call to that tool in between. | Correct behaviour — the agent changed its arguments in response to an error. Counted separately because it is the harder and more valuable capability. |
| `sterile` | The referenced prior call has `outcome = ok`, the tool is `mutating = false`, and no successful mutating call occurred between the two. | The MAST step-repetition class, measured at **17.14%** across published multi-agent runs. This is the number Phase 1 is testing against. |

The `mutating = false` condition is load-bearing: re-reading a file after editing it is not
repetition, it is verification. Without the intervening-write test the metric would punish
the behaviour we want. This is also why the **Tool Specification Standard must declare
`mutating` and `idempotent` per tool** — the repetition metric is unmeasurable without it,
which is one of the two reasons that document is promoted alongside this one.

### Recovery rate

For each `error_class`, over an attempt:

```
recovered(c)  = failed calls of class c followed, before attempt end, by an ok call
                to the same tool with repeat_kind in {recovery_retry, correction}
recovery_rate(c) = recovered(c) / failed(c)
```

`policy_violation` is excluded from the denominator by construction: it terminates the run
and is never retried, because a retry is indistinguishable from searching for a
formulation of the same action that the check does not catch.

## `progress`

The loop contract requires a monotone progress measure. For the Phase 1 task class —
*implement surrogate safety metric M per its published specification, matching reference
values* — it is defined as follows, and it is computed by the harness on the agent's tree,
never reported by the agent.

| Field | Type | Notes |
|---|---|---|
| `observation_index` | int | 0-based within the attempt. |
| `trigger` | enum | `attempt_start` · `post_write_turn` · `attempt_end` |
| `assertions_passing` | int | Visible-criterion assertions passing, out of `progress_scale.assertions_total`. |
| `collection_errors` | int | Assertions that **did not execute** — import failure, syntax error, collection error. |
| `tree_sha256` | str | The tree the observation was made on. |
| `delta` | int | `assertions_passing` minus the previous observation's. |
| `stall_length` | int | Consecutive observations with `delta = 0` **and** a changed `tree_sha256`. |
| `sampled` | bool | True if this observation covers more than one write turn (see below). |

**The measure is `P = assertions_passing`, with `collection_errors` recorded separately and
never subtracted into it.** A tree that does not import scores `P = 0`, and so does a tree
that imports cleanly and computes the wrong number. Those are different states — a check
that failed and a check that did not run are different outcomes, and this is that rule
applied to the progress measure rather than to the verdict. A single scalar that conflates
them would report a syntax error and a wrong formula as the same distance from done.

Three conditions, all mechanically decidable:

- **Monotone** — `delta ≥ 0`.
- **Stall** — `delta = 0` while `tree_sha256` changed. Work happened; nothing improved.
  `stall_length ≥ iteration_cap` is an escalation trigger (`no_monotone_progress`).
- **Regression** — `delta < 0`. Recorded, never silently absorbed. A run that regresses and
  recovers is a different trajectory from one that climbs monotonically, and only one of
  them is evidence of goal seeking.

**When observations are taken:** at attempt start, at attempt end, and after every turn in
which at least one mutating tool call returned `ok`. Turns with no successful write cannot
change `P` and are not observed. If criterion execution exceeds 20% of attempt wall-clock,
observations may be downsampled to every N-th write turn with `sampled = true` and `N`
recorded on `attempt_end` — never to zero, and never adaptively, because a sampling rate
that responds to the run is a rate that can be tuned by the run.

Running the visible criterion for instrumentation leaks nothing: the agent may already see
and retry against it. **The held-out criterion is never executed for progress
measurement.** A progress signal computed from held-out results would make the whole
trajectory a search over the held-out set.

## Reasoning–action divergence

MAST measures reasoning-action mismatch at **13.98%**. It is not fully structurally
detectable, and pretending otherwise would put an unvalidatable judgment in the evidence
plane. What is emitted is a **lower bound** from three decidable flags, plus the raw
content channel so a Phase 2 advisory judge can reclassify without re-running anything.

| Flag on `turn.mismatch_flags` | Rule |
|---|---|
| `stated_no_call` | The content channel names a tool from the declared tool set, the turn emits zero tool calls on either channel, and `stop_reason ≠ stop`. This is the exact shape of the one tool-calling miss observed in the lane benchmark: no call emitted at all, rather than malformed JSON. |
| `announced_mismatch` | The content channel names tool A and the turn's only emitted call is tool B. |
| `abandoned_plan` | The content channel names a tool, the turn emits a call to it, the call errors, and the attempt ends within the same turn with no recovery. |

**A tool call arriving in the content channel is not reasoning-action mismatch.** It is a
serving defect — 15–20% of calls on the selected lane, disproportionately the final one,
in two syntaxes, valid JSON in the wrong channel with nothing raised. It is counted on
`turn.content_channel_calls_parsed`, reported as a serving-quality metric, and must never
be summed into the mismatch rate. Chain completion reads 20% or 100% on identical model
behaviour depending solely on whether the harness salvages it; a metric that blames the
model for the server's channel would make Phase 1's headline capability number a property
of the harness.

Any report of the mismatch rate states that it is a lower bound. A lower bound presented
as a rate is the same class of error as a summary presented as a fact.

## `phase_start` and `phase_end`

The execution lifecycle (`docs/tier3/execution-lifecycle.md`) has seven phases, and until
these records existed the stream could not say which one a turn happened in. Every question
worth asking about the lifecycle — where re-entry actually lands, which phase consumes the
budget, whether the front half was skipped for a task class that did not declare it — is a
question about phase boundaries, and none of them is answerable from `turn` alone.

**These are stream fields, not a store schema.** Per the ownership rule in
`docs/tier1/data-architecture.md`, *the stream is a field set, the store is a schema, and the
store never re-declares a stream field.* Adding these two record types is a change to this
document and to the validator. **It is not a migration.**

### `phase_start`

| Field | Type | Notes |
|---|---|---|
| `phase` | enum | `discover` · `grill` · `architect` · `plan` · `execute` · `review` · `validate`. Closed set; it is the lifecycle's, and a phase this stream can name that the lifecycle does not have is a contract violation. |
| `entry_reason` | enum | `sequence` · `re_entry`. What put the run in this phase. |
| `re_entry_from` | enum \| null | The phase whose failure caused a backward move. Null unless `entry_reason` is `re_entry`. |
| `re_entry_override` | bool | Whether the finder overrode the static default. |
| `re_entry_rationale` | str \| null | Required when `re_entry_override` is true. The lifecycle permits an override only by the party that found the failure, and only upstream; an override with no recorded reason is indistinguishable from a wrong table. |
| `capability_id` | str | The capability dispatched to for this phase. The join to `policy/role-bindings.json` and, through it, to `policy/model-routing.json`. |
| `task_class` | str | The class assigned by the orchestrator before dispatch. Recorded here because it is what scales the front half, and a collapsed front half must be attributable to a declared class rather than to a skipped step. |

**`re_entry_from` is what makes the re-entry table falsifiable.** The lifecycle's static
default is defended on the claim that it is *"never catastrophically wrong, only sometimes
wasteful."* Nothing tests that claim without a record of where re-entry was defaulted and
where it was overridden.

### `phase_end`

| Field | Type | Notes |
|---|---|---|
| `phase` | enum | Must match the open `phase_start`. |
| `outcome` | enum | `terminated` · `failed`. **Two values, deliberately.** The three-valued verdict lives at the merge gate and nowhere else — `indeterminate` means *excluded from the ratio the autonomy gates read*, and upstream phases feed no ratio. |
| `artifact_ref` | str \| null | Hash of the artifact the phase produced (I3 — a hash, never a path). Null only when `outcome` is `failed`. |
| `checked_by` | enum | `orchestrator`. Present and closed to one value, because the value is the point: a phase terminates when its artifact exists and validates, **checked by the orchestrator and never by the child that produced it**. Recording who checked is what makes a later violation visible rather than inferable. |
| `wallclock_ms` | int | From the matching `phase_start.monotonic_ns`. |

**Why `checked_by` is a one-value enum rather than omitted.** On 2026-09-02 two child
sessions holding complete contracts returned `completed` having created no branch, written no
file and posted no comment. The contracts were not the defect; nothing checked the artifacts
before the completion was accepted. A field that always reads `orchestrator` costs nothing
and turns "the child self-certified" from an untracked possibility into a schema violation.

## `escalation`

| Field | Type | Notes |
|---|---|---|
| `primary_cause` | enum | Exactly one. |
| `also_satisfied` | [enum] | Every other trigger true at the same evaluation. |
| `evaluated_at_turn` | int | |
| `attempt_bundle_ref` | str | Artifact hash of the structured bundle: what was tried, what was read, what the criterion said. |

Causes, closed set: `turn_cap` · `token_cap` · `wallclock_cap` · `iteration_cap` ·
`criterion_red_after_n` · `no_monotone_progress` · `protected_path_attempt` ·
`tool_unavailable` · `policy_violation` · `agent_initiated` · `harness_fault`.

**`also_satisfied` is what makes the distribution mean anything.** Caps are frequently
reached together — a run that exhausts its turn cap has usually also exhausted its token
cap — and if only the first trigger to fire is recorded, the escalation-cause distribution
becomes a report on the harness's trigger evaluation order rather than on the agent. That
is a silent, permanent corruption of the one distribution Phase 1 exists to produce.

`agent_initiated` is recorded and is never load-bearing. An agent that can declare itself
blocked can also declare itself done.

## `attempt_end`

| Field | Type | Notes |
|---|---|---|
| `termination` | enum | `verdict` · `escalation` · `harness_fault` |
| `verdict` | enum \| null | `pass` · `fail` · `indeterminate`. Null when `termination = escalation`. |
| `stop_reason` | enum | Final turn's stop reason, or `cap` / `harness`. |
| `turns`, `tool_calls`, `mutating_tool_calls` | int | |
| `wallclock_ms` | int | From `attempt_start.monotonic_ns`. |
| `agent_ms`, `criterion_ms`, `harness_ms` | int | Attribution per I9. A wall-clock-per-merged-task target is unactionable if the split is unknown. |
| `prompt_tokens`, `completion_tokens`, `cached_prefix_tokens` | int | Attempt totals. |
| `tree_sha256` | str | Final tree. |
| `loaded_context_length` | int | **Re-asserted at attempt end.** Recorded at both ends so a mid-attempt lane reload is detectable rather than invisible; a fingerprint field the server can change unobserved is not a fingerprint unless something checks it. |
| `progress_final` | object | `assertions_passing`, `collection_errors`, `stall_length_max`, `regressions`. |
| `premature` | enum \| null | See below. |
| `sterile_repeats`, `recovery_retries`, `corrections` | int | |
| `progress_sample_n` | int | 1 unless downsampled. |

### Premature termination

MAST measures premature termination at **7.82%**. Two decidable forms, and an attempt may
carry only one:

| `premature` | Rule |
|---|---|
| `no_work` | `termination = verdict` and (`mutating_tool_calls = 0` or final `tree_sha256` equals the initial one). An answer was produced without the required work occurring. |
| `stopped_short` | `termination = verdict`, `stop_reason = stop`, final `assertions_passing < assertions_total`, and every budget dimension below 80% consumed. The agent stopped with the work unfinished and the budget available. |

Neither is a verdict. Both are trajectory properties recorded beside the verdict, because
a `fail` reached after exhausting the budget and a `fail` reached by stopping at turn three
are different failures and belong in different rows of the taxonomy.

## `task_end`

| Field | Type | Notes |
|---|---|---|
| `attempts` | int | |
| `retry_budget` | int | |
| `outcome` | enum | `merged` · `rejected` · `escalated` · `abandoned` |
| `wallclock_ms_total` | int | All attempts plus harness time between them. |
| `wallclock_ms_to_outcome` | int | Dispatch to the terminal event. This is the numerator of wall-clock per merged task. |
| `human_review_ms` | int \| null | **Superseded, retained as an alias.** The instrument is the `timing` object on `operator_action` (Mission Control Specification § Review timing capture). This field carries `attended_ms` where that is non-null and is **null otherwise — never 0**, because a review whose instrument did not run and a review that took no time are different outcomes. It is not a second source of truth: it is a projection, and the linter checks the projection agrees. |
| `verdict_final` | enum | |
| `held_out_result` | enum | `pass` · `fail` · `not_run`. Class label only — never the trace, the failing input, or the expected value. |

## `operator_action`

The one record type this stream carries that the harness does not write. D51 requires every
operator action to be an evidence row in the same hash chain; before this section the enum
was closed against it, so the row D51 mandates had no legal place in the stream it was
mandated to enter.

**Field ownership is split, deliberately.** This document owns the *envelope*, the
`record_type` value, and the writer rule below. The **Mission Control Specification owns
the record's own fields** — `action`, `verdict_ref`, `as_of_chain_head`, `decision_basis`,
`timing`, `rationale_sha256`, `waiver_adr_ref`, `idempotency_key` — because they are
properties of the surface that emits them and they will change on that surface's schedule,
not this one's. They are versioned separately by `field_set_version` (int), which appears
on `operator_action` and on no other record type. Two version fields on every record would
be redundant; one version field covering two independently-changing field sets is the
defect D48 recorded, arriving one layer down.

| Field | Type | Notes |
|---|---|---|
| `field_set_version` | int | Version of the mission-control field set. Independent of `schema_version`. |
| *(remainder)* | | Mission Control Specification § Operator actions as evidence. |

### Writers, and why the enum stays closed

Each record type has exactly one legal writer, and the pairing is checkable:

| Records | Written by | `actor_kind` |
|---|---|---|
| `attempt_start` · `phase_start` · `turn` · `tool_call` · `progress` · `phase_end` · `escalation` · `attempt_end` · `task_end` | the harness | `harness` |
| `operator_action` | the mission-control command surface, under `alfred_operator` | `operator` |

A record whose `record_type` and `actor_kind` disagree is a contract violation, not a
warning. The harness cannot write `operator_action` and the command surface can write
nothing else — enforced by SQL grant (Data Architecture § Grant matrix), not by this
sentence.

### ACS-1 domain separation still holds

The hash is taken over `acs_version ‖ 0x00 ‖ record_type ‖ 0x00 ‖ bytes` (ADR-0003), so
`record_type` is hashed input and the separation is by *value*, not by membership of a set.
Three consequences, all of which had to be true before the enum could be widened:

- **Adding a member changes no existing digest.** `operator_action` is a new domain, not a
  modification of an existing one. No previously-hashed record is affected, which is why
  this amendment is not hash-breaking and why it had to happen before the first record is
  written rather than after.
- **An operator row cannot be replayed as a harness row.** Identical bytes under a
  different `record_type` hash differently, so a row cannot be moved between domains
  without breaking the chain.
- **The value is a literal, never derived.** `record_type` is never computed from
  `actor_kind` or from the writing role. A domain separator derived from another field
  separates exactly as well as that field does, and `actor_kind` is a closed enum that a
  future actor kind will widen.

The ACS-1 vector suite has `record_type` domain-separation vectors (added 2026-08-13,
after the audit found the separator had none). **`operator_action` needs its own vector**
— a vector suite that covers only the separator values that existed when it was written
tests the mechanism and not the values in use.

### What this does not change

`operator_action` is written by a process holding an operator credential, not an agent
credential, so the exclusion under *What is deliberately not recorded* is untouched: no
record in this stream is written by any process holding an agent credential, and the agent
process still holds no database credential at all. The operator still writes no verdict
field; an approve authorizes a merge given a verdict that `CriterionRunner` already
computed.

## Derived metrics

Every number in the Phase 1 failure taxonomy is a query over the above. Nothing below is
stored; storing a derived value creates a second source of truth that can disagree with
the first.

| Metric | Definition |
|---|---|
| Turns per attempt | Distribution of `attempt_end.turns`. Report the distribution, not the mean — the mean of 4.1 turns from the probe tells you nothing about whether 30 turns holds. |
| Tool calls per attempt | `attempt_end.tool_calls`. |
| Chain depth | Max consecutive `tool_call` records with no intervening non-tool `stop_reason`. |
| Wall-clock per merged task | `Σ task_end.wallclock_ms_to_outcome` over `outcome = merged`, divided by the count. |
| Tool failure rate by class | `count(tool_call: outcome = error, error_class = c) / count(tool_call)`. |
| Recovery rate by class | As defined under Recovery rate. |
| Progress monotonicity | Fraction of attempts with zero `progress` records where `delta < 0`. |
| Stall rate | Fraction of attempts with `stall_length_max ≥ 2`. |
| Sterile repeat rate | `Σ sterile_repeats / Σ tool_calls`. Compare against MAST's 17.14%. |
| Mismatch lower bound | `count(turn: mismatch_flags ≠ [])` / `count(turn)`. Compare against MAST's 13.98%, stated as a lower bound. |
| Content-channel rate | `Σ content_channel_calls_parsed / (Σ tool_calls_emitted + Σ content_channel_calls_parsed)`. Serving quality, never capability. |
| Salvage dependence | Chain completion computed with and without salvaged calls. Both numbers are reported. The gap was 20% vs 100% on the probe lane; a single number here is a claim about the harness disguised as a claim about the model. |
| Escalation-cause distribution | Over `primary_cause`, with `also_satisfied` co-occurrence reported alongside. |
| Premature termination rate | `count(attempt_end: premature ≠ null) / count(attempt_end)`, split by kind. |
| Turn/token failure correlation | Spearman ρ of `attempt_end.turns` and `completion_tokens` against verdict. Prior: ρ ≈ −0.67 and −0.73. A Phase 1 value far from these is a finding about this system, not a confirmation of the prior. |

## What is deliberately not recorded

- **Any agent self-assessment of progress, completeness or blockage.** The agent cannot
  write `blocked` or `complete`, and it cannot write a progress number either. Every field
  in this specification is harness-computed or harness-observed.
- **Agent-authored summaries of a trajectory.** The raw content channel is stored by hash;
  a summary is lossy compression by an interested party.
- **Held-out criterion detail in any form** beyond a pass/fail class label on `task_end`.
- **Derived aggregates.** Computed at read time from the records.
- **Any record written by a process holding an agent credential.** The agent process holds
  no database credential at all; this stream is written by the harness.

## Instrument verification

**Nothing here is trusted until a deliberately injected defect moves it.** Four for four,
every headline number in this project has been wrong on first read — an unsalted prefill
measured a cache hit, an object benchmark reported 1.3× instead of 60×, a 0/10
tool-calling score was a silently reloaded lane, and a 0.2 chain-completion rate was a
serving-layer channel defect. A verification suite that passes on the first run is also
what a vacuous verifier reports.

Before the first real Phase 1 task dispatches, a scripted agent replaces the model and
produces each trajectory below. The suite fails if the expected field does not move.

| Injected trajectory | Must produce |
|---|---|
| Calls the same read tool with identical arguments five times after a success | `sterile_repeats = 4`, mismatch flags empty |
| Fails one infrastructure call, retries identically, succeeds | `recovery_retries = 1`, `sterile_repeats = 0` |
| Fails one call, changes arguments, succeeds | `corrections = 1` |
| Edits the tree every turn without improving the criterion | `stall_length_max` equal to the turn count, escalation `no_monotone_progress` |
| Breaks a previously passing assertion | a `progress` record with `delta < 0` |
| Introduces a syntax error | `collection_errors > 0` with `assertions_passing = 0`, distinguishable from a wrong-formula run at the same `P` |
| Emits a well-formed call in the content channel, both syntaxes | `content_channel_calls_parsed = 2`, `salvaged = 2`, `channel = content` on both |
| Emits an ambiguous content-channel call | `parsed = 1`, `salvaged = 0`, no `tool_call` record fabricated |
| Announces a tool and emits nothing | `stated_no_call` |
| Stops at turn two with the criterion red and budget remaining | `premature = stopped_short` |
| Returns without touching the tree | `premature = no_work` |
| Exhausts turn and token caps in the same evaluation | one `primary_cause`, the other in `also_satisfied` |
| Runs against a lane reloaded at its default context mid-attempt | `attempt_end.loaded_context_length` differs from `attempt_start` |

The last row is the one most likely to be skipped and is the one with a documented prior:
it has already happened once, silently, and read as a capability collapse.

## Enforcement

The `enforcement: schema` claim on this document is discharged by one mechanism, specified
in full here. **It does not exist yet.** As of 2026-08-15 the repository contains three
scripts — `gen_doc_stubs.py`, `gen_reading_map.py`, `lint_docs.py` — and no CI
configuration of any kind. Nothing today validates a run record, because no run record has
been emitted. The specification is written now for the same reason the records are: a
validator designed after the first stream exists is a validator designed to accept it.

**Build gate.** The linter is green over its fixture set before the first Phase 1 task
dispatches, on the same line as the instrument-verification suite above. A stream emitted
before its validator exists is a stream nobody can later show was well-formed.

### Placement — it is inspector, not tooling

The implementation lives under `harness/` and is in the protected set (D20). The name two
documents already reference, `scripts/lint_run_records.py`, is a thin CLI wrapper and is
protected with it. This is not fussiness: `scripts/` is currently outside the protected
set, and a validator of the evidence stream that an agent may edit validates nothing. The
same argument applies to any future gate entry point placed there.

### What it validates

Input is one or more JSONL streams, or a directory of fixtures. Exit 0 or 1; every failure
names file, line, `event_id` and rule. Seven groups, all decidable from the stream alone:

| # | Group | Rules |
|---|---|---|
| L1 | Envelope | Every field in *Common envelope* present and typed. Nullability exactly as tabulated — `caused_by` null only on `attempt_start`; `attempt_id` null only on `task_end` and task-scoped `operator_action`. |
| L2 | Enumerations | Every enum in this document is closed and checked as closed: `record_type`, `stop_reason`, `channel`, `salvage`, `outcome`, `error_class`, `repeat_kind`, `trigger`, `termination`, `verdict`, `premature`, `mismatch_flags`, `primary_cause`, `also_satisfied`, `actor_kind`, `outcome` on `task_end`, `held_out_result`, and mission control's `action` and `timing_source`. |
| L3 | Referential integrity | Every `caused_by`, `repeat_of` and `verdict_ref` resolves within the stream (or, for `verdict_ref`, to a verdict row the caller supplies). `turn_index` and `call_index` are dense and 0-based. `assertion_ids` on a `progress` record are a subset of `attempt_start.progress_scale.assertion_ids`. |
| L4 | Counter agreement | `attempt_end`'s `turns`, `tool_calls`, `mutating_tool_calls`, token totals, `sterile_repeats`, `recovery_retries`, `corrections` and `progress_final` each equal the value recomputed from the records they summarize. This is the group that catches an instrument that stopped emitting halfway. |
| L5 | Structural rules | No `salvage` on a `channel = tool` call. No `recovery_retry` whose predecessor has `outcome ≠ error` or `error_class ≠ infrastructure`. No `sterile` whose predecessor failed, or with an intervening successful mutating call. `delta` equals the difference from the previous observation. `stall_length` consistent with its neighbours. `premature` at most one value. Exactly one `primary_cause`, and it is absent from `also_satisfied`. |
| L6 | Writer rules | `record_type` and `actor_kind` agree per *Writers*. `field_set_version` present iff `record_type = operator_action`. `human_review_ms` on `task_end` equals `attended_ms` of the terminal `operator_action`, or is null when that is null — never 0. |
| L7 | Operator-action rules | `waiver_adr_ref` non-null iff `action = waive`. `verdict_ref` non-null on `approve`, `decline` **and `waive`**. **A `waive` whose `verdict_ref` resolves to a verdict that is not `fail` is a violation** — see below. `attended_ms ≤ elapsed_ms`. `attended_ms` null iff `timing_source = navigation_only`. `decision_basis` fields present. `as_of_chain_head` present. |

**L7's waive rule, because it is the one that carries weight.** A waiver ADR records gate,
threshold, **actual value**, reason and reversal condition (D28). On an `indeterminate`
there is no actual value, because the gate did not run — so a waiver over an
`indeterminate` is the fail-open that Failure Semantics forbids, wearing the paperwork of a
control that did run. `waive` is therefore available on `fail` only. The surface refuses it
at the endpoint and writes no record (a refused action is not an action); this rule is the
independent check that the endpoint did, and it is the reason `verdict_ref` is required on
`waive` at all. **A `waive` record with a null `verdict_ref` is unresolvable by
construction, which would make the rule uncheckable rather than merely violated** — so the
nullability and the verdict check are one rule in two halves, and a negative fixture exists
for each half.

**Adding a field to the operator-action field set.** Record shapes are closed and an
unknown field is an L1 error, so a new field on `operator_action` or inside its `timing`
object is a `field_set_version` bump plus a validator change, in that order. This is the
cost the split ownership was chosen to make visible rather than to avoid: mission control
may add fields on its own schedule, and the schedule has one step on it.

### Fail-closed, in three specific places

- **Unknown `record_type` → error, never skip.** The enum is closed and it is hashed input;
  a value outside it is either a schema change that skipped the version bump or a fabricated
  record, and a linter that ignores what it does not recognize passes exactly the record
  worth catching. The message names the unknown value verbatim.
- **Unknown `schema_version` → error, and no partial validation.** The linter carries the
  version it implements. Against a higher version it fails with *linter implements version
  N, stream declares M*; it does not validate the fields it happens to recognize, because a
  partial pass reported as a pass is the failure mode this whole document exists to prevent.
- **Unknown field on a known record type → error.** Record shapes are closed. A field the
  linter has never seen is a schema change without a version bump.

The linter erroring is itself a failure: an unproven control is a failed control (Failure
Semantics). It never exits 0 on an exception.

### Where it runs

1. **CI, every change**, over `harness/fixtures/run_records/` — a positive fixture per
   record type, and a negative fixture per rule above, each expected to fail with a named
   rule. A rule with no negative fixture is not covered, and the fixture suite asserts
   every rule id appears in at least one expected failure. A linter whose test suite
   contains only well-formed input reports that it is vacuous by passing.
2. **From Phase 1, on every emitted stream, before the chain writer hashes it.** A stream
   that does not validate is not chained: the run is `indeterminate` and the records are
   retained for diagnosis. Hashing a malformed record makes it permanent.

The linter checks the schema, never the trajectory. It cannot tell whether a run went well
— only whether what was recorded about it is internally consistent and complete enough to
be read later. It is also not a substitute for validation at the write boundary: Pydantic
models in the emitting process reject a malformed record before it is written, and the
linter is the independent check that they did. Two mechanisms, because the write-boundary
check is authored by the same process it constrains.
