"""Every refusal in the patch gate, planted and caught.

The positive control comes first in importance: without a patch that must pass, every
test below is satisfied by a validator that refuses everything, and a gate nobody can get
through is a gate that gets removed.
"""

from __future__ import annotations

import pytest

from harness.patch.validate import (
    INSTRUCTION_FILE_NAMES,
    PatchRefused,
    load_protected_set,
    require_clean,
    validate_patch,
)

CLEAN = """diff --git a/src/metrics/thw.py b/src/metrics/thw.py
--- a/src/metrics/thw.py
+++ b/src/metrics/thw.py
@@ -1,3 +1,4 @@
 import math
+
+VALUE = 2.4
"""


def _rules(diff: str) -> set[str]:
    return {f.rule for f in validate_patch(diff).findings}


def _diff_for(path: str, added: str = "x = 1") -> str:
    return (
        f"diff --git a/{path} b/{path}\n"
        f"--- a/{path}\n+++ b/{path}\n@@ -0,0 +1 @@\n+{added}\n"
    )


# ---------------------------------------------------------------- positive control


def test_an_ordinary_patch_passes() -> None:
    report = require_clean(CLEAN)
    assert report.paths == ["src/metrics/thw.py"]
    assert report.added_lines_scanned == 2


def test_the_scan_reads_added_lines_only() -> None:
    """Context lines are already in the tree. Flagging them would report the same finding
    on every later patch touching the same file, until nobody reads the output."""
    diff = (
        "diff --git a/src/a.py b/src/a.py\n--- a/src/a.py\n+++ b/src/a.py\n"
        "@@ -1,2 +1,3 @@\n ​existing\n+added\n"
    )
    assert _rules(diff) == set()


def test_the_file_header_is_not_read_as_an_added_line() -> None:
    """`+++ b/path` begins with a plus. Counting it would scan the path as content."""
    assert validate_patch(CLEAN).added_lines_scanned == 2


# ------------------------------------------------------------------ protected paths


# Loaded once, at collection: a test file that cannot state its own premise fails loudly
# rather than parametrising over an empty set. The load semantics themselves are
# `test_protected_set.py`'s job, against explicit paths.
_PROTECTED_PREFIXES = [e.path for e in load_protected_set().prefixes]


@pytest.mark.parametrize("prefix", _PROTECTED_PREFIXES)
def test_every_protected_prefix_is_refused(prefix: str) -> None:
    assert "protected-path" in _rules(_diff_for(f"{prefix}thing.py"))


def test_a_quoted_path_cannot_smuggle_a_protected_prefix() -> None:
    """git quotes unusual bytes as a C string, so `harness/` can be written escaped.

    A check running on the raw token does not prefix-match and lets it through. Decoding
    before deciding is the whole reason `_unquote` exists.
    """
    diff = 'diff --git "a/harness/\\150arm.py" "b/harness/\\150arm.py"\n@@ -0,0 +1 @@\n+x = 1\n'
    assert "protected-path" in _rules(diff)


def test_traversal_and_absolute_paths_are_refused() -> None:
    assert "traversal" in _rules(_diff_for("src/../../etc/passwd"))
    assert "absolute-path" in _rules(_diff_for("/etc/passwd"))


def test_a_symlink_is_refused_on_its_mode() -> None:
    """A symlink names one file and delivers another."""
    diff = (
        "diff --git a/src/link.py b/src/link.py\n"
        "new file mode 120000\n@@ -0,0 +1 @@\n+/etc/passwd\n"
    )
    assert "symlink" in _rules(diff)


# ------------------------------------------------- import hooks and instruction files


@pytest.mark.parametrize("name", ["conftest.py", "sitecustomize.py", "hook.pth"])
def test_import_hooks_are_refused(name: str) -> None:
    """BenchJack forced 100% resolve on all 500 SWE-bench Verified instances with a
    seven-line conftest.py, touching no test file."""
    assert "import-hook" in _rules(_diff_for(f"src/{name}"))


@pytest.mark.parametrize("name", sorted(INSTRUCTION_FILE_NAMES))
def test_instruction_files_are_refused(name: str) -> None:
    assert "instruction-file" in _rules(_diff_for(name))


# ----------------------------------------------------------------- A10, invisibles


def test_zero_width_characters_are_refused() -> None:
    """GitHub flags bidi and does not flag zero-width, so the rendered diff shows a
    reviewer nothing at all."""
    assert "invisible-character" in _rules(_diff_for("src/a.py", "x = 1  # note​"))


def test_bidi_override_characters_are_refused() -> None:
    assert "invisible-character" in _rules(_diff_for("src/a.py", "x = 1  # ‮"))


def test_control_characters_are_refused_but_tabs_are_not() -> None:
    assert "control-character" in _rules(_diff_for("src/a.py", "x = 1\x07"))
    assert _rules(_diff_for("src/a.py", "x\t= 1")) == set()


def test_ordinary_non_ascii_text_is_not_refused() -> None:
    """A rule that rejected accented characters would be bypassed rather than obeyed."""
    assert _rules(_diff_for("src/a.py", "# café, naïve, 中文")) == set()


# -------------------------------------------------------------------- the vacuity guard


def test_a_patch_that_parsed_to_nothing_is_refused() -> None:
    """An empty report and a clean report are the same object. The difference between
    'nothing was wrong' and 'nothing was read' is the difference between a gate and a
    formality."""
    with pytest.raises(PatchRefused, match="read nothing"):
        require_clean("")


def test_require_clean_raises_on_findings_and_names_them() -> None:
    with pytest.raises(PatchRefused, match="protected-path"):
        require_clean(_diff_for("harness/criterion/runner.py"))


def test_all_findings_are_collected_rather_than_the_first() -> None:
    """A reviewer handed one refusal at a time re-runs the gate N times and learns the
    rules by exhaustion, which is how a boundary starts being treated as an obstacle."""
    diff = _diff_for("harness/conftest.py", "x = 1  # ​")
    assert {"protected-path", "import-hook", "invisible-character"} <= _rules(diff)
