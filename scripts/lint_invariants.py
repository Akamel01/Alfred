#!/usr/bin/env python3
"""Cross-stage invariants (I1–I17), and the map of what actually enforces each one.

`docs/tier1/cross-stage-invariants.md` is `status: frozen`, `enforcement: ci-gate`, and
says in its body *"Enforced by CI lint. A violation fails the build."* No file named for
that claim existed (#56). Two of the eight checks its § *What the lint checks* enumerates
were already enforced, by siblings written for other reasons — `lint_migrations.py` for I2
and `lint_verdict_boundary.py` for both I17 clauses. The rest were held by nothing.

This file closes four of the remaining six and, for the last two, says so out loud rather
than leaving a gap the register reads as coverage.

  INV1  (I1)  every table a migration creates declares `org_id` and `project_id`.
  INV6  (I6)  every table a migration creates declares `schema_version`.
  INV4  (I4)  no `uuid4()` and no integer primary key in the product tree.
  INV5  (I5)  every mutating API handler declares an idempotency key.
  INVMAP      every invariant names its enforcement, and every named enforcer exists and
              is wired into CI.

INVMAP is the check that keeps the other four honest. An invariant/enforcer table written
in prose is a table that rots the moment a script is renamed; here the referents are
resolved against the filesystem and against `gates.yml`, so the map fails when it stops
being true rather than when someone next reads it.

------------------------------------------------------------------- what is *not* checked

**I3 (content-addressed artifacts) is not statically checked here, and that is a decision
rather than an omission.** The property is "an artifact write goes through the
content-addressed store, never a raw path". Every static form of that check reduces to an
allowlist of modules permitted to write bytes, and the tree has seventeen legitimate byte
writes — bench reports, fixture generation, the restore drill's anchor, the ACS vector
generator. An allowlist that admits all of them discriminates nothing, and a check that
cannot fail is the wish `scripts/lint_ci_coverage.py` exists to name. What holds I3 today
is the `evidence.artifact` table's `uq_artifact_content` uniqueness over
`(org_id, project_id, content_sha256)` — a database constraint, not a lint.

**Scope of INV4 is `src/` and `migrations/`.** `harness/evidence/store.py:322` calls
`uuid.uuid4()` for the primary key of every evidence row, which is exactly what I4 says
not to do — the chain is written serially and in time order, and a v4 key throws away the
sortability I4 is bought for. It is named here rather than checked because `harness/` is
the inspector (D20): an agent may not edit it, so a gate an agent cannot clear is a gate
that gets worked around. Filed, not swept.

Exit 0 clean, 1 on any violation. Protected set: agents may not write this file.
"""

from __future__ import annotations

import argparse
import ast
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from _lintkit import REPO_ROOT, Findings, self_test_exit, vacuity_guard

MIGRATIONS: Final = Path("migrations")
API: Final = Path("src/api")
PRODUCT_TREES: Final = (Path("src"), Path("migrations"))
WORKFLOW: Final = Path(".github/workflows/gates.yml")

#: The envelope every table carries. Named once: I1 owns the first two and I6 the third,
#: and they are checked in one pass because they are declared in one place.
TENANCY: Final = ("org_id", "project_id")
VERSIONED: Final = ("schema_version",)

#: I10. Every record carries what caused it. Nullable on the first record of a chain and
#: on nothing else, which is a constraint the database holds; what this file checks is
#: that the column is declared at all, because a causality link that was never stored
#: cannot be reconstructed afterwards.
CAUSAL: Final = ("caused_by",)

#: Integer column types that must never be a primary key (I4). A sortable identifier is
#: the point; a sequence is sortable and also guessable, enumerable and non-portable
#: across the three databases, which is why I4 names UUIDv7 rather than "something
#: ordered".
INTEGER_TYPES: Final = frozenset({"Integer", "BigInteger", "SmallInteger"})

#: Non-sortable UUID constructors. v7 is the one I4 names; every other version either
#: carries no timestamp or carries one nobody can order on.
FORBIDDEN_UUID: Final = frozenset({"uuid1", "uuid3", "uuid4", "uuid5"})

#: The HTTP methods that mutate. `get` and `head` are absent because an idempotency key on
#: a read is a key that means nothing.
MUTATING_METHODS: Final = frozenset({"post", "put", "patch", "delete"})

IDEMPOTENCY_PARAM: Final = "idempotency_key"


@dataclass(frozen=True)
class Enforcement:
    """Where an invariant is actually held.

    `kind` is `here` (a check in this file), `script` (a sibling lint, named), or `review`
    (held by a human, with the reason stated). There is no fourth value, and in particular
    no value meaning "assumed": an invariant with no enforcement is a row this map refuses
    to carry.
    """

    kind: str
    detail: str


#: Every invariant, and what holds it. This is the table `cross-stage-invariants.md`
#: describes in prose; here it is resolved against the filesystem, so it fails when a
#: named enforcer is renamed or dropped rather than when someone next reads the document.
ENFORCEMENT: Final[dict[str, Enforcement]] = {
    "I1": Enforcement("here", "INV1"),
    "I2": Enforcement("script", "scripts/lint_migrations.py"),
    "I3": Enforcement(
        "review",
        "held by the evidence.artifact uq_artifact_content constraint, not by a lint; "
        "every static form reduces to an allowlist that admits every legitimate write",
    ),
    "I4": Enforcement("here", "INV4"),
    "I5": Enforcement("here", "INV5"),
    "I6": Enforcement("here", "INV6"),
    "I7": Enforcement("review", "no long-running endpoint exists yet; S8 under D13"),
    "I8": Enforcement("review", "no tracing backend is wired; the invariant is a build convention"),
    "I9": Enforcement(
        "review",
        "the attempt_end split (agent_ms / criterion_ms / harness_ms) is specified and "
        "not yet produced by anything a lint could read",
    ),
    "I10": Enforcement("here", "INV10"),
    "I11": Enforcement(
        "review",
        "scripts/capture_run_fingerprint.py records the pins; recording is not enforcing, "
        "and calling it enforcement is the over-claim this map exists to prevent",
    ),
    "I12": Enforcement("review", "port separation is reviewed per module; no static form exists"),
    "I13": Enforcement(
        "review",
        "policy/*.json is the configuration and scripts/lint_topology.py reads it, but "
        "nothing checks that a threshold was not also hard-coded somewhere",
    ),
    "I14": Enforcement(
        "review",
        "harness/evidence/restore_drill.py performs the drill; no lint asserts it ran",
    ),
    "I15": Enforcement(
        "review",
        "harness/evidence/store.py chains and verify_chain re-walks; the off-machine "
        "anchor is operational, not static",
    ),
    "I16": Enforcement("review", "no compaction path exists to assert off yet"),
    "I17": Enforcement("script", "scripts/lint_verdict_boundary.py"),
}


# --------------------------------------------------------------------------- AST helpers


def _column_names(call: ast.Call, helpers: dict[str, list[str]]) -> list[str]:
    """The column names a `create_table` call declares, resolving one helper level.

    One level, not arbitrarily many, and the bound is deliberate. Every migration in the
    tree spreads a single module-level `_envelope()` into each table; a check that only
    read literal `sa.Column(...)` arguments would report every table as missing every
    envelope column, and a check that chased helpers recursively would be answering a
    question the tree does not ask. When a second level appears, this raises the bound —
    visibly, in a diff — rather than silently under-reporting.
    """
    names: list[str] = []
    for arg in call.args:
        if isinstance(arg, ast.Starred):
            inner = arg.value
            if isinstance(inner, ast.Call) and isinstance(inner.func, ast.Name):
                names += helpers.get(inner.func.id, [])
            continue
        if isinstance(arg, ast.Call) and _attr_is(arg.func, "Column") and arg.args:
            first = arg.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                names.append(first.value)
    return names


def _attr_is(node: ast.expr, name: str) -> bool:
    return isinstance(node, ast.Attribute) and node.attr == name


def _helper_columns(tree: ast.Module) -> dict[str, list[str]]:
    """Module-level functions mapped to every column name they mention."""
    helpers: dict[str, list[str]] = {}
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        columns: list[str] = []
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call) and _attr_is(sub.func, "Column") and sub.args:
                first = sub.args[0]
                if isinstance(first, ast.Constant) and isinstance(first.value, str):
                    columns.append(first.value)
        helpers[node.name] = columns
    return helpers


def _tables(tree: ast.Module) -> list[tuple[str, int, list[str], ast.Call]]:
    """Every `create_table` in a module as `(table, line, column names, call)`."""
    helpers = _helper_columns(tree)
    found: list[tuple[str, int, list[str], ast.Call]] = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and _attr_is(node.func, "create_table")):
            continue
        name = "<unnamed>"
        if node.args and isinstance(node.args[0], ast.Constant):
            name = str(node.args[0].value)
        found.append((name, node.lineno, _column_names(node, helpers), node))
    return found


def _migration_files(root: Path) -> list[Path]:
    return sorted(root.rglob("versions/*.py"))


def _python_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if not p.name.startswith("test_"))


# ------------------------------------------------------------------------------- checks


def check_envelope(root: Path, *, required: tuple[str, ...], label: str) -> Findings:
    """INV1 and INV6: every created table declares the named envelope columns.

    One traversal for both because the columns are declared in one place. Splitting it
    would double the parse and let the two answers disagree about which tables exist.
    """
    findings = Findings()
    for path in _migration_files(root):
        findings.scanned += 1
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            findings.violations.append(f"{path}: does not parse ({exc})")
            continue
        for table, line, columns, _ in _tables(tree):
            missing = [name for name in required if name not in columns]
            if missing:
                findings.violations.append(
                    f"{path}:{line}: table `{table}` declares no {', '.join(missing)} "
                    f"— {label}"
                )
    return findings


def check_identifiers(roots: tuple[Path, ...]) -> Findings:
    """INV4: no non-sortable UUID constructor, and no integer primary key.

    Both directions of one property. A `uuid4()` key is unordered; an integer key is
    ordered and is a sequence, which is a different defect with the same cause — reaching
    for whatever the database hands you instead of an identifier the domain owns.
    """
    findings = Findings()
    for root in roots:
        if not root.is_dir():
            continue
        for path in _python_files(root):
            findings.scanned += 1
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError as exc:
                findings.violations.append(f"{path}: does not parse ({exc})")
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    called = node.func
                    name = (
                        called.attr
                        if isinstance(called, ast.Attribute)
                        else called.id
                        if isinstance(called, ast.Name)
                        else ""
                    )
                    if name in FORBIDDEN_UUID:
                        findings.violations.append(
                            f"{path}:{node.lineno}: `{name}()` — I4 names UUIDv7; "
                            "src/domain/ids.py:uuid7 is the one constructor"
                        )
                if not (isinstance(node, ast.Call) and _attr_is(node.func, "Column")):
                    continue
                primary = any(
                    kw.arg == "primary_key"
                    and isinstance(kw.value, ast.Constant)
                    and kw.value.value is True
                    for kw in node.keywords
                )
                if not primary:
                    continue
                for arg in node.args[1:]:
                    if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Attribute):
                        if arg.func.attr in INTEGER_TYPES:
                            column = (
                                node.args[0].value
                                if node.args and isinstance(node.args[0], ast.Constant)
                                else "?"
                            )
                            findings.violations.append(
                                f"{path}:{node.lineno}: primary key `{column}` is "
                                f"{arg.func.attr} — an integer key is a sequence, "
                                "guessable and enumerable, and I4 names UUIDv7"
                            )
    return findings


def check_idempotency(root: Path) -> Findings:
    """INV5: every mutating route handler declares an idempotency key parameter.

    The check scans files, not handlers, and reports the file count. Today the API has two
    modules and no mutating route, so the property holds over an empty set — which is a
    true statement about the tree and a false one about the check's strength. The scanned
    count is what says which of those a green line means.
    """
    findings = Findings()
    if not root.is_dir():
        return findings
    for path in _python_files(root):
        findings.scanned += 1
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            findings.violations.append(f"{path}: does not parse ({exc})")
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            methods = {
                decorator.func.attr
                for decorator in node.decorator_list
                if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute)
            }
            if not (methods & MUTATING_METHODS):
                continue
            args = node.args
            names = {a.arg for a in (*args.posonlyargs, *args.args, *args.kwonlyargs)}
            if IDEMPOTENCY_PARAM not in names:
                findings.violations.append(
                    f"{path}:{node.lineno}: mutating handler `{node.name}` declares no "
                    f"`{IDEMPOTENCY_PARAM}` — retries are inevitable from Phase 3 and "
                    "without a key they corrupt (I5)"
                )
    return findings


def check_enforcement_map(root: Path, workflow: Path) -> Findings:
    """INVMAP: every invariant names an enforcement, and every named enforcer is real.

    Three ways the map can be wrong, and all three fail:

      - a `script` referent that is not a file, so the map names a lint that was renamed
        or deleted;
      - a `script` referent that no CI workflow invokes, so the lint exists and never
        runs, which reads identically to enforcement from inside the document;
      - a `here` referent naming a check this file does not define.

    The `review` rows are not resolved against anything, and cannot be: what makes a
    review row honest is that it states its reason, which is checked for presence and can
    only be checked for presence.
    """
    findings = Findings()
    resolved = root / workflow
    workflow_text = resolved.read_text(encoding="utf-8") if resolved.is_file() else ""
    if not workflow_text:
        findings.violations.append(
            f"{workflow}: unreadable — the map cannot tell an enforced lint from an "
            "unwired one without it"
        )
    local = {"INV1", "INV4", "INV5", "INV6", "INV10"}
    for invariant, enforcement in sorted(ENFORCEMENT.items(), key=lambda kv: int(kv[0][1:])):
        findings.scanned += 1
        if enforcement.kind == "script":
            target = root / enforcement.detail
            if not target.is_file():
                findings.violations.append(
                    f"{invariant}: names `{enforcement.detail}`, which is not a file"
                )
            elif workflow_text and enforcement.detail not in workflow_text:
                findings.violations.append(
                    f"{invariant}: names `{enforcement.detail}`, which {workflow} never "
                    "invokes — a lint that does not run reads exactly like one that passes"
                )
        elif enforcement.kind == "here":
            if enforcement.detail not in local:
                findings.violations.append(
                    f"{invariant}: names check `{enforcement.detail}`, which this file "
                    "does not define"
                )
        elif enforcement.kind == "review":
            if not enforcement.detail.strip():
                findings.violations.append(
                    f"{invariant}: is held by review and states no reason — a review row "
                    "with no reason is an unenforced row with a nicer name"
                )
        else:
            findings.violations.append(
                f"{invariant}: enforcement kind `{enforcement.kind}` is not one of "
                "here/script/review"
            )
    return findings


# ---------------------------------------------------------------------------- self-test


_MIGRATION = '''
import sqlalchemy as sa
from alembic import op


def _envelope():
    return [
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("caused_by", sa.Uuid(), nullable=True),
    ]


def upgrade():
    op.create_table("thing", *_envelope(), sa.Column("body", sa.Text()))
'''

_MIGRATION_NO_TENANCY = _MIGRATION.replace(
    '        sa.Column("org_id", sa.Uuid(), nullable=False),\n', ""
)
_MIGRATION_NO_VERSION = _MIGRATION.replace(
    '        sa.Column("schema_version", sa.Integer(), nullable=False),\n', ""
)
_MIGRATION_NO_CAUSE = _MIGRATION.replace(
    '        sa.Column("caused_by", sa.Uuid(), nullable=True),\n', ""
)
_MIGRATION_INT_PK = _MIGRATION.replace(
    'sa.Column("id", sa.Uuid(), primary_key=True)',
    'sa.Column("id", sa.BigInteger(), primary_key=True)',
)

_API_CLEAN = '''
from fastapi import FastAPI

app = FastAPI()


@app.get("/thing")
def read_thing() -> dict[str, str]:
    return {}


@app.post("/thing")
def make_thing(idempotency_key: str) -> dict[str, str]:
    return {}
'''

_API_MISSING = _API_CLEAN.replace("def make_thing(idempotency_key: str)", "def make_thing()")

_UUID4 = "import uuid\n\n\ndef row_id():\n    return uuid.uuid4()\n"


def _plant(root: Path, relative: str, text: str) -> None:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def self_test() -> int:
    """Plant each violation, require the check to fire, require its control to stay quiet."""
    failures: list[str] = []

    def expect(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    with tempfile.TemporaryDirectory() as raw:
        scratch = Path(raw)

        # --- INV1 / INV6 -----------------------------------------------------
        clean = scratch / "clean"
        _plant(clean, "migrations/x/versions/0001_x.py", _MIGRATION)
        control = check_envelope(clean / "migrations", required=TENANCY, label="I1")
        expect(not control.violations, f"clean migration failed INV1: {control.violations}")
        expect(control.scanned == 1, f"INV1 control scanned {control.scanned}, expected 1")
        version_control = check_envelope(clean / "migrations", required=VERSIONED, label="I6")
        expect(not version_control.violations,
               f"clean migration failed INV6: {version_control.violations}")

        no_tenancy = scratch / "no_tenancy"
        _plant(no_tenancy, "migrations/x/versions/0001_x.py", _MIGRATION_NO_TENANCY)
        planted = check_envelope(no_tenancy / "migrations", required=TENANCY, label="I1")
        expect(any("org_id" in v for v in planted.violations),
               f"a table with no org_id passed INV1: {planted.violations}")

        causal_control = check_envelope(clean / "migrations", required=CAUSAL, label="I10")
        expect(not causal_control.violations,
               f"clean migration failed INV10: {causal_control.violations}")

        no_cause = scratch / "no_cause"
        _plant(no_cause, "migrations/x/versions/0001_x.py", _MIGRATION_NO_CAUSE)
        planted = check_envelope(no_cause / "migrations", required=CAUSAL, label="I10")
        expect(any("caused_by" in v for v in planted.violations),
               f"a table with no caused_by passed INV10: {planted.violations}")

        no_version = scratch / "no_version"
        _plant(no_version, "migrations/x/versions/0001_x.py", _MIGRATION_NO_VERSION)
        planted = check_envelope(no_version / "migrations", required=VERSIONED, label="I6")
        expect(any("schema_version" in v for v in planted.violations),
               f"a table with no schema_version passed INV6: {planted.violations}")

        # The vacuity guard, aimed at the envelope check itself.
        empty = check_envelope(scratch / "nothing-here", required=TENANCY, label="I1")
        expect(empty.scanned == 0, "an empty tree did not report zero migrations scanned")

        # --- INV4 ------------------------------------------------------------
        ok_ids = check_identifiers((clean / "migrations",))
        expect(not ok_ids.violations, f"clean migration failed INV4: {ok_ids.violations}")

        int_pk = scratch / "int_pk"
        _plant(int_pk, "migrations/x/versions/0001_x.py", _MIGRATION_INT_PK)
        planted = check_identifiers((int_pk / "migrations",))
        expect(any("BigInteger" in v for v in planted.violations),
               f"an integer primary key passed INV4: {planted.violations}")

        v4 = scratch / "v4"
        _plant(v4, "src/thing.py", _UUID4)
        planted = check_identifiers((v4 / "src",))
        expect(any("uuid4" in v for v in planted.violations),
               f"a uuid4 call passed INV4: {planted.violations}")

        # --- INV5 ------------------------------------------------------------
        api_ok = scratch / "api_ok"
        _plant(api_ok, "src/api/app.py", _API_CLEAN)
        control = check_idempotency(api_ok / "src/api")
        expect(not control.violations, f"a keyed handler failed INV5: {control.violations}")
        expect(control.scanned == 1, f"INV5 control scanned {control.scanned}, expected 1")

        api_bad = scratch / "api_bad"
        _plant(api_bad, "src/api/app.py", _API_MISSING)
        planted = check_idempotency(api_bad / "src/api")
        expect(any("make_thing" in v for v in planted.violations),
               f"an unkeyed mutating handler passed INV5: {planted.violations}")

        # A GET handler with no key is not a violation: an idempotency key on a read
        # means nothing, and a check that demanded one would be trained around.
        read_only = _API_CLEAN.replace('@app.post("/thing")\ndef make_thing(idempotency_key: str)',
                                       '@app.get("/other")\ndef other_thing()')
        api_read = scratch / "api_read"
        _plant(api_read, "src/api/app.py", read_only)
        expect(not check_idempotency(api_read / "src/api").violations,
               "a GET handler with no idempotency key was reported")

        # --- INVMAP ----------------------------------------------------------
        expect(not check_enforcement_map(REPO_ROOT, WORKFLOW).violations,
               "the enforcement map does not resolve against the repository")

        broken = scratch / "broken_map"
        _plant(broken, WORKFLOW.as_posix(), "jobs: {}\n")
        planted = check_enforcement_map(broken, WORKFLOW)
        expect(any("is not a file" in v for v in planted.violations),
               f"a map naming an absent lint passed: {planted.violations}")

    return self_test_exit(
        failures,
        "OK self-test — a clean migration passes INV1/INV6/INV10 and a table missing any "
        "of the three fails, an empty tree reports zero scanned, an integer primary key "
        "and a uuid4 "
        "call fail INV4 while a UUIDv7 table passes, an unkeyed mutating handler fails "
        "INV5 while a keyed one and a GET pass, and a map naming an absent lint fails\n",
    )


# --------------------------------------------------------------------------------- main


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cross-stage invariant lint (I1–I17).")
    parser.add_argument("--self-test", action="store_true",
                        help="plant violations and verify each check fires")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()

    checks: list[tuple[str, Findings]] = [
        ("INV1 tenancy", check_envelope(REPO_ROOT / MIGRATIONS, required=TENANCY, label="I1")),
        ("INV6 schema_version",
         check_envelope(REPO_ROOT / MIGRATIONS, required=VERSIONED, label="I6")),
        ("INV10 causality", check_envelope(REPO_ROOT / MIGRATIONS, required=CAUSAL, label="I10")),
        ("INV4 identifiers",
         check_identifiers(tuple(REPO_ROOT / tree for tree in PRODUCT_TREES))),
        ("INV5 idempotency", check_idempotency(REPO_ROOT / API)),
        ("INVMAP enforcement", check_enforcement_map(REPO_ROOT, WORKFLOW)),
    ]

    violations = 0
    vacuous = False
    for label, findings in checks:
        for violation in findings.violations:
            sys.stdout.write(f"FAIL {violation}\n")
        violations += len(findings.violations)
        if vacuity_guard(findings.scanned, f"VACUOUS {label}: scanned 0 items\n"):
            vacuous = True

    if violations or vacuous:
        sys.stdout.write(f"\n{violations} invariant violation(s)\n")
        return 1

    summary = ", ".join(f"{label.split()[0]}={findings.scanned}" for label, findings in checks)
    review_held = sorted(
        (key for key, value in ENFORCEMENT.items() if value.kind == "review"),
        key=lambda key: int(key[1:]),
    )
    sys.stdout.write(
        f"OK cross-stage invariants ({summary} items scanned); "
        f"{', '.join(review_held)} are held by review, each with its reason in "
        "ENFORCEMENT\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
