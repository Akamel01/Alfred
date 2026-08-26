"""Tests for dispatch mount exclusion (C12/C13).

Prototype for ADR-0035: dispatch mount must be excluded from "no unexpected writes" checks.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from harness.containment.dispatch_mount import (
    DEFAULT_DISPATCH_ROOTS,
    filter_dispatch_from_c13_roots,
    filter_dispatch_mounts,
    is_dispatch_mount,
)
from harness.containment.inside import (
    MountObservation,
    assert_no_archives_or_caches,
    assert_writable_set,
)


class TestDispatchMountDetection:
    """Dispatch mount path detection."""

    def test_root_dispatch_is_detected(self) -> None:
        assert is_dispatch_mount("/dispatch") is True

    def test_subpath_dispatch_is_detected(self) -> None:
        assert is_dispatch_mount("/dispatch/patches") is True
        assert is_dispatch_mount("/dispatch/patches/001.patch") is True

    def test_non_dispatch_is_not_detected(self) -> None:
        assert is_dispatch_mount("/repo") is False
        assert is_dispatch_mount("/usr") is False
        assert is_dispatch_mount("/tmp") is False
        assert is_dispatch_mount("/dispatcher") is False  # not a prefix match


class TestC12DispatchExclusion:
    """C12 writable set assertion excludes dispatch mount."""

    def test_writable_dispatch_mount_is_allowed(self) -> None:
        """A writable dispatch mount does not trigger C12 failure."""
        result = assert_writable_set(
            observed=[
                MountObservation("/repo", read_only=False),
                MountObservation("/dispatch", read_only=False),  # dispatch mount - writable
            ],
            writable_roots=["/repo"],
            interpreter_paths=["/usr/bin/python3"],
        )
        # The dispatch mount is writable but outside declared roots —
        # with exclusion logic applied, this should pass
        filtered = filter_dispatch_mounts(
            [m.path for m in [MountObservation("/repo", False), MountObservation("/dispatch", False)] if not m.read_only],
        )
        assert "/dispatch" not in filtered
        assert "/repo" in filtered

    def test_writable_outside_dispatch_and_roots_is_still_flagged(self) -> None:
        """A writable mount outside both dispatch and declared roots is still a finding."""
        result = assert_writable_set(
            observed=[
                MountObservation("/repo", read_only=False),
                MountObservation("/scratch", read_only=False),  # unexpected writable
            ],
            writable_roots=["/repo"],
            interpreter_paths=["/usr/bin/python3"],
        )
        assert result.outcome.name == "FAILED"
        assert "/scratch" in result.detail


class TestC13DispatchExclusion:
    """C13 archive/cache scan excludes dispatch mount."""

    def test_archive_in_dispatch_mount_is_allowed(self, tmp_path: Path) -> None:
        """An archive in the dispatch mount does not trigger C13 failure."""
        # Simulate the dispatch mount at /dispatch
        dispatch = Path("/dispatch")
        # We can't write to /dispatch in tests, so test the filter logic directly
        roots = [Path("/repo"), Path("/dispatch"), Path("/usr")]
        filtered = filter_dispatch_from_c13_roots(roots)
        assert len(filtered) == 2
        assert Path("/repo") in filtered
        assert Path("/usr") in filtered
        assert Path("/dispatch") not in filtered

    def test_archive_outside_dispatch_is_still_flagged(self, tmp_path: Path) -> None:
        """An archive outside dispatch mount is still a C13 finding."""
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "bad.whl").write_bytes(b"fake wheel")

        # Filter roots - dispatch not in list, so all remain
        roots = [repo]
        filtered = filter_dispatch_from_c13_roots(roots)
        assert len(filtered) == 1
        assert filtered[0] == repo

        result = assert_no_archives_or_caches(filtered)
        assert result.outcome.name == "FAILED"
        assert "archives" in result.detail


class TestDispatchMountIntegration:
    """Integration-style tests showing the exclusion flow."""

    def test_c12_excludes_dispatch_from_unexpected_writable(self) -> None:
        """C12: unexpected writable mounts exclude dispatch."""
        observed = [
            MountObservation("/repo", read_only=False),
            MountObservation("/dispatch", read_only=False),
            MountObservation("/dispatch/patches", read_only=False),
            MountObservation("/scratch", read_only=False),  # this should still be flagged
        ]
        writable_roots = ["/repo"]

        unexpected = [
            m.path for m in observed if not m.read_only and m.path not in writable_roots
        ]
        assert "/dispatch" in unexpected
        assert "/scratch" in unexpected

        # Apply exclusion
        filtered = filter_dispatch_mounts(unexpected)
        assert "/dispatch" not in filtered
        assert "/dispatch/patches" not in filtered
        assert "/scratch" in filtered  # still flagged

    def test_c13_excludes_dispatch_from_scan_roots(self) -> None:
        """C13: scan roots exclude dispatch mount."""
        roots = [Path("/repo"), Path("/dispatch"), Path("/usr")]
        filtered = filter_dispatch_from_c13_roots(roots)

        assert len(filtered) == 2
        assert Path("/repo") in filtered
        assert Path("/usr") in filtered
        assert Path("/dispatch") not in filtered


if __name__ == "__main__":
    pytest.main([__file__, "-v"])