"""A cheap fingerprint of the inputs, so a served page can tell it has gone stale.

The served page re-reads the working tree on every request, which makes it correct the moment
it loads and says nothing at all after that. A tab open for five hours looks exactly like a tab
open for five seconds. This is the difference: a hash of what the extractors read, cheap enough
to ask for every few seconds, so the page can say *reload* without anyone having to remember to.

**Metadata only.** `(path, mtime_ns, size)` -- no file is opened. A full re-extraction per poll
would be the build running on a timer, which is the cost the poll exists to avoid. The tradeoff
is honest and narrow: an edit that changes neither mtime nor size is invisible here, and nothing
a normal editor or `git` does produces one.

**The generator's own outputs are excluded, and that is load-bearing.** `vault/`, `graph.json`
and `docs-graph.html` are written by the regeneration this stamp exists to prompt. Watching them
would make every successful refresh immediately report the repository as changed -- a staleness
signal whose most reliable trigger is the act of resolving it.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from .textio import ROOT, rel

#: Directories the extractors read. Deliberately a superset of any one extractor's list: a
#: reader wants to know the repository moved, not which extractor would have noticed.
WATCHED_TREES = (
    "docs", "plan", "harness", "src", "tools", "scripts", "bench", "tests",
    "migrations", "policy",
)

WATCHED_FILES = (".github/workflows/gates.yml", "pyproject.toml")

#: Written by the build, never read by it. See the module docstring.
GENERATED = ("vault", "graph.json", "docs-graph.html")

_SKIP_DIRS = {"__pycache__", ".git", ".ruff_cache", ".pytest_cache", "node_modules"}


def _watched(root: Path) -> list[Path]:
    found: list[Path] = []
    for tree in WATCHED_TREES:
        base = root / tree
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if _SKIP_DIRS.intersection(path.parts):
                continue
            found.append(path)
    found.extend(root / name for name in WATCHED_FILES if (root / name).is_file())
    return sorted(found)


def stamp(root: Path = ROOT) -> str:
    """A hex digest of the watched inputs. Equal digests mean nothing the graph reads moved."""
    digest = hashlib.sha256()
    for path in _watched(root):
        rel_path = rel(path, root)
        if any(rel_path == g or rel_path.startswith(g + "/") for g in GENERATED):
            continue
        info = path.stat()
        digest.update(f"{rel_path}\0{info.st_mtime_ns}\0{info.st_size}\n".encode("utf-8"))
    return digest.hexdigest()
