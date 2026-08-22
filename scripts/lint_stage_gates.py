#!/usr/bin/env python3
"""The stage gate, as a check rather than as a sentence somebody reads.

`docs/tier2/stage-gate-definitions.md` carried `enforcement: ci-gate` from the day it was
written and named no check in `.github/workflows/gates.yml`. By that workflow's own rule —
*"if a check a document names is not in this file, that document's enforcement value is a
wish"* — it was falsified by its own frontmatter for its whole life as a stub. Phase 0's exit
criteria lived only as prose in an orchestrator-owned plan file, so the calendar argument that
produced ADR-0022 was made against text nothing could evaluate.

**Two modes, and the split is the substance.**

  default    Register integrity. Every criterion id in the document has exactly one entry in
             `harness/selftest/stage_gate_register.json`; every entry names a live criterion;
             every `met` carries evidence that resolves; every status and kind is legal. This
             runs on every push and is green today. It says nothing about whether the phase may
             be exited — only that the record of the phase is well formed.

  --gate P   The exit gate. Every criterion in phase `P` must be `met`. Run when exit is
             claimed, not on every push. A gate reporting red from the day it is written until
             the day the phase ends is red for reasons nobody reads, and a check nobody reads
             is a check that is off.

**`blocked` is a failure, not a third outcome.** A criterion that could not be evaluated —
P0-6 today, because no Tier 0 recovery objective exists to compare a restore duration against
— is not a criterion that passed. That is F25 applied to gates instead of to containment
assertions, and it is the reason `blocked` carries a mandatory `reason`: an unevaluable
criterion that cannot say why is indistinguishable from one nobody looked at.

**Evidence that does not resolve is a failure.** An `automatic` criterion marked met must name
a path that exists; a criterion may not attest to itself by assertion. This is the same clause
`lint_ci_coverage.py` carries for the failure register, and it exists for the same reason: a
register whose entries are unchecked replaces one unverified claim with another.

**Vacuity guard.** Both modes fail on zero criteria scanned. A gate with nothing to evaluate
reports what a passed gate reports.

`--self-test` plants each violation in a temporary tree and requires the check to fire, and
requires the paired control to stay quiet. Exit 0 clean, 1 on any violation.

Inspector machinery under D20. Authorized by ADR-0022, which specifies this document as the
home of the narrowed criteria; Major-fix #8 permits an existing ADR to be the authorizing one.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from _lintkit import (
    REPO_ROOT,
    Findings as _Findings,
    load_register,
    self_test_exit,
    vacuity_guard,
)

GATE_DOC: Final = Path("docs/tier2/stage-gate-definitions.md")
GATE_REGISTER: Final = Path("harness/selftest/stage_gate_register.json")

LEGAL_STATUSES: Final = frozenset({"met", "unmet", "blocked"})
LEGAL_KINDS: Final = frozenset({"automatic", "attested"})

# Criterion ids look like `P0-4` in a table row: phase digit, hyphen, index. Anchored to the
# leading pipe so a mention in prose is not read as a row, matching the failure-register lint.
CRITERION_ROW: Final = re.compile(r"^\|\s*(P\d+-\d+)\s*\|")

# Which phase a criterion id belongs to. `P0-4` is phase0.
PHASE_OF: Final = re.compile(r"^P(?P<phase>\d+)-\d+$")


@dataclass
class Findings(_Findings):
    met: int = 0


def document_criteria(base: Path = REPO_ROOT) -> list[str]:
    path = base / GATE_DOC
    if not path.is_file():
        return []
    return [
        match.group(1)
        for line in path.read_text(encoding="utf-8").splitlines()
        if (match := CRITERION_ROW.match(line))
    ]


def _phase_key(criterion_id: str) -> str:
    match = PHASE_OF.match(criterion_id)
    return f"phase{match.group('phase')}" if match else ""


def registered_criteria(register: dict[str, Any]) -> dict[str, dict[str, str]]:
    """Flatten `phases.<phase>.criteria` into one id-keyed mapping."""
    flat: dict[str, dict[str, str]] = {}
    for phase in register.get("phases", {}).values():
        for criterion_id, entry in phase.get("criteria", {}).items():
            flat[criterion_id] = entry
    return flat


def check_integrity(base: Path = REPO_ROOT) -> Findings:
    findings = Findings()

    register, error = load_register(base / GATE_REGISTER, display=GATE_REGISTER)
    if error is not None:
        findings.violations.append(error)
        return findings

    in_doc = document_criteria(base)
    duplicates = {c for c in in_doc if in_doc.count(c) > 1}
    if duplicates:
        findings.violations.append(f"duplicate criterion ids in the document: {sorted(duplicates)}")

    doc_set = set(in_doc)
    entries = registered_criteria(register)
    findings.scanned = len(doc_set)

    for missing in sorted(doc_set - set(entries)):
        findings.violations.append(f"{missing} is in the document and not in the register")
    for orphan in sorted(set(entries) - doc_set):
        findings.violations.append(f"register entry {orphan} names no criterion in the document")

    for criterion_id in sorted(doc_set & set(entries)):
        entry = entries[criterion_id]
        status = entry.get("status", "")
        kind = entry.get("kind", "")

        if status not in LEGAL_STATUSES:
            findings.violations.append(
                f"{criterion_id} has status {status!r}; legal values are {sorted(LEGAL_STATUSES)}"
            )
            continue
        if kind not in LEGAL_KINDS:
            findings.violations.append(
                f"{criterion_id} has kind {kind!r}; legal values are {sorted(LEGAL_KINDS)}"
            )
            continue

        # The register must also place the criterion in the phase its id declares, or a
        # criterion could be marked met in one phase and gated in another.
        expected = _phase_key(criterion_id)
        if criterion_id not in register.get("phases", {}).get(expected, {}).get("criteria", {}):
            findings.violations.append(f"{criterion_id} is registered outside {expected}")

        if status == "met":
            findings.met += 1
            evidence = entry.get("evidence", "")
            if not evidence:
                findings.violations.append(f"{criterion_id} is marked met with no evidence")
            elif kind == "automatic" and not (base / evidence).exists():
                # An attested criterion's evidence may be a run or an ADR reference and is not
                # resolvable as a path; an automatic one's must be.
                findings.violations.append(
                    f"{criterion_id} is marked met naming evidence {evidence} which does not exist"
                )
        elif not entry.get("reason", ""):
            # A criterion that is not met must say why. Without it the register records a
            # state and not a situation, and the next reader re-derives it from nothing.
            findings.violations.append(f"{criterion_id} is {status!r} with no reason recorded")

    return findings


def check_gate(phase: str, base: Path = REPO_ROOT) -> Findings:
    findings = Findings()

    register, error = load_register(base / GATE_REGISTER, display=GATE_REGISTER)
    if error is not None:
        findings.violations.append(error)
        return findings

    criteria: dict[str, dict[str, str]] = register.get("phases", {}).get(phase, {}).get("criteria", {})
    findings.scanned = len(criteria)

    for criterion_id in sorted(criteria):
        entry = criteria[criterion_id]
        status = entry.get("status", "")
        if status == "met":
            findings.met += 1
            continue
        reason = entry.get("reason", "(no reason recorded)")
        # `blocked` is reported distinctly from `unmet` because they call for different
        # actions -- one needs the work done, the other needs something to exist before the
        # work can even be judged -- and neither is a pass.
        findings.violations.append(f"{phase} {criterion_id} {status.upper()}: {reason}")

    return findings


# ---------------------------------------------------------------------- self-test


_DOC_HEAD = "| id | Criterion | Kind | Evidence |\n|---|---|---|---|\n"


def _fixture(root: Path, *, doc_ids: tuple[str, ...], criteria: dict[str, dict[str, str]],
             files: tuple[str, ...] = ()) -> None:
    doc = root / GATE_DOC
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text(
        _DOC_HEAD + "".join(f"| {c} | criterion | automatic | evidence |\n" for c in doc_ids),
        encoding="utf-8",
    )

    phases: dict[str, Any] = {}
    for criterion_id, entry in criteria.items():
        phases.setdefault(_phase_key(criterion_id), {"criteria": {}})["criteria"][criterion_id] = entry

    register = root / GATE_REGISTER
    register.parent.mkdir(parents=True, exist_ok=True)
    register.write_text(json.dumps({"phases": phases}), encoding="utf-8")

    for name in files:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("x\n", encoding="utf-8")


def self_test() -> int:
    """Plant each violation, require the check to fire, and require the control to stay quiet.

    Committed as a mode rather than a separate test file so it travels with the lint: a gate's
    negative control is the part most worth keeping next to the gate.
    """
    failures: list[str] = []

    with tempfile.TemporaryDirectory() as raw:
        scratch = Path(raw)

        clean = scratch / "clean"
        _fixture(
            clean,
            doc_ids=("P0-1", "P0-2"),
            criteria={
                "P0-1": {"status": "met", "kind": "automatic", "evidence": "h/test_a.py"},
                "P0-2": {"status": "unmet", "kind": "attested", "reason": "not built"},
            },
            files=("h/test_a.py",),
        )
        control = check_integrity(base=clean)
        if control.violations:
            failures.append(f"integrity control fired on clean input: {control.violations}")
        if control.scanned != 2:
            failures.append(f"integrity control scanned {control.scanned}, expected 2")

        cases: tuple[tuple[str, tuple[str, ...], dict[str, dict[str, str]], tuple[str, ...]], ...] = (
            ("criterion missing from register", ("P0-1", "P0-2"),
             {"P0-1": {"status": "unmet", "kind": "attested", "reason": "r"}}, ()),
            ("orphan register entry", ("P0-1",),
             {"P0-1": {"status": "unmet", "kind": "attested", "reason": "r"},
              "P0-9": {"status": "unmet", "kind": "attested", "reason": "r"}}, ()),
            ("met with no evidence", ("P0-1",),
             {"P0-1": {"status": "met", "kind": "automatic"}}, ()),
            ("met naming evidence that does not exist", ("P0-1",),
             {"P0-1": {"status": "met", "kind": "automatic", "evidence": "h/gone.py"}}, ()),
            ("illegal status", ("P0-1",),
             {"P0-1": {"status": "probably-fine", "kind": "automatic", "evidence": "h/test_a.py"}},
             ("h/test_a.py",)),
            ("illegal kind", ("P0-1",),
             {"P0-1": {"status": "unmet", "kind": "vibes", "reason": "r"}}, ()),
            # The clause that stops the register recording a state without a situation.
            ("unmet with no reason", ("P0-1",),
             {"P0-1": {"status": "unmet", "kind": "attested"}}, ()),
            ("blocked with no reason", ("P0-1",),
             {"P0-1": {"status": "blocked", "kind": "attested"}}, ()),
        )

        for index, (label, doc_ids, criteria, files) in enumerate(cases):
            case = scratch / f"case{index}"
            _fixture(case, doc_ids=doc_ids, criteria=criteria, files=files)
            if not check_integrity(base=case).violations:
                failures.append(f"integrity did not fire on {label}")

        empty = scratch / "empty"
        _fixture(empty, doc_ids=(), criteria={})
        if check_integrity(base=empty).scanned != 0:
            failures.append("integrity on an empty document did not report zero criteria")

        # --- the gate mode, whose controls are separate: it must pass only on all-met, and
        # must refuse `blocked` exactly as it refuses `unmet`.
        passing = scratch / "gate-pass"
        _fixture(
            passing,
            doc_ids=("P0-1",),
            criteria={"P0-1": {"status": "met", "kind": "automatic", "evidence": "h/test_a.py"}},
            files=("h/test_a.py",),
        )
        if check_gate("phase0", base=passing).violations:
            failures.append("gate refused a phase whose every criterion is met")

        for status in ("unmet", "blocked"):
            case = scratch / f"gate-{status}"
            _fixture(
                case,
                doc_ids=("P0-1", "P0-2"),
                criteria={
                    "P0-1": {"status": "met", "kind": "automatic", "evidence": "h/test_a.py"},
                    "P0-2": {"status": status, "kind": "attested", "reason": "r"},
                },
                files=("h/test_a.py",),
            )
            if not check_gate("phase0", base=case).violations:
                failures.append(f"gate passed a phase carrying a {status} criterion")

        # A phase name nobody has written criteria for must not read as an exit.
        if check_gate("phase9", base=passing).scanned != 0:
            failures.append("gate on an unknown phase did not report zero criteria")

    return self_test_exit(
        failures,
        "OK self-test — integrity fires on a missing criterion, an orphan entry, unresolvable "
        "evidence, illegal status and kind, and a reasonless unmet or blocked; the gate refuses "
        "both unmet and blocked and passes only on all-met; both vacuity guards report zero\n",
    )


# --------------------------------------------------------------------------- main


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage gate register integrity, and the exit gate.")
    parser.add_argument("--gate", metavar="PHASE", help="evaluate the exit gate for PHASE, e.g. phase0")
    parser.add_argument("--self-test", action="store_true", help="plant violations and verify each check fires")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    if args.gate:
        findings = check_gate(args.gate)
        for violation in findings.violations:
            sys.stdout.write(f"{violation}\n")
        if vacuity_guard(findings.scanned, f"VACUOUS gate {args.gate}: no criteria registered\n"):
            return 1
        if findings.violations:
            sys.stdout.write(
                f"GATE RED {args.gate}: {findings.met} of {findings.scanned} criteria met. "
                "Exiting requires a waiver ADR naming each criterion above.\n"
            )
            return 1
        sys.stdout.write(f"GATE GREEN {args.gate}: {findings.scanned} of {findings.scanned} criteria met\n")
        return 0

    findings = check_integrity()
    for violation in findings.violations:
        sys.stdout.write(f"{violation}\n")
    if vacuity_guard(findings.scanned, "VACUOUS stage gates: scanned 0 criteria\n"):
        return 1
    if findings.violations:
        return 1
    sys.stdout.write(
        f"OK stage gates — {findings.scanned} criteria registered and agreeing with the document, "
        f"{findings.met} met, evidence resolves. Exit status is `--gate phase0`, not this.\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
