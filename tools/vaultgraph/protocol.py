"""The extractor contract, shaped so a missing vacuity guard is impossible rather than unlikely.

D57 asks every extractor to state a minimum expected count and fail below it. Asking is not
enough — the failure mode being designed out is an author who forgets. So the floors are
constructor arguments on a frozen dataclass with **no defaults**, and `EXTRACTORS` is the only
thing the runner will execute. An extractor with no declared floor is not a weaker extractor;
it is an import error.

`rejected` is the half that is easy to leave out. `unparsed` means *saw it, could not read it*;
`rejected` means *saw it, deliberately refused it* — the eight commentary lookalikes in the plan
that wear a decision's exact shape. Both are counted, and `expect_rejected` is checked for
**equality**, not as a floor: a filter that stops firing admits eight junk nodes, and a filter
that over-tightens reports zero rejections while silently dropping real ones. Only equality
catches both directions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .model import Edge, Minter, Node, NodeKind, SourceRef


@dataclass(frozen=True, slots=True)
class Unparsed:
    """Matched a construct this extractor owns, and could not be resolved. Never dropped."""

    extractor: str
    source: SourceRef
    text: str
    reason: str


@dataclass(frozen=True, slots=True)
class Rejected:
    """Wears the shape of a construct and is deliberately not one."""

    extractor: str
    source: SourceRef
    text: str
    reason: str


@dataclass(frozen=True, slots=True)
class Anomaly:
    """A discrepancy between two sources that the generator must surface, not resolve."""

    kind: str
    detail: str
    refs: tuple[SourceRef, ...] = ()


@dataclass(slots=True)
class Harvest:
    """One extractor's yield. `scanned` mirrors `Findings.scanned` in
    `scripts/lint_verdict_boundary.py` — the count that distinguishes a check that passed
    from a check that had nothing to check."""

    scanned: int = 0
    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    unparsed: list[Unparsed] = field(default_factory=list)
    rejected: list[Rejected] = field(default_factory=list)
    anomalies: list[Anomaly] = field(default_factory=list)


@dataclass(slots=True)
class Context:
    """What an extractor is handed. `root` is a parameter, not a constant, so the self-test
    can point the whole registry at a planted fixture tree."""

    root: Path
    minter: Minter


@dataclass(frozen=True, slots=True)
class ExtractorSpec:
    """No field has a default. Registering an extractor means stating its floors."""

    name: str
    kinds: tuple[NodeKind, ...]
    #: Fail below this many nodes. Exact for mirror-derived sources (the input is byte-frozen),
    #: a true minimum for repo-derived ones (docs/ legitimately grows).
    min_nodes: int
    max_nodes: int | None
    min_edges: int
    #: A committed budget for the known-irregular residue. Drift upward fails.
    max_unparsed: int
    #: Checked for equality where the input is byte-frozen; None where the notion does not apply.
    expect_rejected: int | None
    run: Callable[[Context], Harvest]


class RegistryError(Exception):
    """The registry is malformed. Raised at import time, so it cannot be a silent green."""


def validate_registry(specs: tuple[ExtractorSpec, ...], *, floor: int) -> None:
    """Run at import time by `extract/__init__.py`. Every clause here is a way the D57
    discipline could be quietly lost."""
    if len(specs) < floor:
        raise RegistryError(f"registry holds {len(specs)} extractors, floor is {floor}")
    names: set[str] = set()
    for spec in specs:
        if spec.name in names:
            raise RegistryError(f"duplicate extractor name {spec.name!r}")
        names.add(spec.name)
        if not spec.kinds:
            raise RegistryError(f"extractor {spec.name!r} declares no node kinds")
        if spec.min_nodes <= 0:
            raise RegistryError(
                f"extractor {spec.name!r} declares no floor; D57 requires one"
            )
        if spec.max_nodes is not None and spec.max_nodes < spec.min_nodes:
            raise RegistryError(f"extractor {spec.name!r} has max_nodes below min_nodes")
        if spec.min_edges < 0 or spec.max_unparsed < 0:
            raise RegistryError(f"extractor {spec.name!r} declares a negative budget")
