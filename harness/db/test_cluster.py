"""Tests of the fixture itself, before anything is asserted through it.

A cluster fixture is measurement apparatus, and this project's record on apparatus is
four for four: every headline number has been wrong on first read, each time because
the instrument was trusted before it was checked. So the fixture gets checked first.

These tests verify that the cluster is what it claims to be — schemas exist, roles
exist, ownership is separated, it is ephemeral and isolated. They do **not** verify the
grant matrix; that is `assert_grants.py`, and conflating the two would let a fixture
bug read as a grant result.
"""

from __future__ import annotations

import subprocess

import pytest

from harness.db.cluster import (
    DBNAME,
    PINNED_POSTGRES_IMAGE,
    ROLES,
    SUPERUSER,
    ClusterError,
    ThrowawayCluster,
    _assert_throwaway,
)

pytestmark = pytest.mark.db


def _query(cluster: ThrowawayCluster, sql: str) -> list[str]:
    """One column, one row per line, through the container's own psql."""
    result = subprocess.run(  # noqa: S603
        [
            "docker", "exec", "-i",
            "-e", f"PGPASSWORD={cluster.superuser_password}",
            cluster.container,
            "psql", "-v", "ON_ERROR_STOP=1", "-U", SUPERUSER, "-d", DBNAME,
            "-tAc", sql,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.strip().splitlines() if line]


def test_the_five_schemas_exist(cluster: ThrowawayCluster) -> None:
    found = set(
        _query(
            cluster,
            "SELECT nspname FROM pg_namespace "
            "WHERE nspname IN ('product','control','evidence','heldout','migration_meta')",
        )
    )
    assert found == {"product", "control", "evidence", "heldout", "migration_meta"}


def _role_list_sql() -> str:
    """The matrix roles as a SQL literal list.

    Explicit rather than `LIKE 'alfred\\_%'`: the pattern also matches the fixture's own
    superuser, and a pattern that happens to catch the right set today is not a check on
    the set the matrix names. The first version of the attribute test failed for exactly
    this reason — it flagged `alfred_test_super`, which is legitimately a superuser and
    is not a matrix role.
    """
    return ", ".join(f"'{role}'" for role in ROLES)


def test_every_role_exists_and_can_log_in(cluster: ThrowawayCluster) -> None:
    found = set(_query(cluster, f"SELECT rolname FROM pg_roles WHERE rolname IN ({_role_list_sql()})"))
    assert set(ROLES) <= found

    # alfred_agent must be able to CONNECT. The negative tests need it to reach the
    # server and be refused at the schema; a role that cannot connect proves nothing
    # about grants, and "connection refused" passing as "access denied" is the shape in
    # which a security test most commonly lies.
    canlogin = set(
        _query(cluster, f"SELECT rolname FROM pg_roles WHERE rolcanlogin AND rolname IN ({_role_list_sql()})")
    )
    assert set(ROLES) <= canlogin


def test_no_role_has_a_dangerous_attribute(cluster: ThrowawayCluster) -> None:
    """N9. BYPASSRLS is the one that reads as harmless."""
    dangerous = _query(
        cluster,
        f"SELECT rolname FROM pg_roles WHERE rolname IN ({_role_list_sql()}) AND ("
        "rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls)",
    )
    assert dangerous == [], f"roles hold dangerous attributes: {dangerous}"


def test_ownership_is_separated_from_use(cluster: ThrowawayCluster) -> None:
    """N6, and it is the property the append-only claim actually rests on.

    An owner can ALTER, UPDATE and DROP regardless of grants. If `alfred_harness` owned
    `evidence`, every no-UPDATE row in the grant matrix would be decorative.
    """
    owners = dict(
        line.split("|", 1)
        for line in _query(
            cluster,
            "SELECT nspname || '|' || pg_get_userbyid(nspowner) FROM pg_namespace "
            "WHERE nspname IN ('product','control','evidence','heldout','migration_meta')",
        )
    )
    assert owners["product"] == "alfred_migrator_product"
    assert owners["control"] == "alfred_migrator_control"
    assert owners["evidence"] == "alfred_migrator_evidence"
    assert owners["heldout"] == "alfred_migrator_heldout"
    assert owners["migration_meta"] == "alfred_bootstrap"

    running_services = {"alfred_harness", "alfred_criterion", "alfred_product", "alfred_operator", "alfred_readmodel"}
    assert running_services.isdisjoint(set(owners.values()))


def test_public_holds_nothing(cluster: ThrowawayCluster) -> None:
    """N7 — the row most likely to be true on any cluster nobody has checked."""
    leaked = _query(
        cluster,
        "SELECT nspname FROM pg_namespace "
        "WHERE nspname IN ('product','control','evidence','heldout','migration_meta','public') "
        "AND has_schema_privilege('public', nspname, 'USAGE')",
    )
    assert leaked == [], f"PUBLIC holds USAGE on: {leaked}"


def test_the_four_version_tables_live_in_migration_meta(cluster: ThrowawayCluster) -> None:
    """Alembic UPDATEs its version table; `evidence` grants UPDATE to nobody."""
    tables = set(_query(cluster, "SELECT tablename FROM pg_tables WHERE schemaname = 'migration_meta'"))
    assert tables == {
        "alembic_version_product",
        "alembic_version_control",
        "alembic_version_evidence",
        "alembic_version_heldout",
    }

    stray = _query(
        cluster,
        "SELECT schemaname || '.' || tablename FROM pg_tables "
        "WHERE tablename LIKE 'alembic\\_version%' AND schemaname <> 'migration_meta'",
    )
    assert stray == [], f"version tables outside migration_meta: {stray}"


def test_the_image_is_pinned_by_digest() -> None:
    assert "@sha256:" in PINNED_POSTGRES_IMAGE
    assert ":17" not in PINNED_POSTGRES_IMAGE.split("@")[0], "the resolved image must be a digest, not a tag"


def test_data_is_on_tmpfs_so_no_run_inherits_another(cluster: ThrowawayCluster) -> None:
    result = subprocess.run(  # noqa: S603
        ["docker", "inspect", "--format", "{{json .HostConfig.Tmpfs}}", cluster.container],  # noqa: S607
        capture_output=True,
        text=True,
        check=True,
    )
    assert "/var/lib/postgresql/data" in result.stdout


def test_the_port_is_bound_to_loopback_only(cluster: ThrowawayCluster) -> None:
    result = subprocess.run(  # noqa: S603
        ["docker", "inspect", "--format", "{{json .NetworkSettings.Ports}}", cluster.container],  # noqa: S607
        capture_output=True,
        text=True,
        check=True,
    )
    assert "127.0.0.1" in result.stdout
    assert "0.0.0.0" not in result.stdout, "the test cluster must not be reachable off the host"


def test_the_throwaway_guard_refuses_a_foreign_container() -> None:
    """The guard is what stands between `002_grants.sql` and a real cluster.

    That file opens with REVOKE ALL, so pointing this module at a production database
    would strip its grants before granting the test matrix on top — and the damage
    would look like a successful test run. Tested with no Docker call, because the
    guard must reject on the name before it inspects anything.
    """
    with pytest.raises(ClusterError, match="not an Alfred throwaway cluster"):
        _assert_throwaway("production-postgres", 5432)
