---
status:        provisional
owner:         executable
enforcement:   ci-gate
evidence:      Each invariant is included because its retrofit cost is a migration or a rewrite, and several are the specific omissions that made a prior attempt expensive to correct. Reclassified from frozen by ADR-0064, applying ADR-0063's lesson before a third waiver rather than after: what enforces which invariant moves as enforcement is built out, and a frozen document cannot follow that without a waiver each time. The invariants themselves are the commitment; the enforcement map is what moves.
falsifies_if:  An invariant is found violated in merged code, meaning its stated holder — lint or review — does not actually hold it; or this document describes an invariant as lint-held when scripts/lint_invariants.py's ENFORCEMENT map says review, or the reverse, meaning the description drifted from the code that is the authority.
review_after:  Phase 2
---

# Cross-Stage Invariants

Properties that hold at every phase. These are the actual source of
forward-compatibility: each costs hours in Phase 0 and costs a migration later.

**Enforcement is split, and `scripts/lint_invariants.py`'s `ENFORCEMENT` map is the authority
on which invariant sits where.** Some are held by a CI lint, where a violation fails the build.
The rest are held by review, or by a database constraint, each with its reason stated in that
map. This document deliberately does not re-list which is which: it did, the list drifted, and
#79 is the ticket that caught it.

## The invariants

| # | Invariant | Why day-one |
|---|---|---|
| I1 | **Tenancy scope on every table** (`org_id`, `project_id`) even with one tenant | Retrofitting multi-tenancy means a full migration plus rewriting every query and every access check. The single most expensive omission on this list. |
| I2 | **Append-only for evidence and state transitions**; no destructive updates | Replay, provenance and audit cannot be added later — they must be inherent. Retrofit is a rewrite. |
| I3 | **Content-addressed artifacts** (sha256 keys) | Deduplication, integrity and run-to-run diffing all follow from it. Retrofit means re-ingesting everything. |
| I4 | **Typed, sortable IDs** (UUIDv7; distinct types per entity) | Cheap now. Later it is a migration plus a class of ID-confusion bugs you will not find. |
| I5 | **Idempotency key on every mutating operation** | Retries are inevitable from Phase 3. Without keys, retries corrupt. |
| I6 | **Schema versions on state, criteria and artifacts** | All three will change. Unversioned records cannot be replayed against the code that produced them. |
| I7 | **Async-first API surface** — long operations return a job ID, never block | Converting sync endpoints to async later breaks every client. Trivial from the start. |
| I8 | **Structured logging with trace and span IDs from the first commit** (OpenTelemetry semantics) | Correlation cannot be reconstructed retroactively. |
| I9 | **Cost and wall-clock accounting per run, per node, per capability** | Autonomy gates need this history to exist *before* they are built. Attribution cannot be applied retroactively. |
| I10 | **Causality recorded** — every record carries what caused it | "Why did this happen" is unanswerable if the link was never stored. |
| I11 | **Deterministic seeds and pinned versions** on every computation | Non-negotiable for a replay-based product. Reproducibility is the product. |
| I12 | **All external systems behind ports** (LLM provider, sandbox, VCS, artifact store, dataset source) | The premise is that agents are replaceable workers. That is only true if they sit behind an interface. |
| I13 | **Policy as configuration, not code** — protected paths, permissions, thresholds | These change constantly. Hard-coded, every change is a deploy. |
| I14 | **Off-machine backup with a verified restore drill** | Hardware loss and total evidence loss are otherwise the same event. Append-only defends against the agent, not against an SSD. |
| I15 | **Evidence rows hash-chained**, chain head anchored off-machine daily | Without it, an audit-layer product's own audit log is silently rewritable by anyone with one login, undetectable by construction. |
| I16 | **No compaction or summarization upstream of a verdict node** | Compaction is lossy. A verdict computed on a summary is a verdict on someone's interpretation. Includes asserting off any compaction the executor ships by default. |
| I17 | **Verdict fields unwritable by agent-invoking nodes** | The graph engine raises only on *concurrent* unreducered writes; a sequential write to a verdict field is silent. Lint on return annotations plus import-graph separation. |

## What the lint checks

**Read it from `scripts/lint_invariants.py`'s `ENFORCEMENT` map, not from here.** The map names
every invariant's holder and, for the ones review holds, the reason a static check cannot reach
them. Running the lint prints the split with its scanned counts.

This section previously duplicated that map as a hand-maintained list, and the copy went stale
in both directions: it listed **I3** as lint-checked when the map records it as held by the
`evidence.artifact` `uq_artifact_content` constraint rather than a lint, and it omitted **I10**,
which the lint does check. That is why the list is gone rather than corrected — a second copy of
a machine-readable fact is a copy that drifts, and correcting it would only reset the clock.

Note the asymmetry with the structure fence (ADR-0063), which was deliberately *not* pointed at
its source: the fence is a human declaration that must be able to disagree with the tree, or
`layout-miss` and `layout-ghost` could never fire. This section is the opposite shape — a
description of what code already does, where the code is the authority and disagreement is
simply an error.

## Confidently deferred

These are expensive now and no more expensive later, precisely because the invariants
above already make room for them: Kubernetes, microservices, message bus, graph
database, multi-region, autoscaling, an RBAC administration UI, caching layers, a
distributed-tracing backend. None requires changing what Phase 0 builds.
