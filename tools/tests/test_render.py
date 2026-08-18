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
import sys
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
    assert compare_tree(ROOT, tree) == []


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



def _artifact() -> str:
    result = run(ROOT)
    return render_html.render(
        result.nodes, result.edges, result.anomalies, result.unparsed
    )


def test_the_artifact_is_self_contained() -> None:
    # The artifact CSP blocks every external host, so a CDN link or a font URL is a silent
    # failure rather than a fallback.
    page = _artifact()
    assert "http://" not in page
    assert "https://" not in page
    assert "//cdn" not in page
    assert "@import" not in page
    assert "fetch(" not in page


def test_repository_text_never_becomes_markup() -> None:
    # ADR-0008: the read model is untrusted in the browser. A decision's body is repository
    # prose, and repository prose is not markup.
    page = _artifact()
    script = page.split('<script type="application/json"', 1)[1]
    assert ".innerHTML" not in script
    assert "innerHTML =" not in script


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
