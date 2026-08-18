"""Planted fixtures that prove the guards fire, and a clean control that proves they are quiet.

Shipped as a mode rather than left in the test suite, following
`scripts/lint_verdict_boundary.py:237-284`, so the proof travels with the code and runs in the
same place the generator runs.

The control is the part that is easy to leave out and the part that matters most. A guard that
fires on everything passes every "it fired" assertion and is worthless. So the control fixture
is built to sit *adjacent* to what the extractor rejects — a `docs/` tree holding the two
generated files the enumeration must skip, beside two real documents it must not — and it has
to come back with exactly two nodes and nothing flagged.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from .extract import EXTRACTORS, documents
from .model import Minter, MintError, Node, NodeKind, SourceRef
from .protocol import Context, ExtractorSpec, Harvest, Rejected, Unparsed
from .runner import _audit, run
from .serialize import build_payload, dumps

DOC = """---
status:        frozen
owner:         human
enforcement:   none
evidence:      none — planted fixture
falsifies_if:  This fixture is read as anything other than a fixture.
review_after:  Phase 4
---

# {title}

Body.
"""


def _plant(root: Path) -> None:
    docs = root / "docs"
    (docs / "tier0").mkdir(parents=True)
    (docs / "tier1").mkdir(parents=True)
    (docs / "tier0" / "charter.md").write_text(DOC.format(title="Charter"), encoding="utf-8")
    (docs / "tier1" / "architecture.md").write_text(DOC.format(title="Architecture"), encoding="utf-8")
    # The adjacent pair: same directory, same extension, same frontmatter shape. Generated,
    # therefore excluded — exactly as `lint_docs.main` excludes them.
    (docs / "README.md").write_text(DOC.format(title="Register"), encoding="utf-8")
    (docs / "READING-MAP.md").write_text(DOC.format(title="Reading map"), encoding="utf-8")


def _synthetic(nodes: int, unparsed: int = 0, rejected: int = 0) -> Harvest:
    """A harvest with a chosen shape, for exercising `_audit`'s boundaries directly. The
    boundary is where off-by-one lives, and a fixture tree big enough to straddle a floor of
    71 would prove less about it than this does."""
    src = SourceRef("fixture.md", 1)
    return Harvest(
        scanned=1,
        nodes=[Node(id=f"document:n{i}", kind=NodeKind.DOCUMENT, title="x", source=src)
               for i in range(nodes)],
        unparsed=[Unparsed("f", src, "t", "r") for _ in range(unparsed)],
        rejected=[Rejected("f", src, "t", "r") for _ in range(rejected)],
    )


def _spec(**over: object) -> ExtractorSpec:
    base: dict[str, object] = dict(
        name="fixture", kinds=(NodeKind.DOCUMENT,), min_nodes=10, max_nodes=None,
        min_edges=0, max_unparsed=0, expect_rejected=None, run=lambda ctx: Harvest(),
    )
    base.update(over)
    return ExtractorSpec(**base)  # type: ignore[arg-type]


def self_test() -> int:
    failures: list[str] = []

    def expect(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    # ---- 1. The vacuity guard fires on an empty tree.
    with tempfile.TemporaryDirectory() as tmp:
        result = run(Path(tmp))
        expect(not result.ok, "empty tree produced no failure — the vacuity guard is not wired")
        expect(
            any("VACUOUS" in f for f in result.failures),
            f"empty tree failed for the wrong reason: {result.failures}",
        )
        expect(
            all(r.scanned == 0 for r in result.reports),
            "an extractor reported scanning inputs in an empty tree",
        )

    # ---- 2. The clean control: adjacent generated files must not become nodes, and nothing
    #         may be flagged. A run that rejects everything would still pass case 1.
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _plant(root)
        harvest = documents.extract(_ctx(root))
        expect(harvest.scanned == 2, f"control scanned {harvest.scanned} documents, expected 2")
        docs_found = [n for n in harvest.nodes if n.kind is NodeKind.DOCUMENT]
        expect(len(docs_found) == 2, f"control minted {len(docs_found)} documents, expected 2")
        titles = sorted(n.title for n in docs_found)
        expect(
            titles == ["Architecture", "Charter"],
            f"control minted the generated pair as documents: {titles}",
        )
        expect(not harvest.unparsed, f"control reported unparsed items: {harvest.unparsed}")
        expect(not harvest.rejected, f"control reported rejections: {harvest.rejected}")
        expect(
            len([n for n in harvest.nodes if n.kind is NodeKind.TIER]) == 2,
            "control did not mint one tier node per tier directory",
        )

    # ---- 3. Floor comparison is `<`, not `<=`. An off-by-one guard is not a guard.
    expect(bool(_audit(_spec(min_nodes=10), _synthetic(9))), "floor did not fire at min-1")
    expect(not _audit(_spec(min_nodes=10), _synthetic(10)), "floor fired at exactly min")
    expect(
        bool(_audit(_spec(min_nodes=1, max_nodes=5), _synthetic(6))),
        "ceiling did not fire above max_nodes",
    )
    expect(
        bool(_audit(_spec(min_nodes=1, max_unparsed=0), _synthetic(2, unparsed=1))),
        "unparsed budget did not fire",
    )
    # Two-sided: both too few and too many rejections must fail.
    expect(
        bool(_audit(_spec(min_nodes=1, expect_rejected=8), _synthetic(2, rejected=7))),
        "rejection drift did not fire below the expected count",
    )
    expect(
        bool(_audit(_spec(min_nodes=1, expect_rejected=8), _synthetic(2, rejected=9))),
        "rejection drift did not fire above the expected count",
    )
    expect(
        not _audit(_spec(min_nodes=1, expect_rejected=8), _synthetic(2, rejected=8)),
        "rejection drift fired at the expected count",
    )

    # ---- 4. Id minting refuses the three spellings that make the vault ambiguous.
    for local, why in (("D1", "duplicate"), ("d1", "case-collision"), ("a b", "bad charset")):
        minter = Minter()
        minter.mint(NodeKind.DECISION, "D1", SourceRef("f.md", 1))
        try:
            minter.mint(NodeKind.DECISION, local, SourceRef("f.md", 2))
        except MintError:
            pass
        else:
            failures.append(f"minter accepted a {why} id ({local!r})")

    # ---- 5. Determinism, including across hash seeds. A same-process double build cannot
    #         catch a set-iteration leak; two subprocesses with different seeds can.
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _plant(root)
        first = dumps(build_payload(run(root), {}))
        second = dumps(build_payload(run(root), {}))
        expect(first == second, "two builds of the same fixture differ")
        expect(tmp not in first, "an absolute path from the fixture tree reached the output")

    seeds = [
        subprocess.run(
            [sys.executable, "-c", _SEED_PROBE],
            capture_output=True, text=True, check=True,
            env={"PYTHONHASHSEED": seed, "PATH": "/usr/bin:/bin"},
            cwd=str(Path(__file__).resolve().parent.parent.parent),
        ).stdout
        for seed in ("0", "1")
    ]
    expect(seeds[0] == seeds[1], "output differs across PYTHONHASHSEED — a set is reaching output")

    # ---- 6. Every registered extractor declares floors. Belt and braces: the registry already
    #         raises at import, and this asserts the raise is reachable.
    for spec in EXTRACTORS:
        expect(spec.min_nodes > 0, f"{spec.name} declares no floor")

    for message in failures:
        print(f"FAIL self-test: {message}")
    if failures:
        print(f"\n{len(failures)} self-test failure(s)")
        return 1
    print(
        f"OK self-test — vacuity guard fires on an empty tree, control clean "
        f"(2 documents, 2 tiers, 0 flagged), floors exact at the boundary, "
        f"{len(EXTRACTORS)} extractor(s) declare floors"
    )
    return 0


_SEED_PROBE = (
    "import sys; sys.path.insert(0, '.');"
    "from tools.vaultgraph.runner import run;"
    "from tools.vaultgraph.serialize import build_payload, dumps;"
    "from tools.vaultgraph.textio import ROOT;"
    "sys.stdout.write(dumps(build_payload(run(ROOT), {})))"
)


def _ctx(root: Path) -> Context:
    return Context(root=root, minter=Minter())
