"""What clumps together, computed rather than declared.

`kind` says what a node *is*; it is authored, and the rail has always been able to show it.
Nothing said what the graph's *shape* is -- which nodes actually pull on each other -- and
that is the question a graph drawing exists to answer. Two nodes can share a kind and sit at
opposite ends of the register, or differ in kind and be inseparable.

**Deterministic label propagation, and deliberately not a library.** Modularity clustering is
normally reached for through networkx or graspologic; both are dependencies, and this is
forty lines. More to the point, the usual implementations are *seeded random* -- they iterate
nodes in arbitrary order and break ties by coin flip, which produces a different partition on
every run. `graph.json` is byte-compared by `--check`, so a clustering that moved when nothing
changed would red the build on a whim. Every ordering here is by node id, and every tie is
broken by the lowest label, so the partition is a function of the graph and nothing else.

**Clusters are named after their highest-degree member.** A partition labelled `Community 45`
needs a language model to become readable, which is the point where a local, deterministic
tool acquires a network dependency and a bill. The busiest node in a cluster is already the
best one-line summary of it, and it costs a sort.
"""

from __future__ import annotations

from .. model import Edge, Node

#: Label propagation converges on graphs this size in a handful of sweeps. The cap is a
#: termination guarantee, not a tuning knob: an oscillating pair of labels would otherwise
#: swap forever, and a generator that sometimes does not finish is worse than a coarse
#: partition. Reaching it is reported rather than silently accepted -- see `Clustering.settled`.
MAX_SWEEPS = 20


class Clustering:
    """A partition of the nodes, plus whether the algorithm actually finished."""

    __slots__ = ("labels", "sweeps", "settled")

    def __init__(self, labels: dict[str, str], sweeps: int, settled: bool) -> None:
        self.labels = labels
        self.sweeps = sweeps
        self.settled = settled


def _adjacency(nodes: list[Node], edges: list[Edge]) -> dict[str, list[str]]:
    """Undirected neighbours. Direction carries meaning in this graph -- `blocks` is not
    `blocked_by` -- but it carries none for the question "do these two pull together", and
    honouring it would leave every node that is only ever a target in a cluster of one."""
    near: dict[str, list[str]] = {node.id: [] for node in nodes}
    for edge in edges:
        near[edge.src].append(edge.dst)
        near[edge.dst].append(edge.src)
    return {node_id: sorted(set(neighbours)) for node_id, neighbours in near.items()}


def partition(nodes: list[Node], edges: list[Edge]) -> Clustering:
    """Group the nodes by who pulls on whom.

    `edges` must already be resolvable -- both endpoints defined -- which is the caller's
    job and `model.resolvable`'s purpose. An endpoint with no node would land in the
    adjacency map as a KeyError rather than quietly forming a cluster of one.
    """
    near = _adjacency(nodes, edges)
    order = sorted(near)
    labels = {node_id: node_id for node_id in order}

    sweeps = 0
    settled = False
    for sweeps in range(1, MAX_SWEEPS + 1):  # noqa: B007 - the counter is the report
        moved = False
        for node_id in order:
            neighbours = near[node_id]
            if not neighbours:
                continue
            tally: dict[str, int] = {}
            for other in neighbours:
                tally[labels[other]] = tally.get(labels[other], 0) + 1
            # Most common label, ties to the lowest id. Both halves matter: without the tally
            # this is not clustering, and without the tie-break it is not deterministic.
            best = min(tally.items(), key=lambda item: (-item[1], item[0]))[0]
            if best != labels[node_id]:
                labels[node_id] = best
                moved = True
        if not moved:
            settled = True
            break

    return Clustering(labels=labels, sweeps=sweeps, settled=settled)


def summarise(
    nodes: list[Node], edges: list[Edge], clustering: Clustering
) -> tuple[dict[str, int], list[dict[str, object]]]:
    """`node id -> cluster ordinal`, and the clusters themselves, largest first.

    Ordinals rather than the propagated label: the label is whichever node id won, which is an
    implementation detail that would move a colour from one cluster to another the moment an
    unrelated node was renamed. Size, then name, is stable against that.
    """
    degree: dict[str, int] = {node.id: 0 for node in nodes}
    for edge in edges:
        degree[edge.src] += 1
        degree[edge.dst] += 1

    members: dict[str, list[str]] = {}
    for node in nodes:
        members.setdefault(clustering.labels[node.id], []).append(node.id)

    titles = {node.id: node.title for node in nodes}
    groups = []
    for label, ids in members.items():
        # Named after the busiest member: the best one-line summary of a cluster that a
        # deterministic, offline tool can produce, and it costs a sort.
        head = min(ids, key=lambda node_id: (-degree[node_id], node_id))
        groups.append({"label": label, "ids": sorted(ids), "head": head, "name": titles[head]})

    groups.sort(key=lambda group: (-len(group["ids"]), str(group["name"]), group["label"]))

    of_node: dict[str, int] = {}
    out: list[dict[str, object]] = []
    for ordinal, group in enumerate(groups):
        for node_id in group["ids"]:
            of_node[node_id] = ordinal
        out.append({
            "name": group["name"],
            "size": len(group["ids"]),
            "head": group["head"],
        })
    return of_node, out
