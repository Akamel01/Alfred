"""The engineered half of the graph: packages, modules, schemas, and what D20 protects.

Three things this extractor is careful about.

**`src/thresholds` is declared and absent.** `pyproject.toml` names it in the wheel's package
list and in ruff's first-party set; the directory does not exist. Dropping it would hide
exactly the class of gap this graph is being built to show, so it is minted as a node with
`present: false` and a `declares_absent` edge from the file that declares it.

**D20 protection is a property of a path, recorded on the node.** `scripts/`,
`.github/workflows/`, `policy/`, `migrations/roles/` and `harness/` are inspector machinery
agents may not improve. Which nodes carry that mark is a question the vault should be able to
answer in one query, so it is a tag and an attribute rather than a fact spread across prose.

**Lint and type coverage is recorded, because it is narrower than people assume.** ruff and
pyright are configured over the product tree only -- `harness/`, `bench/`, `scripts/` and
`tools/` are outside both by design. A graph that showed every module under the same gate
would be asserting something false.
"""

from __future__ import annotations

import re

from ..model import Confidence, Edge, EdgeKind, Node, NodeKind, SourceRef
from ..protocol import Anomaly, Context, ExtractorSpec, Harvest
from ..textio import read_lines, rel

NAME = "code"

#: The inspector set, from D20 and `docs/tier4/protected-paths-policy.md`.
PROTECTED = ("scripts/", ".github/workflows/", "policy/", "migrations/roles/", "harness/")

#: Trees that hold importable packages, and whether the product gates reach them.
TREES = (("harness", False), ("src", True))

#: Trees whose files are machinery but not packages -- no `__init__.py`, no dotted name worth
#: minting a parent for. They are minted anyway, because the references extractor finds
#: decision ids in `scripts/lint_verdict_boundary.py` and `policy/oracle-denylist.json` and an
#: edge to a node that does not exist is an edge the renderers silently drop. `scripts/` and
#: `policy/` are also D20-protected, which is a fact the graph should be able to answer.
FLAT_TREES = (("scripts", False), ("bench", False), ("tests", True), ("migrations", False),
              ("policy", False))
FLAT_SUFFIXES = {".py", ".mjs", ".sql", ".json", ".yaml"}

SCHEMA_DIRS = (
    "migrations/product",
    "migrations/harness/control",
    "migrations/harness/evidence",
    "migrations/harness/heldout",
    "migrations/roles",
)

_WHEEL_PACKAGES = re.compile(r"^packages\s*=\s*\[(.+)\]")
_DOCSTRING_TITLE = re.compile(r'^\s*(?:"""|\'\'\')(.+)')
#: The `.mjs` files carry the same rhetorical shape in `//` or `/** */` comments.
_JS_TITLE = re.compile(r"^\s*(?://+|/\*+)\s*(\S.*)")


def is_protected(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in PROTECTED)


def _summary(path, root) -> str:
    """First line of the module docstring. Every module in this repo opens with one, and it
    is a title-cased claim rather than a description -- which makes it the right note title."""
    pattern = _JS_TITLE if path.suffix == ".mjs" else _DOCSTRING_TITLE
    for line in read_lines(path)[:12]:
        match = pattern.match(line)
        if match:
            return match.group(1).strip().rstrip('"\'*/').strip()
        if line.strip() and not line.startswith(("#", '"""', "'''", "from ", "import ")):
            break
    return rel(path, root)


def _declared_packages(root) -> tuple[list[str], SourceRef | None]:
    pyproject = root / "pyproject.toml"
    if not pyproject.is_file():
        return [], None
    for index, line in enumerate(read_lines(pyproject)):
        match = _WHEEL_PACKAGES.match(line.strip())
        if match:
            names = re.findall(r'"([^"]+)"', match.group(1))
            return names, SourceRef("pyproject.toml", index + 1)
    return [], None


def extract(ctx: Context) -> Harvest:
    harvest = Harvest()
    root = ctx.root
    package_ids: dict[str, str] = {}

    for tree, gated in TREES:
        base = root / tree
        if not base.is_dir():
            continue
        for package_dir in sorted(p for p in base.iterdir() if p.is_dir() and p.name != "__pycache__"):
            harvest.scanned += 1
            rel_dir = rel(package_dir, root)
            dotted = rel_dir.replace("/", ".")
            src = SourceRef(rel_dir, 1)
            package_id = ctx.minter.mint(NodeKind.MODULE, dotted, src)
            package_ids[rel_dir] = package_id
            harvest.nodes.append(Node(
                id=package_id, kind=NodeKind.MODULE, title=dotted, source=src, shape="package",
                attrs={
                    "tree": tree,
                    "present": "true",
                    "protected": str(is_protected(rel_dir + "/")).lower(),
                    "lint_gated": str(gated).lower(),
                    "namespace_package": str(not (package_dir / "__init__.py").exists()).lower(),
                },
                tags=("protected",) if is_protected(rel_dir + "/") else (),
                extractor=NAME,
            ))

            sources = sorted(
                p for p in package_dir.rglob("*")
                if p.is_file() and p.suffix in {".py", ".mjs"} and "__pycache__" not in p.parts
            )
            for path in sources:
                harvest.scanned += 1
                rel_path = rel(path, root)
                module_src = SourceRef(rel_path, 1)
                # `.py` drops its suffix and becomes a dotted module name; `.mjs` keeps its
                # own. `harness/acs/acs1.py` and `harness/acs/acs1.mjs` are two independent
                # implementations of the same specification, written from the spec rather
                # than translated -- collapsing them into one node would erase the property
                # the pair exists to demonstrate. The minter caught this rather than the
                # graph silently holding 52 modules where the tree has 53.
                local = rel_path.replace("/", ".")
                if path.suffix == ".py":
                    local = local.removesuffix(".py")
                module_id = ctx.minter.mint(NodeKind.MODULE, local, module_src)
                harvest.nodes.append(Node(
                    id=module_id, kind=NodeKind.MODULE, title=_summary(path, root),
                    source=module_src,
                    shape="javascript" if path.suffix == ".mjs" else "module",
                    attrs={
                        "tree": tree,
                        "path": rel_path,
                        "present": "true",
                        "protected": str(is_protected(rel_path)).lower(),
                        "lint_gated": str(gated and path.suffix == ".py").lower(),
                        "is_test": str(path.name.startswith("test_")).lower(),
                    },
                    tags=("protected",) if is_protected(rel_path) else (),
                    extractor=NAME,
                ))
                harvest.edges.append(Edge(
                    src=package_id, dst=module_id, kind=EdgeKind.CONTAINS,
                    confidence=Confidence.STRUCTURAL, source=module_src,
                    evidence=rel_path, extractor=NAME,
                ))

    # ---- Loose machinery: files that are not packages but are still nodes.
    for tree, gated in FLAT_TREES:
        base = root / tree
        if not base.is_dir():
            continue
        for path in sorted(p for p in base.rglob("*")
                           if p.is_file() and p.suffix in FLAT_SUFFIXES
                           and "__pycache__" not in p.parts):
            rel_path = rel(path, root)
            harvest.scanned += 1
            src = SourceRef(rel_path, 1)
            local = rel_path.replace("/", ".")
            if path.suffix == ".py":
                local = local.removesuffix(".py")
            harvest.nodes.append(Node(
                id=ctx.minter.mint(NodeKind.MODULE, local, src),
                kind=NodeKind.MODULE,
                title=_summary(path, root) if path.suffix in {".py", ".mjs"} else rel_path,
                source=src, shape="file",
                attrs={
                    "tree": tree, "path": rel_path, "present": "true",
                    "protected": str(is_protected(rel_path)).lower(),
                    "lint_gated": str(gated and path.suffix == ".py").lower(),
                    "is_test": str(path.name.startswith("test_")).lower(),
                },
                tags=("protected",) if is_protected(rel_path) else (),
                extractor=NAME,
            ))

    # ---- The workflow file itself, so gate steps have a module to hang from.
    workflow = root / ".github/workflows/gates.yml"
    if workflow.is_file():
        harvest.scanned += 1
        rel_path = ".github/workflows/gates.yml"
        src = SourceRef(rel_path, 1)
        harvest.nodes.append(Node(
            id=ctx.minter.mint(NodeKind.MODULE, rel_path.replace("/", "."), src),
            kind=NodeKind.MODULE, title=rel_path, source=src, shape="file",
            attrs={"tree": ".github", "path": rel_path, "present": "true",
                   "protected": "true", "lint_gated": "false", "is_test": "false"},
            tags=("protected",), extractor=NAME,
        ))

    # ---- Declared but absent. pyproject names src/thresholds; the tree does not have it.
    declared, declared_src = _declared_packages(root)
    for name in declared:
        if name in package_ids or not (root / name).is_dir():
            if (root / name).is_dir():
                continue
            src = declared_src or SourceRef("pyproject.toml", 1)
            absent_id = ctx.minter.mint(NodeKind.MODULE, name.replace("/", ".") + ".absent", src)
            harvest.nodes.append(Node(
                id=absent_id, kind=NodeKind.MODULE, title=f"{name} (declared, absent)",
                source=src, shape="declared-absent",
                attrs={"present": "false", "declared_in": "pyproject.toml", "path": name},
                tags=("absent",), extractor=NAME,
            ))
            harvest.edges.append(Edge(
                src=absent_id, dst=absent_id, kind=EdgeKind.DECLARES_ABSENT,
                confidence=Confidence.STRUCTURAL, source=src,
                evidence=f"pyproject.toml declares {name}; the directory does not exist",
                extractor=NAME,
            ))
            harvest.anomalies.append(Anomaly(
                kind="declared-absent-package",
                detail=f"pyproject.toml declares {name} in the wheel packages; it is not on disk",
                refs=(src,),
            ))

    # ---- Schemas.
    for rel_dir in SCHEMA_DIRS:
        directory = root / rel_dir
        if not directory.is_dir():
            continue
        harvest.scanned += 1
        src = SourceRef(rel_dir, 1)
        schema_id = ctx.minter.mint(NodeKind.SCHEMA, rel_dir.removeprefix("migrations/"), src)
        files = sorted(
            rel(p, root) for p in directory.rglob("*")
            if p.is_file() and p.suffix in {".py", ".sql", ".yaml", ".mako"}
        )
        versions = [f for f in files if "/versions/" in f and f.endswith(".py")]
        harvest.nodes.append(Node(
            id=schema_id, kind=NodeKind.SCHEMA,
            title=rel_dir.removeprefix("migrations/"), source=src, shape="migration-tree",
            attrs={
                "path": rel_dir,
                "migrations": str(len(versions)),
                "protected": str(is_protected(rel_dir + "/")).lower(),
                # Only evidence and heldout are guarded by the additive-only lint.
                "additive_only_lint": str(
                    rel_dir in ("migrations/harness/evidence", "migrations/harness/heldout")
                ).lower(),
            },
            tags=("protected",) if is_protected(rel_dir + "/") else (),
            extractor=NAME,
        ))
    return harvest


SPEC = ExtractorSpec(
    name=NAME,
    kinds=(NodeKind.MODULE, NodeKind.SCHEMA),
    # 9 packages on disk + 1 declared-absent + 5 schema trees + the modules inside them.
    min_nodes=90,
    max_nodes=None,
    min_edges=45,
    max_unparsed=0,
    expect_rejected=None,
    run=extract,
)
