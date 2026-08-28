"""Tests for `grants_declared` parser.

Pure unit tests — no database, no Docker, no external deps.
"""

# pyright: reportPrivateUsage=false, reportUnknownVariableType=false, reportUnknownArgumentType=false

from __future__ import annotations

from pathlib import Path

import pytest
from harness.db.grants_declared import (
    SCHEMA_LETTERS,
    TABLE_LETTERS,
    TOP_LEVEL_KEYS,
    Declaration,
    DeclarationError,
    DefaultPrivilege,
    Grant,
    ObjectGroup,
    Ownership,
    RoleDeclaration,
    _absorb_field,
    _gather_flow,
    _split_items,
    _split_top_level,
    _strip_comment,
    _unquote,
    expand,
    parse,
)

# ────────────────────────────────────────────────────────────────────── helpers


def _write_yaml(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "grants.yaml"
    p.write_text(content, encoding="utf-8")
    return p


# ────────────────────────────────────────────────────────────────────── parsing


def test_strip_comment_removes_trailing_hash() -> None:
    assert _strip_comment("foo: bar  # comment") == "foo: bar"
    assert _strip_comment("foo: bar") == "foo: bar"
    assert _strip_comment("  # comment") == ""
    assert _strip_comment('foo: "bar#baz"  # comment') == 'foo: "bar#baz"'
    assert _strip_comment("foo: 'bar#baz'  # comment") == "foo: 'bar#baz'"


def test_split_items() -> None:
    assert _split_items("[a, b, c]") == ("a", "b", "c")
    assert _split_items("[]") == ()
    assert _split_items("[a]") == ("a",)
    assert _split_items("[a,]") == ("a",)
    assert _split_items("  [ a , b ]  ") == ("a", "b")
    assert _split_items("['a', 'b', \"c\"]") == ("a", "b", "c")
    with pytest.raises(DeclarationError):
        _split_items("not a list")


def test_unquote() -> None:
    assert _unquote("foo") == "foo"
    assert _unquote('"foo"') == "foo"
    assert _unquote("'foo'") == "foo"
    assert _unquote('"foo, bar"') == "foo, bar"


def test_gather_flow_single_line() -> None:
    lines = ["key: [a, b]"]
    text, nxt = _gather_flow(lines, 0, "[")
    assert text == "key: [a, b]"
    assert nxt == 1


def test_gather_flow_multiline() -> None:
    lines = ["key: [", "  a,", "  b]"]
    text, nxt = _gather_flow(lines, 0, "[")
    assert text == "key: [ a, b]"
    assert nxt == 3


def test_gather_flow_unterminated_raises() -> None:
    lines = ["key: [", "  a,"]
    with pytest.raises(DeclarationError, match="unterminated"):
        _gather_flow(lines, 0, "[")


def test_split_top_level() -> None:
    assert _split_top_level("a: 1, b: 2") == ["a: 1", " b: 2"]
    assert _split_top_level("a: [1, 2], b: 3") == ["a: [1, 2]", " b: 3"]
    assert _split_top_level("a: [1, 2], b: [3, 4]") == ["a: [1, 2]", " b: [3, 4]"]


def test_absorb_field() -> None:
    fields: dict[str, str] = {}
    _absorb_field(fields, "key: value", 0)
    assert fields == {"key": "value"}

    # Empty/whitespace text is a no-op (line 363)
    _absorb_field(fields, "", 0)
    _absorb_field(fields, "   ", 0)
    assert fields == {"key": "value"}

    with pytest.raises(DeclarationError, match="expected `key: value`"):
        _absorb_field(fields, "no colon", 0)


# ────────────────────────────────────────────────────────────────────── happy path


VALID_MINIMAL = """\
version: 1
schemas: [product]
database_connect: [alfred_test]
schema_create: {}
object_groups:
  test_group: {schema: product, tables: "*"}
default_privileges: {}
roles:
  alfred_test:
    login: true
    owns: []
    grants: {}
role_memberships: []
must_not_exist: []
"""


def test_parse_minimal_valid(tmp_path: Path) -> None:
    path = _write_yaml(tmp_path, VALID_MINIMAL)
    decl = parse(path)

    assert decl.version == 1
    assert decl.schemas == ("product",)
    assert decl.database_connect == ("alfred_test",)
    assert decl.schema_create == {}
    assert "test_group" in decl.object_groups
    assert decl.default_privileges == {}
    assert "alfred_test" in decl.roles
    assert decl.roles["alfred_test"].login is True
    assert decl.roles["alfred_test"].owns == ()
    assert decl.roles["alfred_test"].grants == {}
    assert decl.role_memberships == ()
    assert decl.must_not_exist == ()


def test_parse_full_example(tmp_path: Path) -> None:  # noqa: ARG001 — fixture required for test harness isolation
    path = Path(__file__).resolve().parents[2] / "migrations" / "roles" / "grants.yaml"
    decl = parse(path)

    assert decl.version == 3
    assert len(decl.schemas) == 5
    assert len(decl.database_connect) == 11
    assert len(decl.object_groups) == 8
    assert len(decl.default_privileges) == 3
    assert len(decl.roles) == 11
    assert len(decl.role_memberships) == 0
    assert len(decl.must_not_exist) == 10


def test_object_group_patterns_and_excluded() -> None:
    group = ObjectGroup(schema="control", patterns=("*",), excluded=("policy_*", "threshold_*"))
    assert group.matches("work_table") is True
    assert group.matches("policy_config") is False
    assert group.matches("threshold_limit") is False


def test_expand_basic(tmp_path: Path) -> None:
    path = _write_yaml(tmp_path, VALID_MINIMAL)
    decl = parse(path)

    tables = {"product": ["table1", "table2"]}
    grants, ownership = expand(decl, tables, "testdb")

    assert any(g.kind == "database" and g.privilege == "CONNECT" for g in grants)
    assert len(grants) >= 1
    assert len(ownership) == 0


def test_expand_with_ownership(tmp_path: Path) -> None:
    yaml = VALID_MINIMAL.replace("owns: []", "owns: [product]")
    path = _write_yaml(tmp_path, yaml)
    decl = parse(path)

    tables = {"product": ["table1", "table2"]}
    _grants, ownership = expand(decl, tables, "testdb")

    schema_ownership = [o for o in ownership if o.kind == "schema"]
    table_ownership = [o for o in ownership if o.kind == "table"]
    assert len(schema_ownership) == 1
    assert len(table_ownership) == 2


def test_expand_role_grants(tmp_path: Path) -> None:
    yaml = VALID_MINIMAL.replace("grants: {}", "grants: {test_group: [U, S, I, Up, D]}")
    path = _write_yaml(tmp_path, yaml)
    decl = parse(path)

    tables = {"product": ["table1", "table2"]}
    grants, _ownership = expand(decl, tables, "testdb")

    table_grants = [g for g in grants if g.kind == "table"]
    assert len(table_grants) == 8  # 2 tables * 4 table privileges (S, I, Up, D)
    schema_grants = [g for g in grants if g.kind == "schema"]
    assert len(schema_grants) == 1  # USAGE on product schema (from U)


def test_expand_default_privileges(tmp_path: Path) -> None:
    yaml = """version: 1
schemas: [product]
database_connect: [alfred_test]
schema_create: {}
object_groups:
  test_group: {schema: product, tables: "*"}
default_privileges:
  test_default: {grantor: alfred_test, schema: product, objtype: r, grantee: alfred_test, privileges: [S, I]}
roles:
  alfred_test:
    login: true
    owns: [product]
    grants: {}
role_memberships: []
must_not_exist: []
"""
    path = _write_yaml(tmp_path, yaml)
    decl = parse(path)

    tables = {"product": ["table1"]}
    grants, _ownership = expand(decl, tables, "testdb")

    default_grants = [g for g in grants if g.kind == "default"]
    assert len(default_grants) == 2  # S and I


def test_expand_schema_create(tmp_path: Path) -> None:
    yaml = VALID_MINIMAL.replace(
        "schema_create: {}",
        "schema_create:\n  product: [alfred_test]",
    )
    path = _write_yaml(tmp_path, yaml)
    decl = parse(path)

    tables = {"product": []}
    grants, _ownership = expand(decl, tables, "testdb")

    schema_grants = [g for g in grants if g.kind == "schema"]
    assert any(g.privilege == "CREATE" for g in schema_grants)
    assert any(g.privilege == "USAGE" for g in schema_grants)


def test_expand_drops_self_grants(tmp_path: Path) -> None:
    yaml = VALID_MINIMAL.replace("grants: {}", "grants: {test_group: [U, S, I, Up, D]}").replace(
        "owns: []", "owns: [product]"
    )
    path = _write_yaml(tmp_path, yaml)
    decl = parse(path)

    tables = {"product": ["table1"]}
    grants, _ownership = expand(decl, tables, "testdb")

    owner = "alfred_test"
    table_grants_for_owner = [g for g in grants if g.grantee == owner and g.kind == "table"]
    assert len(table_grants_for_owner) == 0


# ────────────────────────────────────────────────────────────────────── malformed


def test_parse_missing_required_keys(tmp_path: Path) -> None:
    yaml = "version: 1\nschemas: [product]\n"
    path = _write_yaml(tmp_path, yaml)
    with pytest.raises(DeclarationError, match="missing required keys"):
        parse(path)


def test_parse_unknown_top_level_key(tmp_path: Path) -> None:
    yaml = VALID_MINIMAL + "\nunknown_key: value\n"
    path = _write_yaml(tmp_path, yaml)
    with pytest.raises(DeclarationError, match="unknown top-level key"):
        parse(path)


def test_parse_duplicate_top_level_key(tmp_path: Path) -> None:
    yaml = VALID_MINIMAL.replace("version: 1", "version: 1\nversion: 2")
    path = _write_yaml(tmp_path, yaml)
    with pytest.raises(DeclarationError, match="duplicate top-level key"):
        parse(path)


def test_parse_unexpected_indentation(tmp_path: Path) -> None:
    yaml = VALID_MINIMAL.replace("version: 1", "version: 1\n  indented: value")
    path = _write_yaml(tmp_path, yaml)
    with pytest.raises(DeclarationError, match="unexpected indentation"):
        parse(path)


def test_parse_version_must_be_int(tmp_path: Path) -> None:
    yaml = VALID_MINIMAL.replace("version: 1", "version: not_int")
    path = _write_yaml(tmp_path, yaml)
    with pytest.raises(ValueError):
        parse(path)


def test_parse_schemas_must_be_flow_sequence(tmp_path: Path) -> None:
    yaml = VALID_MINIMAL.replace("schemas: [product]", "schemas: product")
    path = _write_yaml(tmp_path, yaml)
    with pytest.raises(DeclarationError, match="expected a flow sequence"):
        parse(path)


def test_parse_object_group_missing_fields(tmp_path: Path) -> None:
    yaml = VALID_MINIMAL.replace(
        '  test_group: {schema: product, tables: "*"}',
        "  test_group: {schema: product}",
    )
    path = _write_yaml(tmp_path, yaml)
    with pytest.raises(DeclarationError, match="needs `schema` and `tables`"):
        parse(path)


def test_parse_object_group_unknown_keys(tmp_path: Path) -> None:
    yaml = VALID_MINIMAL.replace(
        '  test_group: {schema: product, tables: "*"}',
        '  test_group: {schema: product, tables: "*", unknown: value}',
    )
    path = _write_yaml(tmp_path, yaml)
    with pytest.raises(DeclarationError, match="unknown object_group keys"):
        parse(path)


def test_parse_default_privileges_missing_keys(tmp_path: Path) -> None:
    yaml = VALID_MINIMAL.replace(
        "default_privileges: {}",
        "default_privileges:\n  test: {grantor: foo, schema: bar}",
    )
    path = _write_yaml(tmp_path, yaml)
    with pytest.raises(DeclarationError, match="needs exactly"):
        parse(path)


def test_parse_role_missing_login(tmp_path: Path) -> None:
    yaml = VALID_MINIMAL.replace(
        "    login: true\n    owns: []\n    grants: {}",
        "    owns: []\n    grants: {}",
    )
    path = _write_yaml(tmp_path, yaml)
    with pytest.raises(DeclarationError, match="does not declare `login`"):
        parse(path)


def test_parse_role_missing_grants(tmp_path: Path) -> None:
    yaml = VALID_MINIMAL.replace(
        "    login: true\n    owns: []\n    grants: {}",
        "    login: true\n    owns: []",
    )
    path = _write_yaml(tmp_path, yaml)
    with pytest.raises(DeclarationError, match="does not declare `grants`"):
        parse(path)


def test_parse_role_unknown_attribute(tmp_path: Path) -> None:
    yaml = VALID_MINIMAL.replace(
        "    login: true\n    owns: []\n    grants: {}",
        "    login: true\n    owns: []\n    grants: {}\n    unknown: value",
    )
    path = _write_yaml(tmp_path, yaml)
    with pytest.raises(DeclarationError, match="unknown role attribute"):
        parse(path)


def test_parse_role_grants_unknown_group(tmp_path: Path) -> None:
    yaml = VALID_MINIMAL.replace("grants: {}", "grants: {unknown_group: [U, S]}")
    path = _write_yaml(tmp_path, yaml)
    decl = parse(path)
    with pytest.raises(DeclarationError, match="unknown object group"):
        expand(decl, {"product": ["table1"]}, "testdb")


def test_parse_role_grants_unknown_privilege_letter(tmp_path: Path) -> None:
    yaml = VALID_MINIMAL.replace("grants: {}", "grants: {test_group: [X]}")
    path = _write_yaml(tmp_path, yaml)
    decl = parse(path)
    with pytest.raises(DeclarationError, match="unknown privilege letter"):
        expand(decl, {"product": ["table1"]}, "testdb")


def test_parse_default_privileges_unknown_letter(tmp_path: Path) -> None:
    yaml = """version: 1
schemas: [product]
database_connect: [alfred_test]
schema_create: {}
object_groups:
  test_group: {schema: product, tables: "*"}
default_privileges:
  test: {grantor: alfred_test, schema: product, objtype: r, grantee: alfred_test, privileges: [X]}
roles:
  alfred_test:
    login: true
    owns: [product]
    grants: {}
role_memberships: []
must_not_exist: []
"""
    path = _write_yaml(tmp_path, yaml)
    decl = parse(path)
    with pytest.raises(DeclarationError, match="unknown privilege letter"):
        expand(decl, {"product": ["table1"]}, "testdb")


def test_parse_must_not_exist_format(tmp_path: Path) -> None:
    yaml = VALID_MINIMAL.replace(
        "must_not_exist: []",
        "must_not_exist:\n  - invalid_format",
    )
    path = _write_yaml(tmp_path, yaml)
    with pytest.raises(DeclarationError, match="carry `id` and `rule` only"):
        parse(path)


def test_parse_role_memberships_non_empty_not_implemented(tmp_path: Path) -> None:
    yaml = VALID_MINIMAL.replace(
        "role_memberships: []",
        "role_memberships: [a, b]",
    )
    path = _write_yaml(tmp_path, yaml)
    with pytest.raises(DeclarationError, match="role_memberships is non-empty"):
        parse(path)


# ────────────────────────────────────────────────────────────────────── structure


def test_declared_grant_structure() -> None:
    grant = Grant("table", "product.table1", "alfred_test", "SELECT")
    assert grant.kind == "table"
    assert grant.obj == "product.table1"
    assert grant.grantee == "alfred_test"
    assert grant.privilege == "SELECT"
    assert str(grant) == "table product.table1 -> alfred_test: SELECT"


def test_declared_ownership_structure() -> None:
    ownership = Ownership("table", "product.table1", "alfred_test")
    assert ownership.kind == "table"
    assert ownership.obj == "product.table1"
    assert ownership.owner == "alfred_test"
    assert str(ownership) == "table product.table1 owned by alfred_test"


def test_object_group_structure() -> None:
    group = ObjectGroup(schema="product", patterns=("*",), excluded=())
    assert group.schema == "product"
    assert group.patterns == ("*",)
    assert group.excluded == ()


def test_default_privilege_structure() -> None:
    dp = DefaultPrivilege(
        grantor="alfred_migrator_product",
        schema="product",
        objtype="r",
        grantee="alfred_test",
        privileges=("S", "I"),
    )
    assert dp.grantor == "alfred_migrator_product"
    assert dp.schema == "product"
    assert dp.objtype == "r"
    assert dp.grantee == "alfred_test"
    assert dp.privileges == ("S", "I")


def test_role_declaration_structure() -> None:
    role = RoleDeclaration(login=True, owns=("product",), grants={"test_group": ("U", "S")})
    assert role.login is True
    assert role.owns == ("product",)
    assert role.grants == {"test_group": ("U", "S")}


def test_declaration_all_fields() -> None:
    decl = Declaration(
        version=1,
        schemas=("product",),
        database_connect=("alfred_test",),
        schema_create={"product": ("alfred_test",)},
        object_groups={"test": ObjectGroup("product", ("*",), ())},
        default_privileges={},
        roles={"alfred_test": RoleDeclaration(True, (), {})},
        role_memberships=(),
        must_not_exist=(),
    )
    assert decl.version == 1
    assert decl.schemas == ("product",)
    assert decl.database_connect == ("alfred_test",)
    assert decl.schema_create == {"product": ("alfred_test",)}
    assert "test" in decl.object_groups
    assert decl.default_privileges == {}
    assert "alfred_test" in decl.roles
    assert decl.role_memberships == ()
    assert decl.must_not_exist == ()


# ────────────────────────────────────────────────────────────────────── privilege letters


def test_schema_letters_mapping() -> None:
    assert SCHEMA_LETTERS == {"U": "USAGE"}


def test_table_letters_mapping() -> None:
    assert TABLE_LETTERS == {"S": "SELECT", "I": "INSERT", "Up": "UPDATE", "D": "DELETE"}


def test_top_level_keys_complete() -> None:
    expected = {
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
    assert expected == TOP_LEVEL_KEYS


# ────────────────────────────────────────────────────────────────────── version table owners


def test_version_table_owners_constant() -> None:
    from harness.db.grants_declared import VERSION_TABLE_OWNERS

    assert VERSION_TABLE_OWNERS == {
        "alembic_version_product": "alfred_migrator_product",
        "alembic_version_control": "alfred_migrator_control",
        "alembic_version_evidence": "alfred_migrator_evidence",
        "alembic_version_heldout": "alfred_migrator_heldout",
    }


# ────────────────────────────────────────────────────────────────────── edge cases


def test_parse_empty_grants_block_form(tmp_path: Path) -> None:
    yaml = VALID_MINIMAL.replace(
        "grants: {}",
        "grants:\n      test_group: []",
    )
    path = _write_yaml(tmp_path, yaml)
    decl = parse(path)
    assert decl.roles["alfred_test"].grants == {"test_group": ()}


def test_parse_inline_grants_map(tmp_path: Path) -> None:
    yaml = VALID_MINIMAL.replace(
        "grants: {}",
        "grants: {test_group: [U, S]}",
    )
    path = _write_yaml(tmp_path, yaml)
    decl = parse(path)
    assert decl.roles["alfred_test"].grants == {"test_group": ("U", "S")}


def test_parse_block_grants_map(tmp_path: Path) -> None:
    yaml = VALID_MINIMAL.replace(
        "grants: {}",
        "grants:\n      test_group: [U, S]",
    )
    path = _write_yaml(tmp_path, yaml)
    decl = parse(path)
    assert decl.roles["alfred_test"].grants == {"test_group": ("U", "S")}


def test_parse_role_with_owns(tmp_path: Path) -> None:
    yaml = VALID_MINIMAL.replace("owns: []", "owns: [product, control]")
    path = _write_yaml(tmp_path, yaml)
    decl = parse(path)
    assert decl.roles["alfred_test"].owns == ("product", "control")


def test_parse_object_group_with_array_tables(tmp_path: Path) -> None:
    yaml = VALID_MINIMAL.replace(
        'tables: "*"',
        'tables: ["table1", "table2"]',
    )
    path = _write_yaml(tmp_path, yaml)
    decl = parse(path)
    group = decl.object_groups["test_group"]
    assert group.patterns == ("table1", "table2")


def test_parse_object_group_with_except(tmp_path: Path) -> None:
    yaml = VALID_MINIMAL.replace(
        'tables: "*"',
        'tables: "*", except: ["excluded_*"]',
    )
    path = _write_yaml(tmp_path, yaml)
    decl = parse(path)
    group = decl.object_groups["test_group"]
    assert group.excluded == ("excluded_*",)
    assert group.matches("normal_table") is True
    assert group.matches("excluded_table") is False


def test_expand_with_multiple_schemas(tmp_path: Path) -> None:
    yaml = (
        VALID_MINIMAL.replace(
            "schemas: [product]",
            "schemas: [product, control]",
        )
        .replace(
            'test_group: {schema: product, tables: "*"}',
            'product_group: {schema: product, tables: "*"}\n  control_group: {schema: control, tables: "*"}',
        )
        .replace(
            "grants: {}",
            "grants:\n      product_group: [U, S]\n      control_group: [U, S]",
        )
    )
    path = _write_yaml(tmp_path, yaml)
    decl = parse(path)

    tables = {"product": ["p1"], "control": ["c1"]}
    grants, _ownership = expand(decl, tables, "testdb")

    table_grants = [g for g in grants if g.kind == "table"]
    assert len(table_grants) == 2  # 2 schemas * 1 table * 1 privilege (S)
    schema_grants = [g for g in grants if g.kind == "schema"]
    assert len(schema_grants) == 2  # USAGE on product and control schemas


def test_expand_unknown_table_in_group(tmp_path: Path) -> None:
    path = _write_yaml(tmp_path, VALID_MINIMAL)
    decl = parse(path)

    tables = {"product": ["table1"]}
    grants, _ownership = expand(decl, tables, "testdb")

    # Should not raise, just match nothing
    table_grants = [g for g in grants if g.kind == "table"]
    assert len(table_grants) == 0


def test_parse_with_comments(tmp_path: Path) -> None:
    yaml = VALID_MINIMAL + "\n# trailing comment\n"
    path = _write_yaml(tmp_path, yaml)
    decl = parse(path)
    assert decl.version == 1


def test_parse_inline_comment_in_sequence(tmp_path: Path) -> None:
    yaml = VALID_MINIMAL.replace(
        "schemas: [product]",
        "schemas: [product]  # trailing comment",
    )
    path = _write_yaml(tmp_path, yaml)
    decl = parse(path)
    assert decl.schemas == ("product",)


def test_expand_handles_missing_schema_in_tables(tmp_path: Path) -> None:
    path = _write_yaml(tmp_path, VALID_MINIMAL)
    decl = parse(path)

    tables = {"product": []}  # empty tables list
    grants, _ownership = expand(decl, tables, "testdb")

    table_grants = [g for g in grants if g.kind == "table"]
    assert len(table_grants) == 0


# ────────────────────────────────────────────────────────────────────── error paths


def test_parse_schema_create_not_flow_sequence(tmp_path: Path) -> None:
    yaml = VALID_MINIMAL.replace("schema_create: {}", "schema_create:\n  product: not_a_list")
    path = _write_yaml(tmp_path, yaml)
    with pytest.raises(DeclarationError, match="must be flow sequences"):
        parse(path)


def test_parse_object_group_not_flow_map(tmp_path: Path) -> None:
    yaml = VALID_MINIMAL.replace(
        'test_group: {schema: product, tables: "*"}',
        "test_group: not_a_map",
    )
    path = _write_yaml(tmp_path, yaml)
    with pytest.raises(DeclarationError, match="must be single-line flow maps"):
        parse(path)


def test_parse_default_privileges_not_flow_map(tmp_path: Path) -> None:
    yaml = VALID_MINIMAL.replace(
        "default_privileges: {}",
        "default_privileges:\n  test: not_a_map",
    )
    path = _write_yaml(tmp_path, yaml)
    with pytest.raises(DeclarationError, match="must be single-line flow maps"):
        parse(path)


def test_parse_roles_empty(tmp_path: Path) -> None:
    yaml = """version: 1
schemas: [product]
database_connect: [alfred_test]
schema_create: {}
object_groups:
  test_group: {schema: product, tables: "*"}
default_privileges: {}
roles:
role_memberships: []
must_not_exist: []
"""
    path = _write_yaml(tmp_path, yaml)
    decl = parse(path)
    assert decl.roles == {}


def test_parse_role_name_no_colon(tmp_path: Path) -> None:
    yaml = """version: 1
schemas: [product]
database_connect: [alfred_test]
schema_create: {}
object_groups:
  test_group: {schema: product, tables: "*"}
default_privileges: {}
roles:
  alfred_test:
    login: true
    owns: []
    grants: {}
  bad_role
role_memberships: []
must_not_exist: []
"""
    path = _write_yaml(tmp_path, yaml)
    with pytest.raises(DeclarationError, match="expected a role name followed by"):
        parse(path)


# Line 428 ("attribute outside any role") is unreachable: the first child of
# a role block always defines `role_indent` and is treated as a role name,
# so `current` is never `None` when we encounter an indented attribute.
# Kept in source as a safety net; no test can trigger it.
# def test_parse_role_attribute_outside_role(...): ...


def test_parse_role_attribute_no_sep(tmp_path: Path) -> None:
    yaml = VALID_MINIMAL.replace(
        "    login: true",
        "    login true",
    )
    path = _write_yaml(tmp_path, yaml)
    with pytest.raises(DeclarationError, match="expected `key: value`"):
        parse(path)


def test_parse_role_grants_inline_not_closed(tmp_path: Path) -> None:
    yaml = VALID_MINIMAL.replace(
        "grants: {}",
        "grants: {test_group: [U, S]",
    )
    path = _write_yaml(tmp_path, yaml)
    with pytest.raises(DeclarationError, match="inline grants map must close"):
        parse(path)


def test_parse_role_grants_inline_malformed_entry(tmp_path: Path) -> None:
    yaml = VALID_MINIMAL.replace(
        "grants: {}",
        "grants: {test_group [U, S]}",
    )
    path = _write_yaml(tmp_path, yaml)
    with pytest.raises(DeclarationError, match="expected `group: \\[letters\\]`"):
        parse(path)


def test_parse_role_grants_unexpected_text_after_colon(tmp_path: Path) -> None:
    yaml = VALID_MINIMAL.replace(
        "grants: {}",
        "grants: some_text",
    )
    path = _write_yaml(tmp_path, yaml)
    with pytest.raises(DeclarationError, match="unexpected text after"):
        parse(path)


def test_parse_role_grants_block_wrong_indent(tmp_path: Path) -> None:
    yaml = VALID_MINIMAL.replace(
        "grants: {}",
        "grants:\n      test_group: [U, S]\n        bad_indent: [U]",
    )
    path = _write_yaml(tmp_path, yaml)
    with pytest.raises(DeclarationError, match="unexpected indentation inside grants"):
        parse(path)
