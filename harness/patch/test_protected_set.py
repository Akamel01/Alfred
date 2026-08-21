"""The protected set is policy configuration, and the policy is one home (ADR-0031).

Three things must agree: `policy/protected-paths.json` (what the gate loads), the
behaviour of `validate.py` (what the gate actually refuses), and the table in
`docs/tier4/protected-paths-policy.md` (what a human is told). Set equality in both
directions, on the grants precedent (ADR-0009): a check that compares only one
direction passes on every missing entry, and a missing entry is the only kind of
drift that fails in the safe-looking direction.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from harness.patch.validate import (
    ProtectedSetError,
    load_protected_set,
    validate_patch,
)

REPO = Path(__file__).resolve().parents[2]
DOC = REPO / "docs" / "tier4" / "protected-paths-policy.md"


def _diff_for(path: str, added: str = "x = 1") -> str:
    return (
        f"diff --git a/{path} b/{path}\n"
        f"--- a/{path}\n+++ b/{path}\n@@ -0,0 +1 @@\n+{added}\n"
    )


def _rules(diff: str) -> set[str]:
    return {f.rule for f in validate_patch(diff).findings}


def _doc_row_labels() -> list[str]:
    """The first cell of every row of the frozen table, in order.

    Backticked spans are the paths; a cell with none — the conceptual rows — is its own
    label. The header and separator rows are not rows.
    """
    text = DOC.read_text(encoding="utf-8")
    section = text.split("## The protected set", 1)[1].split("## Enforcement", 1)[0]
    rows: list[str] = []
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        cell = line.split("|")[1].strip()
        if not cell or set(cell) <= {"-", " "} or cell == "Path":
            continue
        spans = re.findall(r"`([^`]+)`", cell)
        rows.append(", ".join(spans) if spans else cell)
    return rows


# Written out rather than derived from the thing under test (the grants precedent):
# every row of the frozen table names the entry that enforces it. A row that names
# none promises protection the set does not carry.
ROW_COVERAGE: dict[str, tuple[str, ...]] = {
    "harness/": ("harness/",),
    "src/provenance/": ("src/provenance/",),
    "src/thresholds/": ("src/thresholds/",),
    "tests/heldout/": ("tests/heldout/",),
    "migrations/harness/, migrations/roles/": ("migrations/harness/", "migrations/roles/"),
    "scripts/": ("scripts/",),
    "policy/": ("policy/",),
    ".github/": (".github/",),
    "docs/tier0/": ("docs/tier0/",),
    "pyproject.toml, uv.lock": ("pyproject.toml", "uv.lock"),
    # Conceptual rows: the thing, not a path. Each resolves to the prefix that covers it.
    "fingerprint tracker": ("migrations/harness/",),
    "oracle environment and its pin": ("harness/",),
    "oracle denylist configuration": ("policy/",),
}


# ----------------------------------------------------------------- the load, fail closed


def test_the_committed_set_loads() -> None:
    protected = load_protected_set()
    assert protected.version >= 1
    assert protected.prefixes and protected.files
    assert all(e.path.endswith("/") for e in protected.prefixes)


def test_a_missing_file_is_refused() -> None:
    with pytest.raises(ProtectedSetError):
        load_protected_set(REPO / "policy" / "no-such-set.json")


def test_an_empty_set_is_refused(tmp_path: Path) -> None:
    """D57. A set that enumerates nothing protects nothing, and passes everything."""
    empty = tmp_path / "empty.json"
    empty.write_text(
        json.dumps({"version": 1, "prefixes": [], "files": []}), encoding="utf-8"
    )
    with pytest.raises(ProtectedSetError):
        load_protected_set(empty)


@pytest.mark.parametrize(
    "body",
    [
        {"version": 1, "prefixes": [{"path": "harness", "contains": "x"}]},  # no slash
        {"version": 1, "prefixes": [{"path": "../harness/", "contains": "x"}]},  # traversal
        {"version": 1, "prefixes": [{"path": "harness/"}]},  # no rationale
        {"version": 1, "prefixes": [{"path": "harness/", "contains": 3}]},  # not text
        {"version": 1, "prefixes": [{"path": "a/", "contains": "x"}, {"path": "a/", "contains": "y"}]},  # twice
        {"version": 1, "files": [{"path": "a/", "contains": "x"}]},  # a directory, not a file
        {"version": "1", "prefixes": [{"path": "a/", "contains": "x"}]},  # a string version
        {"prefixes": [{"path": "a/", "contains": "x"}]},  # no version
    ],
)
def test_a_malformed_set_is_refused(tmp_path: Path, body: dict[str, object]) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(body), encoding="utf-8")
    with pytest.raises(ProtectedSetError):
        load_protected_set(bad)


# --------------------------------------------------------- set equality, both directions


def test_every_document_row_is_accounted_for() -> None:
    """A row in the frozen table with no entry in the set protects nothing — the failure
    direction the document's own `falsifies_if` names."""
    rows = _doc_row_labels()
    assert len(rows) >= 10, "a table parse that found almost nothing proves nothing"
    unaccounted = [row for row in rows if row not in ROW_COVERAGE]
    assert not unaccounted, "table rows with no enforcement entry: " + ", ".join(unaccounted)


def test_every_covered_entry_exists_in_the_set() -> None:
    protected = load_protected_set()
    known = protected.all_paths
    missing = [p for paths in ROW_COVERAGE.values() for p in paths if p not in known]
    assert not missing, "coverage names entries absent from the set: " + ", ".join(missing)


def test_every_set_entry_has_a_document_row() -> None:
    """The other direction: an entry in the set with no row in the table protects
    something nobody was told about."""
    protected = load_protected_set()
    covered = {p for paths in ROW_COVERAGE.values() for p in paths}
    unlisted = sorted(protected.all_paths - covered)
    assert not unlisted, "set entries with no table row: " + ", ".join(unlisted)


# ----------------------------------------------------------------------- the behaviour


@pytest.mark.parametrize(
    "path",
    [e.path + "thing.py" for e in load_protected_set().prefixes]
    + [e.path for e in load_protected_set().files],
)
def test_every_protected_path_is_refused(path: str) -> None:
    assert "protected-path" in _rules(_diff_for(path))


def test_the_gate_protects_its_own_policy_file() -> None:
    """CVE-2025-53773, closed: the file that states the gate's rules is itself protected."""
    assert "protected-path" in _rules(_diff_for("policy/protected-paths.json"))


@pytest.mark.parametrize(
    "path",
    [
        "src/domain/x.py",
        "src/metrics/y.py",
        "src/api/z.py",
        "docs/tier5/a.md",
        "tests/properties/b.py",
        "migrations/product/c.py",  # the product schema is factory, deliberately not protected
        "bench/d.py",
        "README.md",
    ],
)
def test_non_protected_paths_are_not_flagged(path: str) -> None:
    """A gate that refused everything would be obeyed by deleting it. The boundary has a
    width, and this is what pins the outside of it."""
    assert "protected-path" not in _rules(_diff_for(path))
