"""product: scenarios, trajectories, metric results, result stamps.

Revision ID: 0001_product_base
Revises:
Create Date: 2026-08-17

The product schema is **agent-writable** (docs/tier1/data-architecture.md § Migration
layout), so ordinary schema evolution here is expected and this directory is not under
the additive-only lint. That is a deliberate asymmetry: a product table is a place a
number is stored, and an evidence table is a place a claim about a number is stored.

`result_stamp` freezes at the ten keys D55 fixes, `stamp_schema_version` included. The
column exists before the first stamp is written because adding it afterwards changes
the digest of every re-derived stamp with no marker separating old shape from new — a
legitimate schema change presenting as tampering, which is D27's own failure class
occurring inside D27's implementation.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_product_base"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SCHEMA = "product"


def _envelope() -> list[sa.Column[object]]:
    """The columns every table carries (docs/tier1/data-architecture.md § Every table).

    Tenancy is present with one tenant, which is I1's whole point: retrofitting it is a
    full migration plus a rewrite of every query and every access check, and it is the
    single most expensive omission on the invariant list.

    `id` is UUIDv7 and carries no server default. Postgres 17 has no `uuidv7()`; more
    importantly `src/domain/ids.py` makes both the timestamp and the random bytes
    injectable so a replayed run can pin them, and a server-side default would put a
    value into every record that no replay can reproduce.
    """
    return [
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("caused_by", sa.Uuid(), nullable=True),
    ]


def upgrade() -> None:
    op.create_table(
        "scenario",
        *_envelope(),
        # The dataset this came from, and its identifier *there*. CommonRoad scenario
        # IDs are the join back to the corpus, and a run that cannot name its input by
        # the corpus's own name is not reproducible by anyone but Alfred.
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("external_ref", sa.Text(), nullable=False),
        # Content-addressed (I3). Deduplication, integrity and run-to-run diffing all
        # follow from it, and retrofitting means re-ingesting everything.
        sa.Column("content_sha256", sa.Text(), nullable=False),
        sa.UniqueConstraint(
            "org_id", "project_id", "source", "external_ref", name="uq_scenario_ref"
        ),
        schema=SCHEMA,
    )

    op.create_table(
        "trajectory",
        *_envelope(),
        sa.Column("scenario_id", sa.Uuid(), nullable=False),
        sa.Column("track_ref", sa.Text(), nullable=False),
        sa.Column("content_sha256", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["scenario_id"], [f"{SCHEMA}.scenario.id"], name="fk_trajectory_scenario"
        ),
        schema=SCHEMA,
    )
    op.create_index("ix_trajectory_scenario", "trajectory", ["scenario_id"], schema=SCHEMA)

    op.create_table(
        "metric_result",
        *_envelope(),
        sa.Column("scenario_id", sa.Uuid(), nullable=False),
        sa.Column("metric_id", sa.Text(), nullable=False),
        sa.Column("metric_version", sa.Integer(), nullable=False),
        # ADR-0001's tagged union, stored as its three arms rather than as one float.
        # `defined` · `infinite` · `undefined` are three different claims, and a schema
        # that stores a nullable float collapses "provably never occurs" into "could not
        # be computed" — E1 into E7, silently, which is the representation defect
        # ADR-0001 exists to prevent.
        sa.Column("value_kind", sa.Text(), nullable=False),
        sa.Column("value", sa.Double(), nullable=True),
        sa.Column("infinite_sign", sa.SmallInteger(), nullable=True),
        # The reason *name* is what crosses a boundary and what gets hashed (ADR-0002);
        # the integer is a private in-memory encoding and deliberately does not appear.
        sa.Column("reason_name", sa.Text(), nullable=True),
        sa.Column("reason_codebook_version", sa.Integer(), nullable=False),
        # Aggregates report (value, n_defined, n_undefined) — a mean over a series that
        # does not say how much of the series was undefined is not a measurement.
        sa.Column("n_defined", sa.Integer(), nullable=True),
        sa.Column("n_undefined", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "value_kind IN ('defined', 'infinite', 'undefined')", name="ck_metric_result_kind"
        ),
        # The arms are mutually exclusive and each requires exactly its own payload.
        # Without this a row can claim `defined` and carry no value, and every reader
        # downstream has to decide what that means — which is how NaN gets reinvented.
        sa.CheckConstraint(
            "(value_kind = 'defined'   AND value IS NOT NULL AND infinite_sign IS NULL "
            "                          AND reason_name IS NULL) OR "
            "(value_kind = 'infinite'  AND value IS NULL AND infinite_sign IN (-1, 1) "
            "                          AND reason_name IS NULL) OR "
            "(value_kind = 'undefined' AND value IS NULL AND infinite_sign IS NULL "
            "                          AND reason_name IS NOT NULL)",
            name="ck_metric_result_arm_payload",
        ),
        # NaN is not representable anywhere in this product (edge-case specification
        # § Totality). Postgres accepts 'NaN'::double precision, so the ban is a
        # constraint rather than a convention.
        sa.CheckConstraint("value IS NULL OR value = value", name="ck_metric_result_not_nan"),
        sa.ForeignKeyConstraint(
            ["scenario_id"], [f"{SCHEMA}.scenario.id"], name="fk_metric_result_scenario"
        ),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_metric_result_metric", "metric_result", ["metric_id", "metric_version"], schema=SCHEMA
    )

    op.create_table(
        "result_stamp",
        *_envelope(),
        sa.Column("metric_result_id", sa.Uuid(), nullable=False),
        # The ten keys, frozen by D55 / ADR-0006. `stamp_schema_version` is in the
        # preimage and its name and shape are pinned for all time.
        sa.Column("stamp_schema_version", sa.Integer(), nullable=False),
        sa.Column("acs_version", sa.Integer(), nullable=False),
        sa.Column("metric_id", sa.Text(), nullable=False),
        sa.Column("metric_version", sa.Integer(), nullable=False),
        sa.Column("code_commit", sa.Text(), nullable=False),
        sa.Column("assumption_set", sa.Text(), nullable=False),
        sa.Column("input_hash", sa.Text(), nullable=False),
        sa.Column("tolerance", sa.Text(), nullable=False),
        sa.Column("reason_codebook_version", sa.Integer(), nullable=False),
        # `upstream` has no null arm. "Not applicable" is expressed as the positive
        # `corpus` value so the claim is checkable; `unknown` carries a mandatory
        # reason. A nullable column would make "nobody said" and "there is no
        # simulator" the same record.
        sa.Column("upstream", sa.Text(), nullable=False),
        sa.Column("upstream_reason", sa.Text(), nullable=True),
        # Declared by whoever ran the run. Alfred's container never observes the
        # simulator, so the stamp makes the declaration tamper-evident and binds it to
        # a number rather than to a file. It does not make the declaration true, and no
        # assessment conversation may say otherwise.
        sa.Column("upstream_tool_name", sa.Text(), nullable=True),
        sa.Column("upstream_tool_version", sa.Text(), nullable=True),
        sa.Column("upstream_config_digest", sa.Text(), nullable=True),
        # The ACS-1 digest over the ten keys. This is the number a third party
        # recomputes, which is the only reason the stamp is worth having.
        sa.Column("stamp_sha256", sa.Text(), nullable=False),
        sa.CheckConstraint(
            "upstream IN ('simulated', 'corpus', 'unknown')", name="ck_result_stamp_upstream"
        ),
        sa.CheckConstraint(
            "(upstream <> 'unknown') OR (upstream_reason IS NOT NULL)",
            name="ck_result_stamp_unknown_reason",
        ),
        sa.CheckConstraint(
            "(upstream <> 'simulated') OR "
            "(upstream_tool_name IS NOT NULL AND upstream_tool_version IS NOT NULL)",
            name="ck_result_stamp_simulated_toolchain",
        ),
        sa.ForeignKeyConstraint(
            ["metric_result_id"], [f"{SCHEMA}.metric_result.id"], name="fk_result_stamp_metric"
        ),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_result_stamp_recall",
        "result_stamp",
        ["metric_id", "metric_version", "created_at"],
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_index("ix_result_stamp_recall", "result_stamp", schema=SCHEMA)
    op.drop_table("result_stamp", schema=SCHEMA)
    op.drop_index("ix_metric_result_metric", "metric_result", schema=SCHEMA)
    op.drop_table("metric_result", schema=SCHEMA)
    op.drop_index("ix_trajectory_scenario", "trajectory", schema=SCHEMA)
    op.drop_table("trajectory", schema=SCHEMA)
    op.drop_table("scenario", schema=SCHEMA)
