"""SCHEMA nodes for migrations/: one per declared schema directory, one per Alembic revision.

The directory set and the never-agent-migrated markers are declared in SCHEMA_DECLARATIONS,
never inferred from a path. policy/protected-paths.json is read at extract time and every row
is checked against it; a disagreement is an Unparsed, and schema.SPEC.max_unparsed == 0 makes
it fatal. Revision identity comes from the file's own revision/down_revision/SCHEMA
assignments.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from ..model import Confidence, Edge, EdgeKind, Node, NodeKind, SourceRef
from ..protocol import Context, Harvest, Unparsed


NAME = "schema"
POLICY_PATH = "policy/protected-paths.json"

SCHEMA_DECLARATIONS: tuple[tuple[str, bool, bool], ...] = (
    # rel_dir, agent_migratable, additive_only_lint
    ("migrations/product", True, False),
    ("migrations/harness/control", False, False),
    ("migrations/harness/evidence", False, True),
    ("migrations/harness/heldout", False, True),
    ("migrations/roles", False, False),
)

_REVISION = re.compile(r'^revision\s*(?::\s*str)?\s*=\s*"([^"]+)"')
_DOWN = re.compile(r'^down_revision\s*(?::[^=]+)?\s*=\s*(?:"([^"]+)"|None)\s*(?:#.*)?$')
_SCHEMA = re.compile(r'^SCHEMA\s*=\s*"([^"]+)"')


def _policy_prefixes(root: Path) -> tuple[list[str] | None, str | None]:
    """(prefixes, problem). `problem` is a complete reason string, or None."""
    policy_path = root / POLICY_PATH
    if not policy_path.exists():
        return None, f"schema marker cannot be checked: {POLICY_PATH} is missing"
    try:
        text = policy_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None, f"schema marker cannot be checked: {POLICY_PATH} is missing"
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, f"schema marker cannot be checked: {POLICY_PATH} is not valid JSON: {exc}"
    if not isinstance(data, dict):
        return None, f"schema marker cannot be checked: {POLICY_PATH} is not a JSON object with a prefixes list"
    prefixes = data.get("prefixes")
    if not isinstance(prefixes, list):
        return None, f"schema marker cannot be checked: {POLICY_PATH} is not a JSON object with a prefixes list"
    out = []
    for entry in prefixes:
        if isinstance(entry, str):
            out.append(entry)
        elif isinstance(entry, dict) and isinstance(entry.get("path"), str):
            out.append(entry["path"])
        else:
            return None, f"schema marker cannot be checked: {POLICY_PATH} is not a JSON object with a prefixes list"
    if not out:
        return None, f"schema marker cannot be checked: {POLICY_PATH} is not a JSON object with a prefixes list"
    return out, None


def _revision_id(schema_local: str, revision: str) -> str:
    return f"schema:{schema_local}/{revision}"


def extract(ctx: Context) -> Harvest:
    root = ctx.root
    harvest = Harvest()
    prefixes, problem = _policy_prefixes(root)

    if problem is not None:
        harvest.unparsed.append(Unparsed(
            extractor=NAME,
            text=POLICY_PATH,
            source=SourceRef(POLICY_PATH, 1),
            reason=problem,
        ))

    for rel_dir, agent_migratable, additive_only_lint in SCHEMA_DECLARATIONS:
        directory = root / rel_dir
        if not directory.is_dir():
            continue
        harvest.scanned += 1
        schema_local = rel_dir.removeprefix("migrations/")
        src = SourceRef(rel_dir, 1)
        directory_id = ctx.minter.mint(NodeKind.SCHEMA, schema_local, src)
        versions_dir = directory / "versions"
        version_files = []
        if versions_dir.is_dir():
            version_files = sorted(versions_dir.glob("*.py"))
        harvest.nodes.append(Node(
            id=directory_id, kind=NodeKind.SCHEMA,
            title=schema_local, source=src, shape="migration-tree",
            attrs={
                "path": rel_dir,
                "migrations": str(len(version_files)),
                "protected": str(not agent_migratable).lower(),
                "agent_migratable": str(agent_migratable).lower(),
                "additive_only_lint": str(additive_only_lint).lower(),
            },
            tags=("protected",) if not agent_migratable else (),
            extractor=NAME,
        ))

        if prefixes is not None:
            target = rel_dir.rstrip("/") + "/"
            match = next((p for p in prefixes if target == p or target.startswith(p)), None)
            protected_by_policy = match is not None
            if (not agent_migratable) != protected_by_policy:
                if agent_migratable:
                    reason = (
                        f"schema marker disagreement for {rel_dir}/: SCHEMA_DECLARATIONS says "
                        f"agent_migratable=true; {POLICY_PATH} protects it via prefix '{match}'"
                    )
                else:
                    reason = (
                        f"schema marker disagreement for {rel_dir}/: SCHEMA_DECLARATIONS says "
                        f"agent_migratable=false; {POLICY_PATH} does not protect it"
                    )
                harvest.unparsed.append(Unparsed(
                    extractor=NAME,
                    text=rel_dir + "/",
                    source=SourceRef(POLICY_PATH, 1),
                    reason=reason,
                ))

        if not versions_dir.is_dir():
            continue
        for vf in version_files:
            harvest.scanned += 1
            rel_path = str(vf.relative_to(root))
            lines = vf.read_text(encoding="utf-8").splitlines()
            revision = None
            revision_line = 0
            for i, line in enumerate(lines, 1):
                m = _REVISION.match(line.strip())
                if m and revision is None:
                    revision = m.group(1)
                    revision_line = i
            down_revision = "UNSET"
            down_line = 0
            down_line_text = ""
            for i, line in enumerate(lines, 1):
                s = line.strip()
                m = _DOWN.match(s)
                if m:
                    down_line = i
                    down_line_text = s
                    down_revision = m.group(1)
                    break
            declared_schema = None
            for i, line in enumerate(lines, 1):
                m = _SCHEMA.match(line.strip())
                if m:
                    declared_schema = m.group(1)
                    break

            if revision is None:
                harvest.unparsed.append(Unparsed(
                    extractor=NAME, text=rel_path,
                    source=SourceRef(rel_path, 1),
                    reason=f"missing revision assignment in {rel_path}",
                ))
                continue
            if down_line == 0:
                harvest.unparsed.append(Unparsed(
                    extractor=NAME, text=rel_path,
                    source=SourceRef(rel_path, 1),
                    reason=f"missing down_revision assignment in {rel_path}",
                ))
                continue
            if declared_schema is None:
                harvest.unparsed.append(Unparsed(
                    extractor=NAME, text=rel_path,
                    source=SourceRef(rel_path, 1),
                    reason=f"missing SCHEMA assignment in {rel_path}",
                ))
                continue
            expected = rel_dir.rstrip("/").rsplit("/", 1)[-1]
            if declared_schema != expected:
                harvest.unparsed.append(Unparsed(
                    extractor=NAME, text=rel_path,
                    source=SourceRef(rel_path, 1),
                    reason=f"SCHEMA mismatch in {rel_path}",
                ))
                continue

            revision_source = SourceRef(rel_path, revision_line)
            rid = ctx.minter.mint(NodeKind.SCHEMA, f"{schema_local}/{revision}", revision_source)
            harvest.nodes.append(Node(
                id=rid, kind=NodeKind.SCHEMA,
                title=revision, source=revision_source, shape="migration-revision",
                attrs={
                    "path": rel_path,
                    "revision": revision,
                    "down_revision": down_revision if down_revision is not None else "none",
                    "schema": declared_schema,
                },
                extractor=NAME,
            ))
            harvest.edges.append(Edge(
                src=directory_id, dst=rid, kind=EdgeKind.CONTAINS,
                confidence=Confidence.STRUCTURAL,
                source=SourceRef(rel_path, revision_line),
                evidence=rel_path, extractor=NAME,
            ))
            if down_revision is not None:
                target_id = _revision_id(schema_local, down_revision)
                harvest.edges.append(Edge(
                    src=rid, dst=target_id, kind=EdgeKind.REVISES,
                    confidence=Confidence.STRUCTURAL,
                    source=SourceRef(rel_path, down_line),
                    evidence=down_line_text.strip(), extractor=NAME,
                ))

    return harvest


from ..protocol import ExtractorSpec

SPEC = ExtractorSpec(
    name=NAME,
    kinds=(NodeKind.SCHEMA,),
    min_nodes=10,
    max_nodes=None,
    min_edges=6,
    max_unparsed=0,
    expect_rejected=None,
    run=extract,
)
