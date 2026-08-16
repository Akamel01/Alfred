"""Generate docs/READING-MAP.md — what to read, when, and what it binds.

The register index answers "what exists". It does not answer the question someone
actually has when they sit down to build Phase 0: *which of these 57 documents
constrain the code I am about to write, and in what order do they make sense?*

The map is generated rather than written, and the mapping table below is its single
source. `--check` fails when a document exists with no entry, when an entry names a
document that does not exist, or when the committed map is stale — so a document added
without a reading position breaks the build instead of quietly becoming invisible.

    python3 scripts/gen_reading_map.py [--check]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
MAP = DOCS / "READING-MAP.md"
ADR_LOG = DOCS / "tier1" / "adr-log.md"

BINDING = "binding"      # constrains code you are about to write; violating it is a defect
CONTEXT = "context"      # explains why; read once, do not re-read per task
RECORD = "record"        # historical or generated; consult, never follow

# phase -> ordered list of (slug, kind, why)
# Order within a phase is reading order, chosen for dependency rather than tier.
PHASES: list[tuple[str, str, list[tuple[str, str, str]]]] = [
    ("always", "Read once before anything else. Short, and everything downstream assumes them.", [
        ("charter-and-non-goals", CONTEXT, "what Alfred is, what it will not do, and the kill criteria"),
        ("operating-principles", CONTEXT, "nine principles, each naming the failure it answers"),
        ("autonomy-boundaries", BINDING, "what is permanently outside agent reach, and why"),
        ("glossary", CONTEXT, "binding definitions — terms here mean exactly this"),
        ("documentation-standard", BINDING, "the header contract every document obeys; read before writing one"),
    ]),
    ("phase -1", "Model lane selection. Complete — read only to understand why the lane is what it is.", [
        ("supply-chain-policy", BINDING, "model provenance, quantization artifact hashes, fingerprint fields"),
    ]),
    ("phase 0", "Product skeleton. The largest reading set, because Phase 0 builds what cannot be retrofitted.", [
        ("cross-stage-invariants", BINDING, "what every table, ID and API must carry from the first commit"),
        ("data-architecture", BINDING, "schemas, DB roles, the hash chain, held-out isolation by SQL grant"),
        ("adr-log", BINDING, "ADR-0001 to 0004 constrain every metric signature and every hashed record"),
        ("edge-case-and-degeneracy-specification", BINDING, "what each metric returns for degenerate input; defines the property tests"),
        ("domain-specification", BINDING, "the formulas, citations and units being implemented"),
        ("failure-semantics", BINDING, "three-valued verdicts, fail-closed table, error taxonomy, retry rules"),
        ("coding-standards", BINDING, "toolchain, strict typing as a hard gate, source layout"),
        ("testing-strategy", BINDING, "composed property tests are load-bearing; what has no gating role"),
        ("definition-of-done", BINDING, "the twelve executable merge conditions"),
        ("protected-paths-policy", BINDING, "what an agent may never write, and what enforces it"),
        ("sandbox-specification", BINDING, "container contract, network posture, egress canary"),
        ("secrets-management-policy", BINDING, "no secret in the execution plane; startup assertions"),
        ("permission-and-identity-model", BINDING, "identities, held-out isolation, verdict ownership"),
        ("audit-and-retention-policy", BINDING, "append-only, hash chaining, restore drill, recall protocol"),
        ("threat-model", CONTEXT, "the ten threats the controls answer, and what is out of scope"),
        ("task-specification-standard", BINDING, "what makes a task schedulable; criterion structure"),
        ("model-and-algorithm-cards", BINDING, "validity envelopes ship with the product"),
        ("stage-gate-definitions", BINDING, "the executable exits, and the waiver discipline for overriding one"),
        ("branch-release-deploy-protocol", BINDING, "deploy and rollback are Phase 0 exit criteria"),
        ("risk-register", CONTEXT, "open risks with revisit triggers; check before assuming something is handled"),
        ("criterion-authoring-guide", CONTEXT, "stub — promote once real criteria have been authored"),
    ]),
    ("phase 0.5", "Data licensing gate. Blocks any prospect-facing demo.", [
        ("data-classification-and-handling", BINDING, "stub — this phase supplies its evidence"),
    ]),
    ("phase 0.75", "Demand gate. Needs no code and no data licence.", [
        ("product-requirements", CONTEXT, "directional until named buyers say otherwise"),
        ("customer-documentation", CONTEXT, "directional — what a customer needs to reproduce a number"),
    ]),
    ("phase 1", "One agent, one task, human gate.", [
        ("worker-port-contract", BINDING, "what crosses into the execution plane; claim vs fault, read recording, containment preconditions"),
        ("run-instrumentation-specification", BINDING, "what every run emits; must exist BEFORE Phase 1 starts, not after"),
        ("mission-control-specification", BINDING, "the operator surface; the human gate is unrecorded and unmeasured without it"),
        ("mission-control-design", BINDING, "how that surface is built: reachability ladder, routes, forms, and the timing instrument's failure modes"),
        ("agent-definition-standard", BINDING, "an agent is a contract, never a job title"),
        ("agent-catalog", BINDING, "one specification per capability"),
        ("tool-specification-standard", BINDING, "contract, side effects, blast radius, idempotency"),
        ("state-and-graph-specification", BINDING, "field ownership, reducers, projections"),
        ("context-engineering-guide", BINDING, "seed layering; prefix order is architecture, not tuning"),
        ("instruction-and-prompt-standard", BINDING, "prompts are versioned and enter the fingerprint"),
        ("escalation-protocol", BINDING, "structural triggers; the agent cannot declare itself blocked"),
        ("handoff-contract-standard", BINDING, "evidence refs travel, agent-authored summaries do not"),
        ("review-protocol", CONTEXT, "criterion-first review; what the human checks that the harness cannot"),
        ("build-protocol", CONTEXT, "how work moves from intent to merge"),
    ]),
    ("phase 2", "Evidence and measurement. Generated documents become real here.", [
        ("agent-evaluation-protocol", BINDING, "golden sets, effect sizes, what n≈20 can and cannot detect"),
        ("validation-and-benchmark-protocol", BINDING, "what each comparison can support"),
        ("observability-standard", BINDING, "the evidence store is the observability system"),
        ("domain-model", RECORD, "generated from the schemas"),
        ("port-catalog", RECORD, "generated from the port definitions"),
        ("metric-catalog", RECORD, "generated from the metric registry"),
        ("api-reference", RECORD, "generated from the served schema"),
        ("decision-index", RECORD, "generated map from decision to where it is enforced"),
    ]),
    ("phase 3", "Throughput. Human review minutes are the binding resource.", [
        ("human-in-the-loop-policy", BINDING, "stub — needs this phase's capacity data"),
        ("slo-sli-definitions", BINDING, "what the product promises"),
        ("cost-management-policy", BINDING, "ceilings in wall-clock, since inference is free"),
        ("runbooks", CONTEXT, "written from real incidents, not imagined ones"),
    ]),
    ("phase 4", "Earned autonomy.", [
        ("autonomy-graduation-policy", BINDING, "thresholds, evidence, and revocation"),
    ]),
    ("reference", "Consult when relevant. Never a source of instructions.", [
        ("system-blueprint", CONTEXT, "the architecture of record; every other architecture document refines part of it"),
        ("technology-selection-records", RECORD, "what was chosen and what was rejected"),
        ("postmortem-archive", RECORD, "immutable incident history"),
        ("onboarding-guide", CONTEXT, "serves humans and agent context alike"),
    ]),
]

HEADER = """# Reading map

**Generated by `scripts/gen_reading_map.py`. Do not edit by hand.**

The register index lists what exists. This lists what to read, when, and whether it
constrains the code you are about to write.

| Kind | Means |
|---|---|
| **binding** | Constrains the code you are writing. Violating it is a defect, and most are CI-enforced. |
| **context** | Explains why. Read once; do not re-read per task. |
| **record** | Historical or generated. Consult it; never take instructions from it. |

Read **always** first. Then read your phase's list top to bottom — the order is
dependency order, not tier order. A phase inherits nothing: if you are in Phase 1, the
Phase 0 binding documents still bind.

"""

FOOTER_ADR = """
## Architecture decisions

Binding on implementation and easy to miss, since they live inside one document.

"""


def read_titles() -> dict[str, tuple[int, str, str]]:
    """slug -> (tier, title, status). Title is the first `# ` heading."""
    out: dict[str, tuple[int, str, str]] = {}
    for path in sorted(DOCS.glob("tier*/*.md")):
        text = path.read_text()
        tier = int(path.parent.name.removeprefix("tier"))
        title = next((l[2:].strip() for l in text.splitlines() if l.startswith("# ")), path.stem)
        status = ""
        for line in text.splitlines():
            if line.startswith("status:"):
                status = line.split(":", 1)[1].strip()
                break
        is_stub = "**Status: stub.**" in text
        out[path.stem] = (tier, title, "stub" if is_stub else status)
    return out


def read_adrs() -> list[tuple[str, str, str]]:
    """(id, title, status) for every ADR in the log."""
    if not ADR_LOG.exists():
        return []
    adrs: list[tuple[str, str, str]] = []
    text = ADR_LOG.read_text()
    for match in re.finditer(r"^## (ADR-\d+) — (.+)$", text, re.MULTILINE):
        tail = text[match.end():match.end() + 400]
        status = ""
        sm = re.search(r"\*\*Status:\*\* (\w+)", tail)
        if sm:
            status = sm.group(1)
        adrs.append((match.group(1), match.group(2).strip(), status))
    return adrs


def build() -> tuple[str, list[str]]:
    titles = read_titles()
    errors: list[str] = []
    seen: set[str] = set()
    lines = [HEADER]

    for phase, blurb, entries in PHASES:
        lines.append(f"## {phase.capitalize() if phase == 'always' else phase.title()}\n")
        lines.append(f"{blurb}\n")
        lines.append("| # | Document | Kind | Status | Why now |")
        lines.append("|---|---|---|---|---|")
        for n, (slug, kind, why) in enumerate(entries, 1):
            if slug not in titles:
                errors.append(f"reading map names a document that does not exist: {slug}")
                continue
            if slug in seen:
                errors.append(f"document listed in more than one phase: {slug}")
            seen.add(slug)
            tier, title, status = titles[slug]
            link = f"tier{tier}/{slug}.md"
            lines.append(f"| {n} | [{title}]({link}) | {kind} | {status} | {why} |")
        lines.append("")

    missing = sorted(set(titles) - seen)
    for slug in missing:
        errors.append(f"document has no reading-map entry: {slug}")

    adrs = read_adrs()
    if adrs:
        lines.append(FOOTER_ADR.rstrip())
        lines.append("")
        lines.append("| ADR | Decision | Status |")
        lines.append("|---|---|---|")
        for adr_id, title, status in adrs:
            lines.append(f"| [{adr_id}](tier1/adr-log.md) | {title} | {status} |")
        lines.append("")

    counts = {k: 0 for k in (BINDING, CONTEXT, RECORD)}
    for _, _, entries in PHASES:
        for _, kind, _ in entries:
            counts[kind] += 1
    lines.append(
        f"---\n\n**{len(seen)} documents mapped** · {counts[BINDING]} binding · "
        f"{counts[CONTEXT]} context · {counts[RECORD]} record · {len(adrs)} architecture decisions\n"
    )
    return "\n".join(lines), errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    content, errors = build()
    if errors:
        for e in errors:
            print(f"ERROR {e}", file=sys.stderr)
        sys.exit(1)

    if args.check:
        if not MAP.exists() or MAP.read_text() != content:
            print("ERROR docs/READING-MAP.md is stale — run scripts/gen_reading_map.py", file=sys.stderr)
            sys.exit(1)
        print("OK reading map current")
        return

    MAP.write_text(content)
    print(f"wrote {MAP.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
