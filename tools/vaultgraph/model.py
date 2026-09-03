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
from typing import Iterable, Mapping


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
    LAYOUT = "layout"
    PROCESS = "process"
    EFFECT = "effect"


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
    #: One module imports another. The only relation in this graph that answers "what does
    #: this depend on"; every other module edge is containment, which is a tree.
    IMPORTS = "imports"
    #: An ADR closes an operator item. The only hand-written relation in the ADR log that
    #: points outside the log.
    DISCHARGES = "discharges"
    #: A gate step executes a module. Closes the chain decision -> module <- gate step <- gate:
    #: what a decision claims, which code enforces it, and which CI step actually runs that code.
    RUNS = "runs"


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


class EdgeError(Exception):
    """An edge was built that no view could draw."""


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

    def __post_init__(self) -> None:
        if self.src == self.dst:
            # A relation from a node to itself states nothing a node attribute does not state
            # better, and it splits the renderers: three of them dropped it and the payload
            # shipped it, so the page reported one more edge than it drew. Refusing it here
            # is cheaper than agreeing about it in four places.
            raise EdgeError(f"{self.src!r} at {self.source} is related to itself")


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

    def knows(self, node_id: str) -> bool:
        """Whether some earlier extractor already minted this id.

        The alternative was for each extractor that points at modules to re-derive which paths
        `code` would have minted -- which is the rule duplication `module_id` exists to end,
        one level up. Registry order is already load-bearing and already documented as such,
        so the minter is the one authority on what exists yet.
        """
        return node_id in self._seen


def module_id(rel_path: str) -> str:
    """The one path -> module id rule.

    Three extractors need it and each had grown its own copy: `code` mints the nodes,
    `references` points enforcement edges at them, and `workflows` points `runs` edges at them.
    Three spellings of the same rule is three chances for one of them to drift and produce
    edges whose endpoints silently do not exist -- which renders as nothing, not as an error.

    A directory maps to its dotted name; `.py` loses its suffix and `.mjs` keeps its own,
    because `harness/acs/acs1.py` and `harness/acs/acs1.mjs` are two independent
    implementations of one specification and collapsing them would erase the pair.
    """
    local = rel_path.replace("/", ".")
    if rel_path.endswith(".py"):
        local = local.removesuffix(".py")
    return f"{NodeKind.MODULE.value}:{local}"


def resolvable(nodes: Iterable[Node], edges: Iterable[Edge]) -> list[Edge]:
    """The edges a view may draw: both endpoints are nodes this graph defines.

    One rule, called by every renderer and by the gauges that count them. Four independent
    copies of it disagreed -- and a summary computed from unfiltered edges over a payload
    that was filtered is a page contradicting itself in the same screen.
    """
    known = {node.id for node in nodes}
    return [edge for edge in edges if edge.src in known and edge.dst in known]
