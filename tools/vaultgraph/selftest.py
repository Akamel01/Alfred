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

from .extract import EXTRACTORS, code, decisions, documents, references
from .fixtures import _plant, _plant_code, _plant_plan
from .model import Minter, MintError, Node, NodeKind, SourceRef
from .protocol import Context, ExtractorSpec, Harvest, Rejected, Unparsed
from .render import vault as render_vault
from .runner import _audit, run
from .serialize import build_payload, compare_tree, dumps, write_tree

def _imports(path: Path) -> set[str]:
    """Module names a file imports, absolute and relative alike."""
    import ast as _ast

    tree = _ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    package = "tools.vaultgraph" + ("." + path.parent.name if path.parent.name != "vaultgraph" else "")
    for statement in _ast.walk(tree):
        if isinstance(statement, _ast.Import):
            names.update(alias.name for alias in statement.names)
        elif isinstance(statement, _ast.ImportFrom):
            base = statement.module or ""
            if statement.level:
                prefix = package.rsplit(".", statement.level - 1)[0] if statement.level > 1 else package
                base = f"{prefix}.{base}" if base else prefix
            names.add(base)
            names.update(f"{base}.{alias.name}" for alias in statement.names)
    return names


def _reaches(start: Path, forbidden: str) -> list[str] | None:
    """Shortest import trail from `start` into `forbidden`, or None. BFS rather than a one-hop
    check, because `render.note -> helpers -> extract.decisions` is exactly the leak a direct
    check would miss -- the same reason `scripts/lint_verdict_boundary.py` walks the graph."""
    package_root = Path(__file__).resolve().parent
    queue: list[tuple[Path, list[str]]] = [(start, [start.stem])]
    seen = {start}
    while queue:
        current, trail = queue.pop(0)
        for name in sorted(_imports(current)):
            if forbidden in name:
                return trail + [name]
            if not name.startswith("tools.vaultgraph."):
                continue
            candidate = package_root / (name.removeprefix("tools.vaultgraph.").replace(".", "/") + ".py")
            if candidate.is_file() and candidate not in seen:
                seen.add(candidate)
                queue.append((candidate, trail + [candidate.stem]))
    return None


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


    # ---- 7. Every decision shape is read, and every commentary lookalike is refused.
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _plant_plan(root)
        harvest = decisions.extract(_ctx(root))
        numbers = sorted(int(n.attrs["number"]) for n in harvest.nodes)
        expect(
            numbers == [1, 38, 39, 41, 42, 48, 55],
            f"decision shapes: extracted {numbers}, expected [1, 38, 39, 41, 42, 48, 55]",
        )
        shapes = sorted({n.shape for n in harvest.nodes})
        expect(
            shapes == ["bold-paragraph", "heading", "table-row"],
            f"not every shape was exercised: {shapes}",
        )
        expect(
            len(harvest.rejected) == 8,
            f"rejected {len(harvest.rejected)} commentary spans, expected exactly 8: "
            + "; ".join(r.text[:40] for r in harvest.rejected),
        )
        expect(not harvest.unparsed, f"fixture left unparsed items: {harvest.unparsed}")

        # The adjacent control for the title rule. `machine-checkable` puts an ASCII hyphen
        # inside a span that is NOT a definition; accepting a bare hyphen as a title separator
        # read it as one, and this fixture is what said so.
        rejected_text = " ".join(r.text for r in harvest.rejected)
        expect(
            "machine-checkable" in rejected_text,
            "a hyphen inside a compound word is being read as a title separator",
        )
        # A restatement is one node with a second occurrence, never a second node.
        d42 = next(n for n in harvest.nodes if n.attrs["number"] == "42")
        expect(len(d42.occurrences) == 1, f"restatement did not fold into occurrences: {d42.occurrences}")

    # ---- 8. The escaped pipe. Every decision row has three cells; D55's has three only if
    #         `\\|` inside a code span is not treated as a cell boundary.
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _plant_plan(root)
        harvest = decisions.extract(_ctx(root))
        d55 = next((n for n in harvest.nodes if n.attrs["number"] == "55"), None)
        expect(d55 is not None, "the escaped-pipe row was not extracted at all")
        if d55 is not None:
            expect(
                "Simulated | Corpus | Unknown" in d55.body,
                f"escaped pipes were not restored in the cell body: {d55.body[:120]}",
            )

    # ---- 9. A markdown table parser is the wrong tool here, and this asserts it stays gone.
    #         The `| 48 |` row above is separated from the table by a blank line, so a parser
    #         that requires a header row sees a headerless fragment and yields nothing.
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _plant_plan(root)
        harvest = decisions.extract(_ctx(root))
        expect(
            any(n.attrs["number"] == "48" for n in harvest.nodes),
            "the blank-line-separated orphan row was dropped — something is parsing tables",
        )


    # ---- 10. Comment and docstring spans only. A hex literal and an identifier carrying the
    #          same digits are the adjacent control: they must stay silent while the comment
    #          three lines below them is heard.
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _plant_code(root)
        harvest = references.extract(_ctx(root))
        found = sorted({e.src for e in harvest.edges})
        expect(
            found == ["adr:ADR-0001", "decision:D19"],
            f"reference spans: found {found}, expected the docstring ADR and the comment D19 "
            "only — 0xD16ABC and D40_CONSTANT are code, not claims",
        )
        expect(not harvest.unparsed, f"reference fixture left unparsed items: {harvest.unparsed}")
        expect(
            all(e.confidence.value == "derived" for e in harvest.edges),
            "a reference edge claimed structural confidence; a comment is not a table column",
        )

    # ---- 11. Declared-but-absent packages are surfaced, never dropped.
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _plant_code(root)
        (root / "pyproject.toml").write_text(
            '[tool.hatch.build.targets.wheel]\npackages = ["src/domain", "src/ghost"]\n',
            encoding="utf-8",
        )
        harvest = code.extract(_ctx(root))
        absent = [n for n in harvest.nodes if n.shape == "declared-absent"]
        expect(len(absent) == 2, f"declared-absent packages: found {len(absent)}, expected 2")
        expect(
            any(a.kind == "declared-absent-package" for a in harvest.anomalies),
            "a package declared in pyproject and missing from disk raised no anomaly",
        )


    # ---- 12. Renderers are downstream of one extraction and cannot reach it.
    render_dir = Path(__file__).resolve().parent / "render"
    for module in sorted(render_dir.glob("*.py")):
        trail = _reaches(module, "extract")
        expect(
            trail is None,
            f"render/{module.name} reaches the extractors: {' -> '.join(trail or [])}",
        )

    # ---- 13. --check catches a hand edit and a hand-created note. The first is caught by
    #          content comparison; the second only by noticing nobody planned it.
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _plant(root)
        result = run(root)
        tree = render_vault.build(result.nodes, result.edges, result.anomalies, result.unparsed)
        write_tree(root, tree)
        expect(not compare_tree(root, tree), "a freshly written vault did not compare clean")

        edited = root / sorted(tree)[0]
        edited.write_text(edited.read_text(encoding="utf-8") + "\nhand edit\n", encoding="utf-8")
        problems = compare_tree(root, tree)
        expect(any(p.startswith("differs:") for p in problems), "a hand edit was not detected")
        edited.write_text(tree[sorted(tree)[0]], encoding="utf-8")

        stray = root / "vault" / "documents" / "authored-by-hand.md"
        stray.write_text("a fact that exists only here\n", encoding="utf-8")
        problems = compare_tree(root, tree)
        expect(
            any(p.startswith("orphan:") for p in problems),
            "a hand-created note was not detected as an orphan",
        )
        stray.unlink()

        missing = root / sorted(tree)[0]
        missing.unlink()
        expect(
            any(p.startswith("missing:") for p in compare_tree(root, tree)),
            "a deleted note was not detected",
        )

    # ---- 14. Every note carries the banner and a source pointer that resolves.
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _plant(root)
        result = run(root)
        tree = render_vault.build(result.nodes, result.edges, result.anomalies, result.unparsed)
        notes = [c for path, c in sorted(tree.items()) if path.endswith(".md")]
        expect(notes, "the vault built no notes at all")
        expect(
            all("Generated — do not edit" in c for c in notes),
            "a note shipped without the generated banner",
        )

    # ---- 6. Every registered extractor declares floors. Belt and braces: the registry already
    #         raises at import, and this asserts the raise is reachable.
    for spec in EXTRACTORS:
        # A floor on nodes, or -- for an extractor that mints nothing and only relates what
        # others minted -- an explicit max_nodes=0 plus a floor on edges.
        expect(
            spec.min_nodes > 0 or (spec.max_nodes == 0 and spec.min_edges > 0),
            f"{spec.name} declares no floor on anything it produces",
        )

    for message in failures:
        print(f"FAIL self-test: {message}")
    if failures:
        print(f"\n{len(failures)} self-test failure(s)")
        return 1
    print(
        f"OK self-test — vacuity guard fires on an empty tree, docs control clean "
        f"(2 documents, 2 tiers, 0 flagged), all four decision shapes read and 8 "
        f"commentary spans refused, escaped pipes and orphan rows survive, code ids read "
        f"from comment spans and not from hex literals, floors exact at the boundary, "
        f"{len(EXTRACTORS)} extractors declare floors, renderers cannot reach extractors, "
        f"and --check catches an edit, an orphan and a deletion"
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
