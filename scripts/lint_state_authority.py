#!/usr/bin/env python3
"""SA001-SA003: the ownership router's mechanical half, checked.

ADR-0047 extends `docs/tier1/data-architecture.md`'s ownership router with the factory's own
facts and draws one hard line: **runtime state owns nothing and is never evidence.** Most of
that is a property only a reader can check — nothing in CI can tell that a document has quietly
become a second home for a fact. Three parts are mechanical, and a claim with a checkable part
should have the part checked rather than the whole thing left to review.

  SA001 every home the router names as a file path exists. A router pointing at a file nobody
        wrote is worse than a missing row: it reads as settled.
  SA002 no gated document references a runtime path. A document whose `enforcement` is
        `ci-gate` or `schema` is one a machine acts on, and ADR-0047 decision 3 says no gate,
        verdict or audit may cite `.autoforge/` or an ECC store. A citation inside a
        `review-cadence` or `none` document is allowed and is how the boundary gets explained.
  SA003 the router still contains the collision rule. The rule -- *the stream is a field set,
        the store is a schema, and the store never re-declares a stream field* -- is what
        resolves future collisions, and an extension that dropped it would leave the rows with
        nothing deciding between them.

**What this deliberately does not check.** Whether a fact has two homes. That is the property
the router exists for and it is not decidable from text: two documents can describe one fact in
words that share no token. Claiming otherwise here would be the wish `lint_ci_coverage.py`'s
docstring names.

**Vacuity guard.** The scan reports how many rows and documents it read, and zero fails.

`--self-test` plants each violation and requires the check to fire, with a paired control.

Exit 0 clean, 1 on any violation. Protected set: agents may not write this file.
"""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lintkit import REPO_ROOT, Findings, self_test_exit, vacuity_guard

ROUTER_PATH: Path = Path("docs/tier1/data-architecture.md")
DOCS_DIR: Path = Path("docs")

ROUTER_HEADING = "### Ownership, stated once so it is not restated inconsistently"

COLLISION_RULE = "the stream is a field set, the store is a schema, and the store never"

#: Runtime state, named once. ADR-0047 decision 3.
RUNTIME_MARKERS = (".autoforge/", "ecc.state-store", "ecc.memory.v1")

#: A document a machine acts on. The other two values describe rather than enforce.
GATED = ("ci-gate", "schema")

#: A row's first cell, when it names a file rather than a document title.
PATH_CELL = re.compile(r"`([A-Za-z0-9_./-]+\.(?:json|md|py|yml|yaml))`")

ENFORCEMENT = re.compile(r"^enforcement:\s*(\S+)\s*$", re.MULTILINE)


def _router_rows(text: str) -> list[str]:
    """The router's table rows, and nothing after the table."""
    if ROUTER_HEADING not in text:
        return []
    body = text.split(ROUTER_HEADING, 1)[1]
    rows: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("|") and not stripped.startswith("|---"):
            rows.append(stripped)
        elif rows and not stripped.startswith("|") and stripped:
            break
    return rows


def check_state_authority(base: Path = REPO_ROOT) -> Findings:
    findings = Findings()
    router = base / ROUTER_PATH
    if not router.exists():
        findings.violations.append(f"SA000 missing {ROUTER_PATH}")
        return findings

    text = router.read_text(encoding="utf-8")
    rows = _router_rows(text)
    if not rows:
        findings.violations.append(f"SA000 {ROUTER_PATH} has no ownership router table")
        return findings

    # SA001 -- every named file exists.
    for row in rows:
        owner_cell = row.split("|")[1] if row.count("|") > 1 else ""
        for match in PATH_CELL.finditer(owner_cell):
            named = match.group(1)
            if not (base / named).exists():
                findings.violations.append(
                    f"SA001 router names {named!r} as a home, and no such file exists"
                )

    # SA003 -- the rule that decides between the rows is still present. Matched against
    # whitespace-normalized text: the rule wraps across lines in the real document, and a
    # check that only finds it unwrapped would fail on correct prose.
    if COLLISION_RULE not in " ".join(text.split()):
        findings.violations.append(
            "SA003 the collision rule is missing from the router; the rows have nothing "
            "deciding between them"
        )

    # SA002 -- no gated document cites runtime state.
    router_rows = set(rows)
    docs = sorted((base / DOCS_DIR).rglob("*.md"))
    findings.scanned = len(rows) + len(docs)
    for doc in docs:
        body = doc.read_text(encoding="utf-8")
        match = ENFORCEMENT.search(body)
        if match is None or match.group(1) not in GATED:
            continue
        # The router's own rows are exempt, and the exemption is the point rather than a
        # convenience: the router is the one place runtime state is named in order to say it
        # owns nothing. Naming a thing as excluded is the opposite of depending on it, and a
        # check that could not tell those apart would forbid the statement of its own rule.
        scannable = "\n".join(
            line for line in body.splitlines() if line.strip() not in router_rows
        )
        for marker in RUNTIME_MARKERS:
            if marker in scannable:
                findings.violations.append(
                    f"SA002 {doc.relative_to(base)} is enforcement:{match.group(1)} and cites "
                    f"runtime state {marker!r}; ADR-0047 decision 3 forbids a gate citing it"
                )

    return findings


# ------------------------------------------------------------------------------- self-test


_ROUTER_OK = f"""---
status:        frozen
enforcement:   review-cadence
---

# Data Architecture

{ROUTER_HEADING}

| Owner | Owns | Does not own |
|---|---|---|
| **`policy/thing.json`** | A fact. | Another fact. |

The rule that resolves every future collision: **{COLLISION_RULE} re-declares a stream field.**
"""

_GATED_CLEAN = """---
status:        provisional
enforcement:   schema
---

# A Gated Document

It cites no runtime state.
"""


def _write(root: Path, router: str, gated: str, make_thing: bool = True) -> None:
    r = root / ROUTER_PATH
    r.parent.mkdir(parents=True, exist_ok=True)
    r.write_text(router, encoding="utf-8")
    g = root / DOCS_DIR / "tier3" / "gated.md"
    g.parent.mkdir(parents=True, exist_ok=True)
    g.write_text(gated, encoding="utf-8")
    if make_thing:
        t = root / "policy" / "thing.json"
        t.parent.mkdir(parents=True, exist_ok=True)
        t.write_text("{}", encoding="utf-8")


def self_test() -> int:
    failures: list[str] = []

    with tempfile.TemporaryDirectory() as raw:
        scratch = Path(raw)

        clean = scratch / "clean"
        _write(clean, _ROUTER_OK, _GATED_CLEAN)
        ctrl = check_state_authority(base=clean)
        if ctrl.violations:
            failures.append(f"control fired on clean: {ctrl.violations}")

        # SA001 a home that does not exist
        case = scratch / "sa001"
        _write(case, _ROUTER_OK, _GATED_CLEAN, make_thing=False)
        if not any("SA001" in v for v in check_state_authority(base=case).violations):
            failures.append("SA001 did not fire on a home with no file")

        # SA002 a gated document citing runtime state
        case = scratch / "sa002"
        _write(case, _ROUTER_OK, _GATED_CLEAN.replace("It cites no runtime state.", "See .autoforge/state.json."))
        if not any("SA002" in v for v in check_state_authority(base=case).violations):
            failures.append("SA002 did not fire on a gated document citing runtime state")

        # SA002 paired control: an ungated document may cite it, and must be able to
        case = scratch / "sa002-ok"
        ungated = _GATED_CLEAN.replace("enforcement:   schema", "enforcement:   review-cadence")
        _write(case, _ROUTER_OK, ungated.replace("It cites no runtime state.", "See .autoforge/state.json."))
        if any("SA002" in v for v in check_state_authority(base=case).violations):
            failures.append("SA002 fired on an ungated document explaining the boundary")

        # SA003 the collision rule dropped
        case = scratch / "sa003"
        _write(case, _ROUTER_OK.replace(COLLISION_RULE, "some other words"), _GATED_CLEAN)
        if not any("SA003" in v for v in check_state_authority(base=case).violations):
            failures.append("SA003 did not fire on a router missing the collision rule")

    return self_test_exit(
        failures,
        "OK self-test — SA001 missing home, SA002 gated document citing runtime state with "
        "its paired ungated control, SA003 collision rule dropped; control clean\n",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint state authority SA001-SA003")
    parser.add_argument("--check", action="store_true", help="check files (default)")
    parser.add_argument("--self-test", action="store_true", help="plant violations and verify each check fires")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    findings = check_state_authority()
    for violation in findings.violations:
        sys.stdout.write(f"{violation}\n")
    if vacuity_guard(findings.scanned, "VACUOUS state authority: scanned 0 rows+documents\n"):
        return 1
    if findings.violations:
        return 1
    sys.stdout.write(
        f"OK state authority — {findings.scanned} router rows+documents, all SA001-SA003 satisfied\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
