"""The whole vault as a dict of path to content, built in memory before anything is written.

Building the complete tree first is what lets `--check` compare without writing, and it is
what lets the writer detect an **orphan** -- a file present under `vault/` that the generator
did not plan. A hand-*edited* note is caught by content comparison; a hand-*created* one is
only caught by noticing it was never planned. Both are the same defect: a fact that exists
only in the vault.

This module is the only thing that knows about the filesystem layout, and it reaches the
extractors through nothing but a `Graph`. A layering check in `--self-test` asserts that
`render/**` cannot transitively import `extract/**`, so the three renderers stay downstream of
one extraction rather than growing their own.
"""

from __future__ import annotations

from ..model import Edge, Node, NodeKind
from . import canvas, dataview, html, note

VAULT = "vault"

#: Directory per kind, so Obsidian's file tree is navigable before any query is written.
FOLDERS = {
    NodeKind.DOCUMENT: "documents",
    NodeKind.TIER: "documents",
    NodeKind.ADR: "decisions",
    NodeKind.DECISION: "decisions",
    NodeKind.AMENDMENT: "decisions",
    NodeKind.STAGE: "execution",
    NodeKind.OPERATOR_ITEM: "execution",
    NodeKind.UNRESOLVED: "execution",
    NodeKind.KILL_CRITERION: "charter",
    NodeKind.RISK: "charter",
    NodeKind.MODULE: "code",
    NodeKind.SCHEMA: "code",
    NodeKind.GATE: "gates",
    NodeKind.GATE_STEP: "gates",
}


def build(nodes: list[Node], edges: list[Edge], anomalies: list, unparsed: list) -> dict[str, str]:
    by_id = {n.id: n for n in nodes}
    out: dict[str, list[tuple[Edge, Node]]] = {n.id: [] for n in nodes}
    inc: dict[str, list[tuple[Edge, Node]]] = {n.id: [] for n in nodes}
    for edge in edges:
        if edge.src in by_id and edge.dst in by_id and edge.src != edge.dst:
            out[edge.src].append((edge, by_id[edge.dst]))
            inc[edge.dst].append((edge, by_id[edge.src]))

    tree: dict[str, str] = {}
    for node in sorted(nodes, key=lambda n: n.id):
        folder = FOLDERS.get(node.kind, "other")
        path = f"{VAULT}/{folder}/{note.filename(node)}"
        tree[path] = note.render(
            node,
            sorted(out[node.id], key=lambda pair: (pair[0].kind.value, pair[1].id)),
            sorted(inc[node.id], key=lambda pair: (pair[0].kind.value, pair[1].id)),
        )

    tree.update(dataview.boards(nodes, edges))
    tree.update(canvas.boards(nodes, edges))
    tree[f"{VAULT}/_anomalies.md"] = _anomalies(anomalies, unparsed)
    return tree


def artifact(nodes: list[Node], edges: list[Edge], anomalies: list, unparsed: list) -> str:
    """The published page, from the same nodes and edges the vault is built from. One
    extraction, several renderers -- the artifact cannot drift from the vault because there is
    nothing for it to drift from."""
    return html.render(nodes, edges, anomalies, unparsed)


def _anomalies(anomalies: list, unparsed: list) -> str:
    """Discrepancies the generator surfaced and did not resolve, in one note.

    A count that disagrees with a register, a package declared and absent, a dependency naming
    something the graph cannot hold -- each is a real finding, and each would be invisible if
    the generator picked a side. This note is where they are visible without being decided."""
    lines = [
        "---", "kind: index", 'title: "Anomalies"', "generated: true", "---", "",
        "# Anomalies", "", note.BANNER, "",
        "Discrepancies the generator found and deliberately did not resolve. "
        "A generator that picked a side here would be asserting something it does not know.",
        "",
    ]
    lines.append("## Surfaced")
    lines.append("")
    if anomalies:
        lines.append("| Kind | Detail |")
        lines.append("|---|---|")
        for item in sorted(anomalies, key=lambda a: (a.kind, a.detail)):
            lines.append(f"| `{item.kind}` | {item.detail} |")
    else:
        lines.append("None.")
    lines.append("")
    lines.append("## Not parsed")
    lines.append("")
    lines.append(
        "Constructs matched by an extractor and left unresolved. The budget for these is "
        "committed per extractor, so this list shrinking is progress and it growing is a "
        "build failure."
    )
    lines.append("")
    if unparsed:
        lines.append("| Source | Text | Reason |")
        lines.append("|---|---|---|")
        for item in sorted(unparsed, key=lambda u: (u.source.path, u.source.line)):
            text = item.text.replace("|", "\\|")[:120]
            lines.append(f"| `{item.source}` | {text} | {item.reason} |")
    else:
        lines.append("None.")
    return "\n".join(lines) + "\n"
