"""Alembic environment for the `product` schema.

Agent-writable (docs/tier4/protected-paths-policy.md). A product migration cannot
alter an evidence table — not by policy, but because `alfred_migrator_product` holds
no privilege there.
"""

from __future__ import annotations

import os

from alembic import context
from sqlalchemy import engine_from_config, pool

SCHEMA = "product"
ROLE_ENV_VAR = "ALFRED_DB_URL_MIGRATOR_PRODUCT"
VERSION_TABLE = "alembic_version_product"


def _url() -> str:
    url = os.environ.get(ROLE_ENV_VAR)
    if not url:
        # Fail closed and name the variable. An Alembic environment that falls back to
        # a default URL applies migrations to whichever database happened to be
        # reachable, which is the one failure mode a migration must never have.
        raise RuntimeError(
            f"{ROLE_ENV_VAR} is not set. Each migration environment connects as its own "
            f"role; there is no default and no fallback."
        )
    return url


def run_migrations_offline() -> None:
    context.configure(
        url=_url(),
        target_metadata=None,
        literal_binds=True,
        include_schemas=True,
        version_table=VERSION_TABLE,
        version_table_schema="migration_meta",
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    config = context.config
    config.set_main_option("sqlalchemy.url", _url())
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=None,
            include_schemas=True,
            # Only this schema. `include_schemas=True` without a filter would let an
            # autogenerate pass emit DDL against schemas this role cannot touch — it
            # would fail at apply time, but only after producing a migration file that
            # looks legitimate.
            include_object=lambda obj, _name, _type, _reflected, _compare_to: (
                getattr(obj, "schema", None) in (SCHEMA, None)
            ),
            version_table=VERSION_TABLE,
            version_table_schema="migration_meta",
        )
        with context.begin_transaction():
            connection.exec_driver_sql(f"SET search_path TO {SCHEMA}")
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
