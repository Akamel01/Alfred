"""Throwaway Postgres cluster: create, migrate, assert against, destroy.

docs/tier1/data-architecture.md § How the matrix is enforced requires the grant suite
to run "against a migrated throwaway cluster in CI, and again at harness startup
against the live one." This module is the throwaway half.

It lives in `harness/` for the A1 reason: the criterion environment is materialized by
the harness from trusted provenance, never assembled by the thing under test. A cluster
fixture that a test could reconfigure would let the test arrange the privileges it is
about to verify.

**Three properties, each with a failure it prevents:**

*Ephemeral.* Data lives on tmpfs and the container is removed on teardown, so a run
cannot inherit state from a previous one. A grant matrix that passes only because a
previous run left a role behind is the exact defect the assertion exists to catch.

*Isolated.* The container binds a random high port on loopback only, and the module
refuses to operate on any connection it did not create. `_assert_throwaway` is not
politeness — `002_grants.sql` opens with `REVOKE ALL`, so pointing this at a real
cluster would strip its grants before granting the test matrix on top.

*Silent about secrets.* The superuser password is generated per run, held in memory,
and never written to a file or into the compose environment on disk.
"""

from __future__ import annotations

import os
import secrets
import socket
import subprocess
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ROLES_DIR = REPO_ROOT / "migrations" / "roles"

# Pinned by digest, never by tag (docs/tier4/supply-chain-policy.md § Container images).
# A tag is a mutable pointer: `postgres:17.6-alpine` today and next month can be
# different images, and a grant matrix verified against one is not evidence about the
# other. The tag is kept alongside the digest for readability only; the digest is what
# Docker resolves. Resolved 2026-08-16 via `docker buildx imagetools inspect`.
PINNED_POSTGRES_IMAGE = (
    "postgres@sha256:ef257d85f76e48da1c64832459b59fcaba1a4dac97bf5d7450c77753542eee94"
)
PINNED_POSTGRES_TAG = "postgres:17.6-alpine"

# Overridable only so a future arm64/amd64 or version bump can be measured before it is
# pinned. An override is recorded in the run's fingerprint by the caller; it is not a
# way to run the suite against an unpinned image quietly.
def _postgres_image() -> str:
    """Get the Postgres image, reading env at call time for test isolation."""
    return os.environ.get("ALFRED_TEST_POSTGRES_IMAGE") or PINNED_POSTGRES_IMAGE

DBNAME = "alfred_test"
SUPERUSER = "alfred_test_super"

# Every role the matrix names. Passwords are generated per run: the fixture hands each
# role a connection string, and nothing is persisted.
ROLES = (
    "alfred_bootstrap",
    "alfred_migrator_product",
    "alfred_migrator_control",
    "alfred_migrator_evidence",
    "alfred_migrator_heldout",
    "alfred_harness",
    "alfred_criterion",
    "alfred_product",
    "alfred_operator",
    "alfred_readmodel",
    "alfred_agent",
)

STARTUP_TIMEOUT_S = 60.0
POLL_INTERVAL_S = 0.25


class ClusterError(RuntimeError):
    """The cluster could not be created, migrated, or verified as throwaway."""


@dataclass(frozen=True)
class ThrowawayCluster:
    """A live, migrated, disposable cluster. Created only by `throwaway_cluster`."""

    container: str
    host: str
    port: int
    dbname: str
    superuser_password: str
    role_passwords: dict[str, str]

    def url(self, role: str) -> str:
        """Connection string for one role.

        `alfred_agent` is included deliberately: the negative tests must *connect* as it
        and be refused at the schema. A role that cannot connect proves nothing about
        grants, and a test that mistakes "could not connect" for "was denied" is the
        shape in which a security test most commonly lies.
        """
        if role == SUPERUSER:
            password = self.superuser_password
        else:
            try:
                password = self.role_passwords[role]
            except KeyError as exc:
                raise ClusterError(f"unknown role {role!r}; known roles: {sorted(self.role_passwords)}") from exc
        return f"postgresql://{role}:{password}@{self.host}:{self.port}/{self.dbname}"

    def sqlalchemy_url(self, role: str) -> str:
        """The same connection, spelled for SQLAlchemy.

        Bare `postgresql://` resolves to **psycopg2**, which this project does not
        depend on — `pyproject.toml` pins `psycopg[binary]>=3.2`. The driver must
        therefore be named explicitly, and the two spellings are separate methods
        rather than one string with a flag: libpq rejects `postgresql+psycopg://`
        outright, so a single URL used for both would fail on whichever side it was
        not written for.
        """
        return self.url(role).replace("postgresql://", "postgresql+psycopg://", 1)


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _run(argv: list[str], *, input_text: str | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(  # noqa: S603
        argv,
        input=input_text,
        capture_output=True,
        text=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise ClusterError(f"command failed ({result.returncode}): {' '.join(argv)}\n{result.stderr.strip()}")
    return result


def _psql(container: str, password: str, sql: str, *, variables: dict[str, str] | None = None) -> str:
    """Run SQL as the superuser through the container's own psql.

    Through the container rather than a host client, so the test does not depend on a
    psql being installed on the host and does not silently run against a different
    client version than the server.
    """
    argv = [
        "docker", "exec", "-i",
        "-e", f"PGPASSWORD={password}",
        _container_for_port(container),
        "psql", "-v", "ON_ERROR_STOP=1", "-U", SUPERUSER, "-d", DBNAME,
    ]
    for key, value in (variables or {}).items():
        argv.extend(["-v", f"{key}={value}"])
    return _run(argv, input_text=sql).stdout


def _container_for_port(container: str) -> str:
    """Return the container name directly; no global registry needed."""
    return container


def _assert_throwaway(container: str, port: int) -> None:
    """Refuse to proceed unless this is a container this module created.

    `002_grants.sql` begins by revoking everything from every named role. Applied to a
    real cluster it would strip grants before granting the test matrix on top, and the
    damage would look like a successful test run. So the check is fail-closed and runs
    before any SQL is applied, not after.
    """
    if not container.startswith("alfred-throwaway-"):
        raise ClusterError(f"refusing to operate on container {container!r}: not an Alfred throwaway cluster")
    inspect = _run(["docker", "inspect", "--format", "{{.Config.Labels.alfred_throwaway}}", container])
    if inspect.stdout.strip() != "true":
        raise ClusterError(f"refusing to operate on container {container!r}: missing alfred_throwaway=true label")


# The postgres entrypoint runs a *temporary* server on a unix socket to run initdb and
# any init scripts, then shuts it down and starts the real one. `pg_isready` succeeds
# against that temporary server, so readiness cannot be established from it: the first
# version of this function polled pg_isready, passed immediately, and then failed with
# `database "alfred_test" does not exist`. Worse than the failure is the near miss —
# had the target database happened to exist by then, roles would have been applied to a
# server that was about to be shut down and restarted mid-transaction.
_INIT_COMPLETE_MARKER = "PostgreSQL init process complete; ready for start up."


def _wait_ready(container: str, superuser_password: str, timeout_s: float = STARTUP_TIMEOUT_S) -> None:
    """Wait for the real server, not the bootstrap one.

    Two conditions, both required. The log marker proves the temporary server has been
    shut down; the query proves the real one is up and the target database exists. The
    marker alone is not enough (the restart takes a moment) and the query alone is not
    enough (it can succeed against the temporary server).
    """
    deadline = time.monotonic() + timeout_s
    last_error = "no attempt completed"
    saw_marker = False

    while time.monotonic() < deadline:
        if not saw_marker:
            logs = _run(["docker", "logs", container], check=False)
            if _INIT_COMPLETE_MARKER in (logs.stdout + logs.stderr):
                saw_marker = True
            else:
                last_error = "initdb has not finished"
                time.sleep(POLL_INTERVAL_S)
                continue

        probe = _run(
            [
                "docker", "exec", "-i",
                "-e", f"PGPASSWORD={superuser_password}",
                container,
                "psql", "-v", "ON_ERROR_STOP=1", "-U", SUPERUSER, "-d", DBNAME, "-tAc", "SELECT 1",
            ],
            check=False,
        )
        if probe.returncode == 0 and probe.stdout.strip() == "1":
            return
        last_error = (probe.stderr or probe.stdout).strip() or "query returned no rows"
        time.sleep(POLL_INTERVAL_S)

    raise ClusterError(f"cluster {container!r} not ready within {timeout_s}s: {last_error}")


def _set_role_passwords(container: str, superuser_password: str) -> dict[str, str]:
    """Assign a per-run password to every role.

    `001_roles.sql` deliberately sets no password: a literal there would be a credential
    in version control regardless of how the role is later restricted. The fixture
    supplies them at apply time, which is the same mechanism the real deployment uses
    from the secret store.
    """
    passwords = {role: secrets.token_urlsafe(24) for role in ROLES}
    statements = "\n".join(
        # Format-string SQL is acceptable here and only here: the role names are a
        # module constant, never input, and ALTER ROLE takes no parameters.
        f"ALTER ROLE {role} WITH PASSWORD '{password}';"
        for role, password in passwords.items()
    )
    _psql(container, superuser_password, statements)
    return passwords


def _apply_roles_and_grants(container: str, superuser_password: str) -> None:
    for filename in ("001_roles.sql", "002_grants.sql"):
        path = ROLES_DIR / filename
        if not path.is_file():
            raise ClusterError(f"{path} does not exist")
        _psql(container, superuser_password, path.read_text(encoding="utf-8"), variables={"DBNAME": DBNAME})


def _apply_migrations(cluster: ThrowawayCluster) -> None:
    """Run all four Alembic environments, each as its own migrator role.

    With no migration files present this is a no-op that creates four version tables,
    and that is the honest current state rather than a gap: the layout, the roles and
    the grants are what exist, and this proves they hold together.
    """
    environments = {
        "product": "alfred_migrator_product",
        "control": "alfred_migrator_control",
        "evidence": "alfred_migrator_evidence",
        "heldout": "alfred_migrator_heldout",
    }
    for name, role in environments.items():
        env = dict(os.environ)
        env[f"ALFRED_DB_URL_MIGRATOR_{name.upper()}"] = cluster.sqlalchemy_url(role)
        result = subprocess.run(  # noqa: S603
            ["uv", "run", "alembic", "-n", name, "upgrade", "head"],  # noqa: S607
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise ClusterError(f"alembic -n {name} upgrade head failed:\n{result.stderr.strip()}")

    # Grants are re-applied after migrations, and this ordering is load-bearing.
    # `002_grants.sql` grants per-table in `control` and `evidence` because those
    # schemas' grants differ by table name; a table created by a migration therefore
    # has no grants until the file is re-run. Applying it only before migrations would
    # leave every new table ungranted, which reads as a working boundary right up to
    # the moment something needs to read the table.
    _psql(cluster.container, cluster.superuser_password, (ROLES_DIR / "002_grants.sql").read_text(encoding="utf-8"))


@contextmanager
def throwaway_cluster(*, keep: bool = False) -> Iterator[ThrowawayCluster]:
    """Create a migrated throwaway cluster; destroy it on exit.

    `keep=True` leaves the container running for inspection after a failure. It is off
    by default because a kept container holds a port and a name, and the next run would
    silently get a second one.
    """
    container = f"alfred-throwaway-{uuid.uuid4().hex[:12]}"
    port = _free_port()
    superuser_password = secrets.token_urlsafe(24)

    _run(
        [
            "docker", "run", "--detach",
            "--name", container,
            "--label", "alfred_throwaway=true",
            # Loopback only. A test cluster reachable from the network is a cluster
            # with a generated password and no grant matrix yet, exposed.
            "--publish", f"127.0.0.1:{port}:5432",
            # tmpfs: nothing survives the container, so no run can inherit a role or a
            # grant from a previous one.
            "--tmpfs", "/var/lib/postgresql/data:rw,size=512m",
            "--env", f"POSTGRES_USER={SUPERUSER}",
            "--env", f"POSTGRES_PASSWORD={superuser_password}",
            "--env", f"POSTGRES_DB={DBNAME}",
            # Durability is worthless for a cluster that is deleted in a minute, and
            # fsync off makes migrations markedly faster.
            _postgres_image(),
            "-c", "fsync=off",
            "-c", "full_page_writes=off",
            "-c", "synchronous_commit=off",
        ]
    )

    try:
        _assert_throwaway(container, port)
        _wait_ready(container, superuser_password)
        _apply_roles_and_grants(container, superuser_password)
        role_passwords = _set_role_passwords(container, superuser_password)
        cluster = ThrowawayCluster(
            container=container,
            host="127.0.0.1",
            port=port,
            dbname=DBNAME,
            superuser_password=superuser_password,
            role_passwords=role_passwords,
        )
        _apply_migrations(cluster)
        yield cluster
    finally:
        if not keep:
            _run(["docker", "rm", "--force", "--volumes", container], check=False)
