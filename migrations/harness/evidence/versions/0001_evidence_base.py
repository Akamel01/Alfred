"""evidence: run records, verdicts, operator actions, artifacts, defect escapes.

Revision ID: 0001_evidence_base
Revises:
Create Date: 2026-08-17
"""

# Prose lives in comments rather than in the docstring on purpose. The additive-only
# lint (scripts/lint_migrations.py) reads inside every string literal for destructive
# SQL keywords, case-insensitively, and a docstring explaining why this schema grants
# no in-place rewrite would trip its own guard. Comments are not string literals, so
# this is where the reasoning goes. That the guard is awkward to write around is the
# guard working: it has no exception list.
#
# ------------------------------------------------------------------ what is here
#
# `run_record` is specified column-for-column in docs/tier1/data-architecture.md. The
# other four are not, and the shape they get is the one that document prescribes for
# the stream generally: envelope columns, chain columns, and the record body as ACS-1
# bytes plus a jsonb projection. The rule, quoted: the stream is a field set, the store
# is a schema, and the store never re-declares a stream field.
#
# That is not laziness about `verdict` and `operator_action`. One column per field would
# make every field addition an additive migration in the one schema whose migrations are
# additive-only, and Run Instrumentation and this document would drift into disagreeing
# about the same field. `operator_action` carries `field_set_version` because Mission
# Control owns those fields and versions them.
#
# `verdict` and `held_out_result` ARE columns, because the three-valued vocabulary is
# frozen in docs/tier1/failure-semantics.md and every autonomy gate reads it. A verdict
# buried in jsonb is a verdict no constraint can close the vocabulary of.
#
# Golden-set and failure-taxonomy tables are absent: Phase 2's, and marked provisional.
# `defect_escape` is here because D56 starts it at the first merge, and because nothing
# in a merged history distinguishes a clean merge from one nobody has looked at yet.
#
# --------------------------------------------------------- the two unique constraints
#
# NOT from the document, and flagged as a design decision taken here. Each chain gets
# `UNIQUE (chain_id, sha256)` and `UNIQUE NULLS NOT DISTINCT (chain_id, prev_sha256)`.
# The second is the one that matters: two rows cannot share a predecessor, so the chain
# physically cannot fork. S7's restore drill has to assert the walk is total — one head,
# no forks — because a check that verifies each link but never checks they form a single
# path passes on a forked audit log. This makes the fork impossible at insert time rather
# than detectable at audit time, and it costs one index.
#
# `NULLS NOT DISTINCT` is load-bearing and was added on 2026-08-17 after the store's own
# suite demonstrated the hole. A plain UNIQUE treats every NULL as distinct, so it refuses
# a second row on an existing predecessor and cheerfully accepts a **second genesis row** —
# `prev_sha256 IS NULL` twice — which is a fork at the one position where each individual
# link still recomputes perfectly. The walk's totality check catches it, but catching is
# not preventing, and the whole point of putting the constraint in the cluster was that a
# writer which never runs the Python check cannot produce one. Same class as the three
# grant omissions: a rule stated for the general case with the boundary case unexamined.

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_evidence_base"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SCHEMA = "evidence"


def _envelope() -> list[sa.Column[object]]:
    return [
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        # I10. "Why did this happen" is unanswerable if the link was never stored.
        sa.Column("caused_by", sa.Uuid(), nullable=True),
    ]


def _chain() -> list[sa.Column[object]]:
    # The chain is over the canonical ACS-1 bytes, never over the jsonb projection.
    # `prev_sha256` is nullable at exactly one row per chain: the genesis row.
    return [
        sa.Column("chain_id", sa.Text(), nullable=False),
        sa.Column("body_sha256", sa.Text(), nullable=False),
        sa.Column("prev_sha256", sa.Text(), nullable=True),
        sa.Column("sha256", sa.Text(), nullable=False),
    ]


def _chain_constraints(table: str) -> list[sa.SchemaItem]:
    return [
        sa.UniqueConstraint("chain_id", "sha256", name=f"uq_{table}_chain_sha"),
        # No forks, enforced by the cluster rather than by the auditor. NULLS NOT
        # DISTINCT so that the genesis position is covered too: without it a second row
        # with a NULL predecessor is accepted and the chain forks at row one.
        sa.UniqueConstraint(
            "chain_id",
            "prev_sha256",
            name=f"uq_{table}_chain_prev",
            postgresql_nulls_not_distinct=True,
        ),
    ]


def upgrade() -> None:
    # -------------------------------------------------------------- run_record
    op.create_table(
        "run_record",
        *_envelope(),
        *_chain(),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        # Nullable exactly where the run-record stream says it is.
        sa.Column("attempt_id", sa.Uuid(), nullable=True),
        # Also the ACS-1 domain separator, which is why it is indexed and NOT NULL.
        sa.Column("record_type", sa.Text(), nullable=False),
        sa.Column("emitted_at", sa.DateTime(timezone=True), nullable=False),
        # Durations come from the monotonic clock only. A duration computed from two
        # wall-clock stamps is a duration that a clock adjustment can make negative.
        sa.Column("monotonic_ns", sa.BigInteger(), nullable=False),
        # Queried; never the hash input.
        sa.Column("body", postgresql.JSONB(), nullable=False),
        *_chain_constraints("run_record"),
        schema=SCHEMA,
    )
    op.create_index("ix_run_record_task", "run_record", ["task_id", "id"], schema=SCHEMA)
    op.create_index("ix_run_record_type", "run_record", ["record_type"], schema=SCHEMA)

    # ----------------------------------------------------------------- verdict
    # Sole author is CriterionRunner (D5, D39), and that is a grant, not a check in
    # this file. What this file closes is the vocabulary.
    op.create_table(
        "verdict",
        *_envelope(),
        *_chain(),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("attempt_id", sa.Uuid(), nullable=False),
        sa.Column("criterion_ref", sa.Text(), nullable=False),
        sa.Column("criterion_version", sa.Integer(), nullable=False),
        sa.Column("verdict", sa.Text(), nullable=False),
        # Three-valued on both halves. `indeterminate` is excluded from merge rate on
        # both sides and reported separately as harness health, so it must be
        # representable rather than folded into `fail`.
        sa.Column("held_out_result", sa.Text(), nullable=True),
        sa.Column("held_out_provenance_tier", sa.Text(), nullable=True),
        # Present so the null-agent floor test can assert a number and not only a
        # verdict: a do-nothing run must score zero AND read `fail`.
        sa.Column("score", sa.Double(), nullable=True),
        # Why it is `indeterminate`. NOT NULL under that verdict, because an
        # `indeterminate` with no stated cause is indistinguishable from a bug in the
        # thing that produced it, and it is the value that leaves the merge-rate
        # denominator.
        sa.Column("indeterminate_reason", sa.Text(), nullable=True),
        sa.Column("body", postgresql.JSONB(), nullable=False),
        sa.CheckConstraint(
            "verdict IN ('pass', 'fail', 'indeterminate')", name="ck_verdict_vocabulary"
        ),
        sa.CheckConstraint(
            "held_out_result IS NULL OR held_out_result IN ('pass', 'fail', 'indeterminate')",
            name="ck_verdict_heldout_vocabulary",
        ),
        sa.CheckConstraint(
            "held_out_provenance_tier IS NULL OR "
            "held_out_provenance_tier IN ('P1', 'P2', 'P3', 'P4', 'P5')",
            name="ck_verdict_provenance_tier",
        ),
        sa.CheckConstraint(
            "(verdict <> 'indeterminate') OR (indeterminate_reason IS NOT NULL)",
            name="ck_verdict_indeterminate_reason",
        ),
        sa.CheckConstraint("score IS NULL OR score = score", name="ck_verdict_score_not_nan"),
        *_chain_constraints("verdict"),
        schema=SCHEMA,
    )
    op.create_index("ix_verdict_task", "verdict", ["task_id", "attempt_id"], schema=SCHEMA)

    # --------------------------------------------------------- operator_action
    # D51. The one actor who can override every gate becomes an audited writer.
    op.create_table(
        "operator_action",
        *_envelope(),
        *_chain(),
        sa.Column("task_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.Text(), nullable=False),
        # Distinguished from a harness action three ways: the ACS-1 domain separator on
        # `record_type`, the writing process and its role, and these two columns.
        sa.Column("actor_kind", sa.Text(), nullable=False),
        sa.Column("actor_id", sa.Text(), nullable=False),
        # Mission Control owns the field set and versions it.
        sa.Column("field_set_version", sa.Integer(), nullable=False),
        # Emitted as a bracket, never a point estimate. Intervals are not extrapolated,
        # so `attended_ms` undercounts by up to one heartbeat per interval — and
        # undercount is the dangerous direction, because it tells the capacity gate
        # there is more capacity than there is. `null` rather than 0 when the instrument
        # did not run: a zero is a measurement and a null is the absence of one.
        sa.Column("attended_ms", sa.BigInteger(), nullable=True),
        sa.Column("attended_ms_upper", sa.BigInteger(), nullable=True),
        sa.Column("elapsed_ms", sa.BigInteger(), nullable=True),
        sa.Column("interval_count", sa.Integer(), nullable=True),
        sa.Column("full_diff_opened", sa.Boolean(), nullable=True),
        sa.Column("body", postgresql.JSONB(), nullable=False),
        sa.CheckConstraint(
            "action IN ('approve', 'decline', 'request_changes', 'waive', "
            "'escalate_to_self', 'reopen', 'grant_autonomy', 'revoke_autonomy', 'drain')",
            name="ck_operator_action_vocabulary",
        ),
        sa.CheckConstraint("actor_kind IN ('operator')", name="ck_operator_action_actor_kind"),
        # The bracket is a bracket. An upper bound below the point estimate is an
        # instrument fault, and it would bias the capacity ledger in the direction that
        # flatters it.
        sa.CheckConstraint(
            "attended_ms IS NULL OR attended_ms_upper IS NULL OR attended_ms_upper >= attended_ms",
            name="ck_operator_action_bracket_ordered",
        ),
        sa.CheckConstraint(
            "(attended_ms IS NULL) = (attended_ms_upper IS NULL)",
            name="ck_operator_action_bracket_paired",
        ),
        *_chain_constraints("operator_action"),
        schema=SCHEMA,
    )
    op.create_index("ix_operator_action_task", "operator_action", ["task_id"], schema=SCHEMA)

    # ---------------------------------------------------------------- artifact
    # Content-addressed blob storage with lineage links (I3). Artifacts are hashed as
    # stored bytes, so no canonicalization question arises here — that is the other
    # hash, over ACS-1, and ADR-0003 treats them as two different problems.
    op.create_table(
        "artifact",
        *_envelope(),
        sa.Column("content_sha256", sa.Text(), nullable=False),
        sa.Column("media_type", sa.Text(), nullable=False),
        sa.Column("byte_length", sa.BigInteger(), nullable=False),
        sa.Column("storage_ref", sa.Text(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=True),
        sa.Column("attempt_id", sa.Uuid(), nullable=True),
        sa.Column("derived_from", sa.Uuid(), nullable=True),
        sa.CheckConstraint("byte_length >= 0", name="ck_artifact_byte_length"),
        sa.UniqueConstraint("org_id", "project_id", "content_sha256", name="uq_artifact_content"),
        schema=SCHEMA,
    )
    op.create_index("ix_artifact_task", "artifact", ["task_id"], schema=SCHEMA)

    # ----------------------------------------------------------- defect_escape
    # Written at DISCOVERY time, and unreconstructable afterwards. Starts empty, and an
    # empty table is not a zero rate: the gate reads merged tasks under observation for
    # a stated window as its denominator, never the count.
    op.create_table(
        "defect_escape",
        *_envelope(),
        sa.Column("introducing_task_id", sa.Uuid(), nullable=False),
        sa.Column("introducing_fingerprint_sha256", sa.Text(), nullable=False),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("discovery_source", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=False),
        sa.Column("evidence_ref", sa.Uuid(), nullable=True),
        # An escape attributed by judgment is not the same measurement as one attributed
        # by bisect, and a rate that mixes them without saying so is not a rate.
        sa.Column("attribution_basis", sa.Text(), nullable=False),
        sa.CheckConstraint(
            "discovery_source IN ('criterion', 'downstream_task', 'operator', 'customer')",
            name="ck_defect_escape_source",
        ),
        sa.CheckConstraint(
            "attribution_basis IN ('bisect', 'criterion_replay', 'operator_judgment')",
            name="ck_defect_escape_attribution",
        ),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_defect_escape_task", "defect_escape", ["introducing_task_id"], schema=SCHEMA
    )
    op.create_index(
        "ix_defect_escape_fingerprint",
        "defect_escape",
        ["introducing_fingerprint_sha256"],
        schema=SCHEMA,
    )


def downgrade() -> None:
    raise RuntimeError(
        "Migrations in this directory are additive-only: a downgrade that removes an "
        "evidence table is the same defect wearing a reversible name."
    )
