"""The grant matrix, asserted two ways: by set equality, and by being refused.

**Every denial asserts `SQLSTATE 42501` specifically, never "an exception was raised".**
A test that accepts any exception passes on `42P01 undefined_table` — so a typo in a
table name, or a schema that has not been created yet, would read as proof of isolation.
That is the shape in which a security test most commonly lies, and it is the reason this
file compares `exc.sqlstate` rather than catching `Exception`.

**Every denial is paired with a permission.** `alfred_agent` holds no schema `USAGE`, so
Postgres refuses it at the schema before it ever looks for the table — which means a
misspelled table name also yields 42501 and the test would pass against nothing. The
control is the `ALLOWED` half of the same table: the identical statement, on the
identical object, by the role that should hold the privilege, asserted to succeed. A
denial with no matching permission is a denial that proves the object exists nowhere.

**How this suite would be shown vacuous** (D57): stop the parametrisation from
generating cases and every test disappears silently, so `test_case_inventory` asserts
the counts; make `_denied` swallow the sqlstate comparison and `test_denied_helper_
rejects_success` fails; drop every table and the `ALLOWED` half fails while the `DENIED`
half still passes, which is why both halves are in one file and neither may be run alone.
"""

from __future__ import annotations

import psycopg
import pytest
from psycopg import sql

from harness.db.assert_grants import Report, check_matrix, observe
from harness.db.cluster import SUPERUSER, ThrowawayCluster

pytestmark = pytest.mark.db

INSUFFICIENT_PRIVILEGE = "42501"

# Every table the four migrations create. Written out rather than read from the cluster:
# a negative-test inventory derived from the thing under test cannot notice that the
# thing under test lost a table.
EXPECTED_TABLES = {
    "product": ["metric_result", "result_stamp", "scenario", "trajectory"],
    "control": ["fingerprint", "policy_protected_path", "threshold_value", "work"],
    "evidence": [
        "artifact",
        "defect_escape",
        "operator_action",
        "run_record",
        "verdict",
    ],
    "heldout": ["reference_value"],
    "migration_meta": [
        "alembic_version_control",
        "alembic_version_evidence",
        "alembic_version_heldout",
        "alembic_version_product",
    ],
}


# Statements are composed with `psycopg.sql`, never with an f-string. psycopg types
# `execute`'s query parameter as `LiteralString` so that runtime-built SQL does not
# typecheck, and `sql.Identifier` quotes the name properly — so the type error and the
# injection hazard have the same fix. Suppressing it would have left both.
def _ident(table: str) -> sql.Identifier:
    schema, _, name = table.partition(".")
    return sql.Identifier(schema, name)


def _read(table: str) -> sql.Composed:
    return sql.SQL("SELECT 1 FROM {t} LIMIT 1").format(t=_ident(table))


def _insert(table: str) -> sql.Composed:
    # Permission is checked before anything touches a row, and `WHERE false` guarantees
    # no row is touched — so the statement distinguishes "may not" from "may" without
    # needing a valid row to insert, and without leaving one behind if it succeeds.
    return sql.SQL("INSERT INTO {t} SELECT * FROM {t} WHERE false").format(t=_ident(table))


def _update(table: str) -> sql.Composed:
    return sql.SQL("UPDATE {t} SET id = id WHERE false").format(t=_ident(table))


def _delete(table: str) -> sql.Composed:
    return sql.SQL("DELETE FROM {t} WHERE false").format(t=_ident(table))


# (case id, role, statement). Each DENIED row cites the N-rule it enforces.
DENIED: list[tuple[str, str, sql.Composed]] = [
    # N1 — alfred_agent holds nothing anywhere, schema USAGE included.
    ("N1-product", "alfred_agent", _read("product.scenario")),
    ("N1-control", "alfred_agent", _read("control.work")),
    ("N1-evidence", "alfred_agent", _read("evidence.run_record")),
    ("N1-verdict", "alfred_agent", _read("evidence.verdict")),
    ("N1-heldout", "alfred_agent", _read("heldout.reference_value")),
    ("N1-meta", "alfred_agent", _read("migration_meta.alembic_version_product")),
    # N2 — the harness assembles agent context; a SELECT here puts held-out values one
    # bug away from the prompt.
    ("N2-harness-heldout", "alfred_harness", _read("heldout.reference_value")),
    # N3 — the read model is the agent-writable half of the operator surface.
    ("N3-readmodel-heldout", "alfred_readmodel", _read("heldout.reference_value")),
    ("N3-readmodel-insert", "alfred_readmodel", _insert("evidence.run_record")),
    ("N3-readmodel-update", "alfred_readmodel", _update("control.work")),
    ("N3-readmodel-product", "alfred_readmodel", _insert("product.scenario")),
    # N4 — alfred_operator's only INSERT anywhere is evidence.operator_action, and the
    # claim is global rather than local.
    ("N4-operator-verdict", "alfred_operator", _insert("evidence.verdict")),
    ("N4-operator-runrecord", "alfred_operator", _insert("evidence.run_record")),
    ("N4-operator-work", "alfred_operator", _insert("control.work")),
    ("N4-operator-product", "alfred_operator", _read("product.scenario")),
    # N5 — append-only. A held-out reference value silently rewritten changes past
    # verdicts retroactively.
    ("N5-criterion-verdict-update", "alfred_criterion", _update("evidence.verdict")),
    ("N5-criterion-verdict-delete", "alfred_criterion", _delete("evidence.verdict")),
    ("N5-harness-runrecord-update", "alfred_harness", _update("evidence.run_record")),
    ("N5-harness-runrecord-delete", "alfred_harness", _delete("evidence.run_record")),
    ("N5-criterion-heldout-update", "alfred_criterion", _update("heldout.reference_value")),
    ("N5-criterion-heldout-insert", "alfred_criterion", _insert("heldout.reference_value")),
    # The harness may read a verdict and may not write one. D39 makes that physical:
    # separate process, separate role, no import path — this is the database half.
    ("D39-harness-verdict-insert", "alfred_harness", _insert("evidence.verdict")),
    # control config is written by its migrator alone. A role that can rewrite a
    # protected-path row can unprotect a path without touching a protected file.
    ("config-harness-policy", "alfred_harness", _update("control.policy_protected_path")),
    ("config-harness-threshold", "alfred_harness", _insert("control.threshold_value")),
]

# The vacuity control. Same objects, the role that should hold the privilege.
ALLOWED: list[tuple[str, str, sql.Composed]] = [
    ("allow-harness-product", "alfred_harness", _read("product.scenario")),
    ("allow-harness-control", "alfred_harness", _read("control.work")),
    ("allow-harness-work-update", "alfred_harness", _update("control.work")),
    ("allow-harness-evidence", "alfred_harness", _insert("evidence.run_record")),
    ("allow-harness-verdict-read", "alfred_harness", _read("evidence.verdict")),
    ("allow-harness-policy-read", "alfred_harness", _read("control.policy_protected_path")),
    ("allow-criterion-heldout", "alfred_criterion", _read("heldout.reference_value")),
    ("allow-criterion-verdict", "alfred_criterion", _insert("evidence.verdict")),
    ("allow-operator-action", "alfred_operator", _insert("evidence.operator_action")),
    ("allow-operator-verdict-read", "alfred_operator", _read("evidence.verdict")),
    ("allow-readmodel-verdict", "alfred_readmodel", _read("evidence.verdict")),
    ("allow-readmodel-operator", "alfred_readmodel", _read("evidence.operator_action")),
    ("allow-product-write", "alfred_product", _insert("product.scenario")),
    ("allow-product-delete", "alfred_product", _delete("product.scenario")),
]


def _denied(cluster: ThrowawayCluster, role: str, statement: sql.Composed) -> None:
    """Run `statement` as `role`; require Postgres to raise 42501 and nothing else."""
    with psycopg.connect(cluster.url(role)) as conn, conn.cursor() as cur:
        with pytest.raises(psycopg.Error) as caught:
            cur.execute(statement)
        sqlstate = caught.value.sqlstate
        assert sqlstate == INSUFFICIENT_PRIVILEGE, (
            f"{role}: expected SQLSTATE {INSUFFICIENT_PRIVILEGE} (insufficient_privilege), "
            f"got {sqlstate} — {caught.value}. A denial reported under any other code is "
            f"not evidence of isolation: 42P01 means the object is simply not there."
        )
        conn.rollback()


# ------------------------------------------------------------------------ the matrix


def test_matrix_equals_declaration(cluster: ThrowawayCluster) -> None:
    """Set equality, both directions, with EXTRA reported first."""
    with psycopg.connect(cluster.url("alfred_harness")) as conn:
        report = check_matrix(conn)
    assert report.ok, "\n" + report.render()


def test_every_expected_table_exists(cluster: ThrowawayCluster) -> None:
    """The migrations created what this file assumes they created.

    Without this the negative tests below would still pass against a cluster missing
    every table — `alfred_agent` is refused at the schema, so it never reaches the name.
    """
    with psycopg.connect(cluster.url("alfred_harness")) as conn:
        observation = observe(conn, ["alfred_harness"])
    for schema, expected in EXPECTED_TABLES.items():
        assert observation.tables.get(schema) == expected, (
            f"schema {schema}: expected {expected}, observed {observation.tables.get(schema)}"
        )


# ---------------------------------------------------------------- negative and paired


@pytest.mark.parametrize(("case", "role", "statement"), DENIED, ids=[row[0] for row in DENIED])
def test_denied(cluster: ThrowawayCluster, case: str, role: str, statement: sql.Composed) -> None:
    del case
    _denied(cluster, role, statement)


@pytest.mark.parametrize(("case", "role", "statement"), ALLOWED, ids=[row[0] for row in ALLOWED])
def test_allowed(cluster: ThrowawayCluster, case: str, role: str, statement: sql.Composed) -> None:
    """The other half of every denial. Without it a denial proves only that nothing is
    reachable, which is also what an empty cluster proves.
    """
    del case
    with psycopg.connect(cluster.url(role)) as conn, conn.cursor() as cur:
        cur.execute(statement)
        conn.rollback()


# ------------------------------------------------------------------- vacuity controls


def test_case_inventory() -> None:
    """A parametrised suite that generates no cases reports green.

    These numbers are asserted rather than derived so that deleting a case is a failing
    test rather than a smaller run nobody notices.
    """
    assert len(DENIED) == 24
    assert len(ALLOWED) == 14
    assert len({row[0] for row in DENIED}) == len(DENIED), "duplicate DENIED case id"
    assert len({row[0] for row in ALLOWED}) == len(ALLOWED), "duplicate ALLOWED case id"


def test_denied_helper_rejects_success(cluster: ThrowawayCluster) -> None:
    """`_denied` must fail when the statement is permitted.

    The negative control on the negative tests. If this passes, every `test_denied`
    above is asserting something; if `_denied` were ever loosened to catch any
    exception — or to catch none — this is the test that goes red.
    """
    with pytest.raises(pytest.fail.Exception):
        _denied(cluster, "alfred_harness", _read("control.work"))


def test_denied_helper_rejects_wrong_sqlstate(cluster: ThrowawayCluster) -> None:
    """A missing table raises 42P01, and `_denied` must not accept it as a denial.

    This is the exact defect the docstring at the top names: a test that accepts any
    exception reads a typo as proof of isolation.
    """
    with pytest.raises(AssertionError, match="42P01"):
        _denied(cluster, "alfred_harness", _read("control.no_such_table"))


def _report(cluster: ThrowawayCluster) -> Report:
    with psycopg.connect(cluster.url("alfred_harness")) as conn:
        return check_matrix(conn)


def _as_superuser(cluster: ThrowawayCluster, statement: sql.SQL) -> None:
    with psycopg.connect(cluster.url(SUPERUSER), autocommit=True) as conn, conn.cursor() as cur:
        cur.execute(statement)


def test_assertion_detects_an_extra_grant(cluster: ThrowawayCluster) -> None:
    """Mutation control, and the one that matters.

    A subset check would pass this test. `alfred_agent` gains a SELECT it must never
    hold; the assertion must report it as EXTRA. The grant is issued and withdrawn by
    the superuser inside try/finally, and the report is re-checked afterwards so a
    failure here cannot leave the session-scoped cluster mutated for later tests.
    """
    _as_superuser(cluster, sql.SQL("GRANT SELECT ON evidence.verdict TO alfred_agent"))
    try:
        report = _report(cluster)
        rendered = report.render()
        assert not report.ok, "an extra grant was not detected"
        assert "EXTRA" in rendered
        assert "alfred_agent" in rendered
    finally:
        _as_superuser(cluster, sql.SQL("REVOKE SELECT ON evidence.verdict FROM alfred_agent"))
    assert _report(cluster).ok, "the cluster was not restored"


def test_assertion_detects_a_missing_grant(cluster: ThrowawayCluster) -> None:
    """The other direction. Loud rather than silent, but it must still be reported."""
    _as_superuser(cluster, sql.SQL("REVOKE SELECT ON evidence.verdict FROM alfred_harness"))
    try:
        report = _report(cluster)
        rendered = report.render()
        assert not report.ok, "a withdrawn grant was not detected"
        assert "MISSING" in rendered
        assert "alfred_harness" in rendered
    finally:
        _as_superuser(cluster, sql.SQL("GRANT SELECT ON evidence.verdict TO alfred_harness"))
    assert _report(cluster).ok, "the cluster was not restored"
