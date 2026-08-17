"""A1, asserted as an architectural claim rather than as a list of blocked filenames.

**How this suite would be shown vacuous** (D57). Every refusal test here would pass
against a `materialize` that refused everything, so each is paired with a positive
control: the same shape, declared correctly, must cross. The pairing is the suite, not
a convention — `test_declared_file_crosses` is what stops the refusals from being
satisfied by a function that raises unconditionally.

The load-bearing test is `test_undeclared_conftest_does_not_cross`. It does not assert
that `conftest.py` was blocked; it asserts that a file nobody declared is simply absent,
which is the same result an unnamed `.pth`, an unnamed binary, or a file class nobody
has thought of yet would get. A test asserting the *ban* would pass against enumeration
and would go green on the day the enumeration stopped being complete.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from harness.criterion.materialize import (
    MaterializationError,
    MaterializationSpec,
    materialize,
)


def _write(root: Path, relative: str, content: str = "x = 1\n") -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture
def trees(tmp_path: Path) -> tuple[Path, Path, Path]:
    candidate = tmp_path / "candidate"
    trusted = tmp_path / "trusted"
    destination = tmp_path / "env"
    candidate.mkdir()
    trusted.mkdir()
    _write(candidate, "src/metrics/ttc.py", "def ttc() -> float:\n    return 2.4\n")
    _write(trusted, "criteria/test_ttc.py", "def test_ttc() -> None:\n    assert True\n")
    return candidate, trusted, destination


# ----------------------------------------------------------------- positive controls


def test_declared_file_crosses(trees: tuple[Path, Path, Path]) -> None:
    candidate, trusted, destination = trees
    result = materialize(
        candidate_root=candidate,
        trusted_root=trusted,
        spec=MaterializationSpec(
            candidate_paths=("src/metrics/ttc.py",), trusted_paths=("criteria/test_ttc.py",)
        ),
        destination=destination,
    )
    assert (destination / "src/metrics/ttc.py").is_file()
    assert (destination / "criteria/test_ttc.py").is_file()
    assert set(result.manifest) == {"src/metrics/ttc.py", "criteria/test_ttc.py"}


def test_directory_declaration_expands(trees: tuple[Path, Path, Path]) -> None:
    candidate, trusted, destination = trees
    _write(candidate, "src/metrics/pet.py")
    result = materialize(
        candidate_root=candidate,
        trusted_root=trusted,
        spec=MaterializationSpec(candidate_paths=("src/metrics",), trusted_paths=()),
        destination=destination,
    )
    assert set(result.manifest) == {"src/metrics/ttc.py", "src/metrics/pet.py"}


def test_manifest_digest_is_recomputable(trees: tuple[Path, Path, Path]) -> None:
    """The manifest is evidence only if a third party can check it."""
    import hashlib

    candidate, trusted, destination = trees
    result = materialize(
        candidate_root=candidate,
        trusted_root=trusted,
        spec=MaterializationSpec(candidate_paths=("src/metrics/ttc.py",), trusted_paths=()),
        destination=destination,
    )
    on_disk = (destination / "src/metrics/ttc.py").read_bytes()
    assert result.manifest["src/metrics/ttc.py"] == hashlib.sha256(on_disk).hexdigest()


# ------------------------------------------------------------------- the A1 claim


def test_undeclared_conftest_does_not_cross(trees: tuple[Path, Path, Path]) -> None:
    """The BenchJack shape, closed by construction rather than by name.

    This asserts *absence*, never a ban. An undeclared `conftest.py` gets exactly the
    treatment an undeclared `.pth`, an undeclared binary, or a file class nobody has
    enumerated gets: it is not in the declaration, so it is not in the environment.
    """
    candidate, trusted, destination = trees
    _write(
        candidate,
        "conftest.py",
        "def pytest_collection_modifyitems(items):\n    for i in items:\n        i.obj = lambda: None\n",
    )
    result = materialize(
        candidate_root=candidate,
        trusted_root=trusted,
        spec=MaterializationSpec(
            candidate_paths=("src/metrics/ttc.py",), trusted_paths=("criteria/test_ttc.py",)
        ),
        destination=destination,
    )
    assert not (destination / "conftest.py").exists()
    assert "conftest.py" not in result.manifest


def test_undeclared_sibling_does_not_cross(trees: tuple[Path, Path, Path]) -> None:
    """The same claim without a suspicious filename, which is the honest version.

    If only the `conftest.py` case were tested, a maintainer could satisfy the suite with
    a filename ban and the suite would not notice.
    """
    candidate, trusted, destination = trees
    _write(candidate, "src/metrics/secret_helper.py")
    result = materialize(
        candidate_root=candidate,
        trusted_root=trusted,
        spec=MaterializationSpec(candidate_paths=("src/metrics/ttc.py",), trusted_paths=()),
        destination=destination,
    )
    assert not (destination / "src/metrics/secret_helper.py").exists()
    assert list(result.manifest) == ["src/metrics/ttc.py"]


# --------------------------------------------------------------------- refusals


def test_candidate_import_hook_inside_a_declaration_is_refused(
    trees: tuple[Path, Path, Path],
) -> None:
    """The defence-in-depth layer, tested as such.

    A coarse declaration would otherwise admit an import hook the allowlist never meant
    to name. This is enumeration and is not the boundary; the boundary is the test above.
    """
    candidate, trusted, destination = trees
    _write(candidate, "src/metrics/conftest.py")
    with pytest.raises(MaterializationError, match="import hook"):
        materialize(
            candidate_root=candidate,
            trusted_root=trusted,
            spec=MaterializationSpec(candidate_paths=("src/metrics",), trusted_paths=()),
            destination=destination,
        )


def test_symlinked_leaf_is_refused(trees: tuple[Path, Path, Path], tmp_path: Path) -> None:
    candidate, trusted, destination = trees
    outside = tmp_path / "outside.py"
    outside.write_text("SECRET = 1\n", encoding="utf-8")
    (candidate / "src/metrics/linked.py").symlink_to(outside)
    with pytest.raises(MaterializationError, match="symlink"):
        materialize(
            candidate_root=candidate,
            trusted_root=trusted,
            spec=MaterializationSpec(candidate_paths=("src/metrics/linked.py",), trusted_paths=()),
            destination=destination,
        )


def test_symlinked_parent_is_refused(trees: tuple[Path, Path, Path], tmp_path: Path) -> None:
    """The component check, not only the leaf check.

    `a/b/c.py` where `a/b` is a symlink is exactly as much of an escape as a symlinked
    `c.py`, and the leaf-only check is the one that gets written.
    """
    candidate, trusted, destination = trees
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    (outside / "c.py").write_text("SECRET = 1\n", encoding="utf-8")
    (candidate / "src/linked").symlink_to(outside, target_is_directory=True)
    with pytest.raises(MaterializationError, match="symlink"):
        materialize(
            candidate_root=candidate,
            trusted_root=trusted,
            spec=MaterializationSpec(candidate_paths=("src/linked/c.py",), trusted_paths=()),
            destination=destination,
        )


def test_escape_is_refused(trees: tuple[Path, Path, Path]) -> None:
    candidate, trusted, destination = trees
    with pytest.raises(MaterializationError):
        materialize(
            candidate_root=candidate,
            trusted_root=trusted,
            spec=MaterializationSpec(candidate_paths=("../trusted/criteria/test_ttc.py",), trusted_paths=()),
            destination=destination,
        )


def test_absolute_declaration_is_refused(trees: tuple[Path, Path, Path]) -> None:
    candidate, trusted, destination = trees
    with pytest.raises(MaterializationError, match="absolute"):
        materialize(
            candidate_root=candidate,
            trusted_root=trusted,
            spec=MaterializationSpec(candidate_paths=("/etc/hosts",), trusted_paths=()),
            destination=destination,
        )


def test_missing_declaration_is_refused(trees: tuple[Path, Path, Path]) -> None:
    """Fail closed on a typo.

    A declaration naming a path that is not there would otherwise materialize nothing,
    and the criterion would fail for a reason unrelated to the work — or pass vacuously.
    """
    candidate, trusted, destination = trees
    with pytest.raises(MaterializationError, match="does not exist"):
        materialize(
            candidate_root=candidate,
            trusted_root=trusted,
            spec=MaterializationSpec(candidate_paths=("src/metrics/typo.py",), trusted_paths=()),
            destination=destination,
        )


def test_collision_is_refused(trees: tuple[Path, Path, Path]) -> None:
    """A path supplied by both sides has no defensible winner.

    Trusted-wins would let a candidate name a criterion file and have the overwrite read
    as success; candidate-wins is the attack. Refusing is the only answer that reports
    what happened.
    """
    candidate, trusted, destination = trees
    _write(candidate, "criteria/test_ttc.py", "def test_ttc() -> None:\n    assert True\n")
    with pytest.raises(MaterializationError, match="declared by both"):
        materialize(
            candidate_root=candidate,
            trusted_root=trusted,
            spec=MaterializationSpec(
                candidate_paths=("criteria/test_ttc.py",), trusted_paths=("criteria/test_ttc.py",)
            ),
            destination=destination,
        )


def test_existing_destination_is_refused(trees: tuple[Path, Path, Path]) -> None:
    """One environment per run. A reused directory lets a run inherit the last one."""
    candidate, trusted, destination = trees
    destination.mkdir()
    with pytest.raises(MaterializationError, match="already exists"):
        materialize(
            candidate_root=candidate,
            trusted_root=trusted,
            spec=MaterializationSpec(candidate_paths=("src/metrics/ttc.py",), trusted_paths=()),
            destination=destination,
        )


def test_non_regular_file_is_refused(trees: tuple[Path, Path, Path]) -> None:
    import os

    candidate, trusted, destination = trees
    os.mkfifo(candidate / "src/metrics/pipe")
    with pytest.raises(MaterializationError, match="non-regular"):
        materialize(
            candidate_root=candidate,
            trusted_root=trusted,
            spec=MaterializationSpec(candidate_paths=("src/metrics",), trusted_paths=()),
            destination=destination,
        )


def test_executable_bit_does_not_cross(trees: tuple[Path, Path, Path]) -> None:
    """Permissions are not part of what a declaration declares."""
    candidate, trusted, destination = trees
    (candidate / "src/metrics/ttc.py").chmod(0o755)
    materialize(
        candidate_root=candidate,
        trusted_root=trusted,
        spec=MaterializationSpec(candidate_paths=("src/metrics/ttc.py",), trusted_paths=()),
        destination=destination,
    )
    assert not (destination / "src/metrics/ttc.py").stat().st_mode & 0o111
