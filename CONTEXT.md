# Alfred — CONTEXT.md (Glossary)

**Generated:** 2026-08-24  
**Authority:** This file is the project's single glossary. Terms defined here are canonical; code and docs must agree. When a term is resolved in discussion, update this file immediately.

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
| **Protected Paths** | Files/directories an agent may never write. Enforced by `policy/protected-paths.json` and `scripts/lint_protected_paths.py`. Includes `docs/tier0/`, `docs/tier1/adr-log.md`, `harness/acs/`, `bench/results/`, `bench/fingerprints/`. |
| **Append-Only Path** | Protected path where only new files may be added; modifications/deletions fail CI. |
| **ACS-1** | Alfred Canonical Serialization v1 — JSON with floats as normalized scientific strings, keys UTF-8 byte-sorted, no whitespace, NFC-normalized strings, domain-separated hashing. Implemented in `harness/acs/acs1.py` + `harness/acs/acs1.mjs`. |

---

## Stage / Phase Terms

| Term | Definition |
|---|---|
| **S9 — Phase 1 Build** | Worker port + OpenHands adaptor + boot assertions C1–C15 + mission-control command surface. Blocked by O1. |
| **Phase 0** | Architecture & governance (ADRs, vault, register, plan mirror, protected paths). Complete. |
| **Phase −1** | Local-model benchmarking (`bench/`). Evidence only. |
| **O1–O6** | Obligations with deadlines (O1 capacity gate, O3/O4/O6 2026-09-09). |

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