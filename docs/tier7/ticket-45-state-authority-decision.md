---
status:        provisional
owner:         human
enforcement:   none
evidence:      A grilling session on 2026-09-02 against data-architecture.md (frozen), cross-stage-invariants.md, run-instrumentation-specification.md, ECC's state-store.schema.json, and the .autoforge/state.json produced by a real AutoForge run against this repository on 2026-08-29. No factory task has yet written a run record; nothing here rests on an observed write.
falsifies_if:  A fact in the homes table below is written authoritatively in two places; or a gate, verdict or audit is observed reading machine-local runtime state.
review_after:  the first factory task that emits run records
---

# Ticket #45 — state authority: decision record

Resolves [State authority — one home per fact](https://github.com/Akamel01/Alfred/issues/45),
a child of [wayfinder:map — Alfred × ECC: one factory](https://github.com/Akamel01/Alfred/issues/41).

## The reframe

The ticket reads as though Alfred needs a state-authority model built. It has one.
`docs/tier1/data-architecture.md` § *Ownership, stated once so it is not restated
inconsistently* already names three documents, each owning exactly one thing, and states
the rule that resolves collisions:

> **the stream is a field set, the store is a schema, and the store never re-declares a
> stream field**

So this ticket **extends a router**, it does not invent a model.

## The six decisions

### D1 — The homes table extends the existing ownership router; it does not become a fourth describer

`data-architecture.md` is `frozen` — changing it is a breaking change. But its ownership
table is a **router**, not content: a row says "that other document owns this." Adding rows
is the least invasive possible edit and is what the table is for.

*Beat:* a new Tier 1 document owning factory-execution state — which risks becoming a
fourth thing describing overlapping material, the exact failure the section was written to
prevent.

The edit still needs an ADR because the document is frozen. It is a reviewable
few-line diff, not a rewrite.

### D2 — Runtime is never evidence. Hard line.

Everything in `.autoforge/` and any ECC or ECC2 store is **runtime state**: machine-local,
gitignored, disposable, reconstructible or abandonable, and **never cited by a gate, a
verdict, or an audit**. If a fact matters, it is **emitted into the run record stream at the
moment it happens**; the runtime copy is incidental.

*Why not "promote selected records on a trigger":* I2 makes evidence append-only, I15
hash-chains it, I10 requires every record to carry what caused it. A fact promoted into
evidence *later* has no honest `emitted_at` and no honest causality link. A promotion
trigger is a second write path into an append-only store.

**Display-only concession.** Mission Control may render runtime state for liveness. A
rendered runtime fact carries provenance saying it is unverified, and a missing one renders
as **unknown** — never as **none**.

**Immediate consequence:** `objectives` must leave `/Users/akamel/Alfred/.autoforge/state.json`.
That file (from a real AutoForge run, 2026-08-29) currently holds `objectives`, `phase`, and
an `artifacts` map. `objectives` is a mission fact in a gitignored machine-local file — the
precise violation this ticket is named after.

### D3 — Two new record types: `phase_start`, `phase_end`

The stream is attempt-shaped: `attempt_start` → `turn` / `tool_call` / `progress` →
`attempt_end` → `task_end`, plus `escalation` and `operator_action`. It has no notion of a
phase, and [#42](https://github.com/Akamel01/Alfred/issues/42) settled seven of them.

#42's D5 put the phase-termination check on the **orchestrator**, because two child sessions
falsely reported completion on 2026-09-02. **A check whose result is not recorded is a check
nobody can audit** — the same defect one level up.

Front-half phases being *method* (#42 D1) does not make them invisible: method means no gate
blocks on them, not that they leave no trace.

Per the collision rule this is a Run Instrumentation change plus a validator change and
explicitly **not a migration** — `evidence.run_record.body` is `jsonb` for exactly this
reason.

### D4 — Four of the five ECC collisions are not collisions. One is.

Under D2's hard line most of the overlap is *different layers*:

| ECC `state-store.v1` | Alfred home | Collision? |
|---|---|---|
| `sessions` | `attempt_start` / `attempt_end` | No — runtime liveness vs evidence record |
| `skillRuns` | `tool_call` | No — same shape |
| `governanceEvents` | `operator_action` / `run_record` | No — `operator_action`'s fields are owned by the Mission Control Spec, versioned by `field_set_version`, closed writer enum |
| `decisions` | the ADR log | No, and not close — the ADR log is append-only and never edited after publication; ECC `decisions` is `trust: unreviewed` by construction |
| `workItems` | `control.work` | **Yes** |
| `installState`, `skillVersions` | — | ECC-native; they describe ECC's own installation |

**`control.work` is the sole authority for what work exists. ECC `workItems` is unused.**

A task list is not a runtime artifact, so this one does not dissolve. `control.work` carries
four columns that must be set **at dispatch**; a task dispatched without them is
"permanently unstratifiable," and the row cannot be corrected later because the evidence it
joins to forbids `UPDATE`.

*Beat:* splitting by domain (ECC `workItems` for factory work, `control.work` for product
work) — the duplicate-authority failure wearing a domain split; the moment factory work
needs stratifying it needs those four columns and will not have them. Also beat: a derived
projection — one nothing reads is dead weight, one that is read drifts.

If the ECC-side runtime needs a task list to function, it derives it per-invocation from the
spawn contract it was handed.

### D5 — Factory execution state reuses `control` and `evidence`. No new schema.

A factory task is a task: it gets a `control.work` row and emits run records to
`evidence.run_record` like any other.

*Beat:* a new `factory` schema. Under the ownership-separation rule — a role that owns a
table can `ALTER`, `UPDATE` and `DROP` it regardless of grants, which is the entire reason
the evidence schema's append-only property survives — a new schema means new migrator and
consumer roles, a grant-matrix extension, and `assert_grants.py` set-equality updates in
both directions. That is a large amount of machinery to express "this task is about the
factory," which is a **column**, not a schema.

*Also beat:* keeping factory state out of Postgres entirely — which forfeits append-only
hash-chained evidence for exactly the work whose completion claims proved unreliable.

**The accepted cost, stated rather than glossed:** factory and product tasks share one
evidence chain. This is judged correct rather than merely convenient — Alfred's thesis is
that autonomy tracks ground truth the agent did not author, and that applies to a factory
task identically.

### D6 — The lint lands with the document, or the document declares `review-cadence`

`cross-stage-invariants.md` declares I1–I17 *"Enforced by CI lint. A violation fails the
build."* **`scripts/lint_invariants.py` does not exist.** Twelve lints exist; that one is a
ghost, already flagged in `execution-order.md`'s inventory and still absent.

A document declaring `enforcement: ci-gate` against a script nobody wrote is worse than one
declaring `review-cadence`, because it reads as a control.

So: `scripts/lint_state_authority.py` lands **in the same change** that declares it, or the
homes table ships as `review-cadence`. No specifying-without-building.

Checks it performs:
1. No fact appears in two declared homes (declared table vs a small path denylist).
2. `.autoforge/` and any ECC store appear in no gate's read path.
3. `objectives` does not appear in machine-local state.

`scripts/` is protected: this is a **Gate D** change — line-by-line human review plus an ADR.

## The homes table

Authoritative home per fact. Everything else is derived, disposable, or display-only.

| Fact | Authoritative home | Notes |
|---|---|---|
| Mission, objective | **Alfred git** — the register; for charted efforts, the wayfinder map | See the tracker caveat below |
| Stage status (S0–S9) | `docs/tier2/execution-order.md` § Stages | ADR-0041 §3; `stages/*/output/exit.md` is evidence, not a second status |
| Decisions | `docs/tier1/adr-log.md` | Append-only, never edited after publication |
| Task definition, task status, dependency edges (`blocked_by`), task class | `control.work` | Task class set at dispatch by the orchestrator (#42 D3) |
| Role/edge **types** | `policy/node-palette.json`, `orchestration/topology.json` | Protected; ADR-0039. The type graph, not the instance graph |
| Task contract | owned by [#44](https://github.com/Akamel01/Alfred/issues/44) | Not decided here |
| Model + harness selected | declared by [#46](https://github.com/Akamel01/Alfred/issues/46); *selection recorded* in `attempt_start` and the Run Fingerprint | Declaration and record are different facts |
| Agent session identity | `attempt_start` / `attempt_end` | Runtime session id is incidental |
| Session status, session output, context pressure | **runtime** — display-only | Renders as `unknown` when absent |
| Phase entry/termination | `phase_start` / `phase_end` (D3) | New record types |
| Worktree | git refs for the branch; worktree bookkeeping is runtime | Land-or-delete and Gate E unchanged |
| Artifact | content-addressed store (I3), referenced from evidence | Never a raw path |
| Evidence, review verdict, validation verdict | `evidence.run_record`, hash-chained | I2, I15 |
| Escalation | `escalation` record | Triggers owned by `escalation-protocol.md` |
| Human approval | `operator_action` | Fields owned by the Mission Control Spec |
| Cost, wall-clock | per run / node / capability (I9) | Attribution cannot be applied retroactively |
| Autonomy grant | `control` + `autonomy-graduation-policy.md` | Per task-class, revocable |
| Memory | ECC vault, `trust: unreviewed` | Never a home for anything Alfred reads automatically ([#50](https://github.com/Akamel01/Alfred/issues/50)) |
| Risk score | **no home — not adopted** | ECC2 computes one; the capability audit found its derivation not inspectable. Do not adopt a number whose derivation cannot be inspected |

### The tracker caveat, stated because it is a real third store

Wayfinder maps and their decision tickets live on **GitHub Issues** — neither Alfred git nor
Alfred Postgres. That is a third state home for mission-level facts, and it is currently
unaddressed by the ownership router. It works because a map is a *planning* artifact and
nothing gates on it. It stops working the moment a gate reads a ticket. Flagged rather than
resolved; it is not this ticket's destination.

## What this hands off

1. The ownership-router rows in `data-architecture.md` (frozen → needs an ADR).
2. `phase_start` / `phase_end` in `run-instrumentation-specification.md` plus its validator.
3. `scripts/lint_state_authority.py` (protected → Gate D), landing with the document.
4. Removing `objectives` from `.autoforge/state.json` and from whatever writes it.

## Found in passing, not absorbed

`scripts/lint_invariants.py` is absent while `cross-stage-invariants.md` claims CI
enforcement for seventeen invariants. Register-health drift of the ADR-0044 class; belongs
on the ICM map, not this one.
