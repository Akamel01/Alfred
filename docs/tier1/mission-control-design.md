---
status:        provisional
owner:         executable
enforcement:   ci-gate
evidence:      No review has happened, so nothing here rests on an observed one. What it does rest on is arithmetic over the plan's own stated numbers (20+ hrs/week capacity, ~20 tasks over ~3 weeks in Phase 1) and on the mechanical properties of the stack the surface is already committed to: server-rendered HTML has no client state to corrupt, a full-page navigation is observable server-side where a CSS toggle is not, and a monotonic clock read at request receipt cannot be moved by the client. Each friction decision below is stated as a claim with the observation that would refute it.
falsifies_if:  The full diff is opened on a majority of Phase 1 tasks carrying no anomaly flag; or the approve form is reachable on a page whose verdict is not `pass`; or a review page cannot be decided on with the read model dark; or a Phase 1 review produces an `attended_ms` corrupted by a failure mode this document did not name.
review_after:  Phase 1
---

# Mission Control Design

The Mission Control Specification says what the surface must do and refuse. This says how
it is built: what is on which page, what is one navigation away, what is deliberately
expensive to reach, and what the timing instrument does when the machine misbehaves.

It designs, and does not implement. Signatures and form shapes appear where they are the
shortest way to state a decision.

## The one thing this document is for

D22 claims a human adds something the harness cannot, and that the something is *not*
reading the diff. That claim has a failure mode with no error message: the operator opens
the diff, reads it carefully, feels productive, and duplicates work the harness already
did — at the cost of the one resource the whole factory is rate-limited by. Nothing
alarms. The verdicts stay green. The capacity ledger fills up with numbers that are real
measurements of the wrong activity.

Every design decision below is downstream of one question: **what is expensive to reach,
and is the expense recorded?** A surface that answers only "what is shown" has not been
designed, it has been listed.

## What review time may cost — derived, with the assumptions named

Nobody has told this design what review time it must achieve. The capacity ledger
(major-fix #10) is `per-task human minutes × tasks/day + fixed weekly obligations ≤
capacity`, and of its four terms exactly one is stated anywhere: capacity, at **20+
hrs/week = 1200 min/week**. The per-task term is what Phase 1 exists to measure. Tasks
per day and fixed weekly obligations have never been written down.

The gate is therefore **unfalsifiable today**, for the same reason and in the same shape
as D42's kill criterion before it got a date. It is bounded from below, though, and the
bound is informative. Writing `C` = 1200, `F` = fixed weekly minutes, `n` = tasks/day,
`m` = per-task human minutes across authorship, review and escalation:

```
5·n·m + F ≤ C
```

Assuming `F` = 300 min/week (demand track, taxonomy writing, ADRs, maintenance — a guess,
and the number this design most wants supplied):

| `n` (tasks/day) | tasks/week | `m` budget, all three activities |
|---|---|---|
| 1 | 5 | 180 min |
| 2 | 10 | 90 min |
| 3 | 15 | 60 min |
| 5 | 25 | 36 min |
| 10 | 50 | 18 min |

Criterion authorship for a Phase 1 task — assertion, interface signature, threshold
provenance, two grading points with one held out and its provenance tier recorded — is
not plausibly under 25 minutes, and escalation handling amortized at a 20% escalation
rate over 40 minutes adds ~8. Subtracting those 33 minutes of non-review work leaves the
review budget `r`:

| `n` | `r` budget |
|---|---|
| 1 | ~147 min |
| 2 | ~57 min |
| 3 | ~27 min |
| 5 | ~3 min — infeasible |

**Two findings fall out, both worth more than the surface design they were computed for.**

1. **At 20 hrs/week the ledger caps out near 2–3 tasks/day, and the binding term is
   criterion authorship, not review.** Making review instant does not lift the ceiling.
   Phase 2's parameterized criterion families are the throughput lever; the review
   surface is not.
2. **The review design target is nevertheless real: ≤ ~25–30 minutes attended per task.**
   A criterion-first review of a green bundle fits inside that with room. A full-diff read
   of a multi-file change does not — a 45–60 minute review alone consumes the whole budget
   at `n` = 2 and makes `n` = 3 impossible. So the friction decisions below are not
   aesthetic preferences. **Opening the diff by default costs roughly a factor of two on
   the achievable task rate**, and it does so invisibly.

All five inputs above except `C` are stated assumptions. What is needed to replace them is
in *Open inputs* at the end.

## S2 — the evidence bundle

### The reachability ladder

D22's ordering is a claim about cost. The design makes cost mechanical: **each step down
the ladder is a full page navigation to a distinct URL**, never a CSS toggle, an accordion,
or a `<details>` element.

| Depth | Content | Cost |
|---|---|---|
| 0 | Zones 1–4: intent, criterion, verdict and evidence bundle, diff **summary** | The page |
| 1 | Full diff | One navigation, recorded |
| 1 | Targeted diff of a flagged file only | One navigation, recorded separately |
| 1 | Run record (S4) | One navigation, recorded |
| 2 | Raw content channel, by hash, labelled untrusted | Two navigations from S2 |
| 2 | Held-out read | Two navigations, its own confirmation, its own evidence row |

**Why navigation rather than disclosure.** A `<details>` toggle is free, silent and
invisible to the server — which means `full_diff_opened` could not be recorded without
client-side JavaScript reporting it, and a metric reported by the client is a metric the
measured party controls. A navigation is observable in the command surface's own request
log, costs a page repaint, and loses the reading position. All three are the point. The
recording requirement and the friction requirement have the same mechanical answer, which
is a good sign the answer is right.

**How the open is recorded without a GET that writes.** No `GET` appends to the hash
chain. The command surface keeps an append-only `operator_request_log` (its own table, in
the operator-action schema, the only place its role holds INSERT). `decision_basis` is
**computed at decision time** by querying that log for this task over the review window —
never accumulated in a session, never reported by the page. This satisfies the
specification's read-time-derivation rule and its "harness-observed from request logs"
requirement with one mechanism.

The log is append-only but **not hash-chained**: heartbeats arrive every 15 s and chaining
them would swamp the chain with rows nobody will ever read. The chained artifact is the
`operator_action` row, which carries the derived `decision_basis` and `timing` objects
plus `interaction_log_sha256`, a hash over the exact log slice they were derived from.
That gives tamper evidence over the derivation input at one row per decision instead of
hundreds.

**Prefetch is a real hazard and is handled.** A browser that speculatively fetches the
diff link would record an open nobody performed, and the falsified metric would be D51's
own. Three mitigations: pages are already `Cache-Control: no-store`; no link anywhere
carries `rel=prefetch`, `rel=prerender` or `rel=next`; and a request arriving with
`Sec-Purpose: prefetch` is answered `204` and **not logged**.

### The diff link is conditional, not constant

Constant friction gets routed around; it becomes a reflex within a week. Friction that
varies with signal is the actual policy D22 states, so the link varies with signal.

**No anomaly flag set.** The link is rendered in body text, unemphasized, and its label
states what would be duplicated:

> Open full diff — 14 assertions executed and passed, 3 composed properties passed,
> held-out `pass`, static gates green, no anomaly flags. Opening this is recorded.

**Any anomaly flag set.** The link is promoted above the diff summary, names the flags,
and is the visually dominant control on the page. When `premature`, a test-file edit, a
tolerance change, a protected-path attempt or a judge-raised escalation is present, the
diff is the right next step and the surface says so.

This is the correct asymmetry and it is the whole of D22 in one control: **reading the
diff is not discouraged, it is conditioned.** The falsification metric measures whether
the condition is what actually drives it.

### Zone 4 has no per-file diff links, with one exception

Twelve per-file links are the diff-by-default failure arriving as twelve small clicks,
none of which is "the full diff" and none of which trips the metric. Zone 4 therefore
renders file paths, line counts and the per-file classification (source · test ·
criterion-adjacent · configuration · documentation) as **text, not links**.

The exception is exact: files classified `test` or `criterion-adjacent`, and any file
carrying a tolerance change, are linked. Those are the reward-hacking shapes the
specification names as the reason to open a diff at all, so the only diff that is cheap
to reach is the diff of the thing that is suspicious.

Targeted opens are recorded as `targeted_diff_opened: [classification]`, a **separate**
field from `full_diff_opened`. D51's falsification metric reads `full_diff_opened` only.
Folding targeted opens into it would make a reviewer doing exactly the right thing look
like a reviewer who has abandoned criterion-first review.

### Zone 4's anomaly flags are command-surface facts, not read-model output

The specification puts diff summaries in the read model and anomaly flags in the
command-surface-rendered Zone 3. Test-file edits and tolerance changes appear in both
lists. The rule *"the read model may not be the source of any fact an action depends on"*
settles it: **the flags are command-surface-rendered, in Zone 3, and are authoritative.**
The read model supplies the cosmetic file list, hunks and syntax rendering only. An
agent-authored view that omits a test-file edit from its summary changes nothing, because
the flag it would have to suppress is not its to render.

### Zones 1 and 2 must fit on one screen — and if they do not, that is a finding

Intent is a work item in the author's words plus the criterion's purpose sentence.
Criterion is an assertion, an interface signature, threshold provenance, and the grading
points with their tiers. **If those do not fit above the fold at default browser type
size, the task's specification is too complicated to review**, and that is a
task-specification defect surfaced by the layout rather than a layout problem. The
schedulability rule already refuses tasks with no enumerable assertion set; this is the
same idea applied to what a human can hold at once.

Deliberately **not** done: no forced scroll, no "confirm you have read the criterion"
checkbox, no minimum dwell before the actions render. Each is an affordance the operator
can defeat, each trains a reflex, and a dwell gate directly corrupts `attended_ms` by
paying the operator to leave the page open. An instrument and a gate must not be the same
control.

### The three-valued verdict is three page layouts, not three badge colours

A badge is learned in a day and then read instead of the page. The three verdicts are
therefore **three distinct templates**, and the difference is structural.

**`pass`.** Zone 3 renders the twelve Definition-of-Done conditions as recorded facts, the
held-out class label, property and static results, the fingerprint. The approve form is
present.

**`fail`.** Zone 3 leads with which criterion failed and what it asserted. No approve form
exists. `decline`, `request_changes` and `waive` forms are present; `waive` requires
`waiver_adr_ref` and the field is not optional in the form.

**`indeterminate`.** Zone 3 renders **no verdict summary and no green anywhere**. It
renders which criterion did not execute to completion and the fail-closed condition that
fired, and every other condition is rendered as **`not established`** — not as passed, not
as failed, not greyed-out-but-legible-as-green. The reason is not presentation: when
`CriterionRunner` crashed mid-execution, the conditions it did report are also not
established, because a partially-executed criterion set has no meaning. The page's
literal reading is *nothing was learned*, which is what the verdict means.

Only `reopen` is offered. Not approve. **Not waive either** — and this is an addition to
the specification's refusal table, argued rather than assumed:

> **Proposed R10 — `waive` is available on `fail` only.** A waiver ADR records gate,
> threshold, **actual value**, reason and reversal condition (D28). On an `indeterminate`
> there is no actual value: the gate did not run. Waiving a control that did not execute
> is precisely the fail-open that Failure Semantics exists to forbid, wearing the
> paperwork of a control that did. The `waive` form is absent from the `indeterminate`
> template and the endpoint refuses when the referenced verdict is not `fail`.

### `indeterminate` cannot become `pass`, by three independent mechanisms

Structural, not discouraged. Any one of these failing leaves the other two.

1. **The approve form does not exist in the response body** on a non-`pass` verdict. It is
   absent, not disabled — a disabled control is one DOM edit away, and a browser console
   is not a threat model, it is Tuesday. Mechanically: `action/approve` appears in exactly
   one template, `_verdict_pass.html`, and CI asserts that count is one.
2. **The endpoint refuses.** `POST /action/approve` re-queries the verdict through the
   command surface's own role and returns `409` unless the verdict is `pass` with every
   criterion recorded executed, including the held-out class label. **No record is
   written** — a refused action is not an action. A hand-crafted POST fails here.
3. **No endpoint accepts a verdict as input, anywhere.** The only route from
   `indeterminate` to `pass` is `reopen` → fresh dispatch → fresh `CriterionRunner`
   execution → a new verdict row, with both outcomes permanently in the chain.

### Held-out reads live off the decision path

A held-out read is reachable from S2 and S4 only as a link to its own route, which renders
a confirmation form, which POSTs. The two-step is the one place in this design where a
confirmation step is correct, because the action is rare, irreversible in the record, and
marks the task permanently.

It is also not a query. `alfred_operator` holds no grant on `heldout` and neither does
`alfred_readmodel`; only `alfred_criterion` does. So `heldout_read` is a **mediated
request** — the command surface appends its evidence row, then asks the criterion process
to materialize the content for one render. The mediation is what makes the evidence row
unavoidable: there is no path to the bytes that does not go through the writer of the row.

## S1 — Queue

Two lanes, age-ordered oldest first, not reorderable. One row per task: id, one-line
intent, lane, verdict or escalation cause, age, attempt count, anomaly flags. Backlog
depth per lane. No preview, no inline diff, no multi-select, no bulk action.

Three design decisions the specification leaves open:

**Anomaly flags render in a fixed column, with `—` when empty.** A flag list that appears
only when non-empty makes "no flags set" and "flags not computed" look identical on the
page. That is the three-valued rule applied to a queue cell, and it costs one character.

**No colour-coded urgency on age.** Colouring rows by age is a priority system the
operator did not choose, cannot audit, and will follow. Age is a number in a column; the
ordering already encodes the policy.

**No read/unread state, and none is needed.** The specification forbids storing UI state,
and the queue does not want it: a task opened but not decided is still in the queue at its
age position, and rows leave only on a terminal action. The work list is the state.

**No auto-refresh and no polling.** Nothing on this surface changes under the operator's
hands. A queue that re-sorts between reading a row and clicking it is the same hazard
`as_of_chain_head` exists to catch, one layer out. Refresh is a link to the page, and the
page states its render time and chain head.

## S3 — Escalation

Renders, in order: intent; criterion; the escalation trigger set; budget consumption per
dimension; the progress trace; the attempt bundle by artifact hash.

**The trigger set is one list, not a headline and a footnote.** `primary_cause` and
`also_satisfied` are rendered as a single unordered set with the primary marked, never as
"primary: X *(also: Y, Z)*" in smaller type. The record schema went out of its way to
prevent the escalation-cause distribution becoming a report on trigger evaluation order;
subordinating `also_satisfied` visually reproduces that corruption inside the operator's
head, where no linter can reach it.

**`reopen` is the primary control and `escalate_to_self` is not.** Taking the work
yourself silently converts factory throughput into operator throughput, which is the one
resource the capacity ledger says is binding — and it is the action that will feel most
natural at six in the evening. The button order is a capacity decision, so it is argued
rather than defaulted.

**`escalate_to_self` requires a rationale** (`rationale_sha256` non-null). It is the
action most likely to carry a Phase 1 taxonomy entry that nothing else will record, and
it is rare enough that the cost is nil. Proposed as an addition to the action table.

## S4 — Run record

Per attempt: turn and tool-call trajectory, the progress series, the graph and loop
rendering, the read log, `fingerprint_sha256` asserted at both ends, the
`agent_ms`/`criterion_ms`/`harness_ms` split, and the raw content channel by hash behind a
click, labelled agent-authored and untrusted.

**No actions on this screen**, as specified — the held-out read is a link to its own route,
not a control here, which is what preserves that property.

The progress series renders as **a table first and a small SVG second, with the table
authoritative**. At six to twelve observations a sparkline is decoration that invites a
wrong conclusion, and this project has already written that sentence once about trend
lines at n=20. The numbers are the artifact; the picture is a convenience.

## Part B — the graph and loop viewer

### Rendering technology: server-generated inline SVG, emitted from Python, no library

Argued against the alternatives rather than asserted.

**Client-side (Mermaid, d3, Cytoscape).** Refused. D51 commits to no JavaScript
dependency closure to hash-lock, and the Supply Chain Policy's pinning machinery — full
transitive closure resolved by `uv`, hash-pinned, closure hash a fingerprint field — has
no JS equivalent. A vendored blob is worse, not better: it is an unpinned closure with the
audit trail removed.

**Graphviz.** Refused, and the reason is decisive and specific to this artifact. The
specification's central claim about the viewer is that it is a pure function of two
immutable inputs, so *the same URL renders identically forever*. Graphviz is a layout
engine whose output changes across versions, which makes the rendering a function of three
inputs, the third being a native binary nobody pinned. Either the graphviz version becomes
a fingerprint field — absurd for a viewer — or the immutability claim is false.

**Force-directed or any stochastic layout.** Refused for the same reason at one remove: a
diagram that moves between renders is not a stable artifact, and stability is what the
generated category buys.

**Chosen:** deterministic layered layout computed in Python and emitted as SVG text.
Phase 1's graph is a single linear path; the general case is a DAG whose node set comes
from the graph definition. Layers are assigned by emission order, loop iterations are
repeated columns, and the layout function is pure and seeded by nothing. No client
library, no build step, no second toolchain — D13 unchanged.

Accessibility and print are covered by `<title>`/`<desc>` on every node plus the plain-text
traversal below, not by a JS accessibility shim.

### The plain-text traversal, and why the viewer needs a check

The read model is factory: agents may build the viewer. The viewer is where half of Phase
1's exit — a written failure taxonomy — is actually read. Those two facts together are
uncomfortable, even though the viewer drives no action and therefore does not violate the
specification's rule.

The resolution is cheap: `GET /run/{attempt_id}/traversal.txt` on the **command surface**
emits a deliberately ugly plain-text rendering of the same traversal, loop iterations and
escalation trigger set, from the same two inputs. Any claim read off the diagram can be
checked against a harness-authored rendering in one navigation. Agents keep the pretty
thing; the taxonomy keeps a witness.

Both renderings state the two input hashes (`fingerprint_sha256` and the run-record chain
segment hash) on the page. If the graph definition at that run's pinned commit cannot be
resolved, both render the traversal **without** structure and say so, and neither ever
falls back to today's graph definition.

## Composition: the browser talks to one origin

Two processes, two ports, one of them browser-facing.

**The browser loads pages from the command surface only.** The command surface
server-side fetches HTML fragments from the read model over loopback and splices them into
a page whose decision-critical zones it rendered itself. The read model is a subordinate
service, never a peer the browser trusts.

The alternatives were considered and are worse. Two separate origins the operator
navigates between means the decision happens on whichever page they are looking at, which
is exactly the failure the split exists to prevent. An iframe or client-side fetch of the
read model requires JavaScript, cross-origin plumbing, and gives an agent-built page a
frame inside the approval screen.

**Read-model output is untrusted content, on the same footing as a commit message.**
Agents may build the read model, so its HTML enters the page through the same pipe as
agent prose: A10 scan, then re-serialization through an element and attribute allowlist
that admits no `style` attribute, no `<script>`, no `<style>`, no `<foreignObject>`, no
event-handler attribute, and no `id`/`class` outside a reserved prefix. The named attack
is an **overlay**: an agent-authored fragment that positions itself over the verdict and
renders `fail` as `pass`. The allowlist and a strict CSP (`default-src 'none'; style-src
'self'; img-src 'self'; script-src 'self' 'nonce-…'`) close it; decision-critical zones
render first in DOM order and contain no read-model content at all.

There is exactly one sanitizing template (`_fragment.html`) and one untrusted-content
renderer (`_untrusted.html`), so R7's CI assertion has one path to check.

### The dark-read-model test

This is the structural test of the whole split, and it is worth more than the CI lint:

> **With the read model stopped, every review page must still render its
> decision-critical zones and permit `approve` on a `pass`.**

If it cannot, a fact an action depends on came from the read model and the split has been
violated. Under the test, Zones 4 and 5 render as `unavailable` with a banner and the
decision remains possible — which is D22's claim stated as an executable assertion rather
than a preference. If that reads as unacceptable, D22 is wrong, and discovering that is
worth more than the surface.

Operationally: every read-model fetch carries a hard timeout (750 ms) and a response size
cap, and a timeout degrades the zone rather than the page.

## Route and template inventory

### Command surface — `harness/mission_control/`, inspector, `alfred_operator`, loopback

| Method | Route | Screen / purpose |
|---|---|---|
| GET | `/` | 302 → `/queue` |
| GET | `/queue` | S1 |
| GET | `/review/{task_id}` | S2, zones 1–4 |
| GET | `/review/{task_id}/diff` | Zone 5, full diff — logged |
| GET | `/review/{task_id}/diff/{file_sha256}` | Targeted diff, flagged classifications only — logged |
| GET | `/escalation/{task_id}` | S3 |
| GET | `/run/{attempt_id}` | S4 |
| GET | `/run/{attempt_id}/graph.svg` | Viewer, also inlined into S4; separate URL for linking and print |
| GET | `/run/{attempt_id}/traversal.txt` | Harness-authored plain-text witness |
| GET | `/run/{attempt_id}/content/{sha256}` | Raw content channel — scanned, escaped, labelled |
| GET | `/heldout/{task_id}/request` | Confirmation form |
| POST | `/heldout/{task_id}/read` | Writes `heldout_read`, then renders via `alfred_criterion` |
| POST | `/action/approve` | |
| POST | `/action/decline` | |
| POST | `/action/request-changes` | |
| POST | `/action/waive` | `waiver_adr_ref` required; `fail` verdicts only (R10) |
| POST | `/action/escalate-to-self` | Rationale required |
| POST | `/action/reopen` | `caused_by` the record being compensated, where there is one |
| POST | `/hb` | Heartbeat → `204`, no body |
| GET | `/healthz` | Liveness only, no data |

**Every POST carries** `task_id`, `as_of_chain_head`, `form_token`, `idempotency_key`, and
where applicable `rationale`, `waiver_adr_ref`, `verdict_ref`. Every POST answers with
POST-redirect-GET, so a refresh never resubmits.

### Read model — `src/mission_control/`, factory, `alfred_readmodel`, loopback, not browser-facing

| Method | Route | Returns |
|---|---|---|
| GET | `/frag/queue-rows` | Ordering and navigation for S1 |
| GET | `/frag/diff-summary/{task_id}` | Cosmetic file list and counts |
| GET | `/frag/diff/{task_id}` | Full diff rendering |
| GET | `/frag/diff/{task_id}/{file_sha256}` | Single-file rendering |
| GET | `/frag/run-record/{attempt_id}` | Trajectory rendering |
| GET | `/frag/graph/{attempt_id}` | Viewer SVG |
| GET | `/frag/progress/{attempt_id}` | Progress series SVG |
| GET | `/healthz` | |

No import path exists between the two packages, checked by the D39 import-graph lint.

### Templates

`base.html` · `queue.html` · `review.html` · `diff_full.html` · `diff_file.html` ·
`escalation.html` · `run_record.html` · `heldout_request.html` · `error_409_stale.html` ·
`error_409_precondition.html`

Partials: `_zone_intent` · `_zone_criterion` · `_zone_verdict_pass` ·
`_zone_verdict_fail` · `_zone_verdict_indeterminate` · `_zone_diff_summary` ·
`_anomaly_flags` · `_action_approve` · `_action_decline_or_changes` · `_action_waive` ·
`_action_reopen` · `_action_escalate_self` · `_fragment` · `_untrusted` · `_heartbeat`

Three template-layer CI assertions, each making a refusal rule a filesystem fact:

- `action/approve` appears in exactly one template, and that template is included only
  from the `pass` path.
- `action/waive` appears in exactly one template, included only from the `fail` path.
- No `|safe` and no raw interpolation outside `_fragment` and `_untrusted`, and the
  template environment's autoescape flag is asserted **on** by a test — an environment
  with autoescape quietly off is exactly the silent-failure shape this project keeps
  finding.

### Forms, tokens and idempotency

**Form token.** HMAC over a process-startup secret, the `task_id`, the action, and the
`page_render_id`, embedded as a hidden field. A loopback bind does not stop a page in the
operator's browser from POSTing to this service; same-origin policy stops that page from
*reading* the token. Combined with an `Origin` allowlist, a `Host` allowlist, and a
`Sec-Fetch-Site: same-origin` check — all three cost nothing and fail independently.

**Idempotency key.** Generated **server-side at render time**, unique per rendered form,
carried in the form. Uniqueness is enforced by a `UNIQUE (task_id, idempotency_key)`
constraint on the operator-action table — a database constraint, because application-level
idempotency loses the race it exists to prevent. A resubmission returns the original row's
outcome and appends nothing.

**Optimistic concurrency.** A stale `as_of_chain_head` is answered `409` with the
refreshed page and **no record written**.

### Where a partial update genuinely matters: once

The heartbeat, and nothing else. It is a `POST` returning `204` from an inline script of
roughly thirty lines with no dependency and no build step.

**The queue does not poll and does not auto-refresh** — argued above. **No screen updates
itself.** The design constraint that keeps this honest: **if the inline script exceeds
about fifty lines, it has become an application and the no-build-step property is gone.**
That is a review trigger, not a style rule.

## The review-timing instrument

Two numbers, never conflated: `attended_ms` (sum of attended intervals, feeds the ledger)
and `elapsed_ms` (first render to terminal action, feeds latency and backpressure). Plus
`interval_count`, `idle_timeout_ms`, `per_surface_ms`, `timing_source`.

### Mechanism

An inline script posts a heartbeat every 15 s to `/hb` carrying `task_id`, `surface` and
`page_render_id` — **and no timestamp**. It beats only while the page is both `visible`
and focused. A final beat is sent on `pagehide` via `sendBeacon`, which survives the
navigation that `fetch` would not.

**Every duration is computed server-side from a monotonic clock read at request receipt.**
The client supplies no time at all, which removes the entire clock-skew, DST and NTP-step
class of failure in one move — the same rule the run-record envelope already applies for
the same reason. `emitted_at` wall-clock is recorded for human reading and never used for
arithmetic.

**Intervals are derived at read time from the log, never accumulated client-side.** A
client that accumulates is a client the measured party can edit, and the whole point of
this instrument is that the operator does not report their own number.

**Derivation.** Over the global heartbeat sequence ordered by receipt: an interval is a
maximal run of beats sharing one `(task_id, surface)` with no gap exceeding
`idle_timeout_ms` (default 45 s = three beat periods). A beat for a different task closes
the previous interval at its last beat, which is how *at most one interval is open across
the whole surface* is enforced — enforced on the sequence, not by trusting pages to
report closure.

**An interval's duration is `last_beat − first_beat`.** Never extrapolated. A single
isolated beat contributes **0 ms**: one beat establishes presence at an instant, not
duration.

### The bracket, because never-extrapolating undercounts

Never extrapolating means each interval undercounts by up to one beat period, and
**undercount is the dangerous direction**: it tells the capacity gate there is more
capacity than there is, and the operator drowns. Overcount merely refuses affordable
throughput.

The undercount is bounded and computable, so the honest output is a bracket, not a point:

```
attended_ms        = Σ (last_beat − first_beat)                    # lower bound
attended_ms_upper  = attended_ms + interval_count × heartbeat_period_ms
```

The ledger reads the distribution of the bracket and states its bias direction. This is
the same discipline the plan already applied to merge rate when it replaced a point
estimate with a Wilson interval, pointed at a different measurement.

This requires one field the specification does not yet list: **`heartbeat_period_ms` in the
`timing` object**, without which the bracket cannot be recomputed later. Proposed below.

### Failure modes, designed

| # | Failure | Behaviour | Residual |
|---|---|---|---|
| F1 | **Laptop sleep** | Timers stop, gap exceeds timeout, interval closes at the last pre-sleep beat and a new one opens on wake. `attended_ms` excludes the sleep; `elapsed_ms` includes it, correctly, because it is latency; `interval_count` increments, correctly, because it was an interruption. | A sleep shorter than the timeout counts as attended. Bounded at ≤ 45 s per occurrence, and recoverable later because `idle_timeout_ms` is recorded. |
| F2 | **Browser or tab crash** | The interval closes at the last observed beat. Nothing is extrapolated forward. If the operator never returns, there is no action row and the task has no timing at all — correct: nothing was decided. | Undercount ≤ one beat period, inside the bracket. |
| F3 | **Two windows, same task** | The beats interleave into one maximal run and are **merged**, not summed. Attendance is bounded at 1×. | None. This is the case the specification names and it is closed by deriving over the sequence rather than per window. |
| F4 | **Two windows, different tasks, alternating** | Each switch closes the other interval. Total attended across both approximates true attended time; `interval_count` rises sharply on both. | `interval_count` genuinely reflects thrashing and is left unsmoothed. A twelve-minute review in nine sittings is not a twelve-minute review, and the ledger should see that. |
| F5 | **Tab left open overnight, focused, machine unlocked** | The one case visibility and focus do not catch — beats keep arriving. Closed by an **interaction-idle rule**: each beat carries a boolean for whether any `keydown`, `pointermove`, `scroll` or `wheel` occurred since the previous beat, and four consecutive idle beats (60 s of zero input) close the interval **retroactively at the first idle beat**. Intervals closed this way are marked `idle_closed`. | Reading a short page without touching anything for 60 s undercounts. Visible rather than silent: the fraction of intervals closed by idle rather than focus loss is reported, and a high fraction means the threshold is wrong. It is not tuned silently. **Privacy: the beat carries one boolean. No key identity, no coordinates, no content.** |
| F6 | **Clock change, NTP step, DST** | Impossible by construction: the client sends no time, and all arithmetic is on a server monotonic clock. | None from clocks. See F7 for what monotonic clocks cost instead. |
| F7 | **Command-surface restart mid-review** | A monotonic origin resets on restart, so readings are comparable only within a process epoch. Every log row carries `process_epoch_id`; an interval **never spans epochs** — a restart closes the open one at its last beat. The action records `epoch_boundaries_crossed`. | Truncation of up to one beat period per restart, and it is visible in the record rather than silent. |
| F8 | **Forged or replayed heartbeats** | A beat carries a server-issued `page_render_id` bound to task, surface and form token. Beats with an unknown, superseded, or non-live render id are rejected and not logged. | A page in the operator's own browser cannot inflate a task it never rendered. |
| F9 | **Script never runs** (disabled, blocked, unsupported) | `timing_source: navigation_only`, `attended_ms: null`, task **excluded from the ledger** and reported as instrumentation coverage. Never `0`. | None. Zero is a claim; null is the truth. |
| F10 | **Decision reached in under one beat period** | Zero beats is expected, so `attended_ms` is `null`, not `0` — the same rule as F9, for the same reason. Nothing was measured. | The genuinely instant review is invisible to the ledger. Correct: an unmeasured thing is not a measurement of zero. |
| F11 | **Reviewed, walked away, decided the next morning** | Two intervals; `elapsed_ms` large, `attended_ms` small. | None. This is precisely why the two are separate fields, and the naive instrument would have reported a sixteen-hour review. |
| F12 | **Back-button onto a decided task's page** | Beats for a task carrying a terminal `operator_action` row are rejected with `409` and not logged. The derivation window is `[first render, terminal action]`, closed at decision time. | None. |
| F13 | **Review spans a chain-head change** | The action is refused with `409` and the refreshed page; the accumulated timing is retained and continues, because review time is review time regardless of what moved underneath it. | The refused submission's own seconds are attributed to the eventual decision. Correct. |

### Invariants the linter must hold

- `attended_ms ≤ elapsed_ms`.
- `attended_ms` is `null` **iff** `timing_source = navigation_only`, and never `0`.
- `Σ per_surface_ms = attended_ms` — every interval belongs to exactly one surface, so the
  partition is exact and a mismatch is a derivation bug.
- `interval_count = 0` iff `attended_ms` is `null`.
- No interval spans a `process_epoch_id` boundary.
- **No duration anywhere in this instrument is computed by differencing a harness record's
  `monotonic_ns` against an operator record's.** The readings agree on this platform only
  until a reboot, which nothing in the stream marks. Any span from dispatch to approval
  comes from the `timing` object and `elapsed_ms`, never from cross-actor subtraction.
- `attended_ms_upper = attended_ms + interval_count × heartbeat_period_ms`.

### Verification, and why most of it needs no browser

Putting derivation server-side makes it a pure function of a log sequence, so the
interesting cases are testable by posting synthetic heartbeat sequences and asserting the
derived intervals — **no browser, no Playwright, no dev dependency entering the resolved
closure**. Required cases: sleep (F1), crash (F2), same-task double window (F3),
alternating tasks (F4), idle closure (F5), epoch boundary (F7), replay rejection (F8),
absent script (F9), sub-period decision (F10), post-decision beat (F12).

Exactly one case needs a real browser — that the client emitter actually stops beating on
blur, on hidden, and on input idle, and fires its final beat on `pagehide`. That is one
scripted session, and it is where the specification's existing instrument-verification
requirement lands. Any browser-driving library used for it must be argued as a dev
dependency against the Supply Chain Policy's closure rule, or the test must be done by
hand once per release and recorded.

**Nothing here is trusted until an injected defect moves it.** An instrument that passes
on its first run is also what a vacuous instrument reports.

### What this number is, and the one thing the design refuses to claim

`attended_ms` is a bounded proxy for attention, not a measurement of it. It overcounts a
focused window and an absent mind; it undercounts review done away from the page.

The interaction-idle rule (F5) means a moved mouse extends an interval. That is worth
stating plainly rather than hiding: **every attention proxy is influenceable, and the
control that matters is not making it uninfluenceable — which is impossible — but giving
it no affordance.** There is no start button, no stop button, no confirmation, no dwell
gate, and no field the operator fills in. The operator can defeat this instrument by
deciding to; they cannot defeat it by using the surface.

## Enforcement

The `ci-gate` claim is discharged by:

- The three template assertions above (`approve` in one template, `waive` in one template,
  no unsanitized interpolation, autoescape asserted on).
- The D39 import-graph lint extended to both mission-control packages.
- The **dark-read-model test**: with the read model stopped, a `pass` review page renders
  its decision-critical zones and `approve` succeeds.
- Grant assertions as negative tests: `alfred_operator` must **fail** on any verdict-table
  write and on any `heldout` access; `alfred_readmodel` must **fail** on any INSERT
  anywhere and any SELECT against `heldout`.
- Endpoint precondition tests: approve against `fail` and against `indeterminate` produce
  `409` and **zero** evidence rows; waive against `indeterminate` produces `409`; waive
  with an unresolvable `waiver_adr_ref` produces `409`.
- Idempotency: a double-submitted approve appends exactly one row, enforced by the unique
  constraint and asserted by test.
- The timing-derivation suite above, plus its invariants.

Validation of the `operator_action` record's own shape — closed enumerations,
`waiver_adr_ref` non-null on `waive`, `verdict_ref` non-null on `approve` and `decline`,
`caused_by` referential integrity on `reopen`, the timing invariants — is discharged by
**two checks, both required, neither sufficient**:

- **Pydantic model validation at the command surface's write boundary**, which refuses a
  malformed record before it reaches the chain writer; and
- **the run-record validator**, which re-checks the emitted stream independently. It is
  the check that the first check worked, which matters because the write-boundary
  validator is authored by the same process it constrains. Its implementation lives under
  `harness/` in the protected set, with `scripts/lint_run_records.py` as a protected thin
  wrapper — a validator an agent may edit validates nothing.

**Honest status: neither exists, and there is no CI configuration in this repository at
all.** Every assertion in this section is a build gate to be discharged before the first
Phase 1 dispatch, not a control now running.

## Open inputs

Named rather than guessed, with what would close each.

| # | Missing | Why it matters | Who closes it |
|---|---|---|---|
| 1 | **Fixed weekly obligations, in minutes** (`F`) | One of two unknown terms in the capacity gate. Everything above assumed 300 min/week. | Operator, and it belongs with the plan's Step 0 calendar and runway work. |
| 2 | **Target tasks/day at Phase 3** (`n`) | The other unknown term. Until both exist, *projected human-minutes ≤ capacity* cannot be evaluated and is unfalsifiable in the same way D42's kill criterion was before it got a date. | Operator. |
| 3 | **Typical criterion-authorship minutes** | The derivation above finds authorship, not review, is the binding term above ~3 tasks/day. That conclusion rests on a 20–25 minute guess. | Phase 1 measures it — but only if authorship time is recorded, and nothing currently records it. |
| 4 | ~~Whether `record_type` admits `operator_action`~~ — **closed.** It does; ACS-1 separates by value, so adding the member changes no existing digest, and the chain writer stays singular. | — | Closed by the Run Instrumentation Specification. One consequence remains open: the ACS-1 vector suite has no domain-separation vector for `operator_action` and needs one. |
| 5 | Whether a browser-driving dev dependency is admissible for the one client-side timing test | Everything else is testable without one. | Supply Chain Policy, via a technology selection record. |

## Proposed additions to the Mission Control Specification

Stated here rather than edited in, so the specification's owner decides.

1. **R10 — `waive` on `fail` only.** Argued above.
2. **`heartbeat_period_ms`** in the `timing` object, without which the undercount bracket
   cannot be recomputed later.
3. **`attended_ms_upper`**, or its derivation stated, so the ledger reads a bracket rather
   than a point estimate.
4. **`epoch_boundaries_crossed`** and `idle_closed` interval counts in the `timing` object.
5. **`targeted_diff_opened`** in `decision_basis`, distinct from `full_diff_opened`, so the
   D51 falsification metric is not corrupted by reviewers doing the right thing.
6. **`rationale_sha256` required on `escalate_to_self`.**
7. **The dark-read-model test** as an enforcement item, since it is the only executable
   assertion that the boundary split is real rather than declared.
