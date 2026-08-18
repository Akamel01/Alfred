"""The graph's type vocabulary: what a node is, what an edge is, and how ids are minted.

**Ids are minted, never assigned.** `mint()` is the only way a node id is created, and it
asserts three properties the rest of the design silently assumes: that an id is unique, that
it does not collide with another id under case-folding, and that it is spelled in a character
set a filename can carry on every platform. The second one is the reason this function exists
rather than an f-string at each call site — two ids differing only in case are the same file
on macOS and two files on Linux, which makes the vault non-deterministic across the two
machines that will build it.

**Confidence is a required field on every edge.** An edge parsed out of a table column and an
edge guessed from a prose verb are not the same claim, and a graph that renders them
identically is asserting something it does not know. There is no default: the extractor
author has to say which one it is.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Mapping


class NodeKind(StrEnum):
    DOCUMENT = "document"
    ADR = "adr"
    STAGE = "stage"
    OPERATOR_ITEM = "operator-item"
    KILL_CRITERION = "kill-criterion"
    RISK = "risk"
    DECISION = "decision"
    AMENDMENT = "amendment"
    PHASE = "phase"
    PORT = "port"
    INVARIANT = "invariant"
    MAJOR_FIX = "major-fix"
    OPEN_ITEM = "open-item"
    MODULE = "module"
    SCHEMA = "schema"
    GATE = "gate"
    GATE_STEP = "gate-step"
    TIER = "tier"
    UNRESOLVED = "unresolved"


class EdgeKind(StrEnum):
    FALSIFIES = "falsifies"
    SUPERSEDES = "supersedes"
    SUPERSEDED_BY = "superseded_by"
    AMENDS = "amends"
    AMENDED_BY = "amended_by"
    SEE_ALSO = "see_also"
    BLOCKS = "blocks"
    ENFORCED_BY = "enforced_by"
    ENFORCES = "enforces"
    CONTAINS = "contains"
    NEEDS = "needs"
    OWNED_BY = "owned_by"
    IN_PHASE = "in_phase"
    READING_KIND = "reading_kind"
    REFERENCES = "references"
    RESTATES = "restates"
    PROTECTED = "protected"
    DECLARES_ABSENT = "declares_absent"


class Confidence(StrEnum):
    #: Parsed from a dedicated field, table column or heading with a fixed grammar.
    STRUCTURAL = "structural"
    #: A mechanical match inside a constrained span (a comment, a docstring).
    DERIVED = "derived"
    #: Free prose. No human has adjudicated this.
    PROSE = "prose"


@dataclass(frozen=True, order=True, slots=True)
class SourceRef:
    """A pointer that must resolve to a real file:line. Paths are repo-relative POSIX."""

    path: str
    line: int
    end_line: int = 0

    def __post_init__(self) -> None:
        if self.end_line == 0:
            object.__setattr__(self, "end_line", self.line)

    def __str__(self) -> str:
        return f"{self.path}:{self.line}"


@dataclass(frozen=True, slots=True)
class Node:
    id: str
    kind: NodeKind
    title: str
    source: SourceRef
    shape: str = ""
    status: str = ""
    body: str = ""
    attrs: Mapping[str, str] = field(default_factory=dict)
    tags: tuple[str, ...] = ()
    #: Restatements of the same node elsewhere (D45 amended, D45 finalized).
    occurrences: tuple[SourceRef, ...] = ()
    extractor: str = ""


@dataclass(frozen=True, slots=True)
class Edge:
    src: str
    dst: str
    kind: EdgeKind
    confidence: Confidence
    source: SourceRef
    #: The verbatim substring that justifies this edge. A prose edge without its evidence is
    #: unreviewable, and prose edges are exactly the ones that need reviewing.
    evidence: str = ""
    extractor: str = ""


class MintError(Exception):
    """An id was minted that would make the vault ambiguous or unportable."""


_ID_CHARS = re.compile(r"^[A-Za-z0-9:/._-]+$")


class Minter:
    """Mints node ids and refuses the three spellings that break the vault."""

    def __init__(self) -> None:
        self._seen: dict[str, str] = {}      # id -> source, for the duplicate message
        self._folded: dict[str, str] = {}    # casefolded id -> id

    def mint(self, kind: NodeKind, local: str, source: SourceRef) -> str:
        node_id = f"{kind.value}:{local}"
        if not _ID_CHARS.match(node_id):
            raise MintError(f"{node_id!r} at {source} contains a character a filename cannot carry")
        if node_id in self._seen:
            raise MintError(f"{node_id!r} minted twice: {self._seen[node_id]} and {source}")
        folded = node_id.casefold()
        if folded in self._folded:
            # Two ids differing only by case are one file on macOS and two on Linux.
            raise MintError(
                f"{node_id!r} at {source} collides case-insensitively with "
                f"{self._folded[folded]!r} — the vault would differ between macOS and Linux"
            )
        self._seen[node_id] = str(source)
        self._folded[folded] = node_id
        return node_id
