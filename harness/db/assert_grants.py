"""Assert the cluster's grant matrix **equals** `migrations/roles/grants.yaml`.

Set equality, never subset. A subset check passes on every extra grant, and an extra
grant is the only kind of grant defect that matters: it fails in the safe-looking
direction, because everything works. Both directions are therefore reported, and
`EXTRA` is listed first because it is the dangerous one.

**What set equality buys, stated once.** N1, N2, N3, N4, N5, N7 and N8 in
`docs/tier1/data-architecture.md § Grants that must not exist` need no individual check
here: a grant that must not exist is a grant that is not declared, and an undeclared
grant is `EXTRA`. That is the whole reason the assertion is written as an equality
rather than as ten predicates — ten predicates catch the ten things somebody thought
of. N6, N9 and N10 are not grants and are checked explicitly below.

**Owner self-grants are excluded from the observed set.** Postgres materialises an
owner's own privileges into the ACL as soon as anything is granted, so an owner appears
as its own grantee on every object it owns. That is ownership, not a grant, and it is
checked as ownership (N6). Including it would put eleven noise tuples into every diff
and train the reader to skim.

Run it two ways, and the document requires both:

    uv run python -m harness.db.assert_grants          # live cluster, at harness startup
    uv run pytest harness/db/test_grants.py            # throwaway cluster, in CI

Against the live one because the property being asserted is about the cluster in front
of you and not about the file that was supposed to configure it.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import psycopg

from harness.db.grants_declared import Declaration, Grant, Ownership, expand, parse

__all__ = [
    "GrantMismatchError",
    "Observation",
    "Report",
    "assert_matrix",
    "check_matrix",
    "observe",
]

REPO_ROOT = Path(__file__).resolve().parents[2]
GRANTS_YAML = REPO_ROOT / "migrations" / "roles" / "grants.yaml"

# The five named schemas plus `public`. `public` is here deliberately: Postgres grants
# privileges on it by default, and N7 is the row most likely to be true right now on any
# cluster nobody has checked. Nothing is declared for it, so anything found is EXTRA.
OBSERVED_SCHEMAS = ("product", "control", "evidence", "heldout", "migration_meta", "public")

# Roles whose credential a long-running service holds. N6: none of them may own an
# object in `evidence` or `heldout`, because an owner can rewrite a table regardless of
# what is granted — ownership defeats every grant above it.
SERVICE_ROLES = frozenset(
    {"alfred_harness", "alfred_criterion", "alfred_product", "alfred_operator", "alfred_readmodel"}
)

APPEND_ONLY_SCHEMAS = ("evidence", "heldout")

FORBIDDEN_ATTRIBUTES = (
    ("rolsuper", "SUPERUSER"),
    ("rolcreatedb", "CREATEDB"),
    ("rolcreaterole", "CREATEROLE"),
    ("rolreplication", "REPLICATION"),
    ("rolbypassrls", "BYPASSRLS"),
)


class GrantMismatchError(RuntimeError):
    """The observed cluster does not equal the declared matrix."""


@dataclass(frozen=True)
class Observation:
    dbname: str
    tables: dict[str, list[str]]
    grants: frozenset[Grant]
    ownership: frozenset[Ownership]
    memberships: frozenset[tuple[str, str]]
    role_attributes: dict[str, frozenset[str]]
    owner_can_create: frozenset[str]


@dataclass(frozen=True)
class Report:
    extra: tuple[Grant, ...]
    missing: tuple[Grant, ...]
    ownership_extra: tuple[Ownership, ...]
    ownership_missing: tuple[Ownership, ...]
    violations: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not (
            self.extra
            or self.missing
            or self.ownership_extra
            or self.ownership_missing
            or self.violations
        )

    def render(self) -> str:
        lines: list[str] = []
        # EXTRA first, always. It is the direction that fails silently.
        for grant in self.extra:
            lines.append(f"EXTRA    {grant}")
        for owned in self.ownership_extra:
            lines.append(f"EXTRA    {owned}")
        for grant in self.missing:
            lines.append(f"MISSING  {grant}")
        for owned in self.ownership_missing:
            lines.append(f"MISSING  {owned}")
        lines.extend(f"VIOLATES {violation}" for violation in self.violations)
        return "\n".join(lines)


# ----------------------------------------------------------------------- observation

_TABLE_SQL = """
SELECT n.nspname,
       c.relname,
       pg_get_userbyid(c.relowner),
       CASE WHEN a.grantee = 0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END,
       a.privilege_type
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
LEFT JOIN LATERAL aclexplode(c.relacl) a ON true
WHERE n.nspname = ANY(%s) AND c.relkind IN ('r', 'p', 'v', 'm', 'S')
"""

_SCHEMA_SQL = """
SELECT n.nspname,
       pg_get_userbyid(n.nspowner),
       CASE WHEN a.grantee = 0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END,
       a.privilege_type
FROM pg_namespace n
LEFT JOIN LATERAL aclexplode(n.nspacl) a ON true
WHERE n.nspname = ANY(%s)
"""

_DATABASE_SQL = """
SELECT d.datname,
       pg_get_userbyid(d.datdba),
       CASE WHEN a.grantee = 0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END,
       a.privilege_type
FROM pg_database d
LEFT JOIN LATERAL aclexplode(d.datacl) a ON true
WHERE d.datname = current_database()
"""

_FUNCTION_SQL = """
SELECT n.nspname,
       p.proname,
       pg_get_userbyid(p.proowner),
       CASE WHEN a.grantee = 0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END,
       a.privilege_type
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
LEFT JOIN LATERAL aclexplode(p.proacl) a ON true
WHERE n.nspname = ANY(%s)
"""

_DEFAULT_ACL_SQL = """
SELECT pg_get_userbyid(d.defaclrole),
       COALESCE(n.nspname, ''),
       d.defaclobjtype,
       CASE WHEN a.grantee = 0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END,
       a.privilege_type
FROM pg_default_acl d
LEFT JOIN pg_namespace n ON n.oid = d.defaclnamespace,
LATERAL aclexplode(d.defaclacl) a
"""

# Excluding owner self-grants from the comparison means the assertion cannot see whether
# an owner still holds USAGE and CREATE on the schema it owns — and on 2026-08-17 it did
# not, because `002_grants.sql` converges by REVOKE and a revoke makes the ACL explicit,
# taking ownership's implicit privileges with it. So it is asked directly. `has_schema_
# privilege` is version-independent, which the owner's materialised ACL bitmask is not:
# spelling out `arwdDxtm` here would pin the assertion to a Postgres major version.
_OWNER_PRIVILEGE_SQL = """
SELECT n.nspname
FROM pg_namespace n
WHERE n.nspname = ANY(%s)
  AND has_schema_privilege(pg_get_userbyid(n.nspowner), n.nspname, 'USAGE')
  AND has_schema_privilege(pg_get_userbyid(n.nspowner), n.nspname, 'CREATE')
"""

_MEMBERSHIP_SQL = """
SELECT pg_get_userbyid(m.member), pg_get_userbyid(m.roleid)
FROM pg_auth_members m
WHERE pg_get_userbyid(m.member) LIKE 'alfred\\_%'
   OR pg_get_userbyid(m.roleid) LIKE 'alfred\\_%'
"""

_ROLE_SQL = """
SELECT rolname, rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls
FROM pg_roles
WHERE rolname = ANY(%s)
"""


def observe(conn: psycopg.Connection[tuple[object, ...]], roles: Sequence[str]) -> Observation:
    """Read the cluster's actual grant state. No interpretation happens here."""
    grants: set[Grant] = set()
    ownership: set[Ownership] = set()
    tables: dict[str, list[str]] = {schema: [] for schema in OBSERVED_SCHEMAS}
    schemas = list(OBSERVED_SCHEMAS)

    with conn.cursor() as cur:
        cur.execute(_DATABASE_SQL)
        dbname = ""
        for name, owner, grantee, privilege in cur.fetchall():
            dbname = str(name)
            if grantee is None or grantee == owner:
                continue
            grants.add(Grant("database", str(name), str(grantee), str(privilege)))

        cur.execute(_SCHEMA_SQL, (schemas,))
        for schema, owner, grantee, privilege in cur.fetchall():
            ownership.add(Ownership("schema", str(schema), str(owner)))
            if grantee is None or grantee == owner:
                continue
            grants.add(Grant("schema", str(schema), str(grantee), str(privilege)))

        cur.execute(_TABLE_SQL, (schemas,))
        for schema, table, owner, grantee, privilege in cur.fetchall():
            qualified = f"{schema}.{table}"
            ownership.add(Ownership("table", qualified, str(owner)))
            tables.setdefault(str(schema), [])
            if str(table) not in tables[str(schema)]:
                tables[str(schema)].append(str(table))
            if grantee is None or grantee == owner:
                continue
            grants.add(Grant("table", qualified, str(grantee), str(privilege)))

        cur.execute(_FUNCTION_SQL, (schemas,))
        for schema, name, owner, grantee, privilege in cur.fetchall():
            if grantee is None or grantee == owner:
                continue
            grants.add(Grant("function", f"{schema}.{name}", str(grantee), str(privilege)))

        cur.execute(_DEFAULT_ACL_SQL)
        for grantor, schema, objtype, grantee, privilege in cur.fetchall():
            # A grantor's own entry in its own default ACL is not a grant; it is what
            # `ALTER DEFAULT PRIVILEGES ... REVOKE FROM PUBLIC` leaves behind.
            if grantee == grantor:
                continue
            obj = f"{grantor}:{schema}:{objtype}"
            grants.add(Grant("default", obj, str(grantee), str(privilege)))

        cur.execute(_OWNER_PRIVILEGE_SQL, (schemas,))
        owner_can_create = frozenset(str(row[0]) for row in cur.fetchall())

        cur.execute(_MEMBERSHIP_SQL)
        memberships = frozenset((str(member), str(role)) for member, role in cur.fetchall())

        cur.execute(_ROLE_SQL, (list(roles),))
        attributes: dict[str, frozenset[str]] = {}
        for row in cur.fetchall():
            name = str(row[0])
            held = {
                label
                for offset, (_column, label) in enumerate(FORBIDDEN_ATTRIBUTES, start=1)
                if bool(row[offset])
            }
            attributes[name] = frozenset(held)

    for grant_list in tables.values():
        grant_list.sort()

    return Observation(
        dbname=dbname,
        tables=tables,
        grants=frozenset(grants),
        ownership=frozenset(ownership),
        memberships=memberships,
        role_attributes=attributes,
        owner_can_create=owner_can_create,
    )


# ------------------------------------------------------------------------ comparison


def check_matrix(
    conn: psycopg.Connection[tuple[object, ...]], grants_yaml: Path | None = None
) -> Report:
    """Compare the cluster against the declaration. Returns a report; raises nothing."""
    declaration = parse(grants_yaml or GRANTS_YAML)
    observation = observe(conn, sorted(declaration.roles))
    declared_grants, declared_ownership = expand(
        declaration, observation.tables, observation.dbname
    )

    # Ownership of `public` and of the database itself is outside the matrix and is not
    # declared. Comparing it would make every cluster fail on its own superuser.
    observed_ownership = frozenset(
        owned
        for owned in observation.ownership
        if not owned.obj.startswith("public") and owned.obj != "public"
    )

    return Report(
        extra=tuple(sorted(observation.grants - declared_grants)),
        missing=tuple(sorted(declared_grants - observation.grants)),
        ownership_extra=tuple(sorted(observed_ownership - declared_ownership)),
        ownership_missing=tuple(sorted(declared_ownership - observed_ownership)),
        violations=_explicit_checks(declaration, observation),
    )


def _explicit_checks(declaration: Declaration, observation: Observation) -> tuple[str, ...]:
    """N6, N9 and N10. The three that are not grants and so do not fall out of equality."""
    violations: list[str] = []

    # N6 — ownership by a role a running service holds.
    for owned in sorted(observation.ownership):
        schema = owned.obj.split(".", 1)[0]
        if schema in APPEND_ONLY_SCHEMAS and owned.owner in SERVICE_ROLES:
            violations.append(
                f"N6: {owned.obj} is owned by {owned.owner}, whose credential a running "
                f"service holds; an owner can rewrite the table regardless of grants"
            )

    # Not an N-rule, and it is here because excluding owner self-grants hid it. An owner
    # that cannot create in its own schema fails the next migration and nothing before it.
    for schema in declaration.schemas:
        if schema not in observation.owner_can_create:
            violations.append(
                f"OWNER: the owner of schema {schema} does not hold both USAGE and CREATE "
                f"on it; converging grants by REVOKE strips ownership's implicit privileges"
            )

    # N9 — role attributes. BYPASSRLS is the one that reads as harmless.
    for role in sorted(declaration.roles):
        held = observation.role_attributes.get(role)
        if held is None:
            violations.append(f"N9: role {role} is declared but does not exist in the cluster")
            continue
        for attribute in sorted(held):
            violations.append(f"N9: role {role} holds {attribute}")

    # N10 — membership is a privilege path no table-grant query will show.
    declared_pairs = set(declaration.role_memberships)
    for pair in sorted(observation.memberships - declared_pairs):
        violations.append(f"N10: undeclared role membership {pair[0]} IN {pair[1]}")

    return tuple(violations)


def assert_matrix(
    conn: psycopg.Connection[tuple[object, ...]], grants_yaml: Path | None = None
) -> None:
    """Raise `GrantMismatchError` unless the cluster equals the declaration."""
    report = check_matrix(conn, grants_yaml)
    if not report.ok:
        raise GrantMismatchError(
            "the cluster's grant matrix does not equal migrations/roles/grants.yaml:\n"
            + report.render()
        )


def main(argv: Sequence[str] | None = None) -> int:
    """Assert against the live cluster. `ALFRED_DB_URL_ASSERT` names the connection.

    A read-only catalogue connection is sufficient and is what should be used: this
    reads `pg_class`, `pg_namespace`, `pg_default_acl`, `pg_auth_members` and `pg_roles`
    and writes nothing. Running it as a role that could change what it is measuring
    would make the assertion a statement about the auditor.
    """
    del argv
    url = os.environ.get("ALFRED_DB_URL_ASSERT")
    if not url:
        print(
            "ALFRED_DB_URL_ASSERT is not set. There is no default and no fallback: an "
            "assertion that connects to whichever database happened to be reachable is "
            "an assertion about an unknown cluster.",
            file=sys.stderr,
        )
        return 2

    with psycopg.connect(url) as conn:
        report = check_matrix(conn)

    if report.ok:
        print("OK — the cluster's grant matrix equals migrations/roles/grants.yaml")
        return 0

    print(report.render(), file=sys.stderr)
    print(
        f"\n{len(report.extra)} extra, {len(report.missing)} missing, "
        f"{len(report.ownership_extra) + len(report.ownership_missing)} ownership, "
        f"{len(report.violations)} explicit violation(s)",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
