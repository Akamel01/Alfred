"""The import-hook lists in `criterion.materialize` and `patch.validate` answer to each other.

One attack class crosses two channels: a `conftest.py` or `.pth` smuggled through the
candidate tree is refused at materialization time (A1 — the criterion environment is
built from trusted provenance, never copied from the tree under test), and the same file
arriving inside a patch is refused at review time (`harness/patch/validate.py`, the
privileged-side gate per `docs/tier2/execution-order.md` § the patch gate). Neither list
derives from the other; both are restated copies of the same refusal, so the first
divergence must be loud at commit time rather than discovered when an environment admits
what the patch gate rejects, or the reverse.

`materialize.py`'s own docstring names its list as defence in depth over the allowlist,
"not the boundary" — binding the two copies does not change that; it stops the depth from
being shallower on one side than the other.

If you add a member: decide whether it belongs on both channels, change both modules, and
this test passes again.
"""

from __future__ import annotations

from harness.criterion.materialize import (
    IMPORT_HOOK_NAMES as MATERIALIZE_NAMES,
    IMPORT_HOOK_SUFFIXES as MATERIALIZE_SUFFIXES,
)
from harness.patch.validate import (
    IMPORT_HOOK_NAMES as VALIDATE_NAMES,
    IMPORT_HOOK_SUFFIXES as VALIDATE_SUFFIXES,
)


def test_the_name_sets_are_identical() -> None:
    assert MATERIALIZE_NAMES == VALIDATE_NAMES


def test_the_suffix_tuples_are_identical() -> None:
    assert tuple(MATERIALIZE_SUFFIXES) == tuple(VALIDATE_SUFFIXES)


def test_both_sides_actually_carry_the_canonical_members() -> None:
    """Vacuity guard (D57): two empty copies agree perfectly and refuse nothing.

    Equality alone would pass on two sets deleted together. The canonical members are
    pinned here because they are the two spellings BenchJack's ~7-line `conftest.py`
    attack made load-bearing (`materialize.py`'s module docstring).
    """
    assert "conftest.py" in MATERIALIZE_NAMES
    assert "conftest.py" in VALIDATE_NAMES
    assert ".pth" in MATERIALIZE_SUFFIXES
    assert ".pth" in VALIDATE_SUFFIXES
