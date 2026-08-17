"""The append-only chain, asserted from both sides.

**How this suite would be shown vacuous** (D57). Every positive test here would still
pass against a store that appended rows and computed digests over nothing in
particular — a chain is self-consistent by construction if nothing ever checks it
against a second reading. So the load-bearing half is the negative half, and each
negative test carries its own control:

- `test_tamper_is_detected` mutates a stored body as the superuser and requires
  `verify_chain` to raise. Its control is `test_chain_verifies`: the identical walk over
  the identical rows, untampered, must pass — otherwise the walk raises on everything
  and detects nothing.
- `test_fork_is_refused_by_the_cluster` requires the database, not the code, to refuse a
  second row on the same predecessor. Its control is that the same insert with a
  different predecessor succeeds.
- `test_link_digest_is_recomputable_without_the_store` recomputes a stored digest from
  the stored columns alone. If it could not, an external auditor could not either, and
  the chain would be worth nothing to the only reader it exists for.
- `test_autocommit_is_refused` fails closed on a connection whose lock would not hold.

**What none of this proves.** The walk uses the encoder that wrote the rows, so it is
checked against itself. The independent check is the JavaScript re-walk in the restore
drill (S7), and no test in this file substitutes for it.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import psycopg
import pytest
from psycopg import sql

from harness.db.cluster import SUPERUSER, ThrowawayCluster
from harness.evidence.store import (
    VERDICT_RECORD_TYPE,
    Appended,
    ChainBroken,
    ChainForked,
    EvidenceError,
    EvidenceStore,
    link_digest,
)

pytestmark = pytest.mark.db

ORG = uuid.UUID("018f0000-0000-7000-8000-000000000001")
PROJECT = uuid.UUID("018f0000-0000-7000-8000-000000000002")
RECORD_TYPE = "alfred.run.task_start.v1"


def _harness_conn(cluster: ThrowawayCluster) -> psycopg.Connection[Any]:
    return psycopg.connect(cluster.url("alfred_harness"))


def _super_conn(cluster: ThrowawayCluster) -> psycopg.Connection[Any]:
    return psycopg.connect(cluster.url(SUPERUSER), autocommit=True)


def _append(store: EvidenceStore, chain: str, *, n: int) -> Appended:
    return store.append_run_record(
        chain_id=chain,
        org_id=ORG,
        project_id=PROJECT,
        task_id=uuid.uuid4(),
        record_type=RECORD_TYPE,
        body={"seq": n, "note": "a body the projection can query and the chain cannot"},
        schema_version=1,
        emitted_at=datetime.now(UTC),
        monotonic_ns=1_000 * n,
    )


def _chain_id(name: str) -> str:
    return f"{name}-{uuid.uuid4().hex[:8]}"


# ------------------------------------------------------------------------ positive


def test_genesis_has_no_predecessor(cluster: ThrowawayCluster) -> None:
    chain = _chain_id("genesis")
    with _harness_conn(cluster) as conn:
        first = _append(EvidenceStore(conn), chain, n=1)
        conn.commit()
    assert first.prev_sha256 is None


def test_each_row_links_to_the_last(cluster: ThrowawayCluster) -> None:
    chain = _chain_id("link")
    with _harness_conn(cluster) as conn:
        store = EvidenceStore(conn)
        first = _append(store, chain, n=1)
        second = _append(store, chain, n=2)
        third = _append(store, chain, n=3)
        conn.commit()
    assert second.prev_sha256 == first.sha256
    assert third.prev_sha256 == second.sha256


def test_chains_are_independent(cluster: ThrowawayCluster) -> None:
    """Two chains do not see each other's head.

    Without this, `chain_id` would be decorative and every stream would share one
    serial order — which is not wrong, but it is not what the column claims.
    """
    left, right = _chain_id("left"), _chain_id("right")
    with _harness_conn(cluster) as conn:
        store = EvidenceStore(conn)
        _append(store, left, n=1)
        first_right = _append(store, right, n=1)
        conn.commit()
    assert first_right.prev_sha256 is None


def test_chain_verifies(cluster: ThrowawayCluster) -> None:
    chain = _chain_id("verify")
    with _harness_conn(cluster) as conn:
        store = EvidenceStore(conn)
        for n in range(1, 6):
            last = _append(store, chain, n=n)
        conn.commit()
        report = store.verify_chain(table="run_record", chain_id=chain)
    assert report.length == 5
    assert report.head_sha256 == last.sha256
    assert report.total


def test_empty_chain_verifies_as_empty(cluster: ThrowawayCluster) -> None:
    """An absent chain is not a broken chain.

    The distinction matters because "no rows" and "rows that do not walk" would
    otherwise both raise, and the restore drill has to tell a fresh restore from a
    corrupted one.
    """
    with _harness_conn(cluster) as conn:
        report = EvidenceStore(conn).verify_chain(table="run_record", chain_id=_chain_id("absent"))
    assert report.length == 0
    assert report.head_sha256 is None


def test_link_digest_is_recomputable_without_the_store(cluster: ThrowawayCluster) -> None:
    chain = _chain_id("auditor")
    with _harness_conn(cluster) as conn:
        store = EvidenceStore(conn)
        _append(store, chain, n=1)
        second = _append(store, chain, n=2)
        conn.commit()

        with conn.cursor() as cur:
            cur.execute(
                "SELECT prev_sha256, body_sha256, record_type, sha256 "
                "FROM evidence.run_record WHERE id = %s",
                (second.id,),
            )
            prev, body_sha, record_type, stored = cur.fetchone()  # pyright: ignore[reportGeneralTypeIssues]

    recomputed = link_digest(
        chain_id=chain, record_type=record_type, prev_sha256=prev, body_sha256=body_sha
    )
    assert recomputed == stored


def test_verdict_uses_its_own_domain_separator(cluster: ThrowawayCluster) -> None:
    """A verdict and a run record with identical bodies must not share a body digest.

    Domain separation is the property that makes one hash scheme safe to use for
    several record kinds, and it is invisible until two kinds collide.
    """
    from harness.acs.acs1 import acs_sha256

    body = {"seq": 1, "note": "identical"}
    assert acs_sha256(VERDICT_RECORD_TYPE, body) != acs_sha256(RECORD_TYPE, body)


# ------------------------------------------------------------------------ negative


def test_tamper_is_detected(cluster: ThrowawayCluster) -> None:
    """A row rewritten after the fact does not survive the walk.

    Rewritten as the *superuser*, deliberately: no role in the matrix holds `UPDATE`
    here, so the only way to stage this is to step outside the matrix — which is the
    threat the chain exists for, and is exactly the operator-level compromise that
    append-only alone does not survive.
    """
    chain = _chain_id("tamper")
    with _harness_conn(cluster) as conn:
        store = EvidenceStore(conn)
        _append(store, chain, n=1)
        victim = _append(store, chain, n=2)
        _append(store, chain, n=3)
        conn.commit()

    with _super_conn(cluster) as admin, admin.cursor() as cur:
        cur.execute(
            "UPDATE evidence.run_record SET body_sha256 = %s WHERE id = %s",
            ("0" * 64, victim.id),
        )

    with _harness_conn(cluster) as conn, pytest.raises(ChainBroken):
        EvidenceStore(conn).verify_chain(table="run_record", chain_id=chain)


def test_fork_is_refused_by_the_cluster(cluster: ThrowawayCluster) -> None:
    """Two rows cannot share a predecessor, and the database is what refuses it.

    Not the store: a check in Python is a check a second writer does not run. The
    control is the second half — the same insert against a different predecessor
    succeeds, so the constraint is refusing the fork and not the statement.
    """
    chain = _chain_id("fork")
    with _harness_conn(cluster) as conn:
        store = EvidenceStore(conn)
        first = _append(store, chain, n=1)
        second = _append(store, chain, n=2)
        conn.commit()

    with _super_conn(cluster) as admin:
        with admin.cursor() as cur, pytest.raises(psycopg.errors.UniqueViolation):
            cur.execute(_forged_insert(), _forged_params(chain, prev=first.sha256))
        with admin.cursor() as cur:
            cur.execute(_forged_insert(), _forged_params(chain, prev=second.sha256))


def test_second_genesis_is_refused_by_the_cluster(cluster: ThrowawayCluster) -> None:
    """The fork at row one, which a plain UNIQUE does not close.

    A second row with `prev_sha256 IS NULL` is a fork at the one position where both
    individual links still recompute perfectly. Postgres treats NULLs as distinct in a
    unique index by default, so the constraint that refuses every other fork accepts
    this one — which is why it is declared `NULLS NOT DISTINCT`. This test is the
    regression guard on that word: drop it from the migration and this is the only
    thing in the repository that fails.
    """
    chain = _chain_id("twogenesis")
    with _harness_conn(cluster) as conn:
        _append(EvidenceStore(conn), chain, n=1)
        conn.commit()

    with (
        _super_conn(cluster) as admin,
        admin.cursor() as cur,
        pytest.raises(psycopg.errors.UniqueViolation),
    ):
        cur.execute(_forged_insert(), _forged_params(chain, prev=None))


def test_walk_refuses_an_unreachable_row(cluster: ThrowawayCluster) -> None:
    """Reachability, not link integrity — the assertion S7's restore drill needs.

    Removing a row from the middle leaves the tail as an island whose every link still
    recomputes. A check that verifies each link one at a time reports the chain sound.
    Only a walk that counts what it visited against what exists notices.
    """
    chain = _chain_id("island")
    with _harness_conn(cluster) as conn:
        store = EvidenceStore(conn)
        _append(store, chain, n=1)
        middle = _append(store, chain, n=2)
        _append(store, chain, n=3)
        conn.commit()

    with _super_conn(cluster) as admin, admin.cursor() as cur:
        cur.execute("DELETE FROM evidence.run_record WHERE id = %s", (middle.id,))

    with _harness_conn(cluster) as conn, pytest.raises(ChainForked, match="visited"):
        EvidenceStore(conn).verify_chain(table="run_record", chain_id=chain)


def test_autocommit_is_refused(cluster: ThrowawayCluster) -> None:
    with (
        psycopg.connect(cluster.url("alfred_harness"), autocommit=True) as conn,
        pytest.raises(EvidenceError, match="autocommit"),
    ):
        EvidenceStore(conn)


def test_unknown_table_is_refused(cluster: ThrowawayCluster) -> None:
    with _harness_conn(cluster) as conn, pytest.raises(EvidenceError):
        EvidenceStore(conn).verify_chain(table="artifact", chain_id="x")


# ------------------------------------------------------------------------ forging

# A hand-written INSERT used only to stage failures the store cannot produce. It exists
# so the negative tests do not depend on a bug in the store to demonstrate a defect the
# store is supposed to prevent.


def _forged_insert() -> sql.SQL:
    return sql.SQL(
        "INSERT INTO evidence.run_record "
        "(id, org_id, project_id, schema_version, created_at, chain_id, "
        " body_sha256, prev_sha256, sha256, task_id, record_type, emitted_at, "
        " monotonic_ns, body) "
        "VALUES (%(id)s, %(org)s, %(project)s, 1, now(), %(chain)s, %(body_sha)s, "
        "        %(prev)s, %(sha)s, %(task)s, %(record_type)s, now(), 0, '{}'::jsonb)"
    )


def _forged_params(chain: str, *, prev: str | None) -> dict[str, object]:
    body_sha = uuid.uuid4().hex * 2
    return {
        "id": uuid.uuid4(),
        "org": ORG,
        "project": PROJECT,
        "chain": chain,
        "body_sha": body_sha,
        "prev": prev,
        "sha": link_digest(
            chain_id=chain, record_type=RECORD_TYPE, prev_sha256=prev, body_sha256=body_sha
        ),
        "task": uuid.uuid4(),
        "record_type": RECORD_TYPE,
    }
