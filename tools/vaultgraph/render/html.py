"""The published artifact: one self-contained file built from the same graph the vault is.

Self-contained is a hard requirement, not a preference. The artifact CSP blocks every external
host -- no CDN, no font URL, no fetch -- so the stylesheet, the script and the graph are all
inlined here.

**The graph travels as JSON in a `<script type="application/json">` block, not as generated
markup.** `<` is escaped to `\\u003c` so no repository string can close the script element
early, and the script reads it with `JSON.parse` and puts every value on the page through
`textContent`. Under ADR-0008 the read model is untrusted in the browser: a decision's body is
repository prose, and repository prose is not markup.

The payload is reduced rather than embedded whole. A note's full attribute set is what the
vault is for; the artifact needs what it draws and what it shows on selection, and shipping
the rest would triple the page for content nothing reads.
"""

from __future__ import annotations

import json
import re

from ..model import Edge, Node, NodeKind
from .assets import CSS
from .script import JS

OUTPUT = "docs-graph.html"
TITLE = "Alfred Register Graph"

#: One hue per kind, grouped by what the kind is: the register in ultramarine, the argument
#: (decisions, ADRs, amendments) in a warmer blue, the calendar (stages, operator items) in
#: brass, the charter's kill criteria and risks in oxide, the machine in slate. Colour carries
#: the grouping so the rail's order and the canvas agree without a legend to memorise.
KIND_COLOURS = {
    NodeKind.DOCUMENT: "#2D4BC7",
    NodeKind.TIER: "#7E9DF5",
    NodeKind.DECISION: "#4C6EDB",
    NodeKind.ADR: "#3D8FA8",
    NodeKind.AMENDMENT: "#6BA8BC",
    NodeKind.STAGE: "#B58A22",
    NodeKind.OPERATOR_ITEM: "#D2A63C",
    NodeKind.UNRESOLVED: "#9AA3A1",
    NodeKind.KILL_CRITERION: "#A8331F",
    NodeKind.RISK: "#C4614A",
    NodeKind.MODULE: "#587067",
    NodeKind.SCHEMA: "#3F5C52",
    NodeKind.GATE: "#2F6B4F",
    NodeKind.GATE_STEP: "#6BBF95",
}

#: Attributes the inspector shows. Everything else stays in the vault, where a full record
#: belongs; shipping it here would triple the page for content nothing reads.
BODY_LIMIT = 900
EVIDENCE_LIMIT = 160

#: Emphasis markers, stripped for display only. The page shows repository prose as plain text
#: -- it does not render markdown, and it must not, because rendering repository text as
#: markup is the thing ADR-0008 rules out. Leaving the asterisks in would just be noise.
_EMPHASIS = re.compile(r"\*\*|~~|`")


def _plain(text: str) -> str:
    return _EMPHASIS.sub("", text).strip()


def _short(node: Node) -> str:
    """A label the canvas can carry. Ids like `D49` and `S2` read better on a node than the
    sentence-long titles they belong to."""
    local = node.id.split(":", 1)[1]
    number = node.attrs.get("number")
    if number:
        return number
    if node.kind in (NodeKind.GATE, NodeKind.GATE_STEP, NodeKind.TIER):
        return local
    if node.kind is NodeKind.ADR:
        return local
    return _plain(node.title)[:26]


def _payload(nodes: list[Node], edges: list[Edge], anomalies: list, unparsed: list) -> dict:
    known = {n.id for n in nodes}
    return {
        "nodes": [
            {
                "id": n.id,
                "kind": n.kind.value,
                "title": _plain(n.title),
                "short": _short(n),
                "source": str(n.source),
                "status": n.status,
                "body": _plain(n.body)[:BODY_LIMIT],
                "falsifies": _plain(n.attrs.get("falsifies_if", "")),
            }
            for n in sorted(nodes, key=lambda n: n.id)
        ],
        "edges": [
            {
                "src": e.src,
                "dst": e.dst,
                "kind": e.kind.value,
                "confidence": e.confidence.value,
                "evidence": _plain(e.evidence)[:EVIDENCE_LIMIT],
            }
            for e in sorted(
                (e for e in edges if e.src in known and e.dst in known),
                key=lambda e: (e.kind.value, e.src, e.dst, e.evidence),
            )
        ],
        "anomalies": [{"kind": a.kind, "detail": a.detail}
                      for a in sorted(anomalies, key=lambda a: (a.kind, a.detail))],
        "unparsed": [{"source": str(u.source), "text": u.text, "reason": u.reason}
                     for u in sorted(unparsed, key=lambda u: (u.source.path, u.source.line))],
    }


def _embed(payload: dict) -> str:
    """JSON safe inside a script element. `<` cannot appear, so no repository string can close
    the element early; `&` and U+2028/9 are escaped for the same class of reason."""
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return (raw.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
            .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))


def _escape(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def _gauges(nodes: list[Node], edges: list[Edge], anomalies: list, unparsed: list) -> str:
    falsifiable = sum(1 for n in nodes if n.attrs.get("falsifies_if"))
    related: set[str] = set()
    for edge in edges:
        related.add(edge.src)
        related.add(edge.dst)
    isolated = sum(1 for n in nodes if n.id not in related)
    unresolved = sum(1 for n in nodes if n.kind is NodeKind.UNRESOLVED)
    prose = sum(1 for e in edges if e.confidence.value == "prose")
    rows = [
        ("Nodes", str(len(nodes)), ""),
        ("Edges", str(len(edges)), ""),
        ("Falsification conditions", str(falsifiable), "good"),
        ("Edges read from prose", str(prose), ""),
        ("Nodes with no relation", str(isolated), "alarm" if isolated else ""),
        ("Targets nothing defines", str(unresolved), "alarm" if unresolved else ""),
        ("Anomalies surfaced", str(len(anomalies)), "alarm" if anomalies else ""),
        ("Constructs not parsed", str(len(unparsed)), "alarm" if unparsed else ""),
    ]
    return "\n".join(
        f'      <div class="gauge {klass}"><dt>{_escape(label)}</dt>'
        f"<dd>{_escape(value)}</dd></div>"
        for label, value, klass in rows
    )


def render(nodes: list[Node], edges: list[Edge], anomalies: list, unparsed: list) -> str:
    payload = _payload(nodes, edges, anomalies, unparsed)
    colours = json.dumps(
        {kind.value: colour for kind, colour in sorted(KIND_COLOURS.items(), key=lambda p: p[0].value)},
        sort_keys=True,
    )
    legend = "".join(
        f'<span class="legend-key"><svg width="26" height="8" aria-hidden="true">'
        f'<line x1="0" y1="4" x2="26" y2="4" stroke="var(--{level})" stroke-width="1.6"'
        f'{dash}/></svg>{_escape(label)}</span>'
        for level, dash, label in (
            ("structural", "", "structural — parsed from a fixed grammar"),
            ("derived", ' stroke-dasharray="5 3"', "derived — matched in a comment span"),
            ("prose", ' stroke-dasharray="1.5 3"', "prose — read from free text, unverified"),
        )
    )
    return f"""<title>{_escape(TITLE)}</title>
<style>{CSS}</style>

<header>
  <div class="masthead">
    <h1>{_escape(TITLE)}</h1>
    <p class="subtitle">Every document, decision, stage, module and gate in one graph, with
      each relation carrying how it was learned. Derived from the repository; authored nowhere.</p>
  </div>
  <dl class="readout">
{_gauges(nodes, edges, anomalies, unparsed)}
  </dl>
</header>

<main>
  <aside id="rail" aria-label="Filters"></aside>
  <div id="stage">
    <canvas id="stage-canvas" tabindex="0" aria-label="Knowledge graph. Click a node to inspect it."></canvas>
    <div class="stage-controls">
      <input type="search" id="search" placeholder="Filter by title or id" aria-label="Filter nodes">
      <button type="button" class="chip" id="refit">Fit to view</button>
    </div>
    <div id="inspector" data-open="false" aria-live="polite"></div>
  </div>
</main>

<footer>
  {legend}
  <span>Click a node to inspect · scroll to zoom · drag to pan · Esc to close</span>
</footer>

<script type="application/json" id="graph-data">{_embed(payload)}</script>
<script>const KIND_COLOURS = {colours};{JS}</script>
"""
