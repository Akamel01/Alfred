"""Append-only, hash-chained evidence writes.

**The evidence plane is never written by the agent.** That single rule drives more of
this architecture than anything else, and this module is where it becomes code. Two
properties carry it, and neither is a convention:

*Append-only.* This class has no update and no delete, and adding one would be visible
in a diff. Beneath it the grant matrix holds the same line from the other side — no role
holds `UPDATE`, `DELETE` or `TRUNCATE` on anything in `evidence` — so a method added
here would fail at the cluster rather than succeed quietly.

*Chained.* Every row carries its predecessor's digest, over the canonical ACS-1 bytes
(ADR-0003), so an audit log that has been rewritten says so. Append-only is an integrity
property against the agent; the chain is what survives an operator-level compromise or a
bad migration, which is the threat the operator (T10) actually poses.

**Who writes what is a grant, not a check in this file.** The store takes whatever
connection it is handed. `CriterionRunner` holds `alfred_criterion` and is therefore the
only writer that can insert a verdict; the command surface holds `alfred_operator` and
can insert nothing but an operator action. Re-checking that here would be a second,
weaker copy of a control the database already enforces — and the weaker copy is the one
that would drift.

**What the Python re-walk proves, and what it does not.** `verify_chain` recomputes every
link with the same encoder that wrote it. That detects a row mutated after the fact, and
it detects a fork. It does **not** validate the encoder: a chain checked with the encoder
that produced it is checked against itself. The independent check is the JavaScript
re-walk in the restore drill, and this method is not a substitute for it.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Final

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb

from harness.acs.acs1 import acs_sha256

type AcsScalar = str | int | float | bool | None
type AcsValue = AcsScalar | list[AcsValue] | dict[str, AcsValue]
type Body = dict[str, AcsValue]

SCHEMA: Final = "evidence"

# The domain separator for the link digest. Distinct from every body separator, so a
# link and a body of coincidentally identical content cannot collide, and versioned in
# its own name so the scheme can change without silently reinterpreting stored digests.
LINK_RECORD_TYPE: Final = "alfred.evidence.chain_link.v1"

# `verdict` and `operator_action` carry no `record_type` column — their record type is
# the table. Named constants rather than the table name so the domain separator is
# stable if a table is ever renamed, and so D51's "distinguished by ACS-1 domain
# separation by record_type" is a literal in the code and not an intention.
VERDICT_RECORD_TYPE: Final = "alfred.evidence.verdict.v1"
OPERATOR_ACTION_RECORD_TYPE: Final = "alfred.evidence.operator_action.v1"

CHAINED_TABLES: Final = frozenset({"run_record", "verdict", "operator_action"})

class EvidenceError(RuntimeError):
    """A write could not be made, or a chain does not hold."""


class ChainForked(EvidenceError):
    """More than one head, or a row reachable twice. The log is not a single path."""


class ChainBroken(EvidenceError):
    """A stored digest does not match the content it covers."""


@dataclass(frozen=True)
class Appended:
    """What was written. Returned so the caller can order side effects after it."""

    id: uuid.UUID
    chain_id: str
    prev_sha256: str | None
    body_sha256: str
    sha256: str


@dataclass(frozen=True)
class ChainReport:
    """The result of a full re-walk."""

    chain_id: str
    table: str
    length: int
    head_sha256: str | None
    total: bool


def link_digest(
    *, chain_id: str, record_type: str, prev_sha256: str | None, body_sha256: str
) -> str:
    """The digest binding one row to its predecessor.

    A module-level function rather than a method: an external auditor recomputes the
    chain from the stored columns without instantiating anything, and this is the whole
    reason the chain is worth having. Keys are not ordered here because ACS-1 sorts them
    — an ordering written by hand would be a second canonical form.
    """
    return acs_sha256(
        LINK_RECORD_TYPE,
        {
            "body_sha256": body_sha256,
            "chain_id": chain_id,
            "prev_sha256": prev_sha256,
            "record_type": record_type,
        },
    )


def _lock_key(chain_id: str) -> int:
    """A stable advisory-lock key for one chain.

    Signed int64 from the chain id's digest. `hashtext()` would do, but it is an
    undocumented internal whose output has changed across major versions, and a lock key
    that changes on upgrade serializes nothing on the day of the upgrade.
    """
    digest = hashlib.sha256(chain_id.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big", signed=True)


class EvidenceStore:
    """Append-only writer over one connection.

    The connection's role decides what may be written. The caller owns the transaction
    and commits it: **the evidence write is the commit point**, and side effects that
    cannot be undone are ordered after that commit by the caller, not by this class.
    """

    def __init__(self, conn: psycopg.Connection[Any]) -> None:
        if conn.autocommit:
            # Fail closed rather than write. The chain is serialized by a
            # transaction-scoped advisory lock, which under autocommit is released the
            # instant it is taken — so every append would look correct and two
            # concurrent writers would race for the same predecessor. The unique
            # constraint would still refuse the fork, but the failure would surface as
            # an integrity error at some unrelated call site rather than here.
            raise EvidenceError(
                "EvidenceStore requires a transactional connection: autocommit releases "
                "the chain lock immediately and the write ordering is not serialized."
            )
        self._conn = conn

    # ------------------------------------------------------------------ chained

    def append_run_record(
        self,
        *,
        chain_id: str,
        org_id: uuid.UUID,
        project_id: uuid.UUID,
        task_id: uuid.UUID,
        record_type: str,
        body: Body,
        schema_version: int,
        emitted_at: datetime,
        monotonic_ns: int,
        attempt_id: uuid.UUID | None = None,
        caused_by: uuid.UUID | None = None,
    ) -> Appended:
        """One record of the run-record stream.

        `record_type` is the stream's own field and is the ACS-1 domain separator, so
        the store passes it through rather than deriving one. The store owns the
        envelope; Run Instrumentation owns the body, and this class never re-declares a
        stream field.
        """
        return self._append(
            table="run_record",
            record_type=record_type,
            chain_id=chain_id,
            org_id=org_id,
            project_id=project_id,
            schema_version=schema_version,
            caused_by=caused_by,
            body=body,
            columns={
                "task_id": task_id,
                "attempt_id": attempt_id,
                "record_type": record_type,
                "emitted_at": emitted_at,
                "monotonic_ns": monotonic_ns,
            },
        )

    def append_verdict(
        self,
        *,
        chain_id: str,
        org_id: uuid.UUID,
        project_id: uuid.UUID,
        task_id: uuid.UUID,
        attempt_id: uuid.UUID,
        criterion_ref: str,
        criterion_version: int,
        verdict: str,
        body: Body,
        schema_version: int,
        score: float | None = None,
        held_out_result: str | None = None,
        held_out_provenance_tier: str | None = None,
        indeterminate_reason: str | None = None,
        caused_by: uuid.UUID | None = None,
    ) -> Appended:
        """The one row `CriterionRunner` writes and nothing else may.

        The three-valued vocabulary and the `indeterminate` reason requirement are check
        constraints on the table, deliberately not re-implemented here: a value this
        method rejected but the database accepted would mean the two disagreed, and the
        database is the one that is still true after a code change.
        """
        return self._append(
            table="verdict",
            record_type=VERDICT_RECORD_TYPE,
            chain_id=chain_id,
            org_id=org_id,
            project_id=project_id,
            schema_version=schema_version,
            caused_by=caused_by,
            body=body,
            columns={
                "task_id": task_id,
                "attempt_id": attempt_id,
                "criterion_ref": criterion_ref,
                "criterion_version": criterion_version,
                "verdict": verdict,
                "held_out_result": held_out_result,
                "held_out_provenance_tier": held_out_provenance_tier,
                "score": score,
                "indeterminate_reason": indeterminate_reason,
            },
        )

    def append_operator_action(
        self,
        *,
        chain_id: str,
        org_id: uuid.UUID,
        project_id: uuid.UUID,
        action: str,
        actor_id: str,
        field_set_version: int,
        body: Body,
        schema_version: int,
        task_id: uuid.UUID | None = None,
        attended_ms: int | None = None,
        attended_ms_upper: int | None = None,
        elapsed_ms: int | None = None,
        interval_count: int | None = None,
        full_diff_opened: bool | None = None,
        caused_by: uuid.UUID | None = None,
    ) -> Appended:
        """One operator action, written before its side effect is emitted (D51).

        `attended_ms` and `attended_ms_upper` are a bracket and travel together; the
        table refuses one without the other. `null` rather than `0` when the instrument
        did not run, because a zero is a measurement and a null is the absence of one,
        and the capacity ledger reads the difference.
        """
        return self._append(
            table="operator_action",
            record_type=OPERATOR_ACTION_RECORD_TYPE,
            chain_id=chain_id,
            org_id=org_id,
            project_id=project_id,
            schema_version=schema_version,
            caused_by=caused_by,
            body=body,
            columns={
                "task_id": task_id,
                "action": action,
                "actor_kind": "operator",
                "actor_id": actor_id,
                "field_set_version": field_set_version,
                "attended_ms": attended_ms,
                "attended_ms_upper": attended_ms_upper,
                "elapsed_ms": elapsed_ms,
                "interval_count": interval_count,
                "full_diff_opened": full_diff_opened,
            },
        )

    # ------------------------------------------------------------------ the append

    def _append(
        self,
        *,
        table: str,
        record_type: str,
        chain_id: str,
        org_id: uuid.UUID,
        project_id: uuid.UUID,
        schema_version: int,
        caused_by: uuid.UUID | None,
        body: Body,
        columns: dict[str, object],
    ) -> Appended:
        if table not in CHAINED_TABLES:
            raise EvidenceError(f"{table!r} is not a chained evidence table")

        # Hash before projecting. ACS-1 refuses non-finite numbers outright, so a NaN
        # that would land in jsonb as a value no `=` can match is rejected here instead.
        body_sha256 = acs_sha256(record_type, body)

        with self._conn.cursor() as cur:
            # Transaction-scoped, so it is released by the same commit that makes the
            # row visible. The chain has exactly one writer and is written serially; a
            # concurrent writer would produce a fork, and a forked audit log in an audit
            # product is the failure the architecture exists to prevent.
            cur.execute("SELECT pg_advisory_xact_lock(%s)", (_lock_key(chain_id),))
            prev_sha256 = self._head(cur, table, chain_id)

            row_id = uuid.uuid4()
            sha256 = link_digest(
                chain_id=chain_id,
                record_type=record_type,
                prev_sha256=prev_sha256,
                body_sha256=body_sha256,
            )

            values: dict[str, object] = {
                "id": row_id,
                "org_id": org_id,
                "project_id": project_id,
                "schema_version": schema_version,
                "created_at": datetime.now(UTC),
                "caused_by": caused_by,
                "chain_id": chain_id,
                "body_sha256": body_sha256,
                "prev_sha256": prev_sha256,
                "sha256": sha256,
                "body": Jsonb(body),
                **columns,
            }
            names = sorted(values)
            statement = sql.SQL("INSERT INTO {}.{} ({}) VALUES ({})").format(
                sql.Identifier(SCHEMA),
                sql.Identifier(table),
                sql.SQL(", ").join(sql.Identifier(n) for n in names),
                sql.SQL(", ").join(sql.Placeholder() for _ in names),
            )
            cur.execute(statement, [values[n] for n in names])

        return Appended(
            id=row_id,
            chain_id=chain_id,
            prev_sha256=prev_sha256,
            body_sha256=body_sha256,
            sha256=sha256,
        )

    def _head(self, cur: psycopg.Cursor[Any], table: str, chain_id: str) -> str | None:
        """The digest no other row in this chain points back to.

        Derived from the links rather than from `created_at` or insertion order: a head
        chosen by timestamp is a head chosen by the clock, and two rows written in the
        same microsecond would pick one arbitrarily and fork the chain. More than one
        row here means the chain has already forked, which is a fact worth raising on
        every append rather than at audit time.
        """
        statement = sql.SQL(
            "SELECT sha256 FROM {schema}.{table} WHERE chain_id = %(chain)s "
            "AND sha256 NOT IN ("
            "  SELECT prev_sha256 FROM {schema}.{table} "
            "  WHERE chain_id = %(chain)s AND prev_sha256 IS NOT NULL"
            ")"
        ).format(schema=sql.Identifier(SCHEMA), table=sql.Identifier(table))
        cur.execute(statement, {"chain": chain_id})
        heads = [str(row[0]) for row in cur.fetchall()]
        if len(heads) > 1:
            raise ChainForked(f"{table} chain {chain_id!r} has {len(heads)} heads: {sorted(heads)}")
        return heads[0] if heads else None

    # ------------------------------------------------------------------ verify

    def verify_chain(self, *, table: str, chain_id: str) -> ChainReport:
        """Re-walk one chain and assert it is a single unbroken path.

        Three separate claims, and the third is the one usually skipped: every link's
        digest recomputes; there is exactly one genesis; and **the walk is total** —
        every row in the chain is visited exactly once. A check that verifies each link
        but never checks they form one path passes on a forked log, which is the shape
        the S7 restore drill has to defend against.
        """
        if table not in CHAINED_TABLES:
            raise EvidenceError(f"{table!r} is not a chained evidence table")

        record_type_column = "record_type" if table == "run_record" else None
        selected = ["sha256", "prev_sha256", "body_sha256"]
        if record_type_column:
            selected.append(record_type_column)

        statement = sql.SQL("SELECT {} FROM {}.{} WHERE chain_id = %s").format(
            sql.SQL(", ").join(sql.Identifier(c) for c in selected),
            sql.Identifier(SCHEMA),
            sql.Identifier(table),
        )
        with self._conn.cursor() as cur:
            cur.execute(statement, (chain_id,))
            rows = cur.fetchall()

        fixed_type = {
            "verdict": VERDICT_RECORD_TYPE,
            "operator_action": OPERATOR_ACTION_RECORD_TYPE,
        }.get(table)

        by_prev: dict[str | None, str] = {}
        content: dict[str, tuple[str | None, str, str]] = {}
        for row in rows:
            sha, prev, body_sha = str(row[0]), row[1], str(row[2])
            record_type = str(row[3]) if record_type_column else str(fixed_type)
            if prev in by_prev:
                raise ChainForked(f"{table} chain {chain_id!r} branches at {prev!r}")
            by_prev[prev] = sha
            content[sha] = (prev, body_sha, record_type)

        if not rows:
            return ChainReport(chain_id=chain_id, table=table, length=0, head_sha256=None, total=True)

        cursor_sha: str | None = by_prev.get(None)
        if cursor_sha is None:
            raise ChainForked(f"{table} chain {chain_id!r} has no genesis row")

        visited = 0
        head = cursor_sha
        while cursor_sha is not None:
            prev, body_sha, record_type = content[cursor_sha]
            expected = link_digest(
                chain_id=chain_id,
                record_type=record_type,
                prev_sha256=prev,
                body_sha256=body_sha,
            )
            if expected != cursor_sha:
                raise ChainBroken(
                    f"{table} chain {chain_id!r}: row {cursor_sha!r} recomputes to {expected!r}"
                )
            visited += 1
            head = cursor_sha
            cursor_sha = by_prev.get(cursor_sha)

        if visited != len(rows):
            # Reachability, not link integrity. A second genesis, or an island whose
            # predecessor was deleted, leaves rows the walk never touches while every
            # individual link still recomputes.
            raise ChainForked(
                f"{table} chain {chain_id!r}: walk visited {visited} of {len(rows)} rows"
            )

        return ChainReport(
            chain_id=chain_id, table=table, length=visited, head_sha256=head, total=True
        )
