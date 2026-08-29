"""The 63 documents under `docs/tier0`…`tier7`, and the eight tiers that hold them.

**Enumerated from disk, never from a manifest.** `scripts/gen_doc_stubs.py` carries a
`REGISTER` list that is stale — 55 entries against 63 files, with nothing checking it. This
extractor globs the tree exactly as `scripts/lint_docs.py:169-174` does, and excludes the same
two generated files, so it cannot inherit that drift.

**`falsifies_if` is carried as data for the first time.** All 63 documents state the
observation that would kill them, and until now that statement existed only as prose inside a
frontmatter block. It is not modelled as an edge: an edge needs a target node, and "an evidence
row is found mutated after write" is an observation, not a node. Inventing a node per condition
would make the graph look richer while saying nothing more. The condition is a first-class
field on the node, and the count of documents carrying one is asserted.
"""

from __future__ import annotations

from pathlib import Path

from ..model import Confidence, Edge, EdgeKind, Node, NodeKind, SourceRef
from ..protocol import Anomaly, Context, ExtractorSpec, Harvest, Unparsed
from ..textio import frontmatter_end_line, parse_frontmatter, read_lines, rel, title_of

NAME = "documents"

#: Mirrors `lint_docs.TIER_NAMES`. Kept as a copy for the reason `textio.parse_frontmatter`
#: states: `scripts/` is D20-protected, and importing from it would put a factory module in
#: the inspector's import closure.
TIER_NAMES = {
    0: "Constitution",
    1: "Architecture",
    2: "Build protocol",
    3: "Agent specifications",
    4: "Security and governance",
    5: "Product",
    6: "Operations",
    7: "Meta",
}

#: The two files under `docs/` that are generated rather than authored.
GENERATED = ("README.md", "READING-MAP.md")

STUB_SENTINEL = "**Status: stub.**"


def _document_paths(docs: Path) -> list[Path]:
    """Sorted, generated files excluded — the same enumeration `lint_docs.main` performs."""
    skip = {docs / name for name in GENERATED}
    return sorted(
        p for p in docs.rglob("*.md")
        if p not in skip and p.name != "CONTEXT.md"
    )


def extract(ctx: Context) -> Harvest:
    harvest = Harvest()
    docs = ctx.root / "docs"
    if not docs.is_dir():
        return harvest

    paths = _document_paths(docs)
    harvest.scanned = len(paths)

    tiers_seen: dict[int, str] = {}
    falsifies_count = 0

    for path in paths:
        rel_path = rel(path, ctx.root)
        fields, errors = parse_frontmatter(path)
        for message in errors:
            harvest.unparsed.append(
                Unparsed(NAME, SourceRef(rel_path, 1), message, "frontmatter did not parse")
            )
        if not fields:
            # No frontmatter at all: the node would carry none of the metadata that makes it
            # worth having. Report it rather than minting a hollow node.
            harvest.unparsed.append(
                Unparsed(NAME, SourceRef(rel_path, 1), rel_path, "no frontmatter — node not minted")
            )
            continue

        tier_dir = path.parent.name
        if not tier_dir.startswith("tier") or not tier_dir[4:].isdigit():
            harvest.unparsed.append(
                Unparsed(NAME, SourceRef(rel_path, 1), tier_dir, "document outside a tier directory")
            )
            continue
        tier_num = int(tier_dir[4:])
        tiers_seen.setdefault(tier_num, tier_dir)

        lines = read_lines(path)
        body_start = frontmatter_end_line(path) + 1
        title = title_of(lines, path.stem)
        is_stub = any(STUB_SENTINEL in line for line in lines)
        falsifies = fields.get("falsifies_if", "")
        if falsifies:
            falsifies_count += 1

        attrs = {
            "tier": str(tier_num),
            "tier_name": TIER_NAMES.get(tier_num, "unknown"),
            "path": rel_path,
            "written": "stub" if is_stub else "full",
            "evidence": fields.get("evidence", ""),
            "falsifies_if": falsifies,
            "owner": fields.get("owner", ""),
            "enforcement": fields.get("enforcement", ""),
            "review_after": fields.get("review_after", ""),
        }
        if "supersedes" in fields:
            attrs["supersedes"] = fields["supersedes"]

        node_id = ctx.minter.mint(
            NodeKind.DOCUMENT, f"{tier_dir}/{path.stem}", SourceRef(rel_path, 1)
        )
        harvest.nodes.append(
            Node(
                id=node_id,
                kind=NodeKind.DOCUMENT,
                title=title,
                source=SourceRef(rel_path, 1, body_start),
                shape="file",
                status=fields.get("status", ""),
                attrs=attrs,
                tags=(f"tier{tier_num}", fields.get("owner", ""), fields.get("enforcement", "")),
                extractor=NAME,
            )
        )

    for tier_num in sorted(tiers_seen):
        tier_dir = tiers_seen[tier_num]
        tier_src = SourceRef(f"docs/{tier_dir}", 1)
        tier_id = ctx.minter.mint(NodeKind.TIER, tier_dir, tier_src)
        harvest.nodes.append(
            Node(
                id=tier_id,
                kind=NodeKind.TIER,
                title=f"Tier {tier_num} — {TIER_NAMES.get(tier_num, 'unknown')}",
                source=tier_src,
                shape="directory",
                attrs={"tier": str(tier_num)},
                extractor=NAME,
            )
        )
        for node in harvest.nodes:
            if node.kind is NodeKind.DOCUMENT and node.attrs["tier"] == str(tier_num):
                harvest.edges.append(
                    Edge(
                        src=tier_id,
                        dst=node.id,
                        kind=EdgeKind.CONTAINS,
                        confidence=Confidence.STRUCTURAL,
                        source=node.source,
                        evidence=node.attrs["path"],
                        extractor=NAME,
                    )
                )

    documents = [n for n in harvest.nodes if n.kind is NodeKind.DOCUMENT]
    if documents and falsifies_count != len(documents):
        harvest.anomalies.append(
            Anomaly(
                kind="missing-falsification-condition",
                detail=(
                    f"{len(documents) - falsifies_count} of {len(documents)} documents carry no "
                    "falsifies_if — the register requires one wherever evidence is none"
                ),
            )
        )
    return harvest


SPEC = ExtractorSpec(
    name=NAME,
    kinds=(NodeKind.DOCUMENT, NodeKind.TIER),
    # 63 documents + 8 tiers today. A minimum rather than an exact count: docs/ is the one
    # input that legitimately grows, and a new document must not red the build.
    min_nodes=71,
    max_nodes=None,
    min_edges=63,
    max_unparsed=0,
    expect_rejected=None,
    run=extract,
)
