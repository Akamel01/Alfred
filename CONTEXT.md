# Alfred — CONTEXT.md (Glossary — factory + workflow)

**Generated:** 2026-08-24 · **Updated:** 2026-08-29  
**Authority:** This file is the factory + workflow glossary (volatile, evolves with the factory). Architecture + domain terms live in `docs/tier0/glossary.md` (frozen, human, binding across the register). Where they disagree on a shared term, `docs/tier0/glossary.md` wins. Terms defined here are canonical for factory/workflow; code and docs must agree. When a term is resolved in discussion, update this file immediately.

---

## Core Terms

| Term | Definition |
|---|---|
| **Run Fingerprint** | Immutable 27-field record (`RunFingerprint` in `harness/fingerprint/record.py`) stating what a run was measured on. Hash derived via ACS-1, never supplied. Fields grouped: D19 (requalification), D40 (measurement comparability), lane (serving), worker (executor/provisioning). |
| **Capacity Gate (O1)** | Weekly budget `F` (minutes) and daily merge target `n` that size S9 work packets. `F = 1200 min/week`, `n = 5 merged/day`. |
| **Boot Assertions C1–C15** | Containment assertions in `harness/containment/`; C4 & C11 require a Run Fingerprint record to execute. |
| **Worker Port** | `harness/worker/port.py` — executable contract: `Worker` protocol, `SandboxHandle`, `WorkerOutcome`, fault taxonomy. |
| **Rehearsal Adaptor** | First `Worker` implementation (landed `47614cd`) exercising the port against a fake executor. |
| **Real OpenHands Adaptor** | Production `Worker` implementation wrapping `OpenHands/software-agent-sdk@d460d1a0` (pinned by ADR-0018). |
| **Mission-Control Command Surface** | Operator-built (D51) CLI/API over the Worker port; separate from adaptor. |
| **arity** | "The number of independent observations a metric aggregates" (ADR-0037). `len(series)` is actual observations collected; mismatch = data loss/injector bug. |
| **Protected Paths** | The single set `policy/protected-paths.json` (ADR-0031/0035) — prefixes `harness/`, `src/provenance/`, `src/thresholds/`, `tests/heldout/`, `migrations/harness/`, `migrations/roles/`, `scripts/`, `policy/`, `.github/`, `docs/tier0/`, `bench/results/`, `bench/fingerprints/`, `orchestration/` + files `pyproject.toml`, `uv.lock`. Enforced by `harness/patch/validate.py`. |
| **Append-Only Path** | Protected path where only new files may be added; modifications/deletions fail CI. |
| **ACS-1** | Alfred Canonical Serialization v1 — JSON with floats as normalized scientific strings, keys UTF-8 byte-sorted, no whitespace, NFC-normalized strings, domain-separated hashing. Implemented in `harness/acs/acs1.py` + `harness/acs/acs1.mjs`. |

---

## Stage / Phase Terms

| Term | Definition |
|---|---|
| **S9 — Phase 1 Build** | Worker port + OpenHands adaptor + boot assertions C1–C15 + mission-control command surface. Blocked by O1. |
| **Phase 0** | Architecture & governance (ADRs, vault, register, plan mirror, protected paths). Complete. |
| **Phase −1** | Local-model benchmarking (`bench/`). Evidence only. |
| **O1–O9** | Operator-owned obligations in `docs/tier2/execution-order.md` § Operator-owned, non-delegable: O1 capacity gate (blocks S9), O2 defect-escape window, O3 D49 P3, O4 Phase 0 exit, O5 discharged (ADR-0018, 2026-08-18), O6 company formation, O7 EU register lookup, O8 discovery conversations, O9 line-by-line inspector review. Deadlines per that table. |

---

## Vault / Register Terms

| Term | Definition |
|---|---|
| **Vault** | Generated knowledge graph (`vault/`, `graph.json`, `docs-graph.html`) from source extractors. Never hand-edited. Regenerated via `python3 tools/gen_vault.py`. |
| **Register** | Document catalog in `docs/README.md` — what exists, what binds, what is generated. |
| **Extractor** | Module in `tools/vaultgraph/extractors/` that emits vault nodes from a source tree (Python, Markdown, SQL, etc.). |

---

## Policy / Governance Terms

| Term | Definition |
|---|---|
| **D20** | Inspector discipline: protected-path changes require line-by-line human review + ADR + commit message recording the chain. |
| **Gate D** | ADR review gate for inspector-touching changes. |
| **Gate E** | Per-deletion confirmation for git refs (worktrees, branches). |
| **HITL** | Human-in-the-loop — task requires operator action, not AFK. |
| **AFK** | Away-from-keyboard — task executable by agent without operator presence. |
| **Wayfinder Ticket** | Typed work unit: `research` | `prototype` | `grilling` | `task`; each tagged `HITL` or `AFK`. |

---

## Evidence / Bench Terms

| Term | Definition |
|---|---|
| **bench/results/** | Per-seed benchmark evidence (immutable, append-only via protected paths). |
| **bench/fingerprints/** | Per-seed Run Fingerprint records (immutable, append-only). Produced by `scripts/capture_run_fingerprint.py`. |
| **Mutation Testing** | `harness/mutation/` — 47/47 mutants caught at last run; validates criterion/evidence chain. |
| **Verify JS** | `harness/acs/verify_js.mjs` — 505 cross-checks of ACS-1 canonicalization. |

---

## Git / Workflow Terms

| Term | Definition |
|---|---|
| **Plan Mirror** | `plan/` — sha256-pinned copy of the plan of record; CI verifies hash on every runner. |
| **Manifest** | `plan/manifest.json` — maps plan sections to file hashes. |
| **Structural Fix** | Walk-test term: a code change required because a cold agent could not navigate (vs. content fix). |
| **Cold Agent** | Fresh session with no prior conversation context; used for W8 walk test. |

---

## Orchestration Canvas Terms

| Term | Definition |
|---|---|
| **Orchestration Node** | A vertex in the topology graph representing a role/agent kind (from palette). |
| **Node Kind** | The `id` of a palette entry; the type of a node. |
| **Contract Edge** | A directed typed connection between two nodes representing a hand-off or authority relationship. |
| **Port Compatibility** | The rule that an edge's contract type must be legal for the (source-kind, target-kind) pair per the compatibility matrix. |
| **Topology Source** | The hand-authored `orchestration/topology.json` file — the single source of truth for the graph. |
| **Canvas Artifact** | The generated interactive HTML file (`orchestration-canvas.html`) that edits the topology source. |

ENDOADR

---

## Execution Lifecycle Terms

Resolved 2026-09-02 in [ticket #42](https://github.com/Akamel01/Alfred/issues/42).

| Term | Definition |
|---|---|
| **Execution Lifecycle** | The seven-phase sequence a task walks: Discover → Grill → Architect → Plan → Execute → Review → Validate. Method, not machinery — `enforcement: review-cadence`. It owns the *sequence*; it does not restate the merge gate. |
| **Phase** | One step of the lifecycle. A phase terminates when its required artifact exists and validates. It does not terminate because the executing agent says it is done. |
| **Phase termination check** | The verification that a phase's required artifact exists and validates. Performed by the **orchestrator**, never by the child that produced the artifact. |
| **Front half / back half** | Discover · Grill · Architect · Plan are the front half (method, ungated). Execute · Review · Validate are the back half, gated by the twelve Definition-of-Done conditions. The lifecycle document cites DoD; it never restates it. |
| **Critique pass** | The independent challenge of a plan, folded into the Plan phase rather than carried as a separate phase. It is what makes plan auto-approval safe: the check on a plan is a reviewer role, not a human gate. |
| **Re-entry** | A phase moving **backward** after a downstream failure. Distinct from escalation. A static default table gives the re-entry point; the reviewer or validator that found the failure may override it **upstream only**, recording the reason. A finder may never send work downstream of the default. |
| **Escalation** | The run **stopping** and a human being summoned. Distinct from re-entry. Triggers are structural and owned by `docs/tier3/escalation-protocol.md` (`enforcement: schema`), not by agent discretion. Agent-initiated escalation is a budget optimization, never load-bearing. |
| **Task class** | The declared class assigned to a task **by the orchestrator before dispatch**, never chosen by the executing agent. It scales the front half; the back half is unconditional. The `trivial` class definition is owned by [ticket #46](https://github.com/Akamel01/Alfred/issues/46). |
| **Never authoritative** | A capability that may inform a reviewer but may never be a gate. `agent-self-evaluation` is classified this way: a self-reported verdict from the executing session is the failure the execution/review separation exists to prevent. |
---

## State Authority Terms

Resolved 2026-09-02 in [ticket #45](https://github.com/Akamel01/Alfred/issues/45).

| Term | Definition |
|---|---|
| **Ownership router** | The table in `docs/tier1/data-architecture.md` § *Ownership, stated once so it is not restated inconsistently*. It says which document owns which fact; it holds no content of its own. Extended by adding rows, never by describing. |
| **The collision rule** | "The stream is a field set, the store is a schema, and the store never re-declares a stream field." Adding a field to a record is a Run Instrumentation change plus a validator change — never a migration. |
| **Runtime state** | Machine-local, gitignored, disposable state (`.autoforge/`, any ECC or ECC2 store). Never cited by a gate, a verdict, or an audit. If a fact matters it is emitted into the run record stream when it happens; the runtime copy is incidental. |
| **Display-only** | A runtime fact Mission Control may render for liveness, carrying provenance saying it is unverified. A missing display-only fact renders as **unknown**, never as **none**. |
| **Homes table** | The per-fact authority map recorded in `docs/tier7/ticket-45-state-authority-decision.md`. Everything not named as a home is derived, disposable, or display-only. |
| **Type graph / instance graph** | The type graph is `policy/node-palette.json` + `orchestration/topology.json` — which roles exist and how they may connect (protected, ADR-0039). The instance graph is `control.work` — which tasks exist and what blocks what. The instance graph is validated by the type graph; it is not a second authority. |
---

## Role Binding Terms

Resolved 2026-09-02 in [ticket #43](https://github.com/Akamel01/Alfred/issues/43).

| Term | Definition |
|---|---|
| **Role Binding** | The record that turns a palette *role* into an agent *definition*: kind, `bindable`, `capability_id`, agents keyed by phase, a model **reference**, tools, permissions, context budget, and the three version fields. Schema owned by `docs/tier3/agent-definition-standard.md`; executable form in `policy/role-bindings.json` (protected). |
| **`bindable`** | Three states: `agent` (bound), `unbound` (could be, is not), `never` (must never be delegated to an agent — the eight `operator` palette kinds). Cross-checked by lint against `category == "operator"`; disagreement fails. |
| **Model reference** | A binding names a *routing key*, never a literal model. The key resolves against the model-routing policy ([#46](https://github.com/Akamel01/Alfred/issues/46)). A binding that names a literal model is a second home for a fact #46 owns. |
| **Requalification event** | A binding edit. Its version fields are the Run Fingerprint's D19 group, so changing one triggers tiered requalification. This is what keeps a silent binding edit distinguishable from genuine capability drift. |
