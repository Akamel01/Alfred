"""Build the criterion environment from an allowlist, never from the candidate tree.

**A1, and it is an architectural claim rather than a hardening measure.** BenchJack
forced a 100% resolve rate on all 500 SWE-bench Verified instances with a ~7-line
`conftest.py` and without touching a single test file. Enumerating that attack — ban
`conftest.py`, ban `.pth`, ban `sitecustomize` — loses to the next member of a class
nobody has finished listing. The structural answer is to stop copying *from* the
candidate and start building *to* a declaration: the destination tree is assembled from
a list of paths written before the agent ran, and a file the declaration does not name
does not exist in the environment the criterion sees.

The direction is the whole point. **Copy-then-delete is not this.** It materializes the
attack and then tries to remove it, which depends on the remover's list being complete
and leaves a window in which the file is present. Allowlist-then-copy has no window and
no list of bad things.

**Three refusals, each closing a way around the allowlist:**

*Symlinks.* A declared path that is a symlink reads whatever it points at, which may sit
entirely outside the candidate root. Refused rather than resolved — resolving would make
the allowlist name one file and deliver another.

*Escapes.* Every resolved path is required to remain under its root. `..` in a
declaration, or a directory entry that resolves outward, is refused.

*Absences.* A declared path that does not exist is an error, not an empty copy. A typo
in a declaration would otherwise materialize nothing and the criterion would fail for a
reason that has nothing to do with the work — or, worse, pass vacuously.

**One layer that is enumeration, and is labelled as such.** Import-hook filenames
(`conftest.py`, `sitecustomize.py`, `usercustomize.py`, `*.pth`) are refused from the
candidate side even when a declaration would admit them. This is *not* the boundary and
must never be described as one: the boundary is the allowlist. It exists because the
allowlist's strength is its granularity — a task declaring `src/metrics/ttc.py` admits no
such file, while one declaring a whole directory might — and this catches the case where
a declaration is coarser than its author realized. It is defence in depth over a
structural control, which is the only position enumeration is ever safe in.
"""

from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Final

# Never candidate-supplied. Not the boundary — see the module docstring.
IMPORT_HOOK_NAMES: Final = frozenset({"conftest.py", "sitecustomize.py", "usercustomize.py"})
IMPORT_HOOK_SUFFIXES: Final = (".pth",)


class MaterializationError(RuntimeError):
    """The environment could not be built as declared. Always fail closed."""


@dataclass(frozen=True)
class MaterializationSpec:
    """What may cross into the criterion environment, declared before the agent ran.

    `candidate_paths` come from the solution under test. `trusted_paths` come from the
    harness's own tree — the criterion, its fixtures, its configuration — and are copied
    second so that a collision is visible rather than resolved.
    """

    candidate_paths: tuple[str, ...]
    trusted_paths: tuple[str, ...]


@dataclass(frozen=True)
class Materialization:
    """What actually crossed, and its digest.

    The manifest is the evidence. "The environment was built from the declaration" is a
    claim; a path-to-digest map that an auditor can recompute from the destination tree
    is a fact, and it is what a replay pins.
    """

    root: Path
    manifest: dict[str, str]

    @property
    def candidate_file_count(self) -> int:
        return len(self.manifest)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _is_import_hook(name: str) -> bool:
    return name in IMPORT_HOOK_NAMES or name.endswith(IMPORT_HOOK_SUFFIXES)


def _checked_child(root: Path, relative: str, *, origin: str) -> Path:
    """Resolve `relative` under `root`, refusing anything that leaves or links away.

    `is_symlink()` is checked on every component rather than only the leaf: a declared
    path `a/b/c.py` where `a/b` is a symlink is exactly as much of an escape as a
    symlinked `c.py`, and only the leaf check is the one people write.
    """
    if Path(relative).is_absolute():
        raise MaterializationError(f"{origin} path {relative!r} is absolute; declarations are relative")

    candidate = root / relative
    walked = root
    for part in Path(relative).parts:
        walked = walked / part
        if walked.is_symlink():
            raise MaterializationError(
                f"{origin} path {relative!r} traverses a symlink at {walked.relative_to(root)}; "
                f"a symlink names one file and delivers another"
            )

    try:
        resolved = candidate.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise MaterializationError(f"{origin} path {relative!r} does not exist") from exc

    if not resolved.is_relative_to(root.resolve(strict=True)):
        raise MaterializationError(f"{origin} path {relative!r} resolves outside its root")
    return candidate


def _files_under(root: Path, declared: Path, *, origin: str) -> list[Path]:
    """Every regular file the declaration admits, symlinks and specials refused.

    A directory declaration is expanded here rather than passed to `shutil.copytree`,
    because copytree follows or preserves symlinks depending on a flag and does neither
    check. The expansion is what makes every entry pass the same refusals as a
    hand-declared file.
    """
    if declared.is_file():
        return [declared]
    if not declared.is_dir():
        raise MaterializationError(
            f"{origin} path {declared.relative_to(root)!s} is neither a regular file nor a directory"
        )

    found: list[Path] = []
    for entry in sorted(declared.rglob("*")):
        if entry.is_symlink():
            raise MaterializationError(
                f"{origin} tree contains a symlink at {entry.relative_to(root)!s}"
            )
        if entry.is_dir():
            continue
        if not entry.is_file():
            raise MaterializationError(
                f"{origin} tree contains a non-regular file at {entry.relative_to(root)!s}"
            )
        found.append(entry)
    return found


def materialize(
    *,
    candidate_root: Path,
    trusted_root: Path,
    spec: MaterializationSpec,
    destination: Path,
) -> Materialization:
    """Assemble the criterion environment. Nothing undeclared crosses.

    `destination` must not already exist. Reusing a directory would let one run inherit
    the previous run's tree, and a criterion that passes because a file survived from an
    earlier attempt is the same defect as one that passes because the agent wrote it.
    """
    if destination.exists():
        raise MaterializationError(
            f"destination {destination} already exists; the environment is built once per run"
        )
    destination.mkdir(parents=True)

    manifest: dict[str, str] = {}
    written_by: dict[str, str] = {}

    for origin, root, declared_paths in (
        ("candidate", candidate_root, spec.candidate_paths),
        ("trusted", trusted_root, spec.trusted_paths),
    ):
        for relative in declared_paths:
            declared = _checked_child(root, relative, origin=origin)
            for source in _files_under(root, declared, origin=origin):
                key = str(source.relative_to(root))

                if origin == "candidate" and _is_import_hook(source.name):
                    raise MaterializationError(
                        f"candidate supplied an import hook at {key}: collection and import "
                        f"configuration comes from trusted provenance, never from the tree "
                        f"under test"
                    )

                if key in written_by:
                    # Never silently resolved in either direction. Trusted-wins would let
                    # a candidate name a criterion file and have the overwrite look like
                    # success; candidate-wins would be the attack itself.
                    raise MaterializationError(
                        f"{key} is declared by both {written_by[key]} and {origin}; a path "
                        f"supplied twice has no defensible winner"
                    )

                target = destination / key
                target.parent.mkdir(parents=True, exist_ok=True)
                # Bytes only. `copy2` would carry the mode bit that makes a data file
                # executable, and permissions are not part of what a declaration declares.
                shutil.copyfile(source, target)
                manifest[key] = _sha256(target)
                written_by[key] = origin

    return Materialization(root=destination, manifest=manifest)
