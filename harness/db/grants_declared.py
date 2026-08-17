"""`migrations/roles/grants.yaml`, parsed and expanded into concrete grant tuples.

The declared half of the set-equality assertion. `assert_grants.py` reads the cluster;
this module reads the file; the two sets must be **equal**.

**No YAML library.** `lint_docs.py` made the same choice for the same reason and it is
worth restating rather than inheriting: the parser that guards the grant matrix should
not depend on the supply chain the grant matrix exists to bound. So this is a parser for
exactly the constructs `grants.yaml` uses, and it **fails closed on everything else** —
a line it does not recognise raises, and a top-level key it does not know raises. A
parser that skips what it cannot read passes exactly the file worth catching.

**The expansion needs the cluster's table list**, because the object groups are globs
(`"*"`, `policy_*`). That is a real limitation and it is stated rather than hidden: an
unexpected *table* is not caught here, only an unexpected *grant*. What catches an
unexpected table is the migration review, and what catches an unexpected grant *on* it
is that the group's privilege set is then compared as an equality on both sides.
"""

from __future__ import annotations

import fnmatch
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

__all__ = [
    "Declaration",
    "DeclarationError",
    "Grant",
    "Ownership",
    "expand",
    "parse",
]

# Privilege letters, matching docs/tier1/data-architecture.md § Grant matrix.
SCHEMA_LETTERS = {"U": "USAGE"}
TABLE_LETTERS = {"S": "SELECT", "I": "INSERT", "Up": "UPDATE", "D": "DELETE"}

TOP_LEVEL_KEYS = frozenset(
    {
        "version",
        "schemas",
        "database_connect",
        "schema_create",
        "object_groups",
        "default_privileges",
        "roles",
        "role_memberships",
        "must_not_exist",
    }
)

# Alembic's version tables live in `migration_meta` but are CREATEd by whichever
# migrator runs first, so they are owned by that migrator rather than by the schema's
# owner. This mapping is a fact about the four `env.py` files, not about grants.yaml,
# which is why it is here in the open rather than inferred.
VERSION_TABLE_OWNERS = {
    "alembic_version_product": "alfred_migrator_product",
    "alembic_version_control": "alfred_migrator_control",
    "alembic_version_evidence": "alfred_migrator_evidence",
    "alembic_version_heldout": "alfred_migrator_heldout",
}


class DeclarationError(RuntimeError):
    """`grants.yaml` could not be parsed, or declares something incoherent."""


@dataclass(frozen=True, order=True)
class Grant:
    """One privilege, one grantee, one object. The unit of the set comparison."""

    kind: str  # database | schema | table | function | default
    obj: str
    grantee: str
    privilege: str

    def __str__(self) -> str:
        return f"{self.kind} {self.obj} -> {self.grantee}: {self.privilege}"


@dataclass(frozen=True, order=True)
class Ownership:
    """Who owns an object. Checked separately from grants, because an owner can rewrite
    a table regardless of what is granted (N6) — ownership defeats every grant above it.
    """

    kind: str  # schema | table
    obj: str
    owner: str

    def __str__(self) -> str:
        return f"{self.kind} {self.obj} owned by {self.owner}"


@dataclass(frozen=True)
class ObjectGroup:
    schema: str
    patterns: tuple[str, ...]
    excluded: tuple[str, ...]

    def matches(self, table: str) -> bool:
        if any(fnmatch.fnmatchcase(table, pattern) for pattern in self.excluded):
            return False
        return any(fnmatch.fnmatchcase(table, pattern) for pattern in self.patterns)


@dataclass(frozen=True)
class DefaultPrivilege:
    """One `ALTER DEFAULT PRIVILEGES` entry, as `pg_default_acl` stores it."""

    grantor: str
    schema: str
    objtype: str
    grantee: str
    privileges: tuple[str, ...]


@dataclass(frozen=True)
class RoleDeclaration:
    login: bool
    owns: tuple[str, ...]
    grants: Mapping[str, tuple[str, ...]]


@dataclass(frozen=True)
class Declaration:
    version: int
    schemas: tuple[str, ...]
    database_connect: tuple[str, ...]
    schema_create: Mapping[str, tuple[str, ...]]
    object_groups: Mapping[str, ObjectGroup]
    default_privileges: Mapping[str, DefaultPrivilege]
    roles: Mapping[str, RoleDeclaration]
    role_memberships: tuple[tuple[str, str], ...]
    must_not_exist: tuple[str, ...] = field(default=())


# --------------------------------------------------------------------------- parsing

_COMMENT = re.compile(r"""(?:[^'"#]|'[^']*'|"[^"]*")*""")


def _strip_comment(line: str) -> str:
    """Remove a trailing `#` comment, respecting quotes.

    Inline comments are real in this file (`evidence_verdict: [U, S, I]  # sole author
    of verdicts`), and a naive `split('#')` would truncate any pattern containing one.
    None do today, which is exactly why the quote-aware version is written now.
    """
    match = _COMMENT.match(line)
    prefix = match.group(0) if match else line
    return prefix.rstrip()


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _split_items(text: str) -> tuple[str, ...]:
    """`[a, b, c]` or `[]` -> a tuple of unquoted items. Trailing commas permitted."""
    inner = text.strip()
    if not (inner.startswith("[") and inner.endswith("]")):
        raise DeclarationError(f"expected a flow sequence, got {text!r}")
    body = inner[1:-1].strip()
    if not body:
        return ()
    return tuple(_unquote(part) for part in body.split(",") if part.strip())


def _unquote(text: str) -> str:
    value = text.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def _gather_flow(lines: Sequence[str], index: int, opener: str) -> tuple[str, int]:
    """Accumulate a `[...]` or `{...}` that may span lines. Returns (text, next index)."""
    close = "]" if opener == "[" else "}"
    text = lines[index]
    cursor = index
    while text.count(opener) > text.count(close):
        cursor += 1
        if cursor >= len(lines):
            raise DeclarationError(f"unterminated {opener}{close} starting at line {index + 1}")
        text += " " + _strip_comment(lines[cursor]).strip()
    return text, cursor + 1


def parse(path: Path) -> Declaration:
    """Parse `grants.yaml`. Raises `DeclarationError` on anything unrecognised."""
    raw = path.read_text(encoding="utf-8").splitlines()
    # Index-aligned with `raw` so error messages can quote real line numbers.
    lines = [_strip_comment(line) for line in raw]

    found: dict[str, object] = {}
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        if _indent(line) != 0:
            raise DeclarationError(
                f"line {index + 1}: unexpected indentation at top level: {raw[index]!r}"
            )
        key, _, rest = line.partition(":")
        key = key.strip()
        if key not in TOP_LEVEL_KEYS:
            raise DeclarationError(f"line {index + 1}: unknown top-level key {key!r}")
        if key in found:
            raise DeclarationError(f"line {index + 1}: duplicate top-level key {key!r}")
        value, index = _parse_top_level(key, rest, lines, index)
        found[key] = value

    missing = TOP_LEVEL_KEYS - set(found)
    if missing:
        raise DeclarationError(f"grants.yaml is missing required keys: {sorted(missing)}")

    # Each section's parser returns its own concrete type; `found` is heterogeneous, so
    # the narrowing happens once, here, in the open. A cast is a claim about a value the
    # checker cannot see — every one of these is discharged by the parser that produced
    # the entry raising rather than returning something else.
    return Declaration(
        version=cast(int, found["version"]),
        schemas=cast(tuple[str, ...], found["schemas"]),
        database_connect=cast(tuple[str, ...], found["database_connect"]),
        schema_create=cast(Mapping[str, tuple[str, ...]], found["schema_create"]),
        object_groups=cast(Mapping[str, ObjectGroup], found["object_groups"]),
        default_privileges=cast(Mapping[str, DefaultPrivilege], found["default_privileges"]),
        roles=cast(Mapping[str, RoleDeclaration], found["roles"]),
        role_memberships=cast(tuple[tuple[str, str], ...], found["role_memberships"]),
        must_not_exist=cast(tuple[str, ...], found["must_not_exist"]),
    )


def _parse_top_level(
    key: str, rest: str, lines: Sequence[str], index: int
) -> tuple[object, int]:
    inline = rest.strip()

    if key == "version":
        return int(inline), index + 1
    if key in ("schemas", "database_connect", "role_memberships"):
        text, nxt = _gather_flow(lines, index, "[")
        items = _split_items(text.partition(":")[2])
        if key == "role_memberships":
            if items:
                raise DeclarationError(
                    "role_memberships is non-empty; the pair form is not implemented "
                    "because none is declared. Implement it deliberately, do not guess."
                )
            return (), nxt
        return items, nxt
    if key == "schema_create":
        return _parse_schema_create(lines, index)
    if key == "object_groups":
        return _parse_object_groups(lines, index)
    if key == "default_privileges":
        return _parse_default_privileges(lines, index)
    if key == "roles":
        return _parse_roles(lines, index)
    if key == "must_not_exist":
        return _parse_must_not_exist(lines, index)
    raise DeclarationError(f"line {index + 1}: no parser for top-level key {key!r}")


def _child_block(lines: Sequence[str], index: int) -> tuple[list[int], int]:
    """Line numbers of the non-blank children of the block opened at `index`."""
    children: list[int] = []
    cursor = index + 1
    while cursor < len(lines):
        line = lines[cursor]
        if not line.strip():
            cursor += 1
            continue
        if _indent(line) == 0:
            break
        children.append(cursor)
        cursor += 1
    return children, cursor


def _parse_schema_create(
    lines: Sequence[str], index: int
) -> tuple[Mapping[str, tuple[str, ...]], int]:
    children, end = _child_block(lines, index)
    result: dict[str, tuple[str, ...]] = {}
    cursor = 0
    while cursor < len(children):
        line_no = children[cursor]
        name, _, rest = lines[line_no].strip().partition(":")
        if "[" not in rest:
            raise DeclarationError(
                f"line {line_no + 1}: schema_create entries must be flow sequences"
            )
        text, next_line = _gather_flow(lines, line_no, "[")
        result[name.strip()] = _split_items(text.partition(":")[2])
        while cursor < len(children) and children[cursor] < next_line:
            cursor += 1
    return result, end


def _parse_object_groups(lines: Sequence[str], index: int) -> tuple[Mapping[str, ObjectGroup], int]:
    children, end = _child_block(lines, index)
    groups: dict[str, ObjectGroup] = {}
    for line_no in children:
        name, _, rest = lines[line_no].strip().partition(":")
        body = rest.strip()
        if not (body.startswith("{") and body.endswith("}")):
            raise DeclarationError(
                f"line {line_no + 1}: object_groups entries must be single-line flow maps"
            )
        groups[name.strip()] = _parse_group_body(body[1:-1], line_no)
    return groups, end


def _parse_group_body(body: str, line_no: int) -> ObjectGroup:
    """`schema: control, tables: "*", except: ["policy_*", "threshold_*"]`."""
    fields: dict[str, str] = {}
    for fragment in _split_top_level(body):
        _absorb_field(fields, fragment, line_no)

    unknown = set(fields) - {"schema", "tables", "except"}
    if unknown:
        raise DeclarationError(
            f"line {line_no + 1}: unknown object_group keys {sorted(unknown)}"
        )
    if "schema" not in fields or "tables" not in fields:
        raise DeclarationError(f"line {line_no + 1}: object_group needs `schema` and `tables`")

    tables = fields["tables"].strip()
    patterns = _split_items(tables) if tables.startswith("[") else (_unquote(tables),)
    excluded = _split_items(fields["except"]) if "except" in fields else ()
    return ObjectGroup(schema=_unquote(fields["schema"]), patterns=patterns, excluded=excluded)


def _split_top_level(body: str) -> list[str]:
    """Split on commas that are not inside a nested `[...]`."""
    fragments: list[str] = []
    depth = 0
    current = ""
    for char in body:
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
        if char == "," and depth == 0:
            fragments.append(current)
            current = ""
            continue
        current += char
    fragments.append(current)
    return [fragment for fragment in fragments if fragment.strip()]


def _absorb_field(fields: dict[str, str], text: str, line_no: int) -> None:
    if not text.strip():
        return
    key, sep, value = text.partition(":")
    if not sep:
        raise DeclarationError(f"line {line_no + 1}: expected `key: value`, got {text!r}")
    fields[key.strip()] = value.strip()


_DEFAULT_PRIVILEGE_KEYS = frozenset({"grantor", "schema", "objtype", "grantee", "privileges"})


def _parse_default_privileges(
    lines: Sequence[str], index: int
) -> tuple[Mapping[str, DefaultPrivilege], int]:
    children, end = _child_block(lines, index)
    entries: dict[str, DefaultPrivilege] = {}
    for line_no in children:
        name, _, rest = lines[line_no].strip().partition(":")
        body = rest.strip()
        if not (body.startswith("{") and body.endswith("}")):
            raise DeclarationError(
                f"line {line_no + 1}: default_privileges entries must be single-line flow maps"
            )
        fields: dict[str, str] = {}
        for fragment in _split_top_level(body[1:-1]):
            _absorb_field(fields, fragment, line_no)
        if frozenset(fields) != _DEFAULT_PRIVILEGE_KEYS:
            raise DeclarationError(
                f"line {line_no + 1}: default_privileges entry needs exactly "
                f"{sorted(_DEFAULT_PRIVILEGE_KEYS)}, got {sorted(fields)}"
            )
        entries[name.strip()] = DefaultPrivilege(
            grantor=_unquote(fields["grantor"]),
            schema=_unquote(fields["schema"]),
            objtype=_unquote(fields["objtype"]),
            grantee=_unquote(fields["grantee"]),
            privileges=_split_items(fields["privileges"]),
        )
    return entries, end


def _parse_roles(lines: Sequence[str], index: int) -> tuple[Mapping[str, RoleDeclaration], int]:
    children, end = _child_block(lines, index)
    roles: dict[str, RoleDeclaration] = {}
    if not children:
        return roles, end

    role_indent = _indent(lines[children[0]])
    current: str | None = None
    attributes: dict[str, object] = {}
    cursor = 0

    while cursor < len(children):
        line_no = children[cursor]
        line = lines[line_no]
        if _indent(line) == role_indent:
            if current is not None:
                roles[current] = _finish_role(current, attributes)
            name, sep, rest = line.strip().partition(":")
            if not sep or rest.strip():
                raise DeclarationError(f"line {line_no + 1}: expected a role name followed by `:`")
            current = name.strip()
            attributes = {}
            cursor += 1
            continue
        if current is None:
            raise DeclarationError(f"line {line_no + 1}: attribute outside any role")
        cursor = _absorb_role_attribute(attributes, lines, children, cursor)

    if current is not None:
        roles[current] = _finish_role(current, attributes)
    return roles, end


def _absorb_role_attribute(
    attributes: dict[str, object], lines: Sequence[str], children: Sequence[int], cursor: int
) -> int:
    line_no = children[cursor]
    key, sep, rest = lines[line_no].strip().partition(":")
    key = key.strip()
    if not sep:
        raise DeclarationError(f"line {line_no + 1}: expected `key: value`")

    if key == "login":
        attributes["login"] = rest.strip() == "true"
        return cursor + 1
    if key == "owns":
        text, next_line = _gather_flow(lines, line_no, "[")
        attributes["owns"] = _split_items(text.partition(":")[2])
        return _advance(children, cursor, next_line)
    if key != "grants":
        raise DeclarationError(f"line {line_no + 1}: unknown role attribute {key!r}")

    body = rest.strip()
    if body.startswith("{"):
        if not body.endswith("}"):
            raise DeclarationError(
                f"line {line_no + 1}: inline grants map must close on the same line"
            )
        inline_grants: dict[str, tuple[str, ...]] = {}
        for fragment in _split_top_level(body[1:-1]):
            group, sep, letters = fragment.partition(":")
            if not sep:
                raise DeclarationError(
                    f"line {line_no + 1}: expected `group: [letters]`, got {fragment!r}"
                )
            inline_grants[group.strip()] = _split_items(letters)
        attributes["grants"] = inline_grants
        return cursor + 1
    if body:
        raise DeclarationError(f"line {line_no + 1}: unexpected text after `grants:`: {body!r}")

    # Block form: the indented lines beneath, each `group: [letters]`.
    grants: dict[str, tuple[str, ...]] = {}
    grant_indent = None
    cursor += 1
    while cursor < len(children):
        inner_no = children[cursor]
        indent = _indent(lines[inner_no])
        if grant_indent is None:
            grant_indent = indent
        if indent < grant_indent:
            break
        if indent > grant_indent:
            raise DeclarationError(f"line {inner_no + 1}: unexpected indentation inside grants")
        group, _, letters = lines[inner_no].strip().partition(":")
        text, next_line = _gather_flow(lines, inner_no, "[")
        grants[group.strip()] = _split_items(text.partition(":")[2])
        del letters
        cursor = _advance(children, cursor, next_line)
    attributes["grants"] = grants
    return cursor


def _advance(children: Sequence[int], cursor: int, next_line: int) -> int:
    while cursor < len(children) and children[cursor] < next_line:
        cursor += 1
    return cursor


def _finish_role(name: str, attributes: Mapping[str, object]) -> RoleDeclaration:
    if "login" not in attributes:
        raise DeclarationError(f"role {name!r} does not declare `login`")
    if "grants" not in attributes:
        raise DeclarationError(f"role {name!r} does not declare `grants`")
    return RoleDeclaration(
        login=bool(attributes["login"]),
        owns=cast(tuple[str, ...], attributes.get("owns", ())),
        grants=cast(Mapping[str, tuple[str, ...]], attributes["grants"]),
    )


def _parse_must_not_exist(lines: Sequence[str], index: int) -> tuple[tuple[str, ...], int]:
    children, end = _child_block(lines, index)
    ids: list[str] = []
    for line_no in children:
        stripped = lines[line_no].strip()
        if stripped.startswith("- id:"):
            ids.append(stripped.partition(":")[2].strip())
        elif not stripped.startswith("rule:"):
            raise DeclarationError(
                f"line {line_no + 1}: must_not_exist entries carry `id` and `rule` only"
            )
    return tuple(ids), end


# ------------------------------------------------------------------------- expansion


def expand(
    declaration: Declaration,
    tables: Mapping[str, Iterable[str]],
    dbname: str,
) -> tuple[frozenset[Grant], frozenset[Ownership]]:
    """Concrete grant and ownership tuples, given the cluster's actual table list."""
    grants: set[Grant] = set()
    ownership: set[Ownership] = set()

    for role in declaration.database_connect:
        grants.add(Grant("database", dbname, role, "CONNECT"))

    for schema, roles in declaration.schema_create.items():
        for role in roles:
            grants.add(Grant("schema", schema, role, "CREATE"))
            # CREATE without USAGE is unusable, and 002_grants.sql issues them together.
            grants.add(Grant("schema", schema, role, "USAGE"))

    for entry in declaration.default_privileges.values():
        obj = f"{entry.grantor}:{entry.schema}:{entry.objtype}"
        for letter in entry.privileges:
            if letter not in TABLE_LETTERS:
                raise DeclarationError(f"default_privileges: unknown privilege letter {letter!r}")
            grants.add(Grant("default", obj, entry.grantee, TABLE_LETTERS[letter]))

    for role_name, role in declaration.roles.items():
        for schema in role.owns:
            ownership.add(Ownership("schema", schema, role_name))
            for table in tables.get(schema, ()):
                owner = VERSION_TABLE_OWNERS.get(table, role_name)
                ownership.add(Ownership("table", f"{schema}.{table}", owner))
        grants |= _expand_role_grants(declaration, role_name, role, tables)

    return frozenset(_drop_self_grants(grants, ownership)), frozenset(ownership)


def _drop_self_grants(grants: set[Grant], ownership: set[Ownership]) -> set[Grant]:
    """Remove declared grants whose grantee owns the object.

    `assert_grants.observe` excludes an owner's own ACL entry, because Postgres
    materialises it on every object as soon as anything is granted and it is ownership
    rather than a grant. The declared side must apply the identical rule or the two
    disagree about the same fact — which is what happened the first time this ran: the
    four migrators each hold `[U, S, I, Up]` on `migration_meta`, own their own version
    table inside it, and produced twelve MISSING tuples that were not missing at all.

    What is given up is stated: the assertion no longer checks that a migrator can write
    the version table it owns. Alembic's first upgrade checks that, loudly, and an owner
    can re-grant to itself in any case — so this was never a control.
    """
    owners = {(owned.kind, owned.obj): owned.owner for owned in ownership}
    return {
        grant
        for grant in grants
        if owners.get((grant.kind, grant.obj)) != grant.grantee
    }


def _expand_role_grants(
    declaration: Declaration,
    role_name: str,
    role: RoleDeclaration,
    tables: Mapping[str, Iterable[str]],
) -> set[Grant]:
    grants: set[Grant] = set()
    for group_name, letters in role.grants.items():
        try:
            group = declaration.object_groups[group_name]
        except KeyError as exc:
            raise DeclarationError(
                f"role {role_name!r} grants on unknown object group {group_name!r}"
            ) from exc
        matched = [table for table in tables.get(group.schema, ()) if group.matches(table)]
        for letter in letters:
            if letter in SCHEMA_LETTERS:
                grants.add(Grant("schema", group.schema, role_name, SCHEMA_LETTERS[letter]))
                continue
            if letter not in TABLE_LETTERS:
                raise DeclarationError(
                    f"role {role_name!r}, group {group_name!r}: unknown privilege letter {letter!r}"
                )
            privilege = TABLE_LETTERS[letter]
            for table in matched:
                grants.add(Grant("table", f"{group.schema}.{table}", role_name, privilege))
    return grants
