"""C15 — the oracle arriving through the deliverable channel.

Every other containment control faces the container. This one faces the **patch**, because
the patch is the one thing that leaves the container by design. C6 stops the oracle being
fetched, C12 and C13 stop it being installed, C7 asserts it is absent and C14 re-asserts at
the end — and none of them looks at the diff the agent hands back. A patch that adds
`commonroad-crime` to a dependency file, or imports `commonroad_crime`, or vendors the
measure implementation as a new source file, defeats the entire oracle-absence design at the
one moment nothing is watching.

Three clauses, and the third is the one that costs something:

1. **No dependency added.** Any added line in a dependency manifest naming a denied
   distribution.
2. **No import of a denied module.** Any added line importing a denied top-level module.
3. **No file whose normalized content hash matches a denied source file.** The vendoring
   case, which the first two miss entirely: a copied implementation under a new name imports
   nothing denied and declares no dependency.

**Runs outside, privileged, on the diff — never on a working tree.** Same discipline as
`harness/patch/validate.py`, and for the same reason: a check that runs after application has
a dirty tree as its failure mode. This module is separate from that one because the concerns
are separate — `validate.py` refuses patches that attack the *inspector*, this refuses
patches that smuggle the *oracle*, and folding them would make one list of reasons where the
reader needs two.

## The limit, stated so a green result is not over-quoted

Clause 3 is a hash over normalized content: whitespace collapsed, comments dropped, the file
lowercased. **A renamed, reformatted, partially rewritten vendored copy passes it.** That is
the same limit `oracle_absence.py` records for its own name- and hash-based scan, and it is
not closed here. What the clause does catch is the copy-paste case, which is the one an agent
under time pressure actually produces.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Final

from harness.containment.assertions import Assertion, AssertionOutcome
from harness.containment.denylist import Denylist

__all__ = [
    "ASSERTION_C15",
    "DEPENDENCY_FILENAMES",
    "PatchFinding",
    "assert_patch_carries_no_oracle",
    "imported_top_level_names",
    "normalized_source_hash",
]

ASSERTION_C15: Final = "C15"

# Files whose added lines are read as dependency declarations. Matched on the basename, so a
# manifest anywhere in the tree is covered — a monorepo subdirectory is exactly where an
# extra dependency would be least visible in review.
DEPENDENCY_FILENAMES: Final[frozenset[str]] = frozenset(
    {
        "pyproject.toml",
        "requirements.txt",
        "requirements-dev.txt",
        "constraints.txt",
        "setup.py",
        "setup.cfg",
        "environment.yml",
        "Pipfile",
        "poetry.lock",
        "uv.lock",
        "package.json",
    }
)

_ADDED = re.compile(r"\A\+(?!\+\+)")
_DIFF_HEADER = re.compile(r"\A\+\+\+ (?:b/)?(.+?)\s*\Z")
# `@@ -a,b +c,d @@` — `c` is the first line number of the added side. Parsed rather than
# skipped so a finding reports the line a reviewer can actually open.
_HUNK = re.compile(r"\A@@ -\d+(?:,\d+)? \+(?P<start>\d+)(?:,\d+)? @@")

# Deliberately not an AST parse: the input is a diff fragment, which is not valid Python, and
# a parser that failed on a partial hunk would report nothing on the one input this check
# receives. What it must not do is stop at the *first* name on a line.
#
# `import a, b as c, d` — every name, not just `a`. The original pattern read one name and
# passed `import os, commonroad_crime`, which is the same line with the words swapped.
_IMPORT_STATEMENT = re.compile(r"^\s*import\s+(?P<names>[^#;]+)")
# `from x import y`, and `from . import y` / `from .pkg import y` — the relative forms import
# *names* from a package, so the imported names are what matter, not the empty module part.
_FROM_STATEMENT = re.compile(
    r"^\s*from\s+(?P<module>[A-Za-z_.][A-Za-z0-9_.]*)\s+import\s+(?P<names>[^#;]+)"
)
# The dynamic forms. Name-based like everything else here, and equally defeated by a name
# assembled at runtime — which the module docstring already declines to claim it closes.
_DYNAMIC = re.compile(
    r"""(?:__import__|import_module)\s*\(\s*["'](?P<name>[A-Za-z_][A-Za-z0-9_.]*)["']"""
)
_ALIASED = re.compile(r"\A(?P<name>[A-Za-z_][A-Za-z0-9_.]*)(?:\s+as\s+[A-Za-z_][A-Za-z0-9_]*)?\Z")

_COMMENT = re.compile(r"(?m)#.*$|//.*$")
_WHITESPACE = re.compile(r"\s+")


@dataclass(frozen=True)
class PatchFinding:
    """One reason the patch is refused. `clause` says which of the three fired."""

    clause: str
    path: str
    line_number: int
    detail: str


def imported_top_level_names(line: str) -> frozenset[str]:
    """Every top-level module name one added line could bring into scope.

    Top-level only, because that is what the denylist names: `import a.b.c` denies on `a`.
    Returns a set rather than the first hit so that a line naming two modules is read as
    naming two modules.
    """
    found: set[str] = set()

    statement = _IMPORT_STATEMENT.match(line)
    if statement:
        for part in statement.group("names").split(","):
            aliased = _ALIASED.match(part.strip())
            if aliased:
                found.add(aliased.group("name").split(".")[0])

    relative = _FROM_STATEMENT.match(line)
    if relative:
        module = relative.group("module")
        if module.startswith("."):
            # `from . import commonroad_crime` — the module part carries no name, and the
            # names after `import` are what enter scope.
            for part in relative.group("names").split(","):
                aliased = _ALIASED.match(part.strip().removesuffix(")").strip())
                if aliased:
                    found.add(aliased.group("name").split(".")[0])
        else:
            found.add(module.split(".")[0])

    for dynamic in _DYNAMIC.finditer(line):
        found.add(dynamic.group("name").split(".")[0])

    return frozenset(found)


def normalized_source_hash(text: str) -> str:
    """The content hash clause 3 compares against.

    Normalization is deliberately aggressive — comments dropped, all whitespace collapsed,
    lowercased — because the hazard is a copy with a reformat, not a byte-identical copy.
    Aggressive normalization raises the false-positive risk in exchange, which is acceptable
    here: the consequence of a hit is a refused patch and a human look, not a silent verdict.
    """
    stripped = _COMMENT.sub(" ", text)
    collapsed = _WHITESPACE.sub(" ", stripped).strip().lower()
    return hashlib.sha256(collapsed.encode("utf-8")).hexdigest()


def _added_lines(diff_text: str) -> list[tuple[str, int, str]]:
    """`(path, line number in the post-image, text)` for every added line.

    The number comes from the `@@` hunk header, which this used to skip — so a finding in a
    hunk at line 501 was reported as `path:1` and a reviewer opened the wrong line. A
    position that is confidently wrong is worse than none, because it is acted on.
    """
    out: list[tuple[str, int, str]] = []
    path = "<unknown>"
    # 0 means "no hunk header seen yet". A fragment handed in without one still gets scanned
    # — refusing it would make the check easy to disable by trimming a line — and its
    # findings are numbered from 1, which is the honest answer for a position nobody stated.
    line_number = 0
    for raw in diff_text.splitlines():
        header = _DIFF_HEADER.match(raw)
        if header:
            path = header.group(1)
            line_number = 0
            continue
        hunk = _HUNK.match(raw)
        if hunk:
            line_number = int(hunk.group("start"))
            continue
        if raw.startswith("--- "):
            continue
        if _ADDED.match(raw):
            out.append((path, max(line_number, 1), raw[1:]))
            line_number = max(line_number, 1) + 1
        elif not raw.startswith("-"):
            # Context lines advance the post-image; removed lines do not.
            line_number = line_number + 1 if line_number else 0
    return out


def assert_patch_carries_no_oracle(
    diff_text: str,
    denylist: Denylist,
    *,
    denied_source_hashes: Mapping[str, str] | None = None,
) -> Assertion:
    """C15 — the diff adds no dependency, no denied import, and no denied source file.

    `denied_source_hashes` maps a normalized hash to the name of the oracle source file it
    came from. It is supplied by the operator-driven oracle environment — the only place the
    oracle exists — and **an empty mapping disables clause 3 rather than satisfying it**,
    which is why the assertion says so in its detail instead of reporting a clean three-clause
    pass on a two-clause check.
    """
    if not diff_text.strip():
        return Assertion(
            assertion_id=ASSERTION_C15,
            outcome=AssertionOutcome.NOT_EXECUTED,
            detail="the diff is empty; a check over no lines is not a clean check",
        )

    denied_distributions = {name.lower() for name in denylist.denied_distributions}
    denied_modules = set(denylist.denied_modules)
    if not denied_distributions and not denied_modules:
        return Assertion(
            assertion_id=ASSERTION_C15,
            outcome=AssertionOutcome.NOT_EXECUTED,
            detail="the denylist names neither a distribution nor a module; nothing to check for",
        )

    added = _added_lines(diff_text)
    if not added:
        return Assertion(
            assertion_id=ASSERTION_C15,
            outcome=AssertionOutcome.NOT_EXECUTED,
            detail="the diff parsed to zero added lines; a scan of nothing is not a pass",
        )

    findings: list[PatchFinding] = []
    by_path: dict[str, list[str]] = {}

    for path, line_number, text in added:
        by_path.setdefault(path, []).append(text)
        basename = PurePosixPath(path).name
        lowered = text.lower()

        if basename in DEPENDENCY_FILENAMES:
            for distribution in sorted(denied_distributions):
                # Both spellings: a distribution is written `commonroad-crime` in a manifest
                # and `commonroad_crime` in an import, and a manifest can carry either.
                for spelling in {distribution, distribution.replace("-", "_")}:
                    if spelling in lowered:
                        findings.append(
                            PatchFinding(
                                clause="dependency",
                                path=path,
                                line_number=line_number,
                                detail=f"denied distribution {distribution!r} added to {basename}",
                            )
                        )
                        break

        for module in sorted(imported_top_level_names(text) & denied_modules):
            findings.append(
                PatchFinding(
                    clause="import",
                    path=path,
                    line_number=line_number,
                    detail=f"denied module {module!r} imported",
                )
            )

    clause_three_ran = bool(denied_source_hashes)
    if clause_three_ran and denied_source_hashes is not None:
        for path, lines in by_path.items():
            digest = normalized_source_hash("\n".join(lines))
            origin = denied_source_hashes.get(digest)
            if origin is not None:
                findings.append(
                    PatchFinding(
                        clause="vendored-source",
                        path=path,
                        line_number=1,
                        detail=(
                            f"normalized content matches the denied source file {origin!r}; "
                            "the oracle arrived through the deliverable channel"
                        ),
                    )
                )

    if findings:
        rendered = "; ".join(
            f"{f.clause} {f.path}:{f.line_number} — {f.detail}" for f in sorted(
                findings, key=lambda f: (f.path, f.line_number, f.clause)
            )
        )
        return Assertion(
            assertion_id=ASSERTION_C15, outcome=AssertionOutcome.FAILED, detail=rendered
        )

    clauses = "3 clauses" if clause_three_ran else "2 of 3 clauses (no denied source hashes supplied)"
    return Assertion(
        assertion_id=ASSERTION_C15,
        outcome=AssertionOutcome.PASSED,
        detail=f"{len(added)} added lines across {len(by_path)} file(s), {clauses} clean",
        # Clause 3 not running is not an unverified *premise* in ADR-0007's sense, but it is
        # the same shape of thing: a report that reads green over a check that did not run.
        premise_verified=clause_three_ran,
    )
