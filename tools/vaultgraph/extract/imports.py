"""What depends on what: module -> module edges, read from import statements.

**This is the only relation in the graph that answers "what does this depend on".** Before it,
every module edge was `contains`, and every `contains` between modules was package -> submodule
-- a tree. A drawing of a tree can be tidy or untidy, but it cannot show an architecture,
because an architecture is what the tree's leaves say to each other.

**`ast`, not `tokenize`.** The neighbouring `references` extractor uses `tokenize` and states
why: it reads decision ids out of comments, and `ast` discards comments entirely. That
reasoning does not reach here. Imports are statements, `ast` parses them exactly, and a regex
over lines would take `# from harness.acs import canon` in a comment as a live dependency.

**How the yield distributes is itself a finding.** 136 edges over 56 modules, and they are not
evenly spread: the product and inspector trees contribute few, because the verdict-boundary lint
and the D20 factory/inspector split are both forces pushing those apart, and both are working.
Most of the density is inside `tools/` -- this package, which is the one part of the repository
built as an ordinary library. A reader should take the sparse half as the architecture working
rather than as the parser failing.
"""

from __future__ import annotations

import ast

from ..model import Confidence, Edge, EdgeKind, NodeKind, SourceRef, module_id
from ..protocol import Context, ExtractorSpec, Harvest, Unparsed
from ..textio import rel

NAME = "imports"

#: Every tree `code` mints module nodes for. Kept as a plain tuple rather than imported from
#: `code.TREES`: that constant carries a lint-gating flag this extractor has no use for, and
#: reading half a pair is how the half that matters gets missed when the pair changes.
TREES = ("harness", "src", "tools", "scripts", "bench", "tests", "migrations", "policy")


def _names(node: ast.Import | ast.ImportFrom, dotted: str) -> list[str]:
    """The dotted names one statement asks for, each as specific as the statement allows.

    `import a.b` asks for one name. `from a.b import c, d` asks for two -- `a.b.c` and `a.b.d`
    -- and *not* for `a.b`. Returning the head as well was the first spelling of this, and it
    claimed a dependency on the package for every import out of a module inside it: `from
    ..fixture import probe` minted an edge to `harness.fixture` beside the one to
    `harness.fixture.probe`, so packages accumulated inbound edges their submodules had earned.
    The head is still reachable, as the fallback in `_resolve` when no imported name is a module.
    """
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if node.level:
        # A relative import resolves against the importing module's own package. `level` is the
        # number of leading dots, and one dot means "this package", so the module's own final
        # segment is dropped first.
        base = ".".join(dotted.split(".")[: -node.level])
        if not base:
            return []
        head = f"{base}.{node.module}" if node.module else base
    elif node.module:
        head = node.module
    else:
        return []
    return [f"{head}.{alias.name}" for alias in node.names] or [head]


def _resolve(ctx: Context, dotted_target: str) -> str | None:
    """Longest known prefix, or nothing.

    `from harness.acs.acs1 import canon` has to land on `module:harness.acs.acs1` and not on a
    node for the function; walking the name down from the right is what finds the deepest
    module that actually exists. Resolution asks the minter rather than the filesystem, so an
    import of `json` or `pytest` resolves to nothing without a stdlib list to maintain.
    """
    parts = dotted_target.split(".")
    while parts:
        candidate = module_id("/".join(parts))
        if ctx.minter.knows(candidate):
            return candidate
        parts.pop()
    return None


def extract(ctx: Context) -> Harvest:
    harvest = Harvest()
    root = ctx.root

    paths = []
    for tree in TREES:
        base = root / tree
        if base.is_dir():
            paths.extend(sorted(
                p for p in base.rglob("*.py")
                if p.is_file() and "__pycache__" not in p.parts
            ))

    seen: set[tuple[str, str]] = set()
    for path in paths:
        rel_path = rel(path, root)
        harvest.scanned += 1
        source_id = module_id(rel_path)
        if not ctx.minter.knows(source_id):
            # A file `code` chose not to mint -- a benchmark result blob, say. Not a finding:
            # the exclusion is deliberate and documented where it is made.
            continue
        try:
            tree_ast = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError) as error:
            harvest.unparsed.append(Unparsed(
                NAME, SourceRef(rel_path, 1), rel_path, f"could not parse: {error}"
            ))
            continue

        for node in ast.walk(tree_ast):
            if not isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            dotted = source_id.split(":", 1)[1]
            for name in _names(node, dotted):
                target = _resolve(ctx, name)
                # A module importing from its own package resolves to itself. `Edge` refuses a
                # self-loop by raising, and routing around that here would be arguing with a
                # check rather than honouring it.
                if target is None or target == source_id or (source_id, target) in seen:
                    continue
                seen.add((source_id, target))
                harvest.edges.append(Edge(
                    src=source_id, dst=target, kind=EdgeKind.IMPORTS,
                    confidence=Confidence.STRUCTURAL,
                    source=SourceRef(rel_path, node.lineno),
                    evidence=name, extractor=NAME,
                ))
    return harvest


SPEC = ExtractorSpec(
    name=NAME,
    kinds=(NodeKind.MODULE,),
    # Mints nothing: every endpoint is a module `code` already made. Stated as max_nodes=0
    # rather than left as an absent floor, which `protocol.validate_registry` requires -- an
    # extractor that starts minting nodes by accident must not pass unnoticed.
    min_nodes=0,
    max_nodes=0,
    # 136 measured. A floor rather than an exact count: the repository legitimately grows an
    # import. Set well under the measurement but well over the ~40 that survive if relative
    # import resolution breaks -- that is the half most likely to break, and a floor it can
    # pass is not a floor.
    min_edges=90,
    max_unparsed=0,
    expect_rejected=None,
    run=extract,
)
