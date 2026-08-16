-- Roles and schemas. Idempotent and ordered; applied by alfred_bootstrap.
--
-- NOT Alembic. Roles and grants are cluster-level rather than versioned schema, and
-- the correct form is a small script that can be re-applied and compared against
-- migrations/roles/grants.yaml.
--
-- Protected set (docs/tier4/protected-paths-policy.md). Agents may not write this file.
--
-- Passwords are NOT set here. They are injected per-role at apply time from the
-- secret store (docs/tier4/secrets-management-policy.md); a password literal in a
-- committed file is a credential in version control regardless of how the role is
-- later restricted.

\set ON_ERROR_STOP on

BEGIN;

-- --------------------------------------------------------------------- roles
-- NOLOGIN is never used: every role here is a connection identity. `alfred_agent`
-- has LOGIN precisely so the negative tests can connect as it and be refused at the
-- schema — a role that cannot connect proves nothing about grants.

DO $$
DECLARE
    r text;
BEGIN
    FOREACH r IN ARRAY ARRAY[
        'alfred_bootstrap',
        'alfred_migrator_product',
        'alfred_migrator_control',
        'alfred_migrator_evidence',
        'alfred_migrator_heldout',
        'alfred_harness',
        'alfred_criterion',
        'alfred_product',
        'alfred_operator',
        'alfred_readmodel',
        'alfred_agent'
    ]
    LOOP
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = r) THEN
            EXECUTE format('CREATE ROLE %I LOGIN', r);
        END IF;
        -- Re-asserted on every apply, not only at creation: N9. These attributes can
        -- be added later by anyone with CREATEROLE, and BYPASSRLS is the one that
        -- reads as harmless.
        EXECUTE format(
            'ALTER ROLE %I NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS',
            r
        );
    END LOOP;
END
$$;

-- --------------------------------------------------------------------- schemas
-- Ownership is separated from use. The migrator owns; no running service does.
-- An owner can ALTER, UPDATE and DROP regardless of grants, so the append-only
-- property of `evidence` rests on this line rather than on the grant matrix (N6).

CREATE SCHEMA IF NOT EXISTS product        AUTHORIZATION alfred_migrator_product;
CREATE SCHEMA IF NOT EXISTS control        AUTHORIZATION alfred_migrator_control;
CREATE SCHEMA IF NOT EXISTS evidence       AUTHORIZATION alfred_migrator_evidence;
CREATE SCHEMA IF NOT EXISTS heldout        AUTHORIZATION alfred_migrator_heldout;

-- Alembic UPDATEs its version table on every migration. Placing those tables in
-- `evidence` would require an UPDATE grant in the one schema whose entire property
-- is that no UPDATE grant exists. Bookkeeping about migrations is not evidence.
CREATE SCHEMA IF NOT EXISTS migration_meta AUTHORIZATION alfred_bootstrap;

-- --------------------------------------------------------------------- PUBLIC
-- N7, and this is the row most likely to be true right now on any cluster nobody
-- has checked: Postgres grants several of these by default. Revoked before any
-- grant is issued, so no window exists in which a new schema is world-readable.

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA product, control, evidence, heldout, migration_meta FROM PUBLIC;
REVOKE ALL ON DATABASE :"DBNAME" FROM PUBLIC;

-- Functions are granted EXECUTE to PUBLIC by default at creation time. Revoking
-- existing ones is not enough; the default itself is closed in 002_grants.sql.
DO $$
DECLARE
    s text;
BEGIN
    FOREACH s IN ARRAY ARRAY['product', 'control', 'evidence', 'heldout', 'migration_meta']
    LOOP
        EXECUTE format('REVOKE ALL ON ALL FUNCTIONS IN SCHEMA %I FROM PUBLIC', s);
        EXECUTE format('REVOKE ALL ON ALL ROUTINES IN SCHEMA %I FROM PUBLIC', s);
    END LOOP;
END
$$;

COMMIT;
