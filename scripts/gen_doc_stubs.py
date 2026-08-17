"""Generate the Alfred documentation register as stubs (D32).

A stub is header contract + two-sentence purpose + enforcement mechanism +
falsification condition + expiry. Full content is reserved for documents the
current phase can actually falsify; everything else stays a stub until the
evidence exists to write it honestly.

This script never overwrites an existing file. Documents promoted to full
content are edited in place and stay that way.

    python3 scripts/gen_doc_stubs.py [--dry-run]
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"


@dataclass(frozen=True)
class Doc:
    tier: int
    slug: str
    title: str
    owner: str          # human | generated | executable
    enforcement: str    # ci-gate | schema | generated | review-cadence | none
    status: str         # frozen | provisional | directional
    purpose: str
    falsifies_if: str
    review_after: str


REGISTER: list[Doc] = [
    # ---------------------------------------------------------------- Tier 1
    Doc(1, "system-blueprint", "System Blueprint", "human", "review-cadence", "provisional",
        "The architecture of record: control/execution/evidence planes, the graph model, and the "
        "port blueprint across all phases. Every other architecture document refines a part of it.",
        "A phase ships a component that has no seam in this blueprint.", "Phase 2"),
    Doc(1, "domain-model", "Domain Model", "generated", "generated", "provisional",
        "The canonical trajectory and scenario schemas, generated from the Pydantic definitions. "
        "It is the load-bearing abstraction every metric and adapter depends on.",
        "The generated model diverges from what the ingest adapters actually produce.", "Phase 1"),
    Doc(1, "port-catalog", "Port Catalog", "generated", "generated", "provisional",
        "Every port, its responsibility, its fidelity level, and the constraint it must satisfy. "
        "Generated from the port registry so it cannot drift from the interfaces.",
        "An external system is reached without passing through a catalogued port.", "Phase 2"),
    Doc(1, "state-and-graph-specification", "State and Graph Specification", "executable", "schema", "provisional",
        "The typed state channels, their owning writers, and the reducers required for fan-in. "
        "Executable as the LangGraph state schema, not prose.",
        "A state field is written by more than one node without a declared reducer.", "Phase 3"),
    Doc(1, "data-architecture", "Data Architecture", "executable", "schema", "frozen",
        "The Postgres schema, its tenancy scoping, append-only evidence tables, and the migration "
        "split between product and harness roles. Executable as Alembic migrations.",
        "A table lacks org/project scoping, or an evidence row is mutated after write.", "Phase 2"),
    Doc(1, "cross-stage-invariants", "Cross-Stage Invariants", "executable", "ci-gate", "frozen",
        "The dozen properties that must hold from the first commit because each costs hours now and a "
        "migration later. Enforced by CI lint rather than by intention.",
        "Any invariant is found violated in merged code.", "Phase 2"),
    Doc(1, "mission-control-specification", "Mission Control Specification", "executable", "schema", "provisional",
        "The operator surface: queue, escalation inbox, criterion-first evidence bundle, and run record. "
        "Every operator action is an evidence row, and review time is measured by the harness, not reported.",
        "A merge is authorized without a corresponding operator-action row in the evidence chain.", "Phase 1"),
    Doc(1, "failure-semantics", "Failure Semantics and Error Handling", "executable", "ci-gate", "frozen",
        "What the system does when something does not work: the three-valued verdict, the fail-closed table, the "
        "error taxonomy, timeout and retry rules, crash recovery, and errors as an attack surface.",
        "A run reaches a verdict while a gating control cannot be shown to have executed, or a harness fault is "
        "recorded as an agent failure.", "Phase 1"),
    Doc(1, "adr-log", "ADR Log", "human", "none", "frozen",
        "Immutable, dated architecture decision records, including every stage-gate waiver. Historical "
        "claims are never revised, only superseded.",
        "An ADR is edited after publication rather than superseded.", "Phase 4"),
    Doc(1, "technology-selection-records", "Technology Selection Records", "human", "none", "frozen",
        "Immutable records of each technology choice with the evidence and the alternatives rejected. "
        "Includes the Phase -1 lane selection and its measurements.",
        "A technology is adopted with no corresponding record.", "Phase 3"),

    # ---------------------------------------------------------------- Tier 2
    Doc(2, "stage-gate-definitions", "Stage Gate Definitions", "executable", "ci-gate", "frozen",
        "Each phase's exit criteria and forbidden-advancement conditions, expressed as executable checks "
        "where measurable. Overriding one requires an immutable waiver ADR.",
        "A phase is exited with a gate red and no waiver ADR recorded.", "Phase 2"),
    Doc(2, "build-protocol", "Build Protocol", "human", "review-cadence", "provisional",
        "How work moves from intent to merged change, and who or what acts at each step. The narrative "
        "companion to the executable gates.",
        "The described flow no longer matches what the dispatcher actually does.", "Phase 3"),
    Doc(2, "task-specification-standard", "Task Specification Standard", "executable", "schema", "frozen",
        "The schema a work item must satisfy to be schedulable, including its executable acceptance "
        "criterion. Prose-only tasks fail validation and escalate.",
        "A task is dispatched without an executable criterion.", "Phase 1"),
    Doc(2, "criterion-authoring-guide", "Criterion Authoring Guide", "human", "review-cadence", "provisional",
        "How to write a criterion that is executable, non-gameable, and correctly paired with a held-out "
        "counterpart. Written from real authoring experience, not in advance.",
        "Criteria written to this guide show a visible/held-out gap no better than those without it.", "Phase 2"),
    Doc(2, "coding-standards", "Coding Standards", "executable", "ci-gate", "frozen",
        "The ruff and pyright --strict configuration, enforced as a hard gate rather than advice. Strict "
        "mode is enforced while the codebase is small because retrofitting it later is impractical.",
        "Merged code carries a type suppression without a recorded justification.", "Phase 2"),
    Doc(2, "testing-strategy", "Testing Strategy", "human", "ci-gate", "frozen",
        "Property tests over composed operations as the load-bearing correctness control, with the visible "
        "and held-out criterion classes and their separation. Mutation score has no gating role.",
        "A composed property test is found that the agent could satisfy by special-casing.", "Phase 2"),
    Doc(2, "harness-self-test-specification", "Harness Self-Test Specification", "executable", "ci-gate", "provisional",
        "The suites that test the harness itself: two-sided seeded-defect ladder, null-agent floor, "
        "fault injection by disposition, boot-control negative tests, and the restore drill.",
        "A suite here passes while the control it guards is disabled.", "Phase 1"),
    Doc(2, "execution-order", "Execution Order", "human", "review-cadence", "provisional",
        "What gets built in what order, what each stage blocks, and which items are operator-owned. "
        "Distinct from READING-MAP.md, which orders documents rather than work.",
        "A stage is completed out of order without a waiver and the stage it blocked is unaffected.", "Phase 0 exit"),
    Doc(2, "review-protocol", "Review Protocol", "human", "review-cadence", "provisional",
        "Criterion-first review: intent, then criterion, then evidence bundle, then diff summary, with the "
        "full diff read only on signal. Review time is recorded as a task-size signal.",
        "Defects that reach merge are ones a full-diff read would routinely have caught.", "Phase 2"),
    Doc(2, "definition-of-done", "Definition of Done", "executable", "ci-gate", "frozen",
        "The merge gate: every condition a change must satisfy before it can land. Executable, so 'done' is "
        "never a judgment call.",
        "A change merges with any gate condition unmet.", "Phase 1"),
    Doc(2, "branch-release-deploy-protocol", "Branch, Release and Deploy Protocol", "executable", "ci-gate", "frozen",
        "Branch naming, protected refs, release tagging, and the CI-triggered deploy path with rollback. "
        "Agent branches cannot trigger secret-bearing workflows.",
        "A deploy occurs by any path other than CI on merge.", "Phase 2"),

    # ---------------------------------------------------------------- Tier 3
    Doc(3, "agent-definition-standard", "Agent Definition Standard", "executable", "schema", "provisional",
        "The schema every agent definition must satisfy: input contract, output contract, tools, permissions, "
        "criteria, escalation. Roles are not valid agent definitions.",
        "An agent is dispatched whose definition names a job title rather than a capability.", "Phase 2"),
    Doc(3, "agent-catalog", "Agent Catalog", "executable", "schema", "directional",
        "One specification per agent, conforming to the Agent Definition Standard. Written from observed "
        "capability boundaries, not from an imagined org chart.",
        "A catalogued agent has no golden tasks and therefore no measurable merge rate.", "Phase 3"),
    Doc(3, "tool-specification-standard", "Tool Specification Standard", "executable", "schema", "provisional",
        "The contract every tool declares: signature, side effects, blast radius, idempotency. Tool "
        "descriptions are hashed into the fingerprint because descriptions alone can change behaviour.",
        "A tool's behaviour changes without its description hash changing.", "Phase 2"),
    Doc(3, "context-engineering-guide", "Context Engineering Guide", "human", "review-cadence", "provisional",
        "How context is assembled: minimal deterministic seed, most-stable-first ordering for prefix-cache "
        "reuse, retrieved content appended last, and full read-recording. Prefix order is architecture.",
        "A context change invalidates cached prefixes without a context_strategy_version bump.", "Phase 2"),
    Doc(3, "instruction-and-prompt-standard", "Instruction and Prompt Standard", "executable", "schema", "provisional",
        "Prompts are versioned, tested artifacts carrying their own identity in the fingerprint. An unversioned "
        "prompt cannot support an autonomy grant.",
        "A prompt reaches an agent without a recorded version.", "Phase 2"),
    Doc(3, "run-instrumentation-specification", "Run Instrumentation Specification", "executable", "schema", "provisional",
        "Every field a Phase 1 run emits, so that long-horizon execution and goal seeking become measurable "
        "after the fact. Retrofitted instrumentation measures nothing about runs already completed.",
        "A Phase 1 run completes and a question it must answer cannot be answered from the emitted records.", "Phase 1"),
    Doc(3, "agent-evaluation-protocol", "Agent Evaluation Protocol", "human", "ci-gate", "directional",
        "How a capability is measured: golden set construction against parent commits, stratification, and the "
        "detectable effect size every comparison must report.",
        "A configuration change is accepted on an effect size below the set's resolution.", "Phase 3"),
    Doc(3, "autonomy-graduation-policy", "Autonomy Graduation Policy", "executable", "ci-gate", "directional",
        "The thresholds and evidence required to grant unattended operation per task-class, and the conditions "
        "that revoke it. Calibrated on held-out pass rate only.",
        "A grant is issued on visible-criterion pass rate, or survives a fingerprint change.", "Phase 4"),
    Doc(3, "escalation-protocol", "Escalation Protocol", "executable", "schema", "provisional",
        "The structural triggers that raise an escalation and the attempt bundle each carries. Agent-initiated "
        "escalation is permitted as a budget optimization but never load-bearing.",
        "An agent run terminates without either a verdict or a structurally triggered escalation.", "Phase 2"),
    Doc(3, "handoff-contract-standard", "Handoff Contract Standard", "executable", "schema", "provisional",
        "What passes between nodes: content-addressed evidence refs, never agent-authored summaries. A summary "
        "is lossy compression by an interested party.",
        "A handoff carries prose the successor relies on without reading the underlying artifact.", "Phase 3"),

    # ---------------------------------------------------------------- Tier 4
    Doc(4, "threat-model", "Threat Model", "human", "review-cadence", "frozen",
        "The adversaries and failure modes this architecture is built against: prompt injection, tool poisoning, "
        "reward hacking, exfiltration, model substitution, and memory-mediated injection.",
        "An incident occurs whose mechanism is absent from this model.", "Phase 2"),
    Doc(4, "permission-and-identity-model", "Permission and Identity Model", "executable", "schema", "frozen",
        "Which identity may do what: OS users, DB roles with column-level grants, and the separation between "
        "harness and agent. Physical boundaries, never runtime field-name checks.",
        "An agent-role connection succeeds against a held-out or verdict table.", "Phase 1"),
    Doc(4, "protected-paths-policy", "Protected Paths Policy", "executable", "ci-gate", "frozen",
        "The paths no agent may modify, defined by ground-truth provenance rather than enumeration of bad cases. "
        "Enforced by the harness on the patch, outside the container.",
        "A merged diff touches a protected path.", "Phase 1"),
    Doc(4, "sandbox-specification", "Sandbox Specification", "executable", "ci-gate", "frozen",
        "The container contract: ephemerality, filesystem mounts, network deny-by-default with allowlist, and the "
        "egress canary that must fail before a run may start.",
        "A sandbox boots while a known non-allowlisted connection succeeds.", "Phase 1"),
    Doc(4, "secrets-management-policy", "Secrets Management Policy", "executable", "ci-gate", "frozen",
        "Where secrets live, which scopes they carry, and the startup assertion that no secret-bearing environment "
        "variable exists inside the sandbox. No VCS credential ever enters the container.",
        "Any credential is found reachable from agent context.", "Phase 1"),
    Doc(4, "supply-chain-policy", "Supply Chain Policy", "executable", "ci-gate", "frozen",
        "Dependency pinning by hash across the full closure, runtime images pinned by digest and mirrored locally, "
        "and model provenance recorded by artifact hash rather than quant name.",
        "A dependency or image resolves to something other than its pinned digest.", "Phase 1"),
    Doc(4, "data-classification-and-handling", "Data Classification and Handling", "human", "review-cadence", "provisional",
        "How datasets are classified by licence and sensitivity, and what each class permits. Records that the "
        "CommonRoad corpus is used under a software licence applied to data.",
        "A dataset is used outside the permissions its licence grants.", "Phase 0.5"),
    Doc(4, "audit-and-retention-policy", "Audit and Retention Policy", "executable", "ci-gate", "frozen",
        "Hash-chained evidence rows, the off-machine chain-head anchor, retention periods, and the restore drill. "
        "Without the chain, the audit log is silently rewritable by anyone with one login.",
        "A restore drill fails, or a chain-head anchor is missing for any day.", "Phase 2"),
    Doc(4, "human-in-the-loop-policy", "Human-in-the-Loop Policy", "human", "review-cadence", "provisional",
        "Where a human must act, what they are accountable for, and what the harness must never delegate to them. "
        "The human checks what the harness structurally cannot.",
        "A human approval is required for something the harness could have decided deterministically.", "Phase 3"),

    # ---------------------------------------------------------------- Tier 5
    Doc(5, "product-requirements", "Product Requirements", "human", "review-cadence", "directional",
        "What the product must do for a named buyer, written from demand-gate conversations rather than from "
        "imagination. Directional until Phase 0.75 produces evidence.",
        "A requirement here is contradicted by what a named buyer actually asks for.", "Phase 0.75"),
    Doc(5, "domain-specification", "Domain Specification", "human", "ci-gate", "frozen",
        "The surrogate safety metrics Alfred implements, with formulas, citations, units and assumptions pinned to "
        "the published literature. The specification the agent implements against.",
        "An implemented metric diverges from the cited formula without a recorded justification.", "Phase 1"),
    Doc(5, "metric-catalog", "Metric Catalog", "generated", "generated", "provisional",
        "Generated inventory of implemented metrics with versions, units, tolerances and reference values. Derived "
        "from the metric registry so it cannot drift.",
        "A metric ships without a catalog entry.", "Phase 1"),
    Doc(5, "validation-and-benchmark-protocol", "Validation and Benchmark Protocol", "human", "ci-gate", "provisional",
        "How results are validated against the oracle and against held-out perturbations, and how benchmark runs are "
        "recorded immutably. Names what each comparison can and cannot establish.",
        "A benchmark claim is made that its method cannot support.", "Phase 2"),
    Doc(5, "api-reference", "API Reference", "generated", "generated", "provisional",
        "Generated from the FastAPI surface and Pydantic models. Never hand-edited.",
        "The published reference diverges from the served schema.", "Phase 1"),
    Doc(5, "edge-case-and-degeneracy-specification", "Edge Case and Degeneracy Specification", "human", "ci-gate", "frozen",
        "The catalog of degenerate inputs — vanishing denominators, absent conflict areas, sampling gaps, numerical "
        "instability — and the value each metric must return for them. Defines what the property tests assert.",
        "A metric returns a finite number for an input declared undefined, returns NaN anywhere, or a case observed in "
        "real scenario data appears nowhere in the catalog.", "Phase 1"),
    Doc(5, "model-and-algorithm-cards", "Model and Algorithm Cards", "human", "ci-gate", "frozen",
        "Per metric: assumptions, limits, and the published validity envelope stating when the output is meaningful. "
        "Shipped with the product, not internal.",
        "A metric is emitted outside its stated validity envelope without a warning.", "Phase 1"),
    Doc(5, "customer-documentation", "Customer Documentation", "human", "review-cadence", "directional",
        "What a customer needs to run, interpret and audit results, including the advisory feed and the obligation to "
        "apply correctness advisories.",
        "A customer cannot reproduce a delivered number from the documentation alone.", "Phase 2"),

    # ---------------------------------------------------------------- Tier 6
    Doc(6, "slo-sli-definitions", "SLO and SLI Definitions", "executable", "schema", "directional",
        "Service level indicators and objectives, including wall-clock per merged task and review-backlog depth as "
        "first-class factory metrics.",
        "An objective is breached repeatedly with no alarm configured for it.", "Phase 3"),
    Doc(6, "observability-standard", "Observability Standard", "executable", "ci-gate", "frozen",
        "Structured logging with trace and span IDs from the first commit, OpenTelemetry semantics, and causality "
        "recorded on every record. Correlation cannot be reconstructed retroactively.",
        "A record exists whose cause cannot be traced.", "Phase 2"),
    Doc(6, "runbooks", "Runbooks", "human", "review-cadence", "directional",
        "Operational procedures for the failures that actually occur, written after they occur. Empty until Phase 3 "
        "produces incidents.",
        "An incident is handled with no runbook and none is written afterwards.", "Phase 3"),
    Doc(6, "postmortem-archive", "Postmortem Archive", "human", "none", "frozen",
        "Immutable, dated postmortems. Historical claims, never revised.",
        "A postmortem is edited after publication.", "Phase 4"),
    Doc(6, "cost-management-policy", "Cost Management Policy", "executable", "ci-gate", "provisional",
        "The org-level ceilings in the currency that actually binds — lane wall-clock per task tree and tasks "
        "dispatched per day — plus the cash lines the company carries.",
        "A ceiling is exceeded without dispatch halting.", "Phase 3"),

    # ---------------------------------------------------------------- Tier 7
    Doc(7, "onboarding-guide", "Onboarding Guide", "human", "review-cadence", "provisional",
        "How a new human or a new agent context comes up to speed on Alfred. Serves both audiences because both read "
        "the same register.",
        "A newcomer following this guide reaches a wrong mental model of the containment boundary.", "Phase 3"),
    Doc(7, "decision-index", "Decision Index", "generated", "generated", "provisional",
        "Generated index of every architecture decision, amendment and waiver with its current status. The map from "
        "decision number to where it is enforced.",
        "A decision is enforced in code with no index entry.", "Phase 2"),
]

STUB = """---
status:        {status}
owner:         {owner}
enforcement:   {enforcement}
evidence:      none — written pre-Phase-0 as a register stub (D32)
falsifies_if:  {falsifies_if}
review_after:  {review_after}
---

# {title}

**Status: stub.** This document exists to hold its place in the register, declare what
will enforce it, and state what would prove it wrong. It is deliberately not written
out: content written before the evidence exists cannot be current, and a wrong document
is worse than an absent one.

## Purpose

{purpose}

## Enforcement

`{enforcement}` — owned by `{owner}`.

## Falsification condition

{falsifies_if}

## Promotion

Promote this stub to full content when Phase {review_after} can supply evidence for it.
On promotion, replace `evidence:` with what the content actually rests on.
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    created = skipped = 0
    for doc in REGISTER:
        path = DOCS / f"tier{doc.tier}" / f"{doc.slug}.md"
        if path.exists():
            skipped += 1
            continue
        created += 1
        if args.dry_run:
            print(f"would create {path.relative_to(DOCS.parent)}")
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            STUB.format(
                status=doc.status,
                owner=doc.owner,
                enforcement=doc.enforcement,
                falsifies_if=doc.falsifies_if,
                review_after=doc.review_after,
                title=doc.title,
                purpose=doc.purpose,
            )
        )
        print(f"created {path.relative_to(DOCS.parent)}")

    print(f"\n{created} created, {skipped} already present, {len(REGISTER)} in register")


if __name__ == "__main__":
    main()
