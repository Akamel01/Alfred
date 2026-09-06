"""`policy/*.json` — machine-readable Tier 4: the allowlist, the denylist, and the protected set.

**Why this exists.** Issue #5's motivation: the graph cannot answer a policy-edit impact
question. Before this extractor, editing `policy/role-bindings.json` or
`policy/model-routing.json` was invisible to the vault — the only trace was `references`'
D/ADR-number scan of the `_comment` prose, which says nothing about the policy files
relating to *each other*. This extractor mints one node per policy file and the file-to-file
`references` edges the files declare about themselves in their own `authority`/`notes`/
`_comment` fields, so "what does a policy file say it authorizes or defers to" is a graph
fact rather than something a reader re-derives by opening seven JSON files by hand.

**Node granularity is the file, not the entry.** `policy/` holds seven JSON files; each is a
single machine-read record, not a list of independent claims the way `docs/tier1/adr-log.md`
is. Minting a node per `protected-paths.json` prefix or per `role-bindings.json` binding was
considered and rejected for this pass: most of those entries (the eleven protected prefixes,
in particular) name a directory rather than a file `code.py` would have minted a MODULE node
for, so an edge to them would be dangling by construction — a claim the graph cannot check
resolving to a claim the graph cannot check. File granularity is what stays honest.

**Counts are read off the JSON's own shape, never hardcoded.** `count:<key>` mirrors whatever
list- or dict-valued top-level key the file happens to declare (`count:prefixes`,
`count:bindings`, `count:hashes`, ...), computed generically so a file gaining or losing a
top-level collection changes the count without anyone touching this extractor.

**`unset_field_count` — the caution this file's docstring cannot skip.**
`policy/role-bindings.json` has 24 D19 version fields (`prompt_version`, `tool_version`,
`context_strategy_version` × 8 bindings) whose value is the literal string `"unset"`. Modelling
those as real values would assert something the source data explicitly does not claim. So this
extractor counts the literal string `"unset"` wherever it appears (recursively, generically —
not keyed to those three field names) and carries the count as an attribute, never as a title
or a body claim that could be misread as a live version.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Mapping

from ..model import Confidence, Edge, EdgeKind, Node, NodeKind, SourceRef
from ..protocol import Context, ExtractorSpec, Harvest, Unparsed
from ..textio import rel

NAME = "policy"
POLICY_DIR = "policy"

#: The seven files on disk today. Not asserted as a ceiling — `min_nodes` is a floor, and a new
#: policy file must not red the build the way a new `docs/` entry does not red `documents`.
EXPECTED_FILES = 7

_SELF_REF = re.compile(r"policy/[\w-]+\.json")

#: Fields worth mining for a cross-file mention. Each is a place a policy file talks about
#: policy in general or about another policy file specifically — never code, which
#: `references.py` already covers via the `_comment` D/ADR scan.
_PROSE_FIELDS = ("authority", "notes", "_comment")


def _texts(data: object) -> list[str]:
    if not isinstance(data, Mapping):
        return []
    out: list[str] = []
    for field in _PROSE_FIELDS:
        value = data.get(field)
        if isinstance(value, str):
            out.append(value)
        elif isinstance(value, list):
            out.extend(item for item in value if isinstance(item, str))
    return out


def _count_unset(value: object) -> int:
    """How many string leaves anywhere in this JSON are exactly `"unset"`. Recursive and
    generic — it does not know the D19 field names, only the literal placeholder."""
    if isinstance(value, str):
        return 1 if value == "unset" else 0
    if isinstance(value, dict):
        return sum(_count_unset(v) for v in value.values())
    if isinstance(value, list):
        return sum(_count_unset(v) for v in value)
    return 0


def _top_level_counts(data: Mapping) -> dict[str, str]:
    """`count:<key>` for every top-level list or dict the file declares, `_comment` excluded —
    it is prose, not a collection this policy is asserting the size of."""
    counts: dict[str, str] = {}
    for key, value in data.items():
        if key == "_comment":
            continue
        if isinstance(value, (list, dict)):
            counts[f"count:{key}"] = str(len(value))
    return counts


def _title(stem: str) -> str:
    return stem.replace("-", " ").replace("_", " ").title() + " policy"


def extract(ctx: Context) -> Harvest:
    harvest = Harvest()
    policy_dir = ctx.root / POLICY_DIR
    if not policy_dir.is_dir():
        return harvest

    paths = sorted(policy_dir.glob("*.json"))
    harvest.scanned = len(paths)

    by_stem: dict[str, str] = {}   # file stem -> minted node id
    parsed: dict[str, Mapping] = {}
    for path in paths:
        rel_path = rel(path, ctx.root)
        src = SourceRef(rel_path, 1)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            harvest.unparsed.append(Unparsed(NAME, src, rel_path, f"invalid JSON: {error}"))
            continue
        if not isinstance(data, Mapping):
            harvest.unparsed.append(
                Unparsed(NAME, src, rel_path, "top-level JSON value is not an object")
            )
            continue

        stem = path.stem
        node_id = ctx.minter.mint(NodeKind.POLICY, stem, src)
        by_stem[stem] = node_id
        parsed[stem] = data

        authority = data.get("authority", "")
        attrs = {
            "path": rel_path,
            "version": str(data.get("version", "")),
            "authority": authority[:300] if isinstance(authority, str) else "",
            "unset_field_count": str(_count_unset(data)),
        }
        attrs.update(_top_level_counts(data))

        harvest.nodes.append(Node(
            id=node_id,
            kind=NodeKind.POLICY,
            title=_title(stem),
            source=src,
            shape="file",
            attrs=attrs,
            extractor=NAME,
        ))

    # Cross-file mentions: a policy file naming another policy/*.json file in its own
    # authority/notes/_comment prose. Confidence DERIVED — a mechanical regex match inside a
    # constrained span, exactly like `references.py`'s D/ADR scan, not a dedicated relation
    # field with a fixed grammar the way `Discharges:` in the ADR log is.
    seen_edges: set[tuple[str, str]] = set()
    for stem, data in parsed.items():
        src_id = by_stem[stem]
        rel_path = rel(policy_dir / f"{stem}.json", ctx.root)
        for text in _texts(data):
            for match in _SELF_REF.finditer(text):
                target_name = match.group()[len("policy/"):-len(".json")]
                if target_name == stem or target_name not in by_stem:
                    continue
                dst_id = by_stem[target_name]
                key = (src_id, dst_id)
                if key in seen_edges:
                    continue
                seen_edges.add(key)
                harvest.edges.append(Edge(
                    src=src_id, dst=dst_id, kind=EdgeKind.REFERENCES,
                    confidence=Confidence.DERIVED, source=SourceRef(rel_path, 1),
                    evidence=text.strip()[:180], extractor=NAME,
                ))
    return harvest


SPEC = ExtractorSpec(
    name=NAME,
    kinds=(NodeKind.POLICY,),
    min_nodes=EXPECTED_FILES,
    max_nodes=None,
    min_edges=2,
    max_unparsed=0,
    expect_rejected=None,
    run=extract,
)
