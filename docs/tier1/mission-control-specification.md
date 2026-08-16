---
status:        provisional
owner:         executable
enforcement:   schema
evidence:      The surface's obligations are derived from controls that already exist — three-valued verdicts (Failure Semantics), the run record stream's `task_end.human_review_ms` field, which is specified as "recorded from the review interaction, not estimated" and today has no instrument, and the capacity ledger's requirement for human minutes per task. Nothing here rests on an observed review: no review has happened.
falsifies_if:  A Phase 1 merge is authorized without a corresponding operator-action row in the evidence chain; or the capacity ledger cannot be computed from recorded review time because the recorded number is dominated by tab-open wall clock rather than attended time; or criterion-first ordering is observed not to hold — reviewers open the full diff on a majority of tasks with no anomaly flag set.
review_after:  Phase 1
---

# Mission Control Specification

The operator's surface: the queue, the escalation inbox, the evidence bundle, and the
run record. What it shows, what it refuses to do, and what it records about the person
using it.

## Why this exists, as the failure it prevents

Phase 1 places a human gate on every one of 20+ tasks and produces a number — human
minutes per task — that major-fix #10 turns into an executable stage gate: *projected
human-minutes ≤ capacity*. The plan gave that gate no instrument. Without one, three
failures follow, and they are not hypothetical because they are the default state:

1. **The capacity gate reads a guess.** A gate whose input is estimated after the fact
   is a note. Review time recorded by the person being measured is worse than absent,
   because it looks like data.
2. **The most privileged actor is the least audited one.** T10 names the operator as a
   threat and the prior attempt's actual failure. Every other write to the evidence
   chain has a recorded author; an approval taken in a terminal against a patch file has
   none. An approval surface that does not write to the chain makes the one actor who
   can override every gate invisible in the record that exists to catch overrides.
3. **Review collapses into diff reading.** D22's ordering — intent, criterion, evidence
   bundle, diff summary, full diff only on signal — is a claim about what a human adds
   that the harness cannot. A surface whose default view is a diff duplicates the
   harness, produces the fatigue D22 exists to prevent, and does it while consuming the
   scarce resource the whole factory is rate-limited by.

Mission control exists to make the human gate a *measured, recorded, criterion-first*
step rather than an unrecorded judgment taken outside the system.

## Scope

**In:** the review queue, the escalation inbox carrying the structured attempt bundle
(D23), the criterion-first evidence bundle, the run record with the graph and loop
viewer, the five operator actions, and automatic per-review timing.

**Out, deliberately:** charts and trend views, live in-flight run observability,
policy/threshold/criterion editing, agent chat, autonomy-grant administration, drain and
backpressure *controls*. Each is listed with its pull-forward trigger under
*Deliberately deferred*. All of them govern machinery that does not exist yet.

## The boundary split

The surface is two programs, not one, and the split is the point.

| | Command surface | Read model |
|---|---|---|
| Does | approve · decline · request-changes · waive · escalate-to-self, and later grant/revoke autonomy and drain | queries, views, ordering, filtering, rendering |
| Is | **inspector** — permanently agent-protected under D20 | **factory** — agents may build it |
| Lives in | `harness/mission_control/` (owned by `alfred-svc`, in the protected set) | `src/mission_control/` (agent-writable) |
| DB role | `alfred_operator` — INSERT on operator-action evidence only; **no grant on any verdict, held-out or policy table** | `alfred_readmodel` — **SELECT only, everywhere**; it holds no INSERT, UPDATE or DELETE grant on any schema |
| Process | separate process, separate port, both loopback-bound | separate process |

Two rules make the split real rather than declarative:

- **No import path between them**, checked by the same CI lint that enforces D39's
  verdict-module separation. The command surface does not import the read model; the
  read model does not import the command surface.
- **The read model may not be the source of any fact an action depends on.** This is the
  hole the split would otherwise open: if agents may build the views, an agent-authored
  view can render a `fail` as a `pass` and the operator approves it in good faith, with
  every underlying control intact. So the decision-critical panel — verdict triple,
  which criteria executed, held-out class label, the twelve Definition-of-Done condition
  states, budget consumption, anomaly flags — is rendered **by the command surface from
  its own queries**. The read model serves navigation, ordering, diff summaries, run
  records and the graph viewer. A screen composed of both states which half is which.

## The screens

Four, derived rather than assumed. Two work lists, because the two carry different
content and different actions; two detail screens, because a task with a verdict and a
task that stopped are different objects.

### S1 — Queue

Everything awaiting the operator, in two lanes: **awaiting review** (a verdict exists)
and **escalated** (no verdict exists; the run stopped). One row per task. Each row
carries task id, intent in one line, lane, verdict or escalation cause, age since the
terminal event, attempt count, and the anomaly flags set on it. Backlog depth per lane
is displayed from Phase 1 because the number is needed for backpressure long before the
control exists.

Ordering is by age within lane, oldest first, and is **not** operator-configurable in
v1: a reorderable queue is a place where hard tasks sink.

No preview on hover, no inline diff, no multi-select, no bulk action. A decision is
reached on a detail screen or not at all.

### S2 — Review (the evidence bundle)

The load-bearing screen. Specified in full below.

### S3 — Escalation

For tasks with `termination = escalation`. Renders, in order: intent; the criterion;
`primary_cause` **and** `also_satisfied` together, never the primary alone — recording
only the first trigger corrupts the escalation-cause distribution, and rendering only
the first recreates the same corruption in the operator's head; budget consumption per
dimension; the progress trace (`assertions_passing` over observations, stalls and
regressions marked); and the structured attempt bundle by artifact hash — what was
tried, what was read, what the criterion said.

Actions here are `escalate_to_self` (the operator takes the work; the task leaves the
agent queue) and `reopen` (return to the queue, optionally after a configuration change
made elsewhere). There is no approve on this screen: with no verdict there is nothing to
approve, and the surface offers no affordance that would suggest otherwise.

### S4 — Run record

Per attempt, generated from the run record stream: the turn and tool-call trajectory,
the progress series, the graph and loop rendering (Part B), the read log, the
fingerprint asserted at both ends of the attempt, the wall-clock split
(`agent_ms` / `criterion_ms` / `harness_ms`), and the raw content channel by hash —
behind a click, labelled as agent-authored and untrusted.

This screen is where the Phase 1 failure taxonomy is actually read. It carries no
actions at all.

## S2 in detail — the evidence bundle

The order is D22's, and the ordering is the specification. What is easy to reach is a
design decision with a measurable consequence.

**Zone 1 — Intent.** The work item in the author's words. The criterion's *purpose*
sentence. Nothing computed. This is first because the question the human is here to
answer — *was this the right criterion, and did the agent solve the stated problem or a
nearby easier one* — cannot be asked before the stated problem has been read.

**Zone 2 — Criterion.** The criterion as D33 defines it: assertion, interface signature,
threshold provenance. The grading points with their provenance tiers (D49), and which
one was held out. Rendered from the control plane, not from anything the agent produced.

**Zone 3 — Verdict and evidence bundle.** Command-surface rendered. Three-valued verdict
shown as three distinct states, never as a badge on a pass. Per criterion: executed or
not executed, and the outcome. Held-out result as a **class label only** — `pass`,
`fail`, `not_run`. The twelve Definition-of-Done conditions as a checklist of recorded
facts. Property test results including composed properties. Static gates. Result
stamping intact. Fingerprint. Anomaly flags: `premature`, progress regressions, stall
length, sterile repeat count, `indeterminate` anywhere in the attempt history,
test-file edits in the diff, tolerance changes, protected-path attempts, judge-raised
escalations.

**Zone 4 — Diff summary.** Files changed with line counts and a per-file classification
(source · test · criterion-adjacent · configuration · documentation). Patch-validation
result. A10 scan result. Test-file edits and tolerance changes surfaced here explicitly
because those are the reward-hacking shapes, and they are the reason to open the diff.

**Zone 5 — Full diff.** One click. Exactly one, and it is recorded: the operator-action
record carries `full_diff_opened`. That makes D22's central claim measurable — if the
full diff is opened on a majority of tasks carrying no anomaly flag, criterion-first
review is not happening and this document's `falsifies_if` has fired.

### Deliberately hard to reach, and why

- **Held-out detail** — the failing input, the expected value, the trace. Not rendered
  anywhere, in any zone. A held-out read is a separate deliberate action that logs to
  the evidence store (major-fix #2), marks the task, and is reported as harness health.
  The diagnostic convenience is not worth dissolving the boundary the entire autonomy
  ladder rests on.
- **Agent prose** — the content channel, commit messages, any agent-authored
  explanation. Absent from S2 entirely; reachable only from S4, labelled, escaped, and
  scanned. Major-fix #7 strips agent-authored text from the advisory judge so the judged
  cannot argue with its judge. The same argument applies with less force to a human, who
  can at least notice being argued with — but *less force* is not *none*, and the cost of
  omitting it from the review screen is zero.
- **Any agent self-assessment** of progress, completeness or blockage. It is not
  recorded, so it cannot be rendered.
- **The diff as a default view.** No screen in mission control opens onto a diff. No
  queue row previews one. This is the single most important rendering decision in the
  document.

### One rendering rule that is a security control

Everything on these screens that originated outside the harness — issue text, commit
messages, error strings, dependency output, agent prose — passes the **A10 scan before
render**: control, zero-width and bidi characters rejected or made visible, never
silently displayed. T3 is prompt injection through read content; the operator's eyes are
a context window too, and a zero-width-laden commit message rendered inside the approval
screen is that attack with a shorter path. Content that fails the scan is rendered as an
escaped hex dump with a banner, never suppressed — suppression would hide the attempt.

## Operator actions as evidence

Five actions. Each writes exactly one record, and the record is the action: the merge
authorization is emitted only after the evidence row is appended (evidence-write-as-
commit-point).

**Record type `operator_action`**, carrying the run record stream's common envelope —
`schema_version`, `event_id`, `org_id`, `project_id`, `task_id`, `attempt_id`,
`trace_id`, `span_id`, `caused_by`, `emitted_at`, `monotonic_ns` — plus:

| Field | Type | Notes |
|---|---|---|
| `actor_kind` | enum | `operator`. Closed set today; the field exists so that a second actor kind is not a schema change. |
| `actor_id` | str | Constant on a single-operator machine. Present anyway — adding it later changes the digest of every prior record with no marker distinguishing old shape from new, which is the D48 stamp lesson recurring inside the same class of mistake. |
| `field_set_version` | int | The version of *this* field set, separate from `schema_version`. Same reason. |
| `action` | enum | `approve` · `decline` · `request_changes` · `waive` · `escalate_to_self` · `reopen` · `heldout_read` |
| `verdict_ref` | uuid7 \| null | The verdict row the decision is *about*. Null on `escalate_to_self`, `reopen`, `heldout_read`. |
| `as_of_chain_head` | str | The chain head the rendered page was built from. See *Optimistic concurrency*. |
| `decision_basis` | object | `bundle_viewed`, `diff_summary_viewed`, `full_diff_opened`, `run_record_opened`, `heldout_read_refs: [str]` — all **harness-observed from request logs**, never operator-reported. |
| `timing` | object | See *Review timing capture*. |
| `rationale_sha256` | str \| null | Artifact reference to the rationale text, recorded raw. |
| `waiver_adr_ref` | str \| null | Required and non-null when `action = waive`. |
| `idempotency_key` | str | I5. A double-submitted approval appends nothing twice. |

**An approve is not a verdict.** The record authorizes merge *given* a verdict that
already exists and was computed by `CriterionRunner`. The operator never writes, edits or
supplies a verdict field, and the surface holds no grant that would let it.

**What distinguishes an operator action from a harness action in the chain.** Three
things, independently:

1. **`record_type`** — `operator_action` is its own type, and ACS-1 domain-separates the
   hash by `record_type`, so an operator row cannot be replayed as a harness row.
2. **The writing process and its role** — the command surface, running as `alfred-svc`
   under `alfred_operator`, whose only INSERT grant anywhere is on the operator-action
   evidence table. The harness cannot write `operator_action` rows and the command
   surface cannot write anything else.
3. **`actor_kind` / `actor_id`** on the row itself.

The chain writer remains singular. The command surface does not append to the chain
directly; it submits the record to the one serialized chain writer, which is why a
forked chain remains impossible. If the chain head cannot be read, the action is refused
outright — fail-closed, per Failure Semantics.

**Corrections are compensating records.** There is no edit and no delete. A withdrawn
approval is a `reopen` referencing the approval's `event_id` via `caused_by`. The chain
records that the operator changed their mind, which is itself evidence.

**Waivers.** `waive` is the only path by which a task merges without every Definition-of-
Done condition green, and it requires `waiver_adr_ref` resolving to a committed immutable
ADR carrying gate, threshold, actual value, reason and reversal condition (D28). The
endpoint refuses on an unresolvable reference. Waiver count is a health metric, queried
from these rows.

**Optimistic concurrency.** Every rendered page carries the chain head it was built
from. An action posted with a stale `as_of_chain_head` for that task is refused with the
refreshed page. Approving a bundle that changed underneath you is exactly the failure the
whole evidence discipline exists to prevent, and the fix costs one field.

## Review timing capture

`task_end.human_review_ms` is already specified as *recorded from the review interaction,
not estimated*. This section is that instrument.

**The naive measurement is wrong and the wrongness is not small.** Wall clock from first
open to decision includes lunch. On a single-operator machine where the queue is opened
in a tab and left there, tab-open time exceeds attended time by an order of magnitude,
and the capacity gate reading it would conclude that twenty tasks consume a week.

### Two numbers, both recorded, never conflated

| Field | Definition | Feeds |
|---|---|---|
| `attended_ms` | Sum of **attended intervals** across all mission-control screens for this task. | The capacity ledger. |
| `elapsed_ms` | First render of any screen for this task to the terminal action. | Review latency, backpressure, queue-age policy. |
| `interval_count` | Number of attended intervals. | Interruption cost — a 12-minute review in nine sittings is not a 12-minute review. |
| `idle_timeout_ms` | The threshold in force. | Recorded so the number can be reinterpreted later without re-running anything. |
| `per_surface_ms` | `queue` · `review` · `full_diff` · `escalation` · `run_record`. | The ledger's separate lines for review versus escalation, and D22's own falsification. |
| `timing_source` | `heartbeat` · `navigation_only` | See below. |

An **attended interval** opens on the first heartbeat from a mission-control page and
closes when two consecutive heartbeats are missed. Heartbeats are emitted every 15 s by
an inline script — no dependency, no build step — and **only while the page is both
visible and focused**. Default idle timeout is 45 s, recorded per action rather than
assumed by the reader.

**At most one interval is open across the whole surface.** A heartbeat from any page
closes the interval belonging to any other. Without this rule, three open tabs triple
the ledger's input, and the gate that reads it fails in the safe-looking direction of
declaring more capacity consumed than exists.

**If the script does not run, the number is null, not zero.** `timing_source:
navigation_only` reconstructs intervals from page-request timestamps alone, which cannot
see a long read with no navigation. Those tasks are recorded with `attended_ms: null` and
**excluded from the ledger**, reported separately as instrumentation coverage. Zero is a
claim; null is the truth. This is the three-valued-verdict rule applied to a measurement:
a thing that was not measured and a thing measured at zero are different outcomes.

### What this number is, stated honestly

`attended_ms` is a **bounded proxy for attention, not a measurement of it**, and the two
error directions are named rather than hidden:

- **Overcounts** when the page is focused and the operator is not — staring out of the
  window, thinking about something else, on a phone call.
- **Undercounts** when review happens away from the page — reading a printed diff,
  thinking in the shower, discussing the criterion with someone.

The capacity gate therefore reads the **distribution** of `attended_ms` across tasks, and
the ledger states the bias direction. A gate calibrated on a point estimate of a proxy is
the same error as a merge rate reported as a bare point estimate, which this project has
already corrected once.

No start button, no stop button, no confirmation dialog. An operator who can influence
the number being used to gate their own capacity is measuring themselves, which is the
structure D5 exists to forbid, pointed at the human instead of the agent.

## What the surface must refuse to do

Enforceable rules, each with the mechanism that enforces it. None of these is a UI
affordance that is merely absent.

| # | Rule | Enforced by |
|---|---|---|
| R1 | **No verdict write, ever.** | `alfred_operator` holds no grant on any verdict table; the command surface has no import path to the verdict module; both are CI-linted alongside D39's existing check. |
| R2 | **No approve without the criterion having executed.** The approve endpoint requires a verdict row with every criterion recorded as executed and passed, including the held-out class label. Absent or incomplete → 409, and **no record is written**, because a refused action is not an action. | Endpoint precondition, queried by the command surface from its own role. |
| R3 | **`indeterminate` never becomes `pass` through this surface.** The only path is a fresh criterion execution producing a new verdict row; both outcomes remain in the chain. The surface renders `indeterminate` as a third state and offers no approve control on it. | Failure Semantics; R1's grant; the state is not approvable by construction. |
| R4 | **No action the chain does not record.** If the evidence append fails or the chain head is unreadable, the action is refused and no side effect is emitted. | Evidence-write-as-commit-point; fail-closed table. |
| R5 | **No bulk actions and no multi-select.** One task, one decision, one record. | No endpoint accepts more than one `task_id`. |
| R6 | **No editing of policy, thresholds, protected paths, criteria, held-out values, prompts or the graph definition.** All are rendered read-only. Changing them requires the service account and a pull request. | I13, the permission model, D20. The endpoints do not exist. |
| R7 | **No unmarked rendering of untrusted content.** A10 scan before render on everything not harness-authored. | Same scanner as the pre-review gate, invoked in the template layer; CI asserts no template path renders un-scanned external text. |
| R8 | **No held-out content inline.** A held-out read is a separate action, logged, marking the task. | The read model holds no grant on the `heldout` schema at all; only `alfred_criterion` does. |
| R9 | **No dispatch, no cancel, no retry-with-different-criterion.** The surface returns work to the queue (`reopen`) or takes it off the queue (`escalate_to_self`). It does not run anything. | No endpoint. |

R2 deserves one more sentence, because it is where the pressure will land: **approving
over a red criterion is not an approval, it is a waiver**, it requires an ADR, and the
surface routes it there rather than making it a checkbox. That is D28's control aimed at
exactly the moment it was designed for.

## The read model

Views over the evidence store, and nothing else.

- **Every screen is a query executed at request time.** No denormalized dashboard table,
  no materialized view, no application-level cache, no background refresh job. This is
  the run-instrumentation rule — *derived aggregates are computed at read time; storing
  one creates a second source of truth that can disagree with the first* — applied to the
  surface that would be the most tempting place to break it.
- **A cache is a source of truth with a shorter memory.** If a query is too slow, the fix
  is an index or a narrower query. It is never a stored aggregate.
- **The read model cannot write.** `alfred_readmodel` holds SELECT and nothing else, on
  every schema, with no grant at all on `heldout`. Its inability to become a source of
  truth is a database fact rather than a code review outcome — which matters precisely
  because agents may build this half.
- **Pages are `Cache-Control: no-store`.** A browser-cached approval screen showing a
  superseded verdict is the same failure one layer out.
- **Every page states the chain head it was built from**, visible and posted back with
  any action (see *Optimistic concurrency*).
- **Nothing on any screen is stored back.** Sort order, filters, read/unread state,
  annotations — none of it. Persisting UI state would create operator-authored data
  outside the chain, and the moment it influences a decision it is unrecorded evidence.

## Authentication and exposure

Single operator, single machine. The honest statement, neither over- nor under-built:

**Required.**

- **Loopback bind only** — `127.0.0.1`. Asserted at startup; the process refuses to start
  bound to any other interface. This is the actual access control.
- **`Host` header allowlist** — `127.0.0.1:<port>` and `localhost:<port>` only, refusing
  anything else. Without it, DNS rebinding turns any web page the operator visits into a
  client of this service, and the loopback bind buys nothing.
- **`Origin` check plus a per-render form token** derived from a process-startup secret.
  A loopback bind does not stop a page in the operator's browser from POSTing to it. This
  is the one control that a single-user machine does not give away for free, and it is
  the reason "no auth needed" would be wrong.

**Not required, and stating why matters as much as the control.**

- No password, no session store, no user table, no TLS. On a single-user machine the OS
  login *is* the authentication boundary, and a password on a loopback service protects
  against nothing a local process could not bypass by reading the same database.

**The residual, named.** Any local process running as the operator can authorize a merge
through this surface. That is a real exposure and it is accepted, because a compromised
host is already out of scope in the threat model and every control here would fall to the
same adversary. It is written down rather than implied.

**What changes if the surface is ever reachable off-host** — the trigger being a second
operator, or review from a machine that is not this one:

- `actor_id` stops being constant and becomes load-bearing; it is present now for exactly
  this reason, so the change is a behaviour change and not a hash-breaking schema change.
- Real authentication with a per-action identity, TLS, rate limiting, and an audit of the
  read model's query surface against a hostile client rather than a trusted one.
- The residual above stops being acceptable, because "the person at the machine" stops
  being a meaningful identity.

## Deliberately deferred

| Deferred | Pull-forward trigger |
|---|---|
| Charts and trend views | The golden set reaches the size where effect sizes are read routinely (Phase 2 exit, ~150 tasks per D29). Before that a trend line over n=20 is decoration that invites a wrong conclusion. |
| Live in-flight run observability | The first task whose wall-clock exceeds its budget by a margin an operator would have interrupted, *and* an interruption path exists. Until interruption is possible, watching is not observability, it is anxiety. |
| Drain mode and backpressure **controls** (depth is displayed from Phase 1) | Phase 3, where dispatch outruns review and the ceiling becomes operative. |
| Autonomy grant administration | Phase 4, the first grant. |
| Policy, threshold and criterion editing | Permanently deferred for anything in the protected set. For the rest: a measured configuration-change cadence above weekly, and even then it is a pull request, not a form. |
| Agent chat | Not deferred — **refused**. There is no counterparty worth a channel, and an agent that can address the reviewer can argue with its judge. |
| Notifications | Review latency measured above the backpressure ceiling. |
| Multi-user and authentication | The surface becomes reachable off-host, or a second operator exists. |
| A graph **editor** | See below. |

## Part B — the graph and loop viewer

### Why the editor is not first

A graph editor is premature for a reason stronger than "Phase 1 has one path", though
that is true and sufficient on its own: a linear pipeline is a DAG with one path, and a
visual editor for one path edits nothing.

The stronger reason is that **the graph definition is inspector configuration**. It
declares field ownership, which node writes which field, and where the verdict node sits
— the three things D16, D17 and D39 exist to protect, enforced today by a CI lint over
return annotations and the import graph. A GUI that writes the graph definition creates a
second authoring path that routes around that lint, and it does so for the one artifact
where a plausible-looking edit ("move this field's writer") silently disables a control.
Graph changes stay in code, in a pull request, under the lint.

*Revisit trigger:* the graph carries two or more real branch points **and** graph changes
land more often than weekly. Both, not either — branching alone does not justify a
second authoring path.

### Why the viewer earns its place immediately

Half of Phase 1's exit is a written failure taxonomy derived from observed attempts. A
taxonomy is read off trajectories: where the loop iterated, against what progress
measure, where it stalled, where escalation fired and what else was simultaneously true.
Reading that from a JSONL stream is possible and it is how it will be done wrong.

### What it renders

Per attempt, one diagram plus one series:

- **The traversal** — the node path taken in emission order, each node marked agent or
  deterministic, with the fields it wrote attached to it. Node structure and declared
  `reads`/`writes` come from the graph definition; the path comes from the record stream;
  the field attribution comes from declared ownership joined to `caused_by`.
- **Loop iterations** — each cycle rendered as a repeated column, carrying its
  `assertions_passing`, `delta`, and `tree_sha256`. Stalls (`delta = 0` with a changed
  tree) and regressions (`delta < 0`) are marked distinctly, because a run that regresses
  and recovers is a different trajectory from one that climbs, and only one of them is
  evidence of goal seeking. `collection_errors` is shown beside `assertions_passing` and
  never subtracted into it.
- **The loop contract's state** — `max_iterations`, iterations consumed, and the budget
  dimensions at the terminal node.
- **Escalation** — where it fired, with `primary_cause` **and** the full `also_satisfied`
  set rendered together. A viewer that shows only the primary cause reproduces, visually,
  the exact corruption the record schema went out of its way to prevent.
- **`premature`** placement, when set, on the node where the attempt ended.

### Sources, and why drift is impossible

Two inputs, both immutable for a given attempt:

1. the **graph definition** resolved at the run's pinned orchestrator commit and
   `fingerprint_sha256`, and
2. the **run record stream** for that attempt, which is append-only and hash-chained.

The rendering is therefore a pure function of two immutable inputs. **It is never
stored** — generated at request time, as inline SVG produced server-side with no client
library and no build step. The same URL renders identically forever, and there is no
artifact that can go stale, which is what puts it in the register's generated category
rather than its prose one.

If the graph definition for that run's commit cannot be resolved, the viewer renders the
traversal **without** the structure and says so on the page. It never falls back to
today's graph definition. A diagram silently drawn against the wrong structure is the
drift hazard the generated category exists to eliminate, arriving through the back door.

This viewer is a rendering, not a document. Its structural source is the State and Graph
Specification and its trajectory source is the Run Instrumentation Specification; it adds
no register entry of its own.

## Consequences for other documents

- **Run Instrumentation Specification** — **applied 2026-08-15.** `record_type` gained
  `operator_action` and the envelope gained `actor_kind` and `actor_id`.
  `field_set_version` sits on `operator_action` only, not on the envelope: it versions
  *this* document's field set, which changes on this surface's schedule rather than the
  instrumentation document's, and a second version field on every harness record would
  version nothing. That document owns the envelope, the `record_type` value and the writer
  rule; this document owns the operator-action fields themselves.
  `task_end.human_review_ms` is superseded by the `timing` object specified here, with
  `attended_ms` as the ledger's input and `human_review_ms` retained as a projection —
  `attended_ms` where non-null, null otherwise, never 0.
- **Data Architecture** — two roles added: `alfred_operator` (INSERT on operator-action
  evidence only) and `alfred_readmodel` (SELECT only, everywhere, none on `heldout`).
- **Permission and Identity Model** — the command surface is a new identity; the read
  model is a new identity; the operator's authority to approve is distinct from the
  operator's inability to write `harness/`.
- **Human-in-the-Loop Policy** — owns the *policy*; this document owns the *surface*. Its
  `review_after: Phase 3` does not survive: Phase 1 is where its evidence is produced.
- **Definition of Done** — condition 11 ("human review complete, criterion-first") gains
  its mechanism: complete means an `operator_action` row exists with `action = approve`
  and a non-null `verdict_ref`.
- **Autonomy Boundaries** — the command surface joins the permanently protected set.

## Enforcement

The `enforcement: schema` claim is discharged by the four mechanisms below. **None of them
exists yet, and the repository has no CI configuration at all** — so today this claim is a
commitment with a named build gate, not a running control. Each mechanism is green before
the first Phase 1 task dispatches; that ordering is the enforcement until then.

- **The run-record validator, group L7** (Run Instrumentation Specification § Enforcement,
  where it is specified in full and its unbuilt status is recorded): closed enumerations,
  `waiver_adr_ref` non-null iff `waive`, `verdict_ref` non-null on `approve` and `decline`,
  referential integrity of `caused_by` on `reopen`, and timing objects that are internally
  consistent (`attended_ms ≤ elapsed_ms`, `attended_ms` null iff
  `timing_source = navigation_only`). Validation at the write boundary — Pydantic models in
  `harness/mission_control/` — rejects a malformed record before it is written; the
  validator is the independent check that they did. Both, not either: the write-boundary
  check is authored by the same process it constrains, and the validator runs under D20
  protection where an agent cannot reach it.
- SQL grant assertions in the seeded-defect suite, as negative tests, in the same shape as
  the existing held-out negative test: `alfred_operator` must **fail** on any verdict-table
  write; `alfred_readmodel` must **fail** on any INSERT anywhere and on any SELECT against
  `heldout`.
- The D39 import-graph lint extended to the two mission-control modules.
- An instrument-verification suite in the shape the Run Instrumentation Specification
  requires, since a timing instrument that passes on its first run is also what a vacuous
  instrument reports: a scripted browser session that opens a review, idles past the
  timeout, returns, and approves **must** produce two intervals and an `attended_ms`
  materially below `elapsed_ms`. A run with the heartbeat script disabled **must** produce
  `attended_ms: null`, never `0`. An approval attempted against a `fail` verdict **must**
  produce no evidence row at all.
