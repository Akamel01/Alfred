"""Dispatch mount exclusion for C12/C13 containment assertions.

The dispatch mount is where the factory emits patches for the container to apply.
It is a writable mount that must be excluded from "no unexpected writes" checks.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

DISPATCH_MOUNT_PREFIX: Final[str] = "/dispatch"
DISPATCH_MOUNT_PATTERN: Final[str] = "/dispatch*"

DEFAULT_DISPATCH_ROOTS: Final[tuple[str, ...]] = ("/dispatch",)


def is_dispatch_mount(path: str) -> bool:
    """Check if a path is under the dispatch mount."""
    candidate = Path(path)
    for root in DEFAULT_DISPATCH_ROOTS:
        if candidate == Path(root) or Path(root) in candidate.parents:
            return True
    return False


def filter_dispatch_mounts(
    writable_paths: list[str],
    *,
    dispatch_roots: Sequence[str] = DEFAULT_DISPATCH_ROOTS,
) -> list[str]:
    """Remove dispatch mount paths from a list of writable paths.

    Used by C12 to exclude the dispatch mount from "unexpected writable" findings.
    """
    roots = tuple(Path(r) for r in dispatch_roots)

    def under_dispatch(path: str) -> bool:
        candidate = Path(path)
        return any(candidate == root or root in candidate.parents for root in roots)

    return [p for p in writable_paths if not under_dispatch(p)]


def filter_dispatch_from_c13_roots(
    roots: Sequence[Path],
    *,
    dispatch_roots: Sequence[str] = DEFAULT_DISPATCH_ROOTS,
) -> list[Path]:
    """Remove dispatch mount paths from C13 scan roots.

    The dispatch mount will contain patch files (archives) written by the factory.
    These are expected and must not trigger C13 failures.
    """
    dispatch_paths = tuple(Path(r) for r in dispatch_roots)
    filtered: list[Path] = []

    for root in roots:
        # Filter out if root IS a dispatch root or is UNDER a dispatch root
        root_abs = root.resolve()
        if any(
            root_abs == dp.resolve() or dp.resolve() in root_abs.parents
            for dp in dispatch_paths
        ):
            continue
        filtered.append(root)

    return filtered


__all__ = [
    "DISPATCH_MOUNT_PREFIX",
    "DISPATCH_MOUNT_PATTERN",
    "DEFAULT_DISPATCH_ROOTS",
    "is_dispatch_mount",
    "filter_dispatch_mounts",
    "filter_dispatch_from_c13_roots",
]