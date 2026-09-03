---
status:        frozen
owner:         executable
enforcement:   schema
evidence:      The role split and the separate held-out table are required because graph-level visibility controls were found not to constitute a boundary; the hash chain is required because append-only alone does not survive a single login compromise. The Phase 2 tables section rests on no observation at all — it is written against D25/D29/D35/D40/D49 and Phase 1 is its first test; it is included only where the alternative is a measurement that cannot be taken retroactively.
falsifies_if:  An agent-role connection succeeds against a held-out, verdict or policy table; or an evidence row is found mutated after write; or the observed grant set differs from the declared matrix in any direction, an extra grant included; or Phase 2 asks a question of the golden set, the taxonomy or the cost attribution that the tables specified here cannot answer without re-running Phase 1.
review_after:  Phase 2
---

# Data Architecture

Postgres is the only source of truth. This document defines what lives in it, who may
touch what, and which properties are enforced by the database rather than by code.

## Role separation

Boundaries are physical. A runtime field-name check is not a boundary; a SQL grant is.

**The agent process holds no database credential at all.** It runs inside the container
and emits a patch file; nothing it produces reaches Postgres except through the harness.
**Nor does the criterion environment** — the container where agent-authored code executes
under `CriterionRunner`. `alfred_criterion` is held by the runner process, which sits
outside that environment (A1) and injects held-out values as inputs. A credential for the
`heldout` schema inside an environment that executes the code under test would let the
code under test select its own answers, which is the entire boundary, undone by a
connection string.

### The full role set

Eleven roles. Ownership is separated from use throughout, because **a role that owns a
table can `ALTER`, `UPDATE` and `DROP` it regardless of what is granted** — so the
append-only property of the evidence schema survives only if the process that writes
evidence does not own it.

| Role | Login | Owns | Credential held by |
|---|---|---|---|
| `alfred_bootstrap` | yes | roles, grants, the four schemas | operator, deliberately, for role changes only |
| `alfred_migrator_product` | yes | `product` | the migration runner |
| `alfred_migrator_control` | yes | `control` | the migration runner |
| `alfred_migrator_evidence` | yes | `evidence` | the migration runner |
| `alfred_migrator_heldout` | yes | `heldout` | the migration runner |
| `alfred_harness` | yes | nothing | the harness process |
| `alfred_criterion` | yes | nothing | `CriterionRunner`, outside the criterion environment |
| `alfred_product` | yes | nothing | the product API |
| `alfred_operator` | yes | nothing | the mission-control command surface (D51) |
| `alfred_readmodel` | yes | nothing | the mission-control read model (D51) |
| `alfred_agent` | yes | nothing | **nobody.** It exists to be denied; its credential lives in the negative-test fixture and in no configuration file. |

No migrator credential is held by any long-running service. Applying a migration is a
deliberate act by a process that is not the harness, which is what stops a defect in the
harness from becoming DDL.

## Schema split

Four schemas plus one bookkeeping schema:

- `product` — trajectories, scenarios, metric results, result stamps
- `control` — work items, criteria, thresholds, protected paths, permissions, run history
- `evidence` — append-only: artifacts, check results, traces, diffs, verdicts, timings,
  operator actions
- `heldout` — reference values and perturbations, reachable only by `alfred_criterion`
- `migration_meta` — the four Alembic version tables, and nothing else

`migration_meta` exists for one reason: Alembic `UPDATE`s its version table on every
migration. Placing that table inside `evidence` would require an `UPDATE` grant in the one
schema whose whole property is that no `UPDATE` grant exists. Bookkeeping about migrations
is not evidence and does not live with it.

## Migration layout

```
migrations/
  product/                  Alembic, schema `product`          — agent-writable
    env.py  versions/
  harness/                                                     — protected set
    control/   env.py  versions/     Alembic, schema `control`
    evidence/  env.py  versions/     Alembic, schema `evidence`
    heldout/   env.py  versions/     Alembic, schema `heldout`
  roles/                                                       — protected set
    001_roles.sql           idempotent, ordered, applied by `alfred_bootstrap`
    002_grants.sql          the only file in the repository that issues GRANT
    grants.yaml             the declared matrix below, machine-readable
```

Product-schema and harness-schema migrations live in separate directories under separate
roles, so a product migration cannot alter an evidence table — not by policy, but because
the role running it holds no privilege there. The three harness schemas are separate
directories for the same reason applied one level down: one migration environment covering
`evidence` and `heldout` would need a role holding both, and that role would be the
boundary's single point of collapse. Each has its own version table in `migration_meta`.

`migrations/roles/` is **not Alembic.** Roles and grants are cluster-level, not versioned
schema, and the correct form is a small idempotent script that can be re-applied and
compared. `grants.yaml` is the declared state; the assertion below compares the cluster
against it.

## Grant matrix

Read as: role × object × privilege. Schema `USAGE` is listed because without it every
table grant beneath is unreachable, and its absence is the cheapest denial available.
`—` means **no privilege of any kind**, including `USAGE`.

| Role | `product.*` | `control.*` (work, runs) | `control.policy_*`, `control.threshold_*` | `evidence.*` (artifacts, checks, traces, timings) | `evidence.verdict` | `evidence.operator_action` | `heldout.*` | `migration_meta` |
|---|---|---|---|---|---|---|---|---|
| `alfred_agent` | — | — | — | — | — | — | — | — |
| `alfred_harness` | U, S | U, S, I, Up | U, S | U, S, I | U, S | U, S | **—** | — |
| `alfred_criterion` | — | U, S | U, S | U, S, I | U, S, **I** | — | **U, S** | — |
| `alfred_product` | U, S, I, Up, D | — | — | — | — | — | — | — |
| `alfred_operator` | — | U, S | U, S | U, S | U, S | U, S, **I** | **—** | — |
| `alfred_readmodel` | U, S | U, S | U, S | U, S | U, S | U, S | **—** | — |
| `alfred_migrator_product` | owner | — | — | — | — | — | — | U, S, I, Up |
| `alfred_migrator_control` | — | owner | owner | — | — | — | — | U, S, I, Up |
| `alfred_migrator_evidence` | — | — | — | owner | owner | owner | — | U, S, I, Up |
| `alfred_migrator_heldout` | — | — | — | — | — | — | owner | U, S, I, Up |
| `alfred_bootstrap` | — | — | — | — | — | — | — | — |

U = `USAGE` on schema · S = `SELECT` · I = `INSERT` · Up = `UPDATE` · D = `DELETE`.
**No role holds `UPDATE`, `DELETE` or `TRUNCATE` on any object in `evidence` or `heldout`.**
That is not an omission from the table; it is the table's main claim.

Three cells carry the weight:

- **`alfred_operator` holds `INSERT` on exactly one object in the cluster.** D51 requires
  it and it is checkable as a global property, not a local one — see the assertion below.
- **`alfred_criterion` is the only role with any privilege on `heldout`**, and it holds
  `SELECT` only. It cannot write the answers it reads.
- **`alfred_readmodel` holds `SELECT` and nothing else, anywhere**, and holds nothing at
  all on `heldout`. Agents may build the read model; its inability to become a source of
  truth is therefore a database fact rather than a review outcome.

`alfred_bootstrap` holds no data privilege by design: it administers roles and is not a
way to reach rows.

## Grants that must not exist

A grant matrix is checked by what it forbids. **A `SELECT` that should not exist is the
failure mode**, and it fails silently in the safe-looking direction — everything works.

| # | Must not exist | Why it is the interesting one |
|---|---|---|
| N1 | `alfred_agent` holding any privilege, including schema `USAGE`, on anything | The organizing principle's retrieval half. |
| N2 | Any privilege for `alfred_harness` on `heldout` | The harness assembles agent context; a `SELECT` here puts held-out values one bug away from the prompt. |
| N3 | Any privilege for `alfred_readmodel` on `heldout`; any `INSERT`, `UPDATE`, `DELETE` or `TRUNCATE` for it anywhere | It is the agent-writable half of the operator surface. |
| N4 | `INSERT` for `alfred_operator` on any object other than `evidence.operator_action`; any write for it on `evidence.verdict` | D51's "only INSERT grant anywhere" is a **global** claim and must be asserted globally. |
| N5 | `UPDATE`, `DELETE` or `TRUNCATE` for any role on any object in `evidence` or `heldout` | Append-only. A held-out reference value silently updated changes past verdicts retroactively. |
| N6 | Ownership of any `evidence` object by any role whose credential a running service holds | Ownership defeats every grant above it. |
| N7 | Any privilege held by `PUBLIC`: `CONNECT` on the database, `USAGE` on `public` or any schema, `EXECUTE` on any function | Postgres grants some of these by default. This is the row most likely to be true right now on any cluster nobody has checked. |
| N8 | Default privileges (`ALTER DEFAULT PRIVILEGES`) granting anything to `PUBLIC`, or to a role not named in the matrix | Otherwise the *next* table created is granted correctly by accident or wrongly by accident, and nobody looks again. |
| N9 | `SUPERUSER`, `CREATEROLE`, `CREATEDB`, `BYPASSRLS`, or `REPLICATION` on any role in the matrix | `BYPASSRLS` is the one that reads as harmless. |
| N10 | Any role membership (`GRANT role TO role`) not declared in `grants.yaml` | Membership is a privilege path that no table-grant query will show. |
| N11 | Any database credential present in the agent container or the criterion environment | The grant matrix is irrelevant if the credential is on the wrong side of the boundary. Asserted at sandbox boot (C8), not here. |

## How the matrix is enforced

- **Set equality, never subset.** The assertion reads `information_schema.role_table_grants`,
  `table_privileges`, schema and database ACLs, `pg_default_acl` and `pg_auth_members`, and
  requires the observed set to **equal** `grants.yaml`. A subset check passes on every
  extra grant, which is the only kind of grant defect that matters.
- **Negative tests assert the error, not the failure.** Each denial in the table above is a
  test that connects as the role, issues the statement, and requires Postgres to raise
  **SQLSTATE 42501 `insufficient_privilege`** specifically. A test that accepts any
  exception passes on `42P01 undefined_table` — so a typo in the table name, or a schema
  that has not been created yet, reads as proof of isolation. This is the shape in which
  a security test most commonly lies.
- **The suite runs against a migrated throwaway cluster in CI**, and again at harness
  startup against the live one, because the property being asserted is about the cluster
  in front of it and not about the file that was supposed to configure it.

## Additive-only, and what "additive" means

Evidence, verdict, operator-action and held-out migrations are additive-only, CI-linted
over the migration files themselves:

- **Permitted:** `create_table`, `add_column` (nullable, or with a server default), index
  creation, new constraints that cannot fail on existing rows.
- **Rejected:** `drop_table`, `drop_column`, `alter_column`, `rename`, and any `op.execute`
  whose statement contains `UPDATE`, `DELETE`, `TRUNCATE`, `ALTER … TYPE` or `DROP` against
  an object in `evidence` or `heldout`.
- **`downgrade()` in those directories must raise.** A downgrade that drops an evidence
  table is the same defect wearing a reversible name, and the CI lint rejects any
  `downgrade` body that is not a single raise.
- **Held-out values are additive at the row level too.** A corrected reference value is a
  new row under a new version, never an `UPDATE`. Otherwise a verdict computed last week
  cannot be reproduced, and the product is reproducibility.

The lint is a text-and-AST check over `migrations/harness/{evidence,heldout}/versions/`,
and it fails the build rather than reporting. It is a second layer over N5: the grant makes
the write impossible for every role that runs, and the lint catches the migration that
would grant itself the ability by owning the table.

**Status, updated 2026-08-17.** The matrix is **asserted**. `harness/db/assert_grants.py`
compares the cluster against `grants.yaml` by set equality in both directions, reporting
`EXTRA` first; `harness/db/test_grants.py` carries the negative tests, each asserting
`SQLSTATE 42501` specifically and each paired with the identical statement by the role
that should hold the privilege. Two mutation controls are committed beside them, so a
suite that stopped biting would say so. The first migration in each of the four schemas
exists, so the per-table half of the matrix is now populated rather than vacuous — until
2026-08-17 there were no tables, and a table-driven grant script over zero tables grants
nothing. ADR-0009.

**Three omissions in the matrix above, every one found by applying it rather than by
reading it.** All are corrected in `002_grants.sql` and recorded in `grants.yaml`, and
all are worth keeping visible because they are the same class of defect:

- **No role held `CONNECT` on the database.** N7 revokes it from `PUBLIC`, correctly, and
  nothing granted it back. Applied literally, the matrix produced a cluster no role could
  reach — `FATAL: permission denied for database`.
- **The migrators held `USAGE` but not `CREATE` on `migration_meta`.** Alembic creates
  its version table on the first upgrade, and `CREATE` on a schema is a privilege
  distinct from `USAGE`. The schema is owned by `alfred_bootstrap` rather than by any
  migrator, so none of them inherits it — the ownership separation working as designed.
- **No schema owner held `CREATE` on the schema it owns** (2026-08-17, found the first
  time a migration ran). `002_grants.sql` converges by revoking everything from every
  named role, and a schema owner holds `USAGE` and `CREATE` implicitly *only while the
  schema's ACL is null* — the revoke makes it explicit and the implicit privileges go
  with it. The `migration_meta` fix above was this same fact, written as a special case
  about Alembic's version table. All five owners are now granted explicitly, which is
  also the better end state: an implicit privilege is one no assertion can read.

None is a privilege that was granted too widely; all three are privileges the table simply
never mentioned, in a document whose central claim is that a grant matrix is checked by
what it forbids. **A matrix reviewed only for what it grants too much cannot catch a
matrix that grants too little**, and the failure mode is the reverse of the dangerous one
— loud rather than silent, which is the only reason all three surfaced in minutes. Three
instances in two days is no longer an anecdote about this matrix; it is the standing cost
of a deny-by-default design, and it is the right cost to pay.

Everything not yet asserted remains specification. It is written ahead of the code because
none of it is retrofittable: a grant matrix applied after the first evidence row exists
cannot prove what could have been read before it, and the additive-only property has no
meaning once a row has been updated.

## Held-out values are a table, not a visibility setting

This is the correction that matters most. Graph-level mechanisms do **not** isolate
held-out data: `private` state schemas do not hide channels from stream, `output_keys`
is a caller-side argument rather than a graph-level guarantee, the checkpointer persists
everything, and a filter predicate on an index is not a boundary.

So: held-out values live in the `heldout` schema, owned by a separate role, materialized
by `CriterionRunner` at verdict time and never placed in graph state. If subagent
isolation ever enters the design, sibling messaging is denied and context forks are
forbidden — a sibling roster is a lateral channel.

## Append-only and the hash chain

Evidence rows are never updated or deleted. Each row carries `prev_sha256` and its own
`sha256` computed over its content plus its predecessor's hash, forming a chain per
stream. The chain head is anchored off-machine daily.

Append-only is an integrity property against the agent. The chain is what survives an
operator-level compromise or a bad migration — without it, the audit log of an audit
product is rewritable by anyone with one login.

Two hashes with different requirements (ADR-0003). **Artifacts are hashed as stored
bytes** — no canonicalization question arises. **Evidence rows and result stamps are
hashed over ACS-1**, a canonical JSON in which floats are carried as strings, keys sort by
UTF-8 bytes, and the record type and scheme version are prefixed for domain separation.
The second class is the one an external auditor must be able to recompute without running
Alfred's code, which is the only reason the chain is worth having.

## Every table

Carries `org_id`, `project_id`, a UUIDv7 primary key typed distinctly per entity,
`schema_version`, `created_at`, and a causality reference to what caused the row.
Mutating operations carry an idempotency key.

## The Phase 2 tables, and which document owns what

Phase 2's exit — regression detection at effect sizes ≥25pp on a fixed set, and a
queryable failure taxonomy — needs tables that Phase 1 has no use for but whose *inputs*
Phase 1 must already be emitting. This section specifies those tables. It specifies
nothing about Phases 3–7: a table designed before the failures it must group is a table
designed to flatter them.

**Fidelity, stated because this document is otherwise frozen.** Everything above this
section is frozen and changing it is a breaking change. Everything *in* this section is
**provisional** in the blueprint's sense — shape and responsibility specified, expected to
move once Phase 1 has run. It is written now only for the parts that cannot be applied
retroactively: attribution, stratification dimensions, and any record that must be written
at the moment an event happens rather than reconstructed from what survived it.

### Ownership, stated once so it is not restated inconsistently

Each of these owns exactly one thing. Extended by ADR-0047 for the factory's own facts;
the router gains rows, never descriptions — content stays in the home the row names.

| Owner | Owns | Does not own |
|---|---|---|
| **This document** | Every table and column in `product`, `control`, `evidence`, `heldout`; the grant matrix; the append-only and hash-chain properties. | The field set of any record *inside* the run record stream. |
| **Run Instrumentation Specification** | The run record stream: which records exist, their fields, their enumerations, their validator. | Where the stream lands, and every table that is not the stream. |
| **Mission Control Specification** | The fields of `operator_action` only, versioned by `field_set_version`. | The envelope those fields travel in. |
| **`policy/node-palette.json`** | Which roles exist, their ports, and their category. | Which of them run, and on what. |
| **`policy/role-bindings.json`** | The capability tuple per role: `capability_id`, agents, tools, permissions, context budget, and the D19 version fields. | The model. It declares the routing key; it does not resolve it. |
| **`policy/model-routing.json`** | Which model each `capability_id` resolves to, the forbidden identities, and the trivial class. | Which capabilities exist. |
| **Execution Lifecycle** | The phase sequence, the static re-entry table, and phase-to-capability binding. | Any gate. It cites Definition of Done and `failure-semantics.md` rather than restating them. |
| **`control.work`** | Which tasks exist, their state, and what blocks what — the instance graph. | The type graph. It is validated against the palette and topology; it is not a second authority for them. |
| **Runtime state** (`.autoforge/`, any ECC or ECC2 store) | **Nothing.** Machine-local, gitignored, disposable. | Everything. It is never cited by a gate, a verdict, or an audit. If a fact matters it is emitted into the run record stream when it happens; the runtime copy is incidental. |

The rule that resolves every future collision: **the stream is a field set, the store is a
schema, and the store never re-declares a stream field.** `evidence.run_record` holds the
envelope columns needed to index and chain rows, and the record body as ACS-1 bytes plus a
`jsonb` projection for querying. Adding a field to a record is a Run Instrumentation change
and a validator change; it is not a migration. This is why the projection is `jsonb` and
not one column per field — one column per field would make every field addition an
additive migration in the one schema whose migrations are additive-only, and the two
documents would drift into disagreeing about the same field.

| `evidence.run_record` | Type | Notes |
|---|---|---|
| `event_id` | uuid7 | Primary key. Equals the stream's `event_id`; the stream is the authority. |
| `org_id`, `project_id`, `task_id`, `attempt_id` | uuid7 | I1, and the join keys everything below uses. `attempt_id` nullable exactly where the stream says. |
| `record_type` | text | Indexed. Also the ACS-1 domain separator. |
| `schema_version` | int | I6. |
| `emitted_at`, `monotonic_ns` | timestamptz, bigint | Durations from the second only. |
| `caused_by` | uuid7 | I10. |
| `body` | jsonb | The record, projected. Queried; never the hash input. |
| `body_sha256`, `prev_sha256`, `sha256` | text | ACS-1 over the canonical bytes (ADR-0003). The chain is over the bytes, not over the projection. |

### The work item, and the four columns that must be set at dispatch

`control.work` is otherwise a Phase 1 concern, but four of its columns are the ones every
Phase 2 grouping depends on, and a task dispatched without them is permanently
unstratifiable — the row cannot be corrected later without an `UPDATE` the evidence it
joins to does not permit.

| `control.work` | Notes |
|---|---|
| `task_id` | uuid7, and the join key for the entire evidence side. |
| `capability_id` | **Set at dispatch.** The grouping key for cost per capability (I9) and for every autonomy grant (D19). |
| `measure_domain`, `scenario_id` | **Set at dispatch.** Phase 1's exit requires coverage of ≥4 domains and ≥5 scenarios; neither is countable if the task does not say which it is. |
| `held_out_provenance_tier` | **Set at authoring time**, on the criterion rather than on the run. `P1`…`P5` per D49. Merge rate stratified by tier is a Phase 1 exit criterion. |
| `retry_budget`, `budget` | The caps the attempt inherits. |

The remaining columns are Phase 1's to settle. These five are listed here because the cost
of omitting them is paid in Phase 2 and cannot be refunded.

### The golden set (D29)

Two tables, because the *set* and a *replay of the set* are different things and conflating
them is how a regression suite starts reporting on its own composition.

| `control.golden_task` | Type | Notes |
|---|---|---|
| `golden_task_id` | uuid7 | |
| `source_task_id` | uuid7 | The Phase 1–2 task this was promoted from. |
| `repo`, `parent_commit_sha` | text | **The parent of the fix commit, never HEAD.** See below. |
| `criterion_ref`, `criterion_version` | text, int | The visible criterion. Held-out points are referenced, never inlined (§ Held-out values). |
| `capability_id` | text | The capability the task exercises. Grouping key for D19. |
| `measure_domain`, `scenario_id` | text | Stratification axes. Phase 1's exit already requires ≥4 domains and ≥5 scenarios. |
| `held_out_provenance_tier` | enum | `P1`…`P5` per D49. A set stratified without this cannot report merge rate stratified by tier, which the Phase 1 exit requires. |
| `entry_reason` | enum | `merged` · `merged_after_retry` · `rejected` · `escalated` · `near_miss`. |
| `entered_at` | timestamptz | Append-only: membership accumulates, rows are never removed. |

| `control.golden_set_version` | Type | Notes |
|---|---|---|
| `set_version` | int | Monotone. |
| `golden_task_id` | uuid7 | One row per member. A version is a *set of rows*, so a comparison names a version and is reproducible after the set has grown. |
| `frozen_at` | timestamptz | |

| `evidence.golden_run` | Type | Notes |
|---|---|---|
| `golden_run_id`, `golden_task_id`, `set_version` | uuid7, uuid7, int | |
| `fingerprint_sha256`, `seed` | text, bigint | D19 identity and I11. |
| `task_id` | uuid7 | The ordinary run this replay produced — see the constraint below. |
| `verdict`, `held_out_result` | enum | Class labels only. |
| `wallclock_ms_to_outcome`, `lane_ms` | int | The currency (D25 as amended by D35). |

Four rules carry the weight, and each is a check, not a convention:

- **Tasks pin the parent commit.** A golden task checks out `parent_commit_sha`, the commit
  the fix landed on top of. Once the fix is merged the task is trivial, which is why
  SWE-bench is constructed this way. A CI check asserts `parent_commit_sha` is a parent of
  the recorded fix commit and that the fix commit is **not reachable** from the tree handed
  to the agent — including through the retrieval index, which is `context_strategy_version`
  input and therefore part of what a replay pins.
- **All four outcome classes enter, automatically.** Entry is triggered by a task's terminal
  event, not curated. A set built from successes reads ~100% forever and goes green through
  a change that breaks everything else; the failures are the informative half. `near_miss`
  is decidable, not a judgment: `outcome ≠ merged` and final `assertions_passing ≥ 0.8 ×
  assertions_total`, or `outcome = merged` with `attempts > 1` (recorded as
  `merged_after_retry`).
- **A golden run is an ordinary run.** The replayer schedules and compares; it does not
  execute. If replay had its own execution path the set would measure the replayer, and the
  first thing it would hide is a defect in the path that real work takes. This is the whole
  constraint on `EvalRunner`, and it is the reason that port needs no signature yet.
- **Comparisons are paired and quote their resolution.** The same task set, the same seeds,
  one fingerprint field changed. Every comparison reports n, the observed difference, and
  the effect size the set can detect. At n≈20 and p≈0.6 the standard error is roughly 11pp,
  so ≥25pp is what Phase 1's twenty supports; ~5pp needs 150–400 tasks. **The Phase 1 twenty
  and the regression set are two different artifacts** — twenty is ample for a failure
  taxonomy and useless for comparing configurations. *Inference, marked as such: the
  150–400 figure is only reachable because the comparison is paired (discordant pairs only);
  an unpaired comparison at the same power needs roughly an order of magnitude more tasks.
  Pairing is therefore a requirement, not an optimization.*

### The failure taxonomy (a table, from Phase 1's prose)

| `control.failure_mode` | Type | Notes |
|---|---|---|
| `mode_id` | text | Stable. Cited by every observation. |
| `name`, `definition` | text | |
| `decidable_rule` | text \| null | Non-null for structural modes: the query that decides it. Null means an analyst decides. |
| `external_reference` | text \| null | e.g. the MAST mode this corresponds to, with its published frequency. |
| `mode_set_version` | int | The taxonomy is versioned; a reclassification names the version it used. |

| `evidence.failure_observation` | Type | Notes |
|---|---|---|
| `observation_id`, `attempt_id`, `task_id` | uuid7 | |
| `mode_id`, `mode_set_version` | text, int | |
| `role` | enum | `primary` · `also_present`. Exactly one `primary` per attempt. |
| `classifier` | enum | `structural` · `analyst`. |
| `classifier_version` | text | The query version, or the analyst protocol version. |
| `basis_event_id` | uuid7 | The record that supports the classification (I10 applied to a judgment). |

- **Structural modes are computed, never asserted.** Sterile repetition, stall,
  premature termination, cap exhaustion and the mismatch lower bound are already decidable
  from the stream; their observations are the output of a named query, re-runnable after the
  rule changes. **Reclassification writes new rows under a new `mode_set_version`; it never
  updates one** — otherwise a taxonomy revised in Phase 3 silently rewrites Phase 1's
  distribution.
- **`primary` and `also_present` exist for the same reason `primary_cause` and
  `also_satisfied` do.** Modes co-occur, and a table that records only the first one found
  reports on classification order rather than on the agent.
- **No mode is agent-authored.** An analyst classification cites a record; an agent's account
  of why it failed is not evidence about why it failed.

**What Phase 1 must already be emitting for this table to be populatable later — and what
it already emits.** Verified against the Run Instrumentation Specification rather than
assumed: the raw material is present. `attempt_bundle_ref`, `content_sha256`,
`also_satisfied`, `premature`, `sterile_repeats` and the `progress` series all exist, and
the specification already requires the verbatim content channel precisely so Phase 2 can
reclassify without re-running. The dimensions the taxonomy groups *by* —
`measure_domain`, `scenario_id`, `capability_id`, `held_out_provenance_tier` — are task
attributes and reach the taxonomy by join on `task_id`, which is why they are columns of
`control.golden_task` and of the work item above rather than new stream fields. **The
retrofit hazard here is therefore in the control plane, not the stream:** a work item
dispatched without `capability_id` and `held_out_provenance_tier` recorded at dispatch
leaves those tasks permanently unstratifiable, and Phase 1's own exit criterion requires
merge rate stratified by provenance tier.

### Cost attribution — the currency is wall-clock (D25 as amended by D35)

I9 requires accounting per run, per node and per capability, before Phase 4 needs the
history. Under pure-local inference there is no per-token bill, so **no per-run monetary
figure is recorded at all** — a dollar column that is always zero is worse than no column,
because it will eventually be summed and reported. The company's cash lines are org-level
and belong in the Cost Management Policy, not on a run.

Nothing is stored that can be derived. The attribution is a view, not a table:

| Quantity | Unit | Source |
|---|---|---|
| Per attempt, per plane | ms | `attempt_end.agent_ms`, `criterion_ms`, `harness_ms`, from `monotonic_ns` differences. |
| Per task, to outcome | ms | `task_end.wallclock_ms_to_outcome`. The numerator of wall-clock per merged task. |
| **Lane occupancy** | ms | `Σ (turn.prefill_ms + turn.decode_ms)` over the attempt. Under one serialized lane (D37) this, not wall-clock, is the resource two tasks contend for. |
| **Lane wait** | ms | Time an attempt was ready to generate and queued behind another. Not derivable, and deliberately **not emitted yet**: with one task in flight there is nothing to wait behind. It becomes a required `turn` field when Phase 3 introduces concurrent preparation, and the version bump at that point loses nothing, because Phase 1–2 carry no contention to record. |
| Per capability | ms | Join on `control.work.capability_id`. |
| Per node | ms | The three-plane split **is** the per-node split while the graph is single-path. A `node_id` becomes necessary when the graph branches, which is Phase 3. |
| Per fingerprint | ms | Join on `attempt_start.fingerprint_sha256` through the registry below. |

Cost per merged task is `Σ lane_ms` and `Σ wallclock_ms_to_outcome` over merged tasks
divided by their count, always reported with the fingerprint they were measured on. An
orchestrator change is an epoch boundary (D40): historical cost-per-merged-task across one
is incomparable and is not averaged across it.

### The fingerprint registry, and the inputs an autonomy gate will read

`attempt_start.fingerprint_sha256` is a hash. A hash cannot answer *what changed*, and D19's
tiered requalification — smoke subset for prompt or context changes, smoke plus tool-calling
probes for serving-stack or lockfile changes, full golden set for weights, quantization or
orchestrator — is a decision about *which component* moved. So the components are stored in
the clear:

| `control.fingerprint` | Notes |
|---|---|
| `fingerprint_sha256` | Primary key. |
| `capability_id`, `model_version`, `prompt_version`, `tool_version`, `context_strategy_version` | D19. |
| `quant_artifact_sha256`, `inference_runtime_version`, `server_version`, `orchestrator_sha`, `harness_identity` | D40. The quantization *artifact* hash, not the quant name — imatrix variants share names. |
| `first_seen_at` | |

**The `AutonomyGate` needs four quantities and one of them has no source anywhere in the
register.** The gate itself is not specified here — it is a Phase 4 decision procedure and
specifying it now would be specifying against unobserved failures. Its *inputs* are
specified now, because they cannot be backfilled:

| Input | Where it comes from | Exists today? |
|---|---|---|
| Per-task merge rate after the retry budget, on a fingerprint | `task_end.outcome` joined to `control.fingerprint` | Yes |
| Held-out composed pass rate | `task_end.held_out_result`, stratified by `held_out_provenance_tier` | Yes, once the tier is recorded at dispatch |
| Wall-clock per success | The attribution view above | Yes |
| **Measured defect-escape rate** | — | **No** |

A defect-escape rate is the fraction of merged tasks later found defective. It requires a
record written *at discovery time* linking the defect back to the task that introduced it,
and it is unreconstructable afterwards: nothing in the merged history distinguishes "clean"
from "not yet looked at". So:

| `evidence.defect_escape` | Notes |
|---|---|
| `defect_escape_id` | |
| `introducing_task_id`, `introducing_fingerprint_sha256` | The merge being charged. |
| `discovered_at`, `discovery_source` | `criterion` · `downstream_task` · `operator` · `customer`. |
| `severity`, `evidence_ref` | |
| `attribution_basis` | enum: `bisect` · `criterion_replay` · `operator_judgment`. An escape attributed by judgment is not the same measurement as one attributed by bisect, and a rate that mixes them without saying so is not a rate. |

This table is append-only and starts empty. **An empty defect-escape table is not a zero
defect-escape rate**, and the gate must read the denominator — merged tasks under
observation for a stated window — rather than the count. That distinction is the whole
reason the table is specified before Phase 4 rather than during it.

## The queue

Work dispatch uses `SELECT ... FOR UPDATE SKIP LOCKED`. It reaches throughput far beyond
anything a single inference lane can consume, and it is already multi-host aware — so a
second machine is a capital decision, not an architectural one.

### Durable execution is deferred to Phase 3, and the trigger is correctness, not load

A workflow engine — Temporal, a LangGraph checkpointer, or the Postgres queue standing on
its own — is not adopted until a work item genuinely spans multiple irreversible steps.
Phase 1–2 tasks are single-shot and idempotent, so checkpointing buys nothing: the recovery
action for a lost attempt is to run it again, which the retry budget already covers.

**The revisit trigger is a correctness requirement, never a throughput one, and the
distinction is load-bearing because throughput is the argument that will present itself
first.** Postgres `SKIP LOCKED` reaches tens of thousands of claims per second when tuned —
orders of magnitude beyond what a single serialized inference lane (D37) can consume, where
the unit of work occupies the lane for minutes. Queue throughput can therefore never be the
binding constraint on this machine, and an adoption argued from load would be an
architecture bought against a number that was never measured.

What does force the revisit: a work item that must resume **mid-item** after a crash without
repeating a step that already had an external effect **which no idempotency key can make
safe to redo** — a deploy, a release, a write to a system that does not honour one. Phase 1's
single external effect, opening a pull request, does not qualify: it carries an idempotency
key (I5) and re-running the attempt from the start is correct. Until an item exists that
cannot be restarted from the start, a checkpointer is a second store of execution state whose only guaranteed
property is that it can disagree with the evidence store. If one is adopted it remains
**distinct from the evidence store and never the system of record**, which is the standing
constraint on `Checkpointer`.

## Backup and restore

Continuous WAL archiving plus periodic base backups to an off-machine target, covering
both Postgres and the artifact store. **The restore drill is an executable check**, and
"restore verified" is a Phase 0 exit criterion sitting beside "deploy and rollback
verified". A backup that has never been restored is a belief, not a control.

## Retrieval

Version one ships with no index beyond Postgres itself: parameterised SQL over the
evidence store and `tsvector` full-text search for text and code, with file-granular
retrieval and no chunker. Alfred's dominant query shapes are exact tokens — fingerprints,
decision IDs, metric names, hash-chain entries — which is precisely where embeddings
underperform.

Every retrieval call and the row IDs it returns are recorded as reads. The retrieval
function source, the FTS configuration and the seed are hashed into
`context_strategy_version`.

Revisit embeddings when retrieval miss rate measurably costs verdicts, or when the repo
passes roughly 1000 files, settled by a deterministic A/B in Alfred's own harness. If
pgvector is ever adopted it goes second behind BM25, with a hard size budget and a
scheduled rebuild: measured throughput collapses from 2110 QPS at 2M vectors to 12.9 QPS
at 5M once the index exceeds `shared_buffers`, with recall falling from 0.99995 to
0.5444 — and it never reclaims space on delete, which interacts badly with append-only
monotonic growth.
