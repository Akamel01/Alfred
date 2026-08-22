#!/usr/bin/env python3
"""Two claims of CI coverage, checked against what CI actually runs.

`gates.yml` states the rule this file generalizes: *"If a check a document names is not in
this file, that document's enforcement value is a wish."* The same hazard applies one level
down, to things that are covered by enumeration. An enumeration drifts silently, in the
direction that reads green, and this project has now paid for that three times: a document
added without an index entry (2026-08-13), `gen_doc_stubs.py`'s register at 55 entries
against 63 documents, and the two findings below.

  T — every directory holding `test_*.py` under `harness/` and `tests/` is named in a
      `pytest` step in `.github/workflows/gates.yml`.

      This was found false. `harness/stamp` and `harness/fingerprint` ran in no CI job while
      the local baseline command — `pytest tests bench harness`, which walks the tree — read
      green. The local run and CI disagreed, and only the local one was ever looked at.

  F — every row id in `failure-semantics.md`'s fail-closed table has exactly one entry in
      `harness/selftest/failure_register.json`, every entry names a live row, and every entry
      claiming coverage names a file that exists and mentions the id.

      The document's Enforcement section claims CI asserts a one-to-one map from `F1`…`F28`
      to injection ids. Nothing enumerated F ids at all, so the claim was false, and the
      document says in its own words why the ids are stable: *"without stable ids the
      coverage lint below cannot be written at all."* The lint below is that one.

**Why F does not simply require an injection per row.** Requiring one today would report
twenty-four failures and hold CI red, and a lint that cannot be landed green enforces
nothing. So the register carries a status per row and `not-yet-injected` is a legal value —
recorded and counted, never hidden. What the lint forbids is *drift*: a row with no entry, an
entry for no row, or an entry claiming evidence that is not there. The count of covered rows
is printed on every run and is asserted against the number written in the document, so the
prose cannot quietly diverge from the register again.

That leaves one hole, stated rather than closed: a register declaring every row
`not-yet-injected` would pass. It is visible instead — the covered count is in the output and
in the document, so the number going down is a change a reader sees.

**Vacuity guard.** Each check reports what it scanned, and a check that scanned zero fails.
A test-directory scan finding no directories, or a table parse finding no rows, is the exact
shape of a lint that stopped working.

`--self-test` plants each violation in a temporary tree and requires the check to fire, and
requires the paired control to stay quiet. Exit 0 clean, 1 on any violation.

Inspector machinery under D20: agents may not edit this file without an authorizing ADR.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from _lintkit import (
    REPO_ROOT,
    Findings as _Findings,
    load_register,
    self_test_exit,
    vacuity_guard,
)

WORKFLOW: Final = Path(".github/workflows/gates.yml")
TEST_ROOTS: Final = (Path("harness"), Path("tests"))

FAILURE_DOC: Final = Path("docs/tier1/failure-semantics.md")
FAILURE_REGISTER: Final = Path("harness/selftest/failure_register.json")

# Statuses that count as covered. `referenced` is weaker than `injected` and is counted
# separately in the output, because collapsing them would let the covered number rise
# without a single fault being injected.
COVERED: Final = frozenset({"injected", "referenced"})
LEGAL_STATUSES: Final = COVERED | {"not-yet-injected"}

# The document states the covered count in a machine-readable marker rather than in prose.
# Parsing the sentence would tie the lint to wording, which is what the document itself warns
# against when it explains why the row ids are stable.
COUNT_MARKER: Final = re.compile(
    r"<!--\s*failure-register:\s*covered=(?P<covered>\d+)\s+total=(?P<total>\d+)\s*-->"
)

# Table rows look like `| F12 | ... | ... |`. Anchored to the leading pipe so a mention of
# `F12` in prose is not read as a row.
TABLE_ROW: Final = re.compile(r"^\|\s*(F\d+)\s*\|")


@dataclass
class Findings(_Findings):
    # Reported on every run so the number going down is a change a reader sees.
    covered: int = 0


# ------------------------------------------------------------------ T: CI reachability


def test_directories(roots: tuple[Path, ...] = TEST_ROOTS, base: Path = REPO_ROOT) -> list[Path]:
    """Every directory under `roots` holding at least one `test_*.py`, repo-relative.

    Directory-level rather than file-level because that is the granularity `gates.yml` uses:
    its steps name `pytest harness/acs`, not individual files. A file-level check would
    report a violation for every file in a directory CI already runs.
    """
    found: set[Path] = set()
    for root in roots:
        absolute = base / root
        if not absolute.is_dir():
            continue
        for path in absolute.rglob("test_*.py"):
            if "__pycache__" in path.parts:
                continue
            found.add(path.parent.relative_to(base))
    return sorted(found)


def check_ci_reachability(base: Path = REPO_ROOT, workflow: Path = WORKFLOW) -> Findings:
    """Each test directory must appear after `pytest` in some step of the workflow.

    Substring matching against the workflow text, deliberately: parsing the YAML and walking
    steps would let a directory named in a comment count as covered, and matching the literal
    `pytest <dir>` is what a reader checking by eye would do.
    """
    findings = Findings()
    workflow_path = base / workflow
    if not workflow_path.is_file():
        findings.violations.append(f"T missing workflow: {workflow}")
        return findings

    text = workflow_path.read_text(encoding="utf-8")
    # A step naming a parent covers its children: `pytest harness` runs `harness/acs`.
    invoked = {
        match.group("target")
        for match in re.finditer(r"pytest\s+(?P<target>[\w./-]+)", text)
    }

    for directory in test_directories(base=base):
        findings.scanned += 1
        covered = any(
            directory == Path(target) or Path(target) in directory.parents
            for target in invoked
        )
        if not covered:
            findings.violations.append(
                f"T {directory} holds test files and is named in no pytest step of {workflow}"
            )
    return findings


# ------------------------------------------------------------------ F: failure register


def document_row_ids(base: Path = REPO_ROOT, doc: Path = FAILURE_DOC) -> list[str]:
    path = base / doc
    if not path.is_file():
        return []
    return [
        match.group(1)
        for line in path.read_text(encoding="utf-8").splitlines()
        if (match := TABLE_ROW.match(line))
    ]


def check_failure_register(base: Path = REPO_ROOT) -> Findings:
    findings = Findings()

    register, error = load_register(base / FAILURE_REGISTER, display=FAILURE_REGISTER)
    if error is not None:
        findings.violations.append(f"F {error}")
        return findings

    rows: dict[str, dict[str, str]] = register.get("rows", {})
    ids_in_doc = document_row_ids(base=base)
    duplicates = {row for row in ids_in_doc if ids_in_doc.count(row) > 1}
    if duplicates:
        findings.violations.append(f"F duplicate row ids in the document: {sorted(duplicates)}")

    doc_set = set(ids_in_doc)
    findings.scanned = len(doc_set)

    for missing in sorted(doc_set - set(rows), key=_row_sort):
        findings.violations.append(f"F row {missing} is in the table and not in the register")
    for orphan in sorted(set(rows) - doc_set, key=_row_sort):
        findings.violations.append(f"F register entry {orphan} names no row in the table")

    covered = 0
    for row_id in sorted(set(rows) & doc_set, key=_row_sort):
        entry = rows[row_id]
        status = entry.get("status", "")
        if status not in LEGAL_STATUSES:
            findings.violations.append(
                f"F row {row_id} has status {status!r}; legal values are {sorted(LEGAL_STATUSES)}"
            )
            continue
        if status not in COVERED:
            continue
        covered += 1
        evidence = entry.get("evidence", "")
        # The control that stops the register becoming a second unverified claim: an entry
        # may not assert coverage by a file that does not exist or does not mention the row.
        if not evidence:
            findings.violations.append(f"F row {row_id} claims {status!r} with no evidence path")
            continue
        evidence_path = base / evidence
        if not evidence_path.is_file():
            findings.violations.append(f"F row {row_id} names evidence {evidence} which does not exist")
        elif not re.search(rf"\b{row_id}\b", evidence_path.read_text(encoding="utf-8")):
            findings.violations.append(f"F row {row_id} names evidence {evidence} which never mentions it")

    stated = (base / FAILURE_DOC).read_text(encoding="utf-8") if (base / FAILURE_DOC).is_file() else ""
    marker = COUNT_MARKER.search(stated)
    if marker is None:
        findings.violations.append(
            f"F {FAILURE_DOC} carries no `<!-- failure-register: covered=N total=M -->` marker; "
            "the document must state the count it claims"
        )
    else:
        if int(marker.group("covered")) != covered:
            findings.violations.append(
                f"F document states covered={marker.group('covered')}, register holds {covered}"
            )
        if int(marker.group("total")) != len(doc_set):
            findings.violations.append(
                f"F document states total={marker.group('total')}, table holds {len(doc_set)}"
            )

    findings.covered = covered
    return findings


def _row_sort(row_id: str) -> int:
    return int(row_id[1:])


# ---------------------------------------------------------------------- self-test


def _fixture(root: Path, *, workflow_targets: tuple[str, ...], test_dirs: tuple[str, ...]) -> None:
    """A miniature repository: some test directories, and a workflow naming some of them."""
    for directory in test_dirs:
        target = root / directory
        target.mkdir(parents=True, exist_ok=True)
        (target / "test_thing.py").write_text("def test_x() -> None: ...\n", encoding="utf-8")
    workflow = root / WORKFLOW
    workflow.parent.mkdir(parents=True, exist_ok=True)
    steps = "\n".join(f"      - run: uv run pytest {target}" for target in workflow_targets)
    workflow.write_text(f"name: gates\njobs:\n  x:\n    steps:\n{steps}\n", encoding="utf-8")


def self_test() -> int:
    """Plant each violation, require the check to fire, and require the control to stay quiet.

    Committed as a mode rather than a separate test file so it travels with the lint. A
    negative control living somewhere else is a control someone deletes without knowing what
    it was for -- and this lint's whole subject is things that stop being run without anyone
    noticing.
    """
    failures: list[str] = []

    with tempfile.TemporaryDirectory() as raw:
        scratch = Path(raw)

        # T control: every test directory named. Must be silent.
        clean = scratch / "clean"
        _fixture(clean, workflow_targets=("harness/alpha", "tests"), test_dirs=("harness/alpha", "tests"))
        control = check_ci_reachability(base=clean)
        if control.violations:
            failures.append(f"T control fired on clean input: {control.violations}")
        if control.scanned != 2:
            failures.append(f"T control scanned {control.scanned} directories, expected 2")

        # T planted: a directory with tests that no step names.
        planted = scratch / "planted"
        _fixture(planted, workflow_targets=("harness/alpha",), test_dirs=("harness/alpha", "harness/orphan"))
        if not check_ci_reachability(base=planted).violations:
            failures.append("T did not fire on a test directory absent from the workflow")

        # T parent coverage: `pytest harness` must cover `harness/alpha`, or the check would
        # report violations against a workflow that does run the tests.
        parent = scratch / "parent"
        _fixture(parent, workflow_targets=("harness",), test_dirs=("harness/alpha", "harness/beta"))
        if check_ci_reachability(base=parent).violations:
            failures.append("T fired despite a parent-directory pytest step covering the children")

        # T vacuity: no test directories at all must not read as a pass.
        empty = scratch / "empty"
        _fixture(empty, workflow_targets=("harness",), test_dirs=())
        if check_ci_reachability(base=empty).scanned != 0:
            failures.append("T empty tree did not report zero directories scanned")

        failures.extend(_self_test_register(scratch))

    return self_test_exit(
        failures,
        "OK self-test — T fires on an unnamed directory, honours parent steps, and reports "
        "zero on an empty tree; F fires on a missing row, an orphan entry, absent evidence "
        "and a stale count; both controls clean\n",
    )


_DOC_HEAD = "| id | Condition | Disposition |\n|---|---|---|\n"


def _register_fixture(root: Path, *, rows: dict[str, dict[str, str]], doc_ids: tuple[str, ...],
                      covered: int, total: int, evidence: dict[str, str] | None = None) -> None:
    doc = root / FAILURE_DOC
    doc.parent.mkdir(parents=True, exist_ok=True)
    table = _DOC_HEAD + "".join(f"| {row} | condition | disposition |\n" for row in doc_ids)
    doc.write_text(f"{table}\n<!-- failure-register: covered={covered} total={total} -->\n", encoding="utf-8")

    register = root / FAILURE_REGISTER
    register.parent.mkdir(parents=True, exist_ok=True)
    register.write_text(json.dumps({"rows": rows}), encoding="utf-8")

    for path, body in (evidence or {}).items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")


def _self_test_register(scratch: Path) -> list[str]:
    failures: list[str] = []

    ok = scratch / "reg-ok"
    _register_fixture(
        ok,
        rows={"F1": {"status": "referenced", "evidence": "t/test_a.py"}, "F2": {"status": "not-yet-injected"}},
        doc_ids=("F1", "F2"),
        covered=1,
        total=2,
        evidence={"t/test_a.py": "# exercises F1\n"},
    )
    control = check_failure_register(base=ok)
    if control.violations:
        failures.append(f"F control fired on clean input: {control.violations}")
    if control.covered != 1:
        failures.append(f"F control counted {control.covered} covered, expected 1")

    cases: tuple[tuple[str, dict[str, dict[str, str]], tuple[str, ...], int, int, dict[str, str]], ...] = (
        # A row in the table with no register entry.
        ("row missing from register", {"F1": {"status": "not-yet-injected"}}, ("F1", "F2"), 0, 2, {}),
        # A register entry for a row that no longer exists.
        ("orphan register entry",
         {"F1": {"status": "not-yet-injected"}, "F9": {"status": "not-yet-injected"}}, ("F1",), 0, 1, {}),
        # Coverage claimed against a file that is not there.
        ("evidence file absent",
         {"F1": {"status": "injected", "evidence": "t/gone.py"}}, ("F1",), 1, 1, {}),
        # Coverage claimed against a file that never mentions the row -- the control that
        # stops the register becoming a second unverified claim.
        ("evidence never mentions the row",
         {"F1": {"status": "injected", "evidence": "t/test_a.py"}}, ("F1",), 1, 1, {"t/test_a.py": "# nothing\n"}),
        # An illegal status, so a typo cannot silently become a fourth category.
        ("illegal status", {"F1": {"status": "probably-fine"}}, ("F1",), 0, 1, {}),
        # The document's stated count drifting from the register.
        ("stated count stale",
         {"F1": {"status": "referenced", "evidence": "t/test_a.py"}}, ("F1",), 0, 1, {"t/test_a.py": "F1\n"}),
    )

    for index, (label, rows, doc_ids, covered, total, evidence) in enumerate(cases):
        case = scratch / f"reg-{index}"
        _register_fixture(case, rows=rows, doc_ids=doc_ids, covered=covered, total=total, evidence=evidence)
        if not check_failure_register(base=case).violations:
            failures.append(f"F did not fire on {label}")

    # F vacuity: a table with no rows must not read as a pass.
    empty = scratch / "reg-empty"
    _register_fixture(empty, rows={}, doc_ids=(), covered=0, total=0)
    if check_failure_register(base=empty).scanned != 0:
        failures.append("F empty table did not report zero rows scanned")

    return failures


# --------------------------------------------------------------------------- main


def main() -> int:
    parser = argparse.ArgumentParser(description="CI coverage of things covered by enumeration.")
    parser.add_argument("--self-test", action="store_true", help="plant violations and verify each check fires")
    args = parser.parse_args()
    if args.self_test:
        return self_test()

    reachability = check_ci_reachability()
    register = check_failure_register()

    failed = False
    for label, findings in (("T test directories in CI", reachability), ("F failure register", register)):
        for violation in findings.violations:
            sys.stdout.write(f"{violation}\n")
            failed = True
        if vacuity_guard(findings.scanned, f"VACUOUS {label}: scanned 0\n"):
            failed = True

    if failed:
        return 1
    sys.stdout.write(
        f"OK ci coverage — T {reachability.scanned} test directories all named in the workflow; "
        f"F {register.scanned} rows registered, {register.covered} covered, "
        f"{register.scanned - register.covered} declared not-yet-injected\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
