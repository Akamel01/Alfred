"""Dump a chain as raw columns, so something else can check it.

**This module computes nothing.** It selects stored columns and writes them out. That
restraint is the point: the export exists to be read by the JavaScript re-walk, and any
digest, ordering or derivation performed here would be a Python claim the independent
implementation then re-checks against itself. The exporter is allowed to know *which
columns exist*; it is not allowed to know what they should contain.

For the same reason the export does **not** carry the domain separator for `verdict` and
`operator_action`. Those tables have no `record_type` column — their record type is the
table — and if Python wrote it into the file, the JavaScript walker would be recomputing
digests from a separator Python chose. The walker holds its own table-to-separator map
instead, duplicated deliberately, exactly as `acs1.mjs` duplicates the encoder. A
disagreement between the two maps makes every digest mismatch, which is the correct and
loud failure.

Ordering is by `id` and is presentational only. The walk reconstructs order from the
links, because an export ordered by insertion and a chain ordered by its own hashes are
two different claims and only the second is the audit object.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

import psycopg
from psycopg import sql

from harness.evidence.store import CHAINED_TABLES, SCHEMA

# Raw columns only. `body` is excluded: the chain is over `body_sha256`, and shipping the
# projection would invite a checker to hash the jsonb — which is queried, never the hash
# input, and whose key order Postgres does not preserve.
CHAIN_COLUMNS: Final = ("id", "chain_id", "prev_sha256", "body_sha256", "sha256")

EXPORT_FORMAT_VERSION: Final = 1


class ExportError(RuntimeError):
    """The chain could not be exported."""


def export_chain(
    conn: psycopg.Connection[Any], *, table: str, chain_id: str, destination: Path
) -> int:
    """Write every row of one chain to `destination`. Returns the row count."""
    if table not in CHAINED_TABLES:
        raise ExportError(f"{table!r} is not a chained evidence table")

    columns = [*CHAIN_COLUMNS]
    if table == "run_record":
        # A real column here, so it is exported. Elsewhere it is the table's identity and
        # the walker supplies it.
        columns.append("record_type")

    statement = sql.SQL("SELECT {} FROM {}.{} WHERE chain_id = %s ORDER BY id").format(
        sql.SQL(", ").join(sql.Identifier(c) for c in columns),
        sql.Identifier(SCHEMA),
        sql.Identifier(table),
    )
    with conn.cursor() as cur:
        cur.execute(statement, (chain_id,))
        rows = cur.fetchall()

    payload = {
        "export_format_version": EXPORT_FORMAT_VERSION,
        "table": table,
        "chain_id": chain_id,
        "exported_at": datetime.now(UTC).isoformat(),
        "columns": columns,
        "rows": [
            {name: (str(value) if isinstance(value, uuid.UUID) else value)
             for name, value in zip(columns, row, strict=True)}
            for row in rows
        ],
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return len(rows)
