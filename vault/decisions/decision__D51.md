---
kind: decision
id: "decision:D51"
title: "Mission control exists, it is split, and every operator action is an evidence row"
shape: "table-row"
number: "51"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:91"
extractor: "decisions"
aliases:
  - "D51"
  - "Mission control exists, it is split, and every operator action is an evidence row"
generated: true
---

# Mission control exists, it is split, and every operator action is an evidence row

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:91`

## Statement

**Mission control exists, it is split, and every operator action is an evidence row.** Alfred has an operator surface — task queue, escalation inbox carrying the D23 attempt bundle, criterion-first evidence bundle, and a run record with a generated graph/loop viewer — built on FastAPI with server-rendered HTML (D13; no second toolchain, no build step, no JS dependency closure to hash-lock). **Boundary split:** the **command surface** (approve · decline · request-changes · waive · escalate-to-self · reopen, and later grant/revoke autonomy and drain) is **inspector**, permanently protected under D20, running under a DB role whose only INSERT grant anywhere is the operator-action evidence table. The **read model** (views, queries, rendering) is **factory** and agents may build it, under a **SELECT-only** role with no grant on `heldout` — and it **may not be the source of any fact an action depends on**, since an agent-authored view rendering a `fail` as a `pass` would defeat every control beneath it while leaving all of them intact. **Every operator action writes one `operator_action` evidence row into the hash chain** before its side effect is emitted, distinguished from a harness action three ways: ACS-1 domain separation by `record_type`, the writing process and its role, and `actor_kind`/`actor_id` on the row. **Review time is measured by the harness, never reported by the operator** — attended intervals from visibility/focus heartbeats, at most one open across the whole surface, `attended_ms` and `elapsed_ms` recorded separately and never conflated, and `null` rather than `0` when the instrument did not run. **Falsifies if:** a Phase 1 merge is authorized without a corresponding operator-action row in the chain; or the capacity ledger cannot be computed because the recorded number is dominated by tab-open wall clock rather than attended time; or the full diff is opened on a majority of Phase 1 tasks carrying no anomaly flag, meaning criterion-first review is not what is happening.

## Falsifies if

> a Phase 1 merge is authorized without a corresponding operator-action row in the chain; or the capacity ledger cannot be computed because the recorded number is dominated by tab-open wall clock rather than attended time; or the full diff is opened on a majority of Phase 1 tasks carrying no anomaly flag, meaning criterion-first review is not what is happening.

## Fields

| Field | Value |
|---|---|
| `rationale` | Phase 1 places a human gate on every one of 20+ tasks and major-fix #10 makes *"projected human-minutes ≤ capacity"* an executable gate whose input is human minutes per task — a number the plan gave no instrument for. `run-instrumentation-specification.md` already specifies `task_end.human_review_ms` as *"recorded from the review interaction, not estimated"*, **a field with no producer anywhere in |

## Enforced by (code)

- **enforced_by** → [[module__harness_evidence_store|Append-only, hash-chained evidence writes.]] — # stable if a table is ever renamed, and so D51's "distinguished by ACS-1 domain
- **enforced_by** → [[module__harness_evidence_store|Append-only, hash-chained evidence writes.]] — """One operator action, written before its side effect is emitted (D51).

        `attended_ms` and `attended_ms_upper` 
- **enforced_by** → [[module__migrations_harness_evidence_versions_0001_evidence_base|evidence: run records, verdicts, operator actions, artifacts, defect escapes.]] — # D51. The one actor who can override every gate becomes an audited writer.
- **enforced_by** → [[module__migrations_roles_002_grants_sql|migrations/roles/002_grants.sql]] — D51. This INSERT is alfred_operator's only INSERT anywhere in the
- **enforced_by** → [[module__migrations_roles_grants_yaml|migrations/roles/grants.yaml]] — Mission control command surface (D51). Its ONLY INSERT anywhere in the cluster is
- **enforced_by** → [[module__migrations_roles_grants_yaml|migrations/roles/grants.yaml]] — Mission control read model (D51) — agents may build it. SELECT and nothing else,
