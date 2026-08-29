"""The top-level layout as declared in the coding-standards structure fence.

ADR-0033 made the fence the one home for "what is in the tree". This extractor mints
one node per directory the fence names, so a fence that loses a line fails the floor,
and it walks the tree for top-level directories the fence does not name, which surface
as anomalies: a directory that grew in is a layout the canonical document does not yet
carry, and a fence line for a directory that is not there is the protected set's ghost
row wearing a layout hat.

The walked set is the filesystem minus what the ignore files declare, which is what lets
the check run on a `git archive` copy as well as a clone: `git ls-tree` is the exact
source but has no root outside a worktree. A pattern with a glob or a subpath in it
cannot name a top-level directory here, and an undecided directory stays in the set:
the error direction is a surfaced anomaly, never a silent pass.
"""

from __future__ import annotations

import re

from ..model import Node, NodeKind, SourceRef
from ..protocol import Anomaly, Context, ExtractorSpec, Harvest
from ..textio import read_lines

NAME = "layout"
STANDARDS = "docs/tier2/coding-standards.md"
HEADING = "## Structure"

#: ADR-0040's floor: every tracked top-level directory is named in the fence.
#: Eighteen on the ICM workspace (fence v2, ADR-0040), `.github` included.
EXPECTED = 18

# Machine-local state the in-repo ignore files do not name: `.git` is the repository
# itself, and `.claude` holds parked worktrees (its contents are excluded in
# .git/info/exclude, which is machine-local and absent from an archive copy).
# ponytail: these two are the known untracked top-level dirs; a tool that adds a
# third one surfaces as a layout-miss until it is named here.
_MACHINE_LOCAL = {".git", ".claude"}

_FENCE = re.compile(r"^```")
_GLOB = re.compile(r"[*?\[]")


def _ignored_dirs(root) -> set[str]:
    """Top-level directory names the ignore files declare, from literal `name/` patterns.

    `.gitignore` plus `.git/info/exclude`, so a machine-local exclusion works on the
    operator's checkout as well as in CI and in an archive copy.
    """
    out: set[str] = set(_MACHINE_LOCAL)
    for rel in (".gitignore", ".git/info/exclude"):
        path = root / rel
        if not path.is_file():
            continue
        for line in read_lines(path):
            line = line.strip()
            if not line or line.startswith("#") or not line.endswith("/"):
                continue
            name = line.rstrip("/")
            if _GLOB.search(name) or "/" in name:
                continue
            out.add(name)
    return out


def _fence_entries(path) -> list[tuple[str, str, int]]:
    """(name, description, line) for each top-level entry of the structure fence.

    The fence is the first code block after the heading, and only that block. The
    document carries a ```python sample earlier (the suppression form, whose sample
    line a fence-toggle read as a directory), and a block that opens after the layout
    fence has closed is an example, not a line of the layout.
    """
    entries: list[tuple[str, str, int]] = []
    in_section = False
    in_fence = False
    fence_closed = False
    for index, line in enumerate(read_lines(path)):
        if line.startswith(HEADING):
            in_section, in_fence, fence_closed = True, False, False
            continue
        if not in_section:
            continue
        if _FENCE.match(line):
            if in_fence:
                fence_closed = True
                in_fence = False
            elif not fence_closed:
                in_fence = True
            continue
        if in_fence and line and not line[:1].isspace():
            name, _, rest = line.partition(" ")
            entries.append((name.strip("/"), rest.strip(), index + 1))
    return entries


def extract(ctx: Context) -> Harvest:
    harvest = Harvest()
    path = ctx.root / STANDARDS
    if not path.is_file():
        return harvest
    harvest.scanned += 1

    entries = _fence_entries(path)
    fence: set[str] = set()
    for name, desc, line in entries:
        src = SourceRef(STANDARDS, line)
        harvest.nodes.append(Node(
            id=ctx.minter.mint(NodeKind.LAYOUT, name, src),
            kind=NodeKind.LAYOUT, title=f"{name}/", source=src, shape="fence-line",
            status="named", body=desc,
            attrs={"directory": name, "description": desc},
            extractor=NAME,
        ))
        fence.add(name)

    ignored = _ignored_dirs(ctx.root)
    tree = sorted(p.name for p in ctx.root.iterdir() if p.is_dir() and p.name not in ignored)
    on_disk = set(tree)
    for name in sorted(d for d in tree if d not in fence):
        harvest.anomalies.append(Anomaly(
            kind="layout-miss",
            detail=f"top-level directory {name}/ is not named in the coding-standards structure fence",
        ))
    for name in sorted(n for n in fence if n not in on_disk):
        harvest.anomalies.append(Anomaly(
            kind="layout-ghost",
            detail=f"the structure fence names {name}/, which is not a top-level directory",
        ))
    return harvest


SPEC = ExtractorSpec(
    name=NAME,
    kinds=(NodeKind.LAYOUT,),
    min_nodes=EXPECTED,
    max_nodes=None,
    min_edges=0,
    max_unparsed=0,
    expect_rejected=None,
    run=extract,
)
