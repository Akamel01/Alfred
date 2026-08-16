"""Pytest fixtures for the throwaway cluster.

Session-scoped: creating a cluster costs a few seconds, and the properties under test
are about a cluster built from `migrations/roles/` and the four Alembic environments,
which is the same cluster for every test in a run.

**Skips, not failures, when Docker is unavailable** — and the skip message says which
of the two reasons applied. A developer without Docker running should not see a red
suite; CI must never skip silently, which is why the CI job sets
`ALFRED_REQUIRE_DB=1` and the fixture then fails instead of skipping. A gate that
skips when its dependency is missing is a gate that reports green on the day it stops
running.
"""

from __future__ import annotations

import os
import subprocess
from collections.abc import Iterator

import pytest

from harness.db.cluster import ClusterError, ThrowawayCluster, throwaway_cluster


def _docker_available() -> tuple[bool, str]:
    try:
        result = subprocess.run(  # noqa: S603
            ["docker", "info", "--format", "{{.ServerVersion}}"],  # noqa: S607
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
    except FileNotFoundError:
        return False, "docker is not installed"
    except subprocess.TimeoutExpired:
        return False, "docker info timed out after 15s"
    if result.returncode != 0:
        return False, f"docker daemon is not running: {result.stderr.strip() or 'no detail'}"
    return True, result.stdout.strip()


@pytest.fixture(scope="session")
def cluster() -> Iterator[ThrowawayCluster]:
    available, detail = _docker_available()
    required = os.environ.get("ALFRED_REQUIRE_DB") == "1"

    if not available:
        if required:
            # CI sets ALFRED_REQUIRE_DB=1. Without this branch the database gates would
            # skip on a runner whose Docker service failed to start, and the run would
            # be green for the one reason that should never produce green.
            pytest.fail(f"ALFRED_REQUIRE_DB=1 but {detail}")
        pytest.skip(f"database tests need Docker: {detail}")

    keep = os.environ.get("ALFRED_KEEP_CLUSTER") == "1"
    try:
        with throwaway_cluster(keep=keep) as live:
            yield live
    except ClusterError as exc:
        # Never a skip. A cluster that could not be built or migrated is a failure of
        # the thing under test — the roles file, the grants file, or a migration — and
        # skipping it would hide exactly the defect this fixture exists to surface.
        pytest.fail(f"throwaway cluster failed: {exc}")
