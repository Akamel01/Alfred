#!/usr/bin/env python3
"""Additive-only lint over the evidence and held-out migration directories.

docs/tier1/data-architecture.md § Additive-only. This is the **second** layer over the
grant matrix, not the first. The grant makes the destructive write impossible for every
role that runs; this lint catches the migration that would grant itself the ability by
owning the table, which is the one path the matrix cannot close.

Two checks, deliberately of different kinds:

  AST  — an `op.<name>` call from the rejected set. Structural, so it cannot be
         evaded by formatting, and it sees through aliasing of the call target.
  TEXT — a destructive SQL keyword inside any string literal. `op.execute` takes a
         string, so the AST alone sees an opaque blob; the text check reads inside it.

Neither subsumes the other, and that is the point. A single check of either kind reads
as coverage while leaving the other half open.

`downgrade()` must be a single raise. A downgrade that drops an evidence table is the
same defect wearing a reversible name, so "reversible" is not a defence here.

Exit 0 clean, 1 on any violation. Prints file:line for every finding.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

# Directories whose migrations are additive-only. `product` and `control` are absent
# deliberately: product schema is agent-writable and ordinary schema evolution there
# is expected, and control carries configuration rather than evidence.
GUARDED = (
    Path("migrations/harness/evidence/versions"),
    Path("migrations/harness/heldout/versions"),
)

# Alembic operations that destroy or rewrite existing rows or columns.
REJECTED_OPS = frozenset(
    {
        "drop_table",
        "drop_column",
        "drop_constraint",
        "drop_index",
        "alter_column",
        "rename_table",
        "bulk_insert",  # takes a table object and rows; use a migration, not a load
    }
)

# Destructive statements inside a string literal, most often reached via op.execute.
# Word-bounded so `updated_at` does not match UPDATE and `deleted` does not match
# DELETE — a lint that cries wolf on a column name gets disabled within a week.
DESTRUCTIVE_SQL = re.compile(
    r"\b(UPDATE|DELETE\s+FROM|TRUNCATE|DROP\s+(TABLE|COLUMN|SCHEMA|INDEX|CONSTRAINT)"
    r"|ALTER\s+\w+\s+ALTER\s+COLUMN|ALTER\s+TABLE\s+\w+\s+DROP)\b",
    re.IGNORECASE,
)


class Finding:
    def __init__(self, path: Path, line: int, message: str) -> None:
        self.path = path
        self.line = line
        self.message = message

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.message}"


def _call_name(node: ast.Call) -> str | None:
    """`op.drop_table(...)` -> 'drop_table'. Anything else -> None."""
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def check_file(path: Path) -> list[Finding]:
    source = path.read_text(encoding="utf-8")
    findings: list[Finding] = []

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        # A migration that does not parse is a failure, never a skip. A linter that
        # ignores what it cannot read passes exactly the file worth catching.
        return [Finding(path, exc.lineno or 0, f"does not parse: {exc.msg}")]

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = _call_name(node)
            if name in REJECTED_OPS:
                findings.append(
                    Finding(path, node.lineno, f"rejected operation `{name}` — this directory is additive-only")
                )
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            match = DESTRUCTIVE_SQL.search(node.value)
            if match:
                findings.append(
                    Finding(
                        path,
                        node.lineno,
                        f"destructive SQL in a string literal: `{match.group(0).strip()}`",
                    )
                )

    findings.extend(_check_downgrade(path, tree))
    return findings


def _check_downgrade(path: Path, tree: ast.Module) -> list[Finding]:
    """`downgrade()` must be a single raise, and nothing else."""
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "downgrade":
            body = [stmt for stmt in node.body if not _is_docstring(stmt)]
            if len(body) == 1 and isinstance(body[0], ast.Raise):
                return []
            return [
                Finding(
                    path,
                    node.lineno,
                    "downgrade() must be a single `raise` — a downgrade that drops an "
                    "evidence table is the same defect wearing a reversible name",
                )
            ]
    return [Finding(path, 1, "no downgrade() defined; it must exist and must raise")]


def _is_docstring(stmt: ast.stmt) -> bool:
    return isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str)


def main() -> int:
    findings: list[Finding] = []
    checked = 0

    for directory in GUARDED:
        if not directory.is_dir():
            print(f"error: {directory} does not exist", file=sys.stderr)
            return 1
        for path in sorted(directory.glob("*.py")):
            if path.name == "__init__.py":
                continue
            checked += 1
            findings.extend(check_file(path))

    for finding in findings:
        print(finding, file=sys.stderr)

    if findings:
        print(f"\n{len(findings)} violation(s) in {checked} migration(s)", file=sys.stderr)
        return 1

    # Zero migrations is currently the true state and is reported as such rather than
    # as a pass. "0 files checked, OK" and "12 files checked, OK" are different facts,
    # and a lint that renders them identically is how an empty guard reads as a green
    # one — the same three-valued distinction the verdict vocabulary makes.
    if checked == 0:
        print("OK — no migrations to check yet (evidence and held-out versions/ are empty)")
    else:
        print(f"OK — {checked} migration(s), additive-only")
    return 0


if __name__ == "__main__":
    sys.exit(main())
