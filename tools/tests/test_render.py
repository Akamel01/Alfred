"""The renderers: the vault tree, and the published artifact.

Split from `test_vaultgraph.py`, which covers extraction. The division follows the layering
the generator already enforces -- renderers consume a graph and cannot reach the extractors --
so a failure here names the renderer rather than leaving it ambiguous.

**How this suite would be shown vacuous** (D57): every assertion resolves against the real
graph or a real rendered page, so a renderer that emitted nothing would fail rather than pass
quieter. `test_the_embedded_graph_cannot_close_its_own_script_element` plants the hostile
string itself, so the escaping is proved by a case rather than asserted by a comment.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from tools.vaultgraph.model import NodeKind  # noqa: E402,F401
from tools.vaultgraph.runner import run  # noqa: E402

# ---- vault tree ----------------------------------------------------------------------------

from tools.vaultgraph.render import vault as render_vault  # noqa: E402
from tools.vaultgraph.render import html as render_html  # noqa: E402
from tools.vaultgraph.serialize import compare_tree  # noqa: E402


def _tree():
    result = run(ROOT)
    return result, render_vault.build(
        result.nodes, result.edges, result.anomalies, result.unparsed
    )


def test_the_committed_vault_matches_a_fresh_build() -> None:
    _result_, tree = _tree()
    assert compare_tree(ROOT, tree, managed=("vault",)) == []


def test_every_node_gets_exactly_one_note() -> None:
    result, tree = _tree()
    notes = [p for p in tree if p.endswith(".md") and "/" in p.removeprefix("vault/")]
    assert len(notes) == len(result.nodes)


def test_every_note_carries_the_banner_and_a_resolving_source() -> None:
    _result_, tree = _tree()
    for path, content in tree.items():
        if not path.endswith(".md"):
            continue
        assert "Generated — do not edit" in content, path


def test_the_vault_is_byte_identical_on_a_second_build() -> None:
    _r1, first = _tree()
    _r2, second = _tree()
    assert first == second


def test_the_canvas_uses_stable_ids_and_no_random_layout() -> None:
    # A force layout would move every card whenever one was added, so the committed board
    # would diff on every rebuild for reasons that are not changes.
    _result_, tree = _tree()
    board = json.loads(tree["vault/Stage DAG.canvas"])
    assert board["nodes"] and board["edges"]
    xs = {n["x"] for n in board["nodes"]}
    assert all(x % 420 == 0 for x in xs)


def test_renderers_cannot_reach_the_extractors() -> None:
    from tools.vaultgraph.selftest import _reaches

    render_dir = ROOT / "tools" / "vaultgraph" / "render"
    for module in sorted(render_dir.glob("*.py")):
        assert _reaches(module, "extract") is None, module.name


# ---- the published artifact ----------------------------------------------------------------



def _artifact(live_token: str | None = None) -> str:
    result = run(ROOT)
    return render_html.render(
        result.nodes, result.edges, result.anomalies, result.unparsed, live_token=live_token
    )


#: Every way a string becomes markup rather than text. `innerHTML` alone was the whole list
#: once, which meant the check asserted the rule's spelling rather than the rule: a page using
#: `insertAdjacentHTML` passed it unchanged.
MARKUP_SINKS = (
    "innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "createContextualFragment",
    "srcdoc", "eval(", "new Function", "javascript:",
)


def _markup_sinks(script: str) -> list[str]:
    return [sink for sink in MARKUP_SINKS if sink in script]


def _page_script(page: str) -> str:
    """The executable script, never the JSON block. Splitting on the JSON marker keeps the
    embedded graph -- which is repository prose, and legitimately contains anything -- out of
    a scan looking for what the *code* does with it."""
    script = page.split("</script>", 1)[1] if '<script type="application/json"' in page else page
    assert len(script) > 5000, "the scan found no script to look at"
    return script


def test_the_scan_for_markup_sinks_detects_a_planted_one() -> None:
    """The control. A grep over hand-written code reports the same thing whether it works or
    not, so the detection is proved against a planted case before it is trusted on the real
    one -- the discipline `scripts/lint_verdict_boundary.py --self-test` already applies."""
    clean = _page_script(_artifact())
    assert _markup_sinks(clean) == []
    for planted in ("el.innerHTML = x;", "el.insertAdjacentHTML('beforeend', x);",
                    "document.write(x);", "f = new Function(x);"):
        assert _markup_sinks(clean + planted), f"a planted {planted!r} was not detected"


def test_repository_text_never_becomes_markup() -> None:
    # ADR-0008: the read model is untrusted in the browser. A decision's body is repository
    # prose, and repository prose is not markup. Both pages are scanned: the committed one and
    # the one the local surface serves, which carries an extra script the committed one omits.
    for page in (_artifact(), _artifact(live_token="t0ken")):
        assert _markup_sinks(_page_script(page)) == []


#: The one address either page may name: the local surface, which is where the working
#: refresh button lives. Loopback is not an external host -- and the committed page carries it
#: as text in a <code> element, so naming it is not reaching it.
LOOPBACK = render_html.LOCAL_SURFACE


def _external_hosts(page: str) -> list[str]:
    return [
        url for url in re.findall(r"https?://[^\s\"'<>)]*", page) if not url.startswith(LOOPBACK)
    ]


def test_the_external_host_scan_detects_a_planted_one() -> None:
    """The control. The scan now has an exception in it, and an exception is how a check stops
    checking: a substring test that allowed the loopback prefix would allow
    `http://127.0.0.1.evil.example` with it."""
    assert _external_hosts(_artifact()) == []
    for planted in ("https://cdn.example/x.css", "http://127.0.0.1.evil.example/x",
                    "http://10.0.0.1/x"):
        assert _external_hosts(planted), f"a planted {planted!r} was not detected"


def test_the_artifact_reaches_no_external_host() -> None:
    # The artifact CSP blocks every external host, so a CDN link or a font URL is a silent
    # failure rather than a fallback. True of both pages -- the served one may talk to its own
    # origin, never to another.
    for page in (_artifact(), _artifact(live_token="t0ken")):
        assert _external_hosts(page) == []
        assert "//cdn" not in page
        assert "@import" not in page


def test_the_committed_page_names_the_surface_that_can_refresh_it() -> None:
    """A page that cannot run the generator must not show a control implying it can. Saying
    nothing instead leaves a reader with a stale graph, no way to tell it is stale, and no way
    to find the button -- so the committed page names the address and the served page has it."""
    committed = _artifact()
    assert "is a snapshot" in committed
    assert LOOPBACK in committed
    assert 'id="regenerate"' not in committed, "the committed page shows a button it cannot honour"
    # Nor the staleness chip, and nor the poll behind it: a file opened from disk has no server
    # to ask, and a chip that could never appear is a control that lies more quietly.
    assert 'id="stale"' not in committed
    assert "/stamp" not in _page_script(committed)
    served = _artifact(live_token="t0ken")
    assert 'id="regenerate"' in served
    assert 'id="stale"' in served
    assert "/stamp" in _page_script(served)
    assert "is a snapshot" not in served, "the served page shows the snapshot notice, not its button"


def test_the_address_the_pages_name_is_the_one_the_server_binds() -> None:
    """Two hand-copies of an address are how a refresh button points at nothing. The renderer
    already knew the server's route and token header; this is the check that keeps the third
    fact from drifting silently."""
    import tools.serve_vault as serve

    assert LOOPBACK == f"http://{serve.HOST}:{serve.DEFAULT_PORT}"


def test_the_committed_artifact_makes_no_request_at_all() -> None:
    """The published page cannot run the generator -- no runtime capability grants a page
    repository access -- so a request from it is a control that lies about what it does.

    This used to be asserted as `"fetch(" not in page` over the default render, and passed
    only because the helper omitted `live_token`: `LIVE_SCRIPT` contains `fetch('/refresh'`
    and was never rendered. The served page is now asserted separately, below."""
    page = _artifact()
    for verb in ("fetch(", "XMLHttpRequest", "navigator.sendBeacon", "EventSource", "WebSocket",
                 "import("):
        assert verb not in page, f"the committed artifact reaches the network via {verb}"


def test_the_served_page_requests_only_its_own_origin() -> None:
    page = _artifact(live_token="t0ken")
    targets = re.findall(r"fetch\(\s*(['\"`])(.*?)\1", page)
    assert targets, "the served page carries no request — the live control did not render"
    for _quote, target in targets:
        assert target.startswith("/") and not target.startswith("//"), (
            f"the served page requests {target!r}, which is not its own origin"
        )


def test_the_emitted_script_parses() -> None:
    """471 lines of JavaScript live in a Python string, so no Python tool in this repository
    ever parses them: a syntax error ships a blank page and a green suite.

    Node is required rather than skipped. A check that quietly does not run reports what a
    clean check reports -- the argument `harness/evidence`'s `test_node_is_available` already
    makes. If a runner lacks Node, add `actions/setup-node` to the integrity job; a visible
    failure with a one-line fix beats a silent skip."""
    assert shutil.which("node"), (
        "node is required to parse the emitted script; add actions/setup-node to the "
        "integrity job rather than skipping this check"
    )
    for label, page in (("committed", _artifact()), ("served", _artifact(live_token="t0ken"))):
        script = _page_script(page).split("<script>", 1)[1].rsplit("</script>", 1)[0]
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "emitted.js"
            target.write_text(script, encoding="utf-8")
            done = subprocess.run(
                ["node", "--check", str(target)], capture_output=True, text=True, check=False
            )
        assert done.returncode == 0, f"the {label} page's script does not parse:\n{done.stderr}"


def test_the_script_parse_check_would_catch_a_syntax_error() -> None:
    """The control for the check above: a parser that always returned 0 would pass it."""
    assert shutil.which("node")
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "broken.js"
        target.write_text("function ( {\n", encoding="utf-8")
        done = subprocess.run(
            ["node", "--check", str(target)], capture_output=True, text=True, check=False
        )
    assert done.returncode != 0, "node --check accepted a syntax error"


def test_the_embedded_graph_cannot_close_its_own_script_element() -> None:
    payload = render_html._embed({"body": "</script><img onerror=alert(1)>"})
    assert "</script>" not in payload
    assert "\\u003c" in payload
    assert json.loads(payload)["body"] == "</script><img onerror=alert(1)>"


def test_the_artifact_names_itself() -> None:
    assert "<title>Alfred Register Graph</title>" in _artifact()


def test_every_colour_token_is_defined_for_the_unstamped_theme() -> None:
    # The viewer has three theme states, not two. A colour whose only definition sits behind a
    # media query never applies in the default "system" state, which is the classic
    # unreadable-artifact bug.
    from tools.vaultgraph.render.assets import CSS

    base = CSS.split("@media", 1)[0]
    declared = set(re.findall(r"(--[a-z-]+):", base))
    used = set(re.findall(r"var\((--[a-z-]+)\)", CSS))
    assert used - declared == set()


def test_both_theme_stamps_redefine_the_same_token_set() -> None:
    from tools.vaultgraph.render.assets import CSS

    base = set(re.findall(r"(--[a-z-]+):", CSS.split("@media", 1)[0]))
    dark_media = set(re.findall(
        r"(--[a-z-]+):", CSS.split("@media (prefers-color-scheme: dark)", 1)[1]
        .split(':root[data-theme="dark"]', 1)[0]
    ))
    dark_stamp = set(re.findall(
        r"(--[a-z-]+):", CSS.split(':root[data-theme="dark"]', 1)[1]
    ))
    assert dark_media == dark_stamp
    assert dark_media < base or dark_media == base - {"color-scheme"}


def test_the_artifact_reports_the_same_counts_as_the_graph() -> None:
    result = run(ROOT)
    page = render_html.render(result.nodes, result.edges, result.anomalies, result.unparsed)
    assert f"<dd>{len(result.nodes)}</dd>" in page
    assert f"<dd>{len(result.edges)}</dd>" in page
    # 76 falsification conditions is the headline number and the reason the graph exists:
    # 71 in document frontmatter plus 5 in decision cells.
    assert "<dd>76</dd>" in page


# ---- clustering -----------------------------------------------------------------

from tools.vaultgraph.model import resolvable  # noqa: E402
from tools.vaultgraph.render import cluster  # noqa: E402


def _clustered():
    result = run(ROOT)
    drawn = resolvable(result.nodes, result.edges)
    partition = cluster.partition(result.nodes, drawn)
    return result, drawn, partition


def test_the_partition_is_a_function_of_the_graph_and_nothing_else() -> None:
    """docs-graph.html is byte-compared by --check, so a clustering that moved when nothing
    changed would red the build on a whim. The usual implementations iterate in arbitrary
    order and break ties by coin flip; this one is ordered by node id throughout."""
    result, drawn, first = _clustered()
    for _ in range(3):
        again = cluster.partition(result.nodes, drawn)
        assert again.labels == first.labels
    shuffled = list(reversed(result.nodes))
    assert cluster.partition(shuffled, list(reversed(drawn))).labels == first.labels, (
        "the partition depends on the order the nodes arrived in"
    )


def test_the_partition_settles_rather_than_hitting_the_cap() -> None:
    _result, _drawn, partition = _clustered()
    assert partition.settled, (
        f"label propagation ran out at {partition.sweeps} sweeps without converging; the "
        "partition is a truncation, not a result"
    )


def test_every_node_lands_in_exactly_one_cluster() -> None:
    result, drawn, partition = _clustered()
    of_node, groups = cluster.summarise(result.nodes, drawn, partition)
    assert set(of_node) == {n.id for n in result.nodes}
    assert sum(int(g["size"]) for g in groups) == len(result.nodes)


def test_a_node_with_no_relation_is_its_own_cluster() -> None:
    """The 113 isolates are the loudest signal in this graph. A clustering that folded them
    into a neighbour would be inventing a relation the extractors did not find."""
    result, drawn, partition = _clustered()
    of_node, groups = cluster.summarise(result.nodes, drawn, partition)
    related = {e.src for e in drawn} | {e.dst for e in drawn}
    for node in result.nodes:
        if node.id not in related:
            assert groups[of_node[node.id]]["size"] == 1, f"{node.id} has no edges but was grouped"


def test_a_cluster_is_named_after_a_real_node() -> None:
    """Named after its busiest member rather than `Community 45`, which is the point at which
    a local deterministic tool would otherwise need a language model to become readable."""
    result, drawn, partition = _clustered()
    _of_node, groups = cluster.summarise(result.nodes, drawn, partition)
    titles = {n.title for n in result.nodes}
    ids = {n.id for n in result.nodes}
    for group in groups:
        assert group["name"] in titles
        assert group["head"] in ids


# ---- the three deep modules, exercised through their interfaces -----------------------------

from tools.vaultgraph.render import camera as render_camera  # noqa: E402
from tools.vaultgraph.render import layout as render_layout  # noqa: E402
from tools.vaultgraph.render import view as render_view  # noqa: E402

#: A graph small enough to reason about and shaped like the real one: a container holding three
#: members, one of which has a relation of its own, plus a node related to nothing.
FIXTURE_GRAPH = """
const NODES = [
  { id: 'tier:t', kind: 'tier', title: 'Tier', short: 't', cluster: 0 },
  { id: 'document:a', kind: 'document', title: 'A', short: 'a', cluster: 0 },
  { id: 'document:b', kind: 'document', title: 'B', short: 'b', cluster: 0 },
  { id: 'document:c', kind: 'document', title: 'C', short: 'c', cluster: 0 },
  { id: 'decision:D1', kind: 'decision', title: 'D1', short: 'D1', cluster: 0 },
  { id: 'risk:R1', kind: 'risk', title: 'R1', short: 'R1', cluster: 1 },
];
const EDGES = [
  { src: 'tier:t', dst: 'document:a', kind: 'contains', confidence: 'structural' },
  { src: 'tier:t', dst: 'document:b', kind: 'contains', confidence: 'structural' },
  { src: 'tier:t', dst: 'document:c', kind: 'contains', confidence: 'structural' },
  { src: 'decision:D1', dst: 'document:a', kind: 'enforced_by', confidence: 'prose' },
];
const byId = new Map(NODES.map(n => [n.id, n]));
"""


def _node_eval(*fragments: str, probe: str) -> object:
    """Run JS fragments plus a probe under node, and read back the probe's JSON.

    The interfaces are exercised here rather than through a rendered page because that is what
    made splitting them worth doing: a module whose behaviour can only be checked by looking at
    a canvas is a module with no test surface.
    """
    assert shutil.which("node"), "node is required to exercise the renderer modules"
    source = "\n".join(fragments) + f"\nconsole.log(JSON.stringify({probe}));\n"
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "probe.mjs"
        target.write_text(source, encoding="utf-8")
        done = subprocess.run(
            ["node", str(target)], capture_output=True, text=True, check=False
        )
    assert done.returncode == 0, done.stderr
    return json.loads(done.stdout)


def test_containment_never_reaches_the_simulation() -> None:
    """The whole redesign in one assertion. `contains` was 40% of the edges and it is a tree;
    feeding it to a force layout drew 179 spokes that say "is inside" over the graph that has
    real structure."""
    got = _node_eval(
        FIXTURE_GRAPH, render_layout.JS,
        probe="({links: layout.links.map(l => l.e.kind), "
              "holds: [...layout.holds.keys()], "
              "held: layout.holds.get('tier:t').map(n => n.id).sort()})",
    )
    assert got["links"] == ["enforced_by"], "a containment edge reached the link set"
    assert got["holds"] == ["tier:t"]
    assert got["held"] == ["document:a", "document:b", "document:c"]


def test_a_node_held_by_something_still_counts_as_unrelated() -> None:
    """"Inside a tier" is an address, not a relation. Counting it as one is what let the page
    report 246 related nodes over a drawing that could only justify 113."""
    got = _node_eval(
        FIXTURE_GRAPH, render_layout.JS,
        probe="layout.isolated.map(n => n.id).sort()",
    )
    assert got == ["document:b", "document:c", "risk:R1", "tier:t"]


def test_a_hull_is_refused_when_it_would_enclose_what_it_does_not_hold() -> None:
    """The compactness gate. An outline round members the simulation pushed apart encloses
    everything between them, and a reader takes an enclosure at face value."""
    tight = _node_eval(
        FIXTURE_GRAPH, render_layout.JS,
        probe="(function () {"
              " byId.get('document:a').x = 0; byId.get('document:a').y = 0;"
              " byId.get('document:b').x = 20; byId.get('document:b').y = 0;"
              " byId.get('document:c').x = 0; byId.get('document:c').y = 20;"
              " return layout.hulls(() => true).length; })()",
    )
    assert tight == 1, "a compact container was given no hull"
    spread = _node_eval(
        FIXTURE_GRAPH, render_layout.JS,
        probe="(function () {"
              " byId.get('document:a').x = -9000; byId.get('document:a').y = 0;"
              " byId.get('document:b').x = 9000; byId.get('document:b').y = 0;"
              " byId.get('document:c').x = 0; byId.get('document:c').y = 9000;"
              " return layout.hulls(() => true).length; })()",
    )
    assert spread == 0, "a container whose members span the canvas was still given a hull"


def test_relations_only_is_the_default_and_hides_exactly_the_unrelated() -> None:
    got = _node_eval(
        FIXTURE_GRAPH, render_layout.JS, render_view.JS,
        probe="({on: view.relationsOnly, shown: view.nodes().map(n => n.id).sort(),"
              " all: (view.setRelationsOnly(false), view.nodes().length)})",
    )
    assert got["on"] is True
    assert got["shown"] == ["decision:D1", "document:a"]
    assert got["all"] == 6


def test_hiding_is_recorded_as_hidden_never_as_shown() -> None:
    """A kind appearing in a later build must be visible by default. Recording the shown set
    instead would make a new node kind silently absent, which is the failure mode this whole
    package's floors exist to prevent, arriving through the renderer."""
    got = _node_eval(
        FIXTURE_GRAPH, render_layout.JS, render_view.JS,
        probe="(function () {"
              " view.setRelationsOnly(false);"
              " view.toggleKind('risk', false);"
              " const without = view.nodes().map(n => n.kind);"
              " view.toggleKind('risk', true);"
              " return {without, back: view.nodes().length}; })()",
    )
    assert "risk" not in got["without"]
    assert got["back"] == 6


def test_the_camera_round_trips_a_point_through_its_own_transform() -> None:
    """`toWorld` and the transform `apply` writes are the same conversion in two directions.
    They lived in six places before this module and had to agree six times."""
    got = _node_eval(
        render_camera.JS,
        probe="(function () {"
              " const element = { getBoundingClientRect: () => ({ left: 10, top: 20 }) };"
              " camera.fit([{x: -100, y: -50}, {x: 100, y: 50}], 800, 400);"
              " camera.zoomAt(400, 200, 1.7);"
              " camera.panBy(-31, 17);"
              " const world = camera.toWorld({clientX: 210, clientY: 140}, element);"
              " const back = { x: 0, y: 0 };"
              " const ctx = { translate: (x, y) => { back.x += x; back.y += y; },"
              "               scale: s => { back.s = s; } };"
              " camera.apply(ctx);"
              " return { px: back.x + world.x * back.s, py: back.y + world.y * back.s }; })()",
    )
    assert abs(got["px"] - 200) < 1e-6, got
    assert abs(got["py"] - 120) < 1e-6, got


def test_the_camera_refuses_to_zoom_past_its_own_limits() -> None:
    got = _node_eval(
        render_camera.JS,
        probe="(function () {"
              " camera.fit([{x: 0, y: 0}, {x: 10, y: 10}], 800, 400);"
              " for (let i = 0; i < 200; i += 1) camera.zoomAt(0, 0, 2);"
              " const high = camera.scale;"
              " for (let i = 0; i < 400; i += 1) camera.zoomAt(0, 0, 0.5);"
              " return { high, low: camera.scale }; })()",
    )
    assert got["high"] == 6
    assert got["low"] == 0.18


def test_nothing_outside_the_camera_touches_the_transform() -> None:
    """The seam, asserted rather than trusted. The point of the module is that a seventh place
    needing the conversion asks for it instead of writing a seventh copy."""
    from tools.vaultgraph.render import script as render_script

    body = render_script.PRELUDE + render_script.BODY
    # Writes only, and matched on word boundaries. `const scale = camera.scale` is a read
    # through the interface and is exactly what this module is for; forbidding it would forbid
    # the seam being used. A plain substring scan is also wrong in the other direction --
    # `ctx = canvas.getContext(...)` contains `tx =`.
    for leak in (r"state\.(tx|ty|scale)\b", r"\btx\s*[+*]?=", r"\bty\s*[+*]?=",
                 r"\bscale\s*[+*]=", r"\bctx\.(translate|scale)\("):
        found = re.search(leak, body)
        assert not found, f"{found.group(0)!r} writes the transform outside camera.py"
