---
status:        frozen
owner:         executable
enforcement:   schema
evidence:      The role split and the separate held-out table are required because graph-level visibility controls were found not to constitute a boundary; the hash chain is required because append-only alone does not survive a single login compromise.
falsifies_if:  An agent-role connection succeeds against a held-out, verdict or policy table; or an evidence row is found mutated after write; or the observed grant set differs from the declared matrix in any direction, an extra grant included.
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

**Status, updated 2026-08-16.** The layout, the four Alembic environments, the role
script and the grant script exist and have been applied to a real cluster; the
additive-only lint (`scripts/lint_migrations.py`) runs in CI and is mutation-checked.
What does not yet exist is `harness/db/assert_grants.py` — the set-equality assertion —
so the matrix below is **applied and partially verified, not yet asserted.**

**Two omissions in the matrix above, found by applying it rather than by reading it.**
Both are now corrected in `002_grants.sql` and recorded in `grants.yaml` (version 2), and
both are worth keeping visible because they are the same class of defect:

- **No role held `CONNECT` on the database.** N7 revokes it from `PUBLIC`, correctly, and
  nothing granted it back. Applied literally, the matrix produced a cluster no role could
  reach — `FATAL: permission denied for database`.
- **The migrators held `USAGE` but not `CREATE` on `migration_meta`.** Alembic creates
  its version table on the first upgrade, and `CREATE` on a schema is a privilege
  distinct from `USAGE`. The schema is owned by `alfred_bootstrap` rather than by any
  migrator, so none of them inherits it — the ownership separation working as designed.

Neither is a privilege that was granted too widely; both are privileges the table simply
never mentioned, in a document whose central claim is that a grant matrix is checked by
what it forbids. **A matrix reviewed only for what it grants too much cannot catch a
matrix that grants too little**, and the failure mode is the reverse of the dangerous one
— loud rather than silent, which is the only reason it surfaced in minutes.

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

## The queue

Work dispatch uses `SELECT ... FOR UPDATE SKIP LOCKED`. It reaches throughput far beyond
anything a single inference lane can consume, and it is already multi-host aware — so a
second machine is a capital decision, not an architectural one.

A workflow engine is not adopted until a work item genuinely spans multiple irreversible
steps. Phase 1–2 tasks are single-shot and idempotent, so checkpointing buys nothing.

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
