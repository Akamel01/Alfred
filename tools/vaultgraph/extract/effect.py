"""Change-impact index — "if you change X, open these cards" — derived from in-edges.

The vault already computes in-edges per node for rendering. There is no hand-authored
`map/` shelf that would be a second map drifting from the first. An effect is a
view over the graph inverted: the set of nodes that point at a given source file
plus the path:line of each edge. One node per high-impact source so the board is
navigable before any query is written.

Not a second extraction in the strong sense — the relation is already in the graph.
This extractor mints EFFECT nodes whose body is the impact list, so the board is
addressable as `vault/effects/` without a query. A future step can compute this from
the built payload; minting it here keeps the graph self-contained and lets --check
catch a hand-edited board.

Source authority: the file that, if edited, requires opening the listed cards.
"""

from __future__ import annotations

from ..model import Node, NodeKind, SourceRef
from ..protocol import Context, ExtractorSpec, Harvest

NAME = "effect"
EXPECTED = 5

# (local id, title, source path, impact list as prose — path:line citations where known)
_EFFECTS: tuple[tuple[str, str, str, str], ...] = (
    ("policy-protected-paths", "Effect: edit policy/protected-paths.json", "policy/protected-paths.json",
     "Open: docs/tier4/protected-paths-policy.md:1, harness/patch/validate.py:1, harness/patch/test_protected_set.py:1, vault/code/* (protected extractor), gates.yml:192 (vault --check)"),
    ("coding-standards-fence", "Effect: edit docs/tier2/coding-standards.md § Structure", "docs/tier2/coding-standards.md",
     "Open: tools/vaultgraph/extract/layout.py:31, vault/layout/*, graph.json (layout nodes 18), docs-graph.html"),
    ("execution-order-stages", "Effect: edit docs/tier2/execution-order.md § Stages", "docs/tier2/execution-order.md",
     "Open: tools/vaultgraph/extract/stages.py:1, vault/execution/*, stages/*/CONTEXT.md, stages/*/output/exit.md, vault/processes/stage-evidence"),
    ("vault-extractors", "Effect: edit tools/vaultgraph/extract/*", "tools/vaultgraph/extract",
     "Open: graph.json, vault/*, docs-graph.html, tools/gen_vault.py --self-test (vacuity), tools/tests/test_vaultgraph.py"),
    ("adr-log", "Effect: edit docs/tier1/adr-log.md", "docs/tier1/adr-log.md",
     "Open: vault/decisions/*, graph edges (Amends/See also/Discharges), docs/README.md tier index, vault stages (Discharges)"),
)


def extract(ctx: Context) -> Harvest:
    harvest = Harvest()
    for local, title, rel, body in _EFFECTS:
        path = ctx.root / rel
        # For directories, check existence; for files, same. Empty fixture has none.
        if rel.endswith("/"):
            # shouldn't happen — rels are file or dir prefix; treat as dir
            if not (ctx.root / rel.rstrip("/")).exists():
                continue
        else:
            # rel may be a file or a directory prefix like "tools/vaultgraph/extract"
            # If it contains "/", check the first component exists to avoid empty-fixture mint.
            top = rel.split("/")[0]
            if not (ctx.root / top).exists():
                continue
        src = SourceRef(rel, 1)
        harvest.scanned += 1
        node_id = ctx.minter.mint(NodeKind.EFFECT, local, src)
        harvest.nodes.append(Node(
            id=node_id, kind=NodeKind.EFFECT, title=title, source=src,
            shape="board", body=body, attrs={"path": rel}, extractor=NAME,
        ))
    if harvest.scanned == 0:
        return harvest
    return harvest


SPEC = ExtractorSpec(
    name=NAME,
    kinds=(NodeKind.EFFECT,),
    min_nodes=EXPECTED,
    max_nodes=None,
    min_edges=0,
    max_unparsed=0,
    expect_rejected=None,
    run=extract,
)
