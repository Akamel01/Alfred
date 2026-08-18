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


def test_the_artifact_reaches_no_external_host() -> None:
    # The artifact CSP blocks every external host, so a CDN link or a font URL is a silent
    # failure rather than a fallback. True of both pages -- the served one may talk to its own
    # origin, never to another.
    for page in (_artifact(), _artifact(live_token="t0ken")):
        assert "http://" not in page
        assert "https://" not in page
        assert "//cdn" not in page
        assert "@import" not in page


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
    # 68 falsification conditions is the headline number and the reason the graph exists.
    assert "<dd>68</dd>" in page
