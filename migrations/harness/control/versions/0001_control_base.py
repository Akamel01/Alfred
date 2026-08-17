"""control: work items, fingerprints, protected paths, thresholds.

Revision ID: 0001_control_base
Revises:
Create Date: 2026-08-17

`control` splits in two for grant purposes and the split is visible in the table names:
`policy_*` and `threshold_*` are the configuration `PolicyEngine` enforces, and only
their migrator writes them. A role that can UPDATE a protected-path row can unprotect a
path without touching a single protected file, which is why the boundary is a grant and
not a review rule. The prefixes are therefore load-bearing rather than cosmetic —
`002_grants.sql` matches on them.

Four of `control.work`'s columns are set **at dispatch** and cannot be corrected later:
the evidence they join to permits no UPDATE, so a task dispatched without them is
permanently unstratifiable and Phase 1's exit requires merge rate stratified by
provenance tier. That is the entire reason this table exists before Phase 1 needs it.

Golden-set and failure-taxonomy tables are deliberately absent. They are Phase 2's, and
`data-architecture.md` marks that whole section provisional: a table designed before the
failures it must group is a table designed to flatter them. What is created here is the
part that cannot be applied retroactively.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_control_base"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SCHEMA = "control"


def _envelope() -> list[sa.Column[object]]:
    return [
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("caused_by", sa.Uuid(), nullable=True),
    ]


def upgrade() -> None:
    # ------------------------------------------------------------------ work
    op.create_table(
        "work",
        *_envelope(),
        # The four set at dispatch. All NOT NULL, which is the enforcement: a work item
        # that cannot say which capability, domain and scenario it exercises cannot be
        # inserted, rather than being inserted and discovered unstratifiable in Phase 2.
        sa.Column("capability_id", sa.Text(), nullable=False),
        sa.Column("measure_domain", sa.Text(), nullable=False),
        sa.Column("scenario_ref", sa.Text(), nullable=False),
        # Set at authoring time, on the criterion rather than on the run. P1…P5 per D49.
        sa.Column("held_out_provenance_tier", sa.Text(), nullable=False),
        sa.Column("criterion_ref", sa.Text(), nullable=False),
        sa.Column("criterion_version", sa.Integer(), nullable=False),
        # The caps the attempt inherits (D23). A task with no retry budget is not
        # schedulable: merge rate is measured per task *after* a bounded retry budget,
        # and an unbounded one turns acceptance into a search over the visible criteria.
        sa.Column("retry_budget", sa.Integer(), nullable=False),
        sa.Column("turn_budget", sa.Integer(), nullable=False),
        sa.Column("wallclock_budget_ms", sa.BigInteger(), nullable=False),
        sa.Column("state", sa.Text(), nullable=False),
        # I5. Retries are inevitable from Phase 3 and without a key they corrupt.
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        sa.CheckConstraint(
            "held_out_provenance_tier IN ('P1', 'P2', 'P3', 'P4', 'P5')",
            name="ck_work_provenance_tier",
        ),
        # The vocabulary is closed here rather than in code because the dispatcher and
        # the read model are separate processes under separate roles, and a state name
        # agreed only in Python is agreed only inside one of them.
        sa.CheckConstraint(
            "state IN ('queued', 'claimed', 'running', 'awaiting_review', "
            "'merged', 'declined', 'escalated', 'abandoned')",
            name="ck_work_state",
        ),
        sa.CheckConstraint("retry_budget >= 0", name="ck_work_retry_budget_nonneg"),
        sa.UniqueConstraint("org_id", "project_id", "idempotency_key", name="uq_work_idempotency"),
        schema=SCHEMA,
    )
    # The dispatch query is `SELECT ... FOR UPDATE SKIP LOCKED` ordered by id, which is
    # UUIDv7 and therefore time-sortable — no separate ordering column is needed (I4).
    op.create_index("ix_work_queue", "work", ["state", "id"], schema=SCHEMA)
    op.create_index("ix_work_capability", "work", ["capability_id"], schema=SCHEMA)

    # ----------------------------------------------------------- fingerprint
    # `attempt_start.fingerprint_sha256` is a hash, and a hash cannot answer *what
    # changed*. D19's tiered requalification is a decision about which component moved,
    # so the components are stored in the clear beside the hash.
    op.create_table(
        "fingerprint",
        *_envelope(),
        sa.Column("fingerprint_sha256", sa.Text(), nullable=False),
        # D19.
        sa.Column("capability_id", sa.Text(), nullable=False),
        sa.Column("model_version", sa.Text(), nullable=False),
        sa.Column("prompt_version", sa.Text(), nullable=False),
        sa.Column("tool_version", sa.Text(), nullable=False),
        sa.Column("context_strategy_version", sa.Text(), nullable=False),
        # D40. The quantization *artifact* hash, never the quant name: imatrix variants
        # share names, and a 4-bit and a 6-bit quant of the same weights are different
        # models for grant purposes.
        sa.Column("quant_artifact_sha256", sa.Text(), nullable=False),
        sa.Column("inference_runtime_version", sa.Text(), nullable=False),
        sa.Column("server_version", sa.Text(), nullable=False),
        sa.Column("orchestrator_sha", sa.Text(), nullable=False),
        sa.Column("harness_identity", sa.Text(), nullable=False),
        # Two fields the serving stack sets by default and nothing observed until it
        # cost a measurement. `loaded_context_length`: the lane silently auto-unloaded
        # and JIT-reloaded at the default, turning 10/10 tool calling into 0/10 with no
        # error anywhere. `parallel_slots`: cross-request prefix reuse is 140x at 1 and
        # 1.0x above 1, and the two lanes are indistinguishable on record without it.
        sa.Column("loaded_context_length", sa.Integer(), nullable=False),
        sa.Column("parallel_slots", sa.Integer(), nullable=False),
        sa.Column("lockfile_sha256", sa.Text(), nullable=False),
        sa.Column("tool_description_sha256", sa.Text(), nullable=False),
        sa.Column("criterion_set_version", sa.Integer(), nullable=False),
        sa.Column("criterion_set_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("fingerprint_sha256", name="uq_fingerprint_sha256"),
        sa.CheckConstraint("parallel_slots >= 1", name="ck_fingerprint_parallel_slots"),
        schema=SCHEMA,
    )

    # ------------------------------------------- protected paths, configuration
    op.create_table(
        "policy_protected_path",
        *_envelope(),
        sa.Column("policy_set_version", sa.Integer(), nullable=False),
        sa.Column("pattern", sa.Text(), nullable=False),
        # `deny` is the only disposition today. It is an enumerated column rather than a
        # boolean so that adding a disposition later is an additive change and so that a
        # row cannot be neutralized by flipping a flag whose name reads as metadata.
        sa.Column("disposition", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.CheckConstraint("disposition IN ('deny')", name="ck_protected_path_disposition"),
        sa.UniqueConstraint(
            "org_id", "project_id", "policy_set_version", "pattern", name="uq_protected_path"
        ),
        schema=SCHEMA,
    )

    # ---------------------------------------------- thresholds, configuration
    # D34: thresholds are declared, cited, versioned configuration inputs — never
    # agent-authored and never presented as facts. `citation` is NOT NULL because
    # threshold *selection* is a contested judgment with no standard, and an uncited
    # threshold is Alfred's own opinion wearing a configuration file's clothes.
    op.create_table(
        "threshold_value",
        *_envelope(),
        sa.Column("threshold_set_version", sa.Integer(), nullable=False),
        sa.Column("threshold_id", sa.Text(), nullable=False),
        sa.Column("metric_id", sa.Text(), nullable=False),
        sa.Column("value", sa.Double(), nullable=False),
        sa.Column("units", sa.Text(), nullable=False),
        sa.Column("citation", sa.Text(), nullable=False),
        sa.Column("validity_envelope", sa.Text(), nullable=False),
        sa.CheckConstraint("value = value", name="ck_threshold_not_nan"),
        sa.UniqueConstraint(
            "org_id", "project_id", "threshold_set_version", "threshold_id", name="uq_threshold"
        ),
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_table("threshold_value", schema=SCHEMA)
    op.drop_table("policy_protected_path", schema=SCHEMA)
    op.drop_table("fingerprint", schema=SCHEMA)
    op.drop_index("ix_work_capability", "work", schema=SCHEMA)
    op.drop_index("ix_work_queue", "work", schema=SCHEMA)
    op.drop_table("work", schema=SCHEMA)
