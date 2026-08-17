-- The only file in the repository that issues GRANT.
--
-- Applies migrations/roles/grants.yaml. The two must agree, and agreement is checked
-- by assertion against the cluster rather than by reading these two files against
-- each other: the property being asserted is about the cluster in front of you, not
-- about the file that was supposed to configure it.
--
-- Idempotent. Every schema starts with a REVOKE ALL so that re-applying converges
-- rather than accumulating — an extra grant left behind by an earlier version of this
-- file is exactly the defect the assertion exists to catch, and the fix should not
-- depend on noticing it.
--
-- Protected set (docs/tier4/protected-paths-policy.md). Agents may not write this file.

\set ON_ERROR_STOP on

BEGIN;

-- --------------------------------------------------------------------- converge
-- Revoke everything from every named role before granting anything. `alfred_agent`
-- appears here and never again: N1 is that it holds nothing, including schema USAGE.

DO $$
DECLARE
    r text;
    s text;
BEGIN
    FOREACH r IN ARRAY ARRAY[
        'alfred_harness', 'alfred_criterion', 'alfred_product',
        'alfred_operator', 'alfred_readmodel', 'alfred_agent',
        'alfred_migrator_product', 'alfred_migrator_control',
        'alfred_migrator_evidence', 'alfred_migrator_heldout',
        'alfred_bootstrap'
    ]
    LOOP
        FOREACH s IN ARRAY ARRAY['product', 'control', 'evidence', 'heldout', 'migration_meta']
        LOOP
            EXECUTE format('REVOKE ALL ON ALL TABLES IN SCHEMA %I FROM %I', s, r);
            EXECUTE format('REVOKE ALL ON ALL SEQUENCES IN SCHEMA %I FROM %I', s, r);
            EXECUTE format('REVOKE ALL ON SCHEMA %I FROM %I', s, r);
        END LOOP;
    END LOOP;
END
$$;

-- ------------------------------------------------------- owner schema privileges
-- Found on 2026-08-17 by running a migration for the first time, and it is the THIRD
-- omission of the same class as the two the first real apply exposed. The converge
-- block above revokes ALL on every schema from every named role, migrators included.
-- A schema owner holds USAGE and CREATE implicitly only while its ACL is null; the
-- revoke makes the ACL explicit and the implicit privileges go with it. So the owner of
-- `product` could not create a table in `product`:
--
--     permission denied for schema product
--     LINE 2: CREATE TABLE product.scenario (
--
-- `migration_meta` was already granted explicitly, on 2026-08-16, for exactly this
-- reason — and the fix was written as a special case about Alembic's version table
-- rather than as the general fact it is. The general fact is stated here instead:
-- **converging by REVOKE removes ownership's implicit grants, so every owner's schema
-- privileges must be re-issued explicitly.** Being explicit is also the better end
-- state: an implicit privilege is one no assertion can read.
--
-- Same shape as the other two: a privilege the matrix never mentioned, failing loud
-- rather than silent. A matrix reviewed only for what it grants too much cannot catch
-- a matrix that grants too little.

GRANT USAGE, CREATE ON SCHEMA product        TO alfred_migrator_product;
GRANT USAGE, CREATE ON SCHEMA control        TO alfred_migrator_control;
GRANT USAGE, CREATE ON SCHEMA evidence       TO alfred_migrator_evidence;
GRANT USAGE, CREATE ON SCHEMA heldout        TO alfred_migrator_heldout;
GRANT USAGE, CREATE ON SCHEMA migration_meta TO alfred_bootstrap;

-- --------------------------------------------------------------------- CONNECT
-- Found by running this file against a real cluster on 2026-08-16: the grant matrix in
-- docs/tier1/data-architecture.md never granted CONNECT on the database. N7 revokes it
-- from PUBLIC, correctly, and nothing granted it back — so the matrix applied literally
-- produced a cluster no role could reach. `FATAL: permission denied for database`.
--
-- Every role gets CONNECT, `alfred_agent` included and deliberately: the negative tests
-- must connect as it and be refused at the *schema*. A role that cannot connect proves
-- nothing about grants, and a test that reads "connection refused" as "access denied"
-- is the shape in which a security test most commonly lies — which is also why those
-- tests assert SQLSTATE 42501 specifically.
--
-- current_database() rather than a name: this file is applied to the throwaway test
-- cluster and to the live one, and hardcoding either would silently no-op on the other.

DO $$
BEGIN
    EXECUTE format(
        'GRANT CONNECT ON DATABASE %I TO %s',
        current_database(),
        'alfred_harness, alfred_criterion, alfred_product, alfred_operator, '
        'alfred_readmodel, alfred_agent, alfred_migrator_product, '
        'alfred_migrator_control, alfred_migrator_evidence, alfred_migrator_heldout, '
        'alfred_bootstrap'
    );
END
$$;

-- --------------------------------------------------------------------- USAGE
-- Without schema USAGE every table grant beneath is unreachable. Its absence is the
-- cheapest denial available, which is why the matrix lists it explicitly and why `—`
-- in that table means "no privilege of any kind, USAGE included".

GRANT USAGE ON SCHEMA product  TO alfred_harness, alfred_product, alfred_readmodel;
GRANT USAGE ON SCHEMA control  TO alfred_harness, alfred_criterion, alfred_operator, alfred_readmodel;
GRANT USAGE ON SCHEMA evidence TO alfred_harness, alfred_criterion, alfred_operator, alfred_readmodel;

-- alfred_criterion is the ONLY role with any privilege on heldout, anywhere.
GRANT USAGE ON SCHEMA heldout  TO alfred_criterion;

-- CREATE as well as USAGE, and this was the second omission the first real apply
-- exposed (2026-08-16): the matrix grants USAGE, SELECT, INSERT and UPDATE on
-- migration_meta, but Alembic *creates* its version table on the first upgrade, and
-- CREATE on the schema is a separate privilege. `permission denied for schema
-- migration_meta`. The schema is owned by alfred_bootstrap rather than by any migrator,
-- so no migrator gets it implicitly — which is the ownership separation working as
-- designed, not a reason to move ownership.
GRANT USAGE, CREATE ON SCHEMA migration_meta TO
    alfred_migrator_product, alfred_migrator_control,
    alfred_migrator_evidence, alfred_migrator_heldout;

-- --------------------------------------------------------------------- product
GRANT SELECT                         ON ALL TABLES IN SCHEMA product TO alfred_harness, alfred_readmodel;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA product TO alfred_product;

-- --------------------------------------------------------------------- control
-- Split: policy_* and threshold_* are the configuration PolicyEngine enforces. A role
-- that can UPDATE a protected-path row can unprotect a path without touching a single
-- protected file, so only the migrator writes them.

DO $$
DECLARE
    t text;
BEGIN
    FOR t IN
        SELECT tablename FROM pg_tables WHERE schemaname = 'control'
    LOOP
        IF t LIKE 'policy\_%' OR t LIKE 'threshold\_%' THEN
            EXECUTE format(
                'GRANT SELECT ON control.%I TO alfred_harness, alfred_criterion, alfred_operator, alfred_readmodel', t);
        ELSE
            EXECUTE format('GRANT SELECT, INSERT, UPDATE ON control.%I TO alfred_harness', t);
            EXECUTE format(
                'GRANT SELECT ON control.%I TO alfred_criterion, alfred_operator, alfred_readmodel', t);
        END IF;
    END LOOP;
END
$$;

-- --------------------------------------------------------------------- evidence
-- No UPDATE, no DELETE, no TRUNCATE is granted to anyone on anything in this schema.
-- That is not an omission; it is the schema's only real property (N5). The grant makes
-- the write impossible for every role that runs; the additive-only migration lint
-- catches the migration that would grant itself the ability by owning the table.

DO $$
DECLARE
    t text;
BEGIN
    FOR t IN
        SELECT tablename FROM pg_tables WHERE schemaname = 'evidence'
    LOOP
        IF t = 'verdict' THEN
            -- Sole author of verdicts is CriterionRunner (D5, D39). The harness may
            -- read them and may not write them, which is the separation D39 makes
            -- physical rather than a runtime field-name check.
            EXECUTE 'GRANT SELECT ON evidence.verdict TO alfred_harness, alfred_operator, alfred_readmodel';
            EXECUTE 'GRANT SELECT, INSERT ON evidence.verdict TO alfred_criterion';
        ELSIF t = 'operator_action' THEN
            -- D51. This INSERT is alfred_operator's only INSERT anywhere in the
            -- cluster, and N4 asserts that globally rather than locally.
            EXECUTE 'GRANT SELECT ON evidence.operator_action TO alfred_harness, alfred_readmodel';
            EXECUTE 'GRANT SELECT, INSERT ON evidence.operator_action TO alfred_operator';
        ELSE
            EXECUTE format(
                'GRANT SELECT, INSERT ON evidence.%I TO alfred_harness, alfred_criterion', t);
            EXECUTE format(
                'GRANT SELECT ON evidence.%I TO alfred_operator, alfred_readmodel', t);
        END IF;
    END LOOP;
END
$$;

-- --------------------------------------------------------------------- heldout
-- SELECT only, to one role. It cannot write the answers it reads.
GRANT SELECT ON ALL TABLES IN SCHEMA heldout TO alfred_criterion;

-- --------------------------------------------------------------------- meta
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA migration_meta TO
    alfred_migrator_product, alfred_migrator_control,
    alfred_migrator_evidence, alfred_migrator_heldout;

-- --------------------------------------------------------------------- defaults
-- N8. Without this the NEXT table created is granted correctly by accident or wrongly
-- by accident, and nobody looks again. Default privileges are per-(grantor, schema),
-- so they are set FOR the migrator that will create the objects.

ALTER DEFAULT PRIVILEGES FOR ROLE alfred_migrator_product IN SCHEMA product
    REVOKE ALL ON TABLES FROM PUBLIC;
ALTER DEFAULT PRIVILEGES FOR ROLE alfred_migrator_control IN SCHEMA control
    REVOKE ALL ON TABLES FROM PUBLIC;
ALTER DEFAULT PRIVILEGES FOR ROLE alfred_migrator_evidence IN SCHEMA evidence
    REVOKE ALL ON TABLES FROM PUBLIC;
ALTER DEFAULT PRIVILEGES FOR ROLE alfred_migrator_heldout IN SCHEMA heldout
    REVOKE ALL ON TABLES FROM PUBLIC;

ALTER DEFAULT PRIVILEGES FOR ROLE alfred_migrator_product IN SCHEMA product
    GRANT SELECT ON TABLES TO alfred_harness, alfred_readmodel;
ALTER DEFAULT PRIVILEGES FOR ROLE alfred_migrator_product IN SCHEMA product
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO alfred_product;

-- Deliberately NOT set as a default for `control`, `evidence` or `heldout`: those
-- schemas' grants are per-table (policy_* vs work tables; verdict vs operator_action
-- vs the rest), so a blanket default would grant the wrong thing to the next table.
-- Re-running this file after a migration is the mechanism, and the grant assertion is
-- what catches a migration whose author forgot.

-- Functions default to EXECUTE for PUBLIC at creation. Close it for every migrator.
DO $$
DECLARE
    m text;
    s text;
BEGIN
    FOREACH m IN ARRAY ARRAY[
        'alfred_migrator_product', 'alfred_migrator_control',
        'alfred_migrator_evidence', 'alfred_migrator_heldout', 'alfred_bootstrap'
    ]
    LOOP
        FOREACH s IN ARRAY ARRAY['product', 'control', 'evidence', 'heldout', 'migration_meta']
        LOOP
            EXECUTE format(
                'ALTER DEFAULT PRIVILEGES FOR ROLE %I IN SCHEMA %I REVOKE ALL ON FUNCTIONS FROM PUBLIC',
                m, s);
        END LOOP;
    END LOOP;
END
$$;

COMMIT;
