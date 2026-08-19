"""control: the run-fingerprint fields the register had no column for.

Revision ID: 0002_fingerprint_run_fields
Revises: 0001_control_base
Create Date: 2026-08-19

`control.fingerprint` stores D19's and D40's components in the clear so tiered
requalification can answer *which component moved*. Eight fields the run is actually
measured on had no column, and their absence was not cosmetic: two containment assertions
could not be written at all without a declared value to compare against. C4 compares the
runtime image digest and C11 the serving lane, and `runtime_image_digest` appeared nowhere
in the repository — not in a column, not in a constant, not in a type. ADR-0020.

`control` is configuration rather than evidence, so it is deliberately outside
`scripts/lint_migrations.py`'s additive-only guard and ordinary column addition is
permitted here. The columns are `NOT NULL` with no server default: the table starts empty
in every environment, and a nullable fingerprint field is a field an assertion cannot be
written against — which is the state this migration exists to end.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_fingerprint_run_fields"
down_revision: str | None = "0001_control_base"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SCHEMA = "control"

# Each column and the change it exists to detect. Grouped as the record groups them, so a
# reader can match this table to `harness/fingerprint/record.py` without inference.
def _columns() -> tuple[sa.Column[object], ...]:
    """Built fresh on each call. A module-level `sa.Column` is a single object that
    `add_column` binds to a table, so reusing one across two runs in one process fails
    in a way that reads as a schema problem rather than an aliasing one."""
    return (
        # The lane, beside `loaded_context_length` and `parallel_slots` which 0001 already
        # carries. `model_id` is what the server is asked for; `model_version` is what Alfred
        # calls the weights. They are not the same string and neither substitutes.
        sa.Column("model_id", sa.Text(), nullable=False),
        sa.Column("quantization", sa.Text(), nullable=False),
        # The worker's contribution. Every one is a field something else can change without
        # notice, which is the whole reason it is a fingerprint field rather than a note.
        sa.Column("executor_name", sa.Text(), nullable=False),
        # The canonical repository path redirects and the destination is what gets pinned.
        sa.Column("executor_commit_sha", sa.Text(), nullable=False),
        # Harness identity alone moves the same model by percentage points.
        sa.Column("adaptor_version", sa.Text(), nullable=False),
        # C4's subject. Pinned by digest, mirrored locally, pulled outside the sandbox netns.
        sa.Column("runtime_image_digest", sa.Text(), nullable=False),
        # A run measured under one denylist is not comparable to one measured under a weaker
        # one, and the denylist is policy configuration that can be edited between runs.
        sa.Column("oracle_denylist_version", sa.Text(), nullable=False),
        # Reordering the seed invalidates every cached prefix and re-pays full prefill.
        sa.Column("seed_layer_order_sha256", sa.Text(), nullable=False),
    )


def upgrade() -> None:
    for column in _columns():
        op.add_column("fingerprint", column, schema=SCHEMA)


def downgrade() -> None:
    raise NotImplementedError(
        "control.fingerprint is append-only in practice: a fingerprint row is what a "
        "measurement was taken on, and dropping a column rewrites what past rows claim. "
        "Roll forward."
    )
