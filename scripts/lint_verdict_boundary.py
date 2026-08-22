#!/usr/bin/env python3
"""D16/D39: the verdict boundary, enforced structurally rather than by convention.

**Why this exists as a lint and not as a graph-engine feature.** LangGraph raises only on
*concurrent* unreducered writes. A **sequential** write to a verdict field raises nothing,
so "agent nodes are schema-forbidden from writing verdicts" is a convention unless
something checks it. D39 draws the conclusion: the boundary is physical — a module with no
import path from any agent module, in a separate process, under a separate DB role — and
the security property comes from port separation, never from inspecting field names at
runtime.

Two of those three are enforced elsewhere. The process is a process; the role is a grant,
asserted by `harness/db/assert_grants.py`. **The import path is what this file asserts**,
plus the vocabulary half of D16.

Three checks, each closing a direction the others leave open:

  V — no module in the agent-writable tree declares a verdict-vocabulary field or returns
      one. This is D16 read literally: an agent-invoking node cannot return what it cannot
      name.
  I — no module in the agent-writable tree reaches a verdict-writing module, transitively.
      This is D39. The transitive part is the point: a one-hop check passes on
      `agent_node -> helpers -> evidence.store`.
  R — no verdict-writing module reaches the agent-writable tree. The reverse direction,
      and the one that gets forgotten. `CriterionRunner` executes candidate code as a
      subprocess and must never import it: an import would put agent-authored code inside
      the process that holds the `heldout` credential.

**`harness/acs` is deliberately not a verdict module.** `src/provenance/encoding.py`
imports the ACS-1 encoder, and that edge is correct — there must be exactly one canonical
form, and a second encoder in the product tree would be a second canonical form. Banning
all of `harness/` would forbid the one import the architecture requires.

**Vacuity guard.** Every check reports the number of files it scanned, and a check that
scanned zero files fails. Today the V check has no agent-invoking node to look at, because
no graph exists — so without this guard the lint would report green for a reason that has
nothing to do with the property, and would keep reporting green on the day the first agent
node lands in a directory the globs do not cover.

`--self-test` builds fixture trees in a temporary directory and requires each check to
fire on a planted violation and to stay quiet on its paired control. A lint with no
negative control reports the same thing whether it works or not.

Exit 0 clean, 1 on any violation. Protected set: agents may not write this file.
"""

from __future__ import annotations

import argparse
import ast
import sys
import tempfile
from collections import deque
from pathlib import Path
from typing import Final

from _lintkit import REPO_ROOT, Findings, self_test_exit, vacuity_guard

# The agent-writable tree. `src` is the package root, so `src/metrics/value.py` is the
# module `metrics.value` — matching [tool.pyright].extraPaths and the documented layout.
AGENT_TREE: Final = Path("src")

# Modules that write or compose a verdict. Prefixes, matched on the dotted module name.
VERDICT_MODULES: Final = ("harness.evidence", "harness.criterion")

# The vocabulary D16 forbids an agent-invoking node from naming. Deliberately short:
# `score` is absent because it is an ordinary word that a metric module may legitimately
# use, and a lint that fires on ordinary words gets disabled rather than obeyed.
VERDICT_FIELDS: Final = frozenset({"verdict", "held_out_result", "indeterminate_reason"})

# A return annotation enumerating the three-valued vocabulary is a verdict type whatever
# it is called, so the name check alone would miss `-> Literal["pass", "fail",
# "indeterminate"]` on a function named `classify`.
VERDICT_LITERALS: Final = frozenset({"pass", "fail", "indeterminate"})


def _module_name(path: Path, root: Path, *, strip_root: bool) -> str:
    relative = path.relative_to(REPO_ROOT / root if strip_root else REPO_ROOT)
    parts = list(relative.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _python_files(root: Path, base: Path = REPO_ROOT) -> list[Path]:
    directory = base / root
    if not directory.is_dir():
        return []
    return sorted(p for p in directory.rglob("*.py") if "__pycache__" not in p.parts)


# ------------------------------------------------------------------ V: vocabulary


def _annotation_names(node: ast.expr | None) -> set[str]:
    if node is None:
        return set()
    found: set[str] = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
            found.add(sub.value)
        elif isinstance(sub, ast.Name):
            found.add(sub.id)
        elif isinstance(sub, ast.Attribute):
            found.add(sub.attr)
    return found


def check_vocabulary(roots: tuple[Path, ...], base: Path = REPO_ROOT) -> Findings:
    result = Findings()
    for root in roots:
        for path in _python_files(root, base):
            result.scanned += 1
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            display = path.relative_to(base)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    names = _annotation_names(node.returns)
                    named = sorted(names & VERDICT_FIELDS)
                    if named:
                        result.violations.append(
                            f"{display}:{node.lineno}: {node.name} returns a type naming "
                            f"{', '.join(named)}"
                        )
                    if VERDICT_LITERALS <= names:
                        result.violations.append(
                            f"{display}:{node.lineno}: {node.name} returns the three-valued "
                            f"verdict vocabulary"
                        )
                elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                    if node.target.id in VERDICT_FIELDS:
                        result.violations.append(
                            f"{display}:{node.lineno}: declares field {node.target.id!r}"
                        )
    return result


# --------------------------------------------------------------- I/R: import graph


def _imports(tree: ast.AST) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.add(node.module)
            # `from a.b import c` may name a module or a name; both are recorded, and a
            # non-module simply never matches a real module in the graph.
            found.update(f"{node.module}.{alias.name}" for alias in node.names)
    return found


def _build_graph() -> tuple[dict[str, set[str]], dict[str, Path]]:
    graph: dict[str, set[str]] = {}
    origin: dict[str, Path] = {}
    for root, strip in ((AGENT_TREE, True), (Path("harness"), False)):
        for path in _python_files(root):
            name = _module_name(path, root, strip_root=strip)
            if not name:
                continue
            origin[name] = path
            graph[name] = _imports(ast.parse(path.read_text(encoding="utf-8"), filename=str(path)))
    return graph, origin


def _reaches(
    graph: dict[str, set[str]], start: str, predicate: object
) -> list[str] | None:
    """Shortest import path from `start` to a module the predicate accepts, or None."""
    assert callable(predicate)
    queue: deque[tuple[str, list[str]]] = deque([(start, [start])])
    seen = {start}
    while queue:
        current, trail = queue.popleft()
        for target in sorted(graph.get(current, set())):
            if target in seen:
                continue
            seen.add(target)
            path = [*trail, target]
            if predicate(target):
                return path
            if target in graph:
                queue.append((target, path))
    return None


def check_imports(graph: dict[str, set[str]], origin: dict[str, Path]) -> tuple[Findings, Findings]:
    agent_modules = sorted(
        name for name, path in origin.items() if path.is_relative_to(REPO_ROOT / AGENT_TREE)
    )
    verdict_modules = sorted(
        name for name in origin if name.startswith(VERDICT_MODULES)
    )

    forward = Findings(scanned=len(agent_modules))
    for name in agent_modules:
        trail = _reaches(graph, name, lambda target: target.startswith(VERDICT_MODULES))
        if trail:
            forward.violations.append(
                f"{origin[name].relative_to(REPO_ROOT)}: reaches a verdict module: "
                f"{' -> '.join(trail)}"
            )

    agent_roots = tuple(p.name for p in (REPO_ROOT / AGENT_TREE).iterdir() if p.is_dir())
    reverse = Findings(scanned=len(verdict_modules))
    for name in verdict_modules:
        trail = _reaches(
            graph, name, lambda target: target.split(".")[0] in agent_roots
        )
        if trail:
            reverse.violations.append(
                f"{origin[name].relative_to(REPO_ROOT)}: reaches the agent tree: "
                f"{' -> '.join(trail)}"
            )
    return forward, reverse


# ---------------------------------------------------------------------- self-test


SELF_TEST_CASES: Final = (
    ("V", "verdict-named return", 'def decide() -> "verdict": ...\n'),
    ("V", "three-valued literal", 'from typing import Literal\ndef decide() -> Literal["pass", "fail", "indeterminate"]: ...\n'),
    ("V", "declared field", "class Out:\n    verdict: str\n"),
)


def self_test() -> int:
    """Plant each violation and require the check to fire; then require it to stay quiet.

    Written as a committed mode rather than as a separate test file so it travels with
    the lint: a negative control in another repository directory is a control someone
    deletes without noticing what it was for.

    The I and R controls below are the two checks whose absence was this file's own
    stated purpose gap: until they landed the self-test planted V violations only, so
    the import-graph checks — the reason D39 gives this lint its job, and the half a
    one-hop review of the tree cannot do — fired on nothing but whatever the live tree
    happened to contain.
    """
    failures: list[str] = []

    with tempfile.TemporaryDirectory() as raw:
        scratch = Path(raw)
        clean = scratch / "clean"
        clean.mkdir()
        (clean / "ok.py").write_text(
            # Deliberately adjacent to the vocabulary without being in it. A control
            # using an obviously unrelated function would not notice a check that fired
            # on any annotated return at all.
            "def score_of(x: float) -> float:\n    return x\n",
            encoding="utf-8",
        )

        baseline = check_vocabulary((Path("clean"),), scratch)
        if baseline.violations:
            failures.append(f"control fired on clean input: {baseline.violations}")
        if baseline.scanned != 1:
            failures.append(f"control scanned {baseline.scanned} files, expected 1")

        for index, (check, label, source) in enumerate(SELF_TEST_CASES):
            planted = scratch / f"case{index}"
            planted.mkdir()
            (planted / "bad.py").write_text(source, encoding="utf-8")
            found = check_vocabulary((Path(f"case{index}"),), scratch)
            if not found.violations:
                failures.append(f"{check} did not fire on {label}")

        # The vacuity guard itself, which is the control most likely to be absent.
        if check_vocabulary((Path("nothing-here"),), scratch).scanned != 0:
            failures.append("empty-tree scan did not report zero files")

    # --- I and R, planted against fabricated graphs rather than files: `check_imports`
    # is pure over `(graph, origin)`, so the fixtures need no tempdir and no tree at all,
    # the same property `lint_adr_numbers.py` claims for its planted logs.

    # The reverse check's predicate asks which directories exist under src/, so the plant
    # names one that does, read at run time rather than hard-coded.
    agent_dir = next(p.name for p in (REPO_ROOT / AGENT_TREE).iterdir() if p.is_dir())

    def origin(paths: dict[str, str]) -> dict[str, Path]:
        return {name: REPO_ROOT / rel for name, rel in paths.items()}

    # I planted: an agent node reaching a verdict module through a helper — exactly the
    # second hop that makes this check transitive rather than one-hop.
    forward_planted, reverse_quiet = check_imports(
        {"src.node": {"helpers"}, "helpers": {"harness.evidence.store"}},
        origin({"src.node": "src/node.py", "helpers": "helpers.py",
                "harness.evidence.store": "harness/evidence/store.py"}),
    )
    if not forward_planted.violations:
        failures.append("I did not fire on an agent module transitively reaching a verdict module")
    if forward_planted.scanned != 1:
        failures.append(f"I scanned {forward_planted.scanned} agent modules, expected 1")
    if reverse_quiet.violations:
        failures.append(f"R fired on a verdict module importing nothing: {reverse_quiet.violations}")

    # R planted: a verdict-writing module reaching the agent tree — the direction that
    # would put candidate code inside the process holding the `heldout` credential.
    _, reverse_planted = check_imports(
        {"harness.criterion.runner": {f"{agent_dir}.candidate"}},
        origin({"harness.criterion.runner": "harness/criterion/runner.py",
                f"{agent_dir}.candidate": f"src/{agent_dir}/candidate.py"}),
    )
    if not reverse_planted.violations:
        failures.append("R did not fire on a verdict module reaching the agent tree")
    if reverse_planted.scanned != 1:
        failures.append(f"R scanned {reverse_planted.scanned} verdict modules, expected 1")

    # I control: the same node importing nothing verdict-shaped must stay quiet — the arm
    # that separates "the boundary holds" from "the check reports red unconditionally".
    forward_control, _ = check_imports(
        {"src.node": {"json"}},
        origin({"src.node": "src/node.py"}),
    )
    if forward_control.violations:
        failures.append(f"I fired on an agent module importing only stdlib: {forward_control.violations}")

    planted_count = len(SELF_TEST_CASES) + 2  # the I and R plants above
    return self_test_exit(
        failures,
        f"OK self-test — {planted_count} planted violations detected "
        f"(V vocabulary, I forward reach, R reverse reach), "
        f"control clean, vacuity guard reports zero\n",
    )


# --------------------------------------------------------------------------- main


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="plant violations and verify each check fires")
    args = parser.parse_args()
    if args.self_test:
        return self_test()

    vocabulary = check_vocabulary((AGENT_TREE,))
    graph, origin = _build_graph()
    forward, reverse = check_imports(graph, origin)

    checks = (
        ("V vocabulary in the agent tree", vocabulary),
        ("I agent tree reaches a verdict module", forward),
        ("R verdict module reaches the agent tree", reverse),
    )

    failed = False
    for label, findings in checks:
        for violation in findings.violations:
            sys.stdout.write(f"{violation}\n")
            failed = True
        if vacuity_guard(findings.scanned, f"VACUOUS {label}: scanned 0 files\n"):
            failed = True

    if failed:
        return 1
    summary = ", ".join(f"{label.split()[0]}={findings.scanned}" for label, findings in checks)
    sys.stdout.write(f"OK verdict boundary holds ({summary} files/modules scanned)\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
