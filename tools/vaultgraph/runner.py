"""Runs the registry and fails on every way an extraction can be quietly empty.

This is `scripts/lint_verdict_boundary.py:307-321` applied to a generator instead of a lint.
That file's comment states the reason better than a restatement would: a check with nothing to
check reports the same thing as a check that passed, and this project has paid for that
confusion more than once. A generator has the same failure mode with a worse blast radius —
a regex that stops matching produces a smaller vault, a green run, and a graph that is missing
exactly the nodes nobody will now notice are gone.

Five guards, all fatal, none warnings:

* `scanned == 0`            — the extractor had no input at all.
* `nodes < min_nodes`       — it read its input and produced less than the floor.
* `nodes > max_nodes`       — only where the input is byte-frozen; over-matching is a defect too.
* `edges < min_edges`       — nodes survived and relations did not, which is a graph in name only.
* `unparsed > max_unparsed` — the known-irregular residue grew.
* `rejected != expected`    — two-sided; see `protocol.ExtractorSpec`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .extract import EXTRACTORS
from .model import Edge, Minter, Node
from .protocol import Anomaly, Context, ExtractorSpec, Harvest, Rejected, Unparsed


@dataclass(slots=True)
class ExtractorReport:
    name: str
    scanned: int
    nodes: int
    edges: int
    unparsed: int
    rejected: int
    min_nodes: int
    max_nodes: int | None
    min_edges: int
    max_unparsed: int
    expect_rejected: int | None


@dataclass(slots=True)
class RunResult:
    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    unparsed: list[Unparsed] = field(default_factory=list)
    rejected: list[Rejected] = field(default_factory=list)
    anomalies: list[Anomaly] = field(default_factory=list)
    reports: list[ExtractorReport] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.failures


def _audit(spec: ExtractorSpec, harvest: Harvest) -> list[str]:
    failures: list[str] = []
    if harvest.scanned == 0:
        failures.append(f"VACUOUS {spec.name}: scanned 0 inputs")
    if len(harvest.nodes) < spec.min_nodes:
        failures.append(
            f"VACUOUS {spec.name}: {len(harvest.nodes)} nodes, floor is {spec.min_nodes}"
        )
    if spec.max_nodes is not None and len(harvest.nodes) > spec.max_nodes:
        failures.append(
            f"OVERMATCH {spec.name}: {len(harvest.nodes)} nodes, ceiling is {spec.max_nodes}"
        )
    if len(harvest.edges) < spec.min_edges:
        failures.append(
            f"VACUOUS {spec.name}: {len(harvest.edges)} edges, floor is {spec.min_edges}"
        )
    if len(harvest.unparsed) > spec.max_unparsed:
        failures.append(
            f"UNPARSED {spec.name}: {len(harvest.unparsed)} items, budget is {spec.max_unparsed}"
        )
    if spec.expect_rejected is not None and len(harvest.rejected) != spec.expect_rejected:
        failures.append(
            f"REJECTION DRIFT {spec.name}: rejected {len(harvest.rejected)}, "
            f"expected exactly {spec.expect_rejected}"
        )
    return failures


def run(root: Path, specs: tuple[ExtractorSpec, ...] = EXTRACTORS) -> RunResult:
    """Run every registered extractor against `root`. Never raises on a vacuous extractor —
    it collects, so one run reports every failure rather than the first."""
    result = RunResult()
    ctx = Context(root=root, minter=Minter())

    for spec in specs:
        harvest = spec.run(ctx)
        result.nodes.extend(harvest.nodes)
        result.edges.extend(harvest.edges)
        result.unparsed.extend(harvest.unparsed)
        result.rejected.extend(harvest.rejected)
        result.anomalies.extend(harvest.anomalies)
        result.failures.extend(_audit(spec, harvest))
        result.reports.append(
            ExtractorReport(
                name=spec.name,
                scanned=harvest.scanned,
                nodes=len(harvest.nodes),
                edges=len(harvest.edges),
                unparsed=len(harvest.unparsed),
                rejected=len(harvest.rejected),
                min_nodes=spec.min_nodes,
                max_nodes=spec.max_nodes,
                min_edges=spec.min_edges,
                max_unparsed=spec.max_unparsed,
                expect_rejected=spec.expect_rejected,
            )
        )

    known = {node.id for node in result.nodes}
    dangling = sorted({e.dst for e in result.edges if e.dst not in known} |
                      {e.src for e in result.edges if e.src not in known})
    if dangling:
        # Dangling targets become `unresolved` nodes once the extractor that owns them lands.
        # Until then they are an anomaly, so the number is visible and shrinking rather than
        # discovered later by a renderer that silently drops the edge.
        result.anomalies.append(
            Anomaly(
                kind="dangling-edge-endpoint",
                detail=f"{len(dangling)} edge endpoints have no node: {', '.join(dangling[:10])}",
            )
        )
    return result
