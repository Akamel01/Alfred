"""Obsidian Canvas boards — the stage DAG, laid out deterministically.

**Coordinates come from a pure function of position, never from a layout engine.** A force
layout would move every node whenever one was added, so the committed `.canvas` file would
diff on every rebuild for reasons that are not changes. Element ids are derived from the node
id by hash rather than generated, for the same reason.

**Structural and prose edges are both drawn, and drawn differently.** The stage dependency
clauses are prose -- that is how the execution order writes them -- so omitting them would
leave the DAG empty. They are labelled with the clause that produced them, so what is read
off the board can be checked against what the document said.
"""

from __future__ import annotations

import hashlib
import json

from ..model import Confidence, Edge, Node, NodeKind, resolvable

VAULT = "vault"

COLUMN = 420
ROW = 190
WIDTH = 330
HEIGHT = 120

#: Canvas colour slots: 1 red, 2 orange, 4 green, 6 purple.
COLOURS = {
    "done": "4",
    "partial": "2",
    "not-started": "1",
    "fired": "1",
    "armed": "6",
}


def _element_id(node_id: str) -> str:
    return hashlib.sha1(node_id.encode("utf-8")).hexdigest()[:16]


def _card(node: Node, path: str, column: int, row: int) -> dict[str, object]:
    return {
        "id": _element_id(node.id),
        "type": "file",
        "file": path,
        "x": column * COLUMN,
        "y": row * ROW,
        "width": WIDTH,
        "height": HEIGHT,
        "color": COLOURS.get(node.status, "6"),
    }


def _edge(edge: Edge, index: int) -> dict[str, object]:
    return {
        "id": _element_id(f"{edge.src}->{edge.dst}:{edge.kind.value}:{index}"),
        "fromNode": _element_id(edge.src),
        "fromSide": "right",
        "toNode": _element_id(edge.dst),
        "toSide": "left",
        # The clause is the label, so a reader can check the board against the document.
        "label": edge.evidence[:60] if edge.confidence is Confidence.PROSE else edge.kind.value,
    }


def boards(nodes: list[Node], edges: list[Edge]) -> dict[str, str]:
    from .note import filename

    wanted = {NodeKind.STAGE, NodeKind.OPERATOR_ITEM, NodeKind.UNRESOLVED}
    board_nodes = sorted((n for n in nodes if n.kind in wanted), key=lambda n: n.id)
    by_id = {n.id: n for n in board_nodes}

    # Columns by kind, rows by sorted position within the kind. Inserting a stage shifts only
    # its own column, and only below the insertion point.
    columns = {NodeKind.OPERATOR_ITEM: 0, NodeKind.STAGE: 1, NodeKind.UNRESOLVED: 2}
    rows: dict[NodeKind, int] = {}
    cards: list[dict[str, object]] = []
    for node in board_nodes:
        row = rows.get(node.kind, 0)
        rows[node.kind] = row + 1
        folder = "execution"
        cards.append(_card(node, f"{VAULT}/{folder}/{filename(node)}", columns[node.kind], row))

    drawn: list[dict[str, object]] = []
    for index, edge in enumerate(sorted(
        # `board_nodes`, not every node: this board is a subset view, and an edge it may
        # draw is one whose endpoints are both on the board.
        resolvable(board_nodes, edges),
        key=lambda e: (e.src, e.dst, e.kind.value, e.evidence),
    )):
        drawn.append(_edge(edge, index))

    payload = {"nodes": cards, "edges": drawn}
    return {
        f"{VAULT}/Stage DAG.canvas":
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    }
