"""heldout: reference values and perturbations.

Revision ID: 0001_heldout_base
Revises:
Create Date: 2026-08-17
"""

# As in the evidence directory, the prose is in comments: the additive-only lint reads
# inside string literals, so a docstring explaining why nothing here may be rewritten
# in place would trip the guard it is explaining.
#
# ------------------------------------------------------- why this is a table at all
#
# Graph-level mechanisms do not isolate held-out data. `private` state schemas do not
# hide channels from stream, `output_keys` is a caller-side argument rather than a
# graph-level guarantee, the checkpointer persists everything, and a filter predicate on
# an index is not a boundary. So the isolation is a schema owned by a separate role,
# reachable by `alfred_criterion` and by nothing else, with SELECT and no write.
#
# `alfred_criterion` is held by CriterionRunner, which runs OUTSIDE the criterion
# environment (A1). The criterion environment holds no credential at all: agent-authored
# code executes there, and a heldout credential inside it would let the code under test
# select its own answers — the entire boundary, undone by a connection string.
#
# ------------------------------------------------ additive at the ROW level, too
#
# A corrected reference value is a new row under a new `value_version`, never a rewrite
# of the old one. Otherwise a verdict computed last week cannot be reproduced, and
# reproducibility is the product. `(measure_id, input_hash, value_version)` is unique;
# the current value is the greatest version, resolved by the reader.
#
# ---------------------------------------------------------- the provenance tier
#
# D49. Every schedulable task carries at least two grading points, at least one held
# out, and at least one level-fixing point from P1 through P3. P4 alone is invalid:
# invariance fixes a result's shape and never its level, so a uniformly scaled wrong
# answer satisfies it. The tier is a column because merge rate is reported stratified by
# it and because a set stratified without it cannot be stratified afterwards.
#
# `quantum` is here because CriMe rounds every measure output before returning it —
# 0.1 for WTTC, 0.01 for most, 0.0001 for BTN. A P3 resampled point counts only if it
# clears a whole bucket, which is a two-sided squeeze D49 never states. Recording the
# quantum beside the value is what makes that check possible at verdict time instead of
# being rediscovered per measure.

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_heldout_base"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SCHEMA = "heldout"


def upgrade() -> None:
    op.create_table(
        "reference_value",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("caused_by", sa.Uuid(), nullable=True),
        sa.Column("measure_id", sa.Text(), nullable=False),
        sa.Column("scenario_ref", sa.Text(), nullable=False),
        # What the value is a value OF. Content-addressed, so a perturbed slice and the
        # slice it was perturbed from are distinguishable without storing either.
        sa.Column("input_hash", sa.Text(), nullable=False),
        sa.Column("value_version", sa.Integer(), nullable=False),
        # Same tagged union as product.metric_result. A reference value of `+inf` is a
        # claim that the event provably never occurs, and it is a different claim from
        # "the oracle could not compute this" — collapsing them is how a degenerate case
        # becomes a passing test.
        sa.Column("value_kind", sa.Text(), nullable=False),
        sa.Column("value", sa.Double(), nullable=True),
        sa.Column("infinite_sign", sa.SmallInteger(), nullable=True),
        sa.Column("reason_name", sa.Text(), nullable=True),
        sa.Column("tolerance", sa.Double(), nullable=False),
        sa.Column("quantum", sa.Double(), nullable=False),
        # D49 tier, and the oracle that produced it. `oracle_commit_sha` is NOT NULL
        # because CriMe has zero tags and one branch, so a commit SHA is the only
        # available pin and a value recorded without one cannot be re-derived.
        sa.Column("provenance_tier", sa.Text(), nullable=False),
        sa.Column("oracle_name", sa.Text(), nullable=False),
        sa.Column("oracle_commit_sha", sa.Text(), nullable=False),
        # Non-null for P3: the seed that selected the resampled slice. Without it the
        # point is not reproducible, and a held-out point that cannot be reproduced
        # cannot be used to reverse a verdict later.
        sa.Column("resample_seed", sa.BigInteger(), nullable=True),
        sa.CheckConstraint(
            "value_kind IN ('defined', 'infinite', 'undefined')",
            name="ck_reference_value_kind",
        ),
        sa.CheckConstraint(
            "(value_kind = 'defined'   AND value IS NOT NULL AND infinite_sign IS NULL "
            "                          AND reason_name IS NULL) OR "
            "(value_kind = 'infinite'  AND value IS NULL AND infinite_sign IN (-1, 1) "
            "                          AND reason_name IS NULL) OR "
            "(value_kind = 'undefined' AND value IS NULL AND infinite_sign IS NULL "
            "                          AND reason_name IS NOT NULL)",
            name="ck_reference_value_arm_payload",
        ),
        sa.CheckConstraint("value IS NULL OR value = value", name="ck_reference_value_not_nan"),
        sa.CheckConstraint(
            "provenance_tier IN ('P1', 'P2', 'P3', 'P4', 'P5')",
            name="ck_reference_value_tier",
        ),
        sa.CheckConstraint(
            "(provenance_tier <> 'P3') OR (resample_seed IS NOT NULL)",
            name="ck_reference_value_p3_seed",
        ),
        # The tolerance must be able to resolve the oracle's own rounding. A tolerance
        # inside one quantum cannot distinguish a correct answer from the next
        # representable one, and LatJ is the worked example: pinned at 0.01, one quantum
        # above zero, where a stub returning 0.0 satisfies every resample below 0.005.
        sa.CheckConstraint("tolerance > 0 AND quantum > 0", name="ck_reference_value_positive"),
        sa.CheckConstraint("tolerance >= quantum", name="ck_reference_value_resolvable"),
        sa.UniqueConstraint(
            "org_id",
            "project_id",
            "measure_id",
            "input_hash",
            "value_version",
            name="uq_reference_value_version",
        ),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_reference_value_lookup",
        "reference_value",
        ["measure_id", "input_hash", "value_version"],
        schema=SCHEMA,
    )


def downgrade() -> None:
    raise RuntimeError(
        "Migrations in this directory are additive-only: a downgrade that removes a "
        "held-out reference value is the same defect wearing a reversible name."
    )
