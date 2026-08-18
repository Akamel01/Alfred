"""The local refresh surface, and the four controls that keep it from being a liability.

A local server with a state-changing POST is reachable from any page the operator's browser
visits. A plain HTML form can cross-post to `127.0.0.1` without a preflight and without
reading the response, which is enough to make a machine run a generator on a stranger's cue.
Each control is asserted separately here, because a suite that only tests the happy path
would pass with every one of them removed.

**How this suite would be shown vacuous** (D57): `test_the_authorized_path_actually_works`
is the control — it proves the refusals below are refusing something that otherwise
succeeds, rather than the route being broken for everyone.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

PORT = 8799
BASE = f"http://127.0.0.1:{PORT}"


@pytest.fixture(scope="module")
def server():
    # DEVNULL rather than PIPE: nothing here reads the server's log, and an unread pipe left
    # open trips filterwarnings = ["error"] on teardown.
    process = subprocess.Popen(
        [sys.executable, "tools/serve_vault.py", "--port", str(PORT)],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    for _ in range(60):
        try:
            urllib.request.urlopen(f"{BASE}/graph.json", timeout=2).read()
            break
        except Exception:
            time.sleep(0.25)
    else:
        process.kill()
        pytest.fail("the local surface did not come up")
    yield process
    process.terminate()
    process.wait(timeout=10)


def _request(method: str, path: str, headers: dict[str, str] | None = None):
    request = urllib.request.Request(f"{BASE}{path}", method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        # Closed explicitly: pytest runs with filterwarnings = ["error"], so an unclosed
        # error response turns a passing refusal into a failing test.
        with error:
            return error.code, error.read().decode("utf-8")


def _token(server) -> str:
    _status, page = _request("GET", "/")
    found = re.search(r'const REFRESH_TOKEN = "([^"]+)"', page)
    assert found, "the served page carries no refresh token"
    return found.group(1)


def test_the_served_page_carries_a_live_control(server) -> None:
    status, page = _request("GET", "/")
    assert status == 200
    assert 'id="regenerate"' in page


def test_the_committed_page_does_not(server) -> None:
    # The published artifact cannot run the generator — no runtime capability grants a page
    # repository access — so a refresh button there would be a control that lies.
    committed = (ROOT / "docs-graph.html").read_text(encoding="utf-8")
    assert 'id="regenerate"' not in committed
    assert "REFRESH_TOKEN" not in committed


def test_refresh_without_the_token_is_refused(server) -> None:
    status, body = _request("POST", "/refresh")
    assert status == 403
    assert "token" in json.loads(body)["error"]


def test_refresh_with_a_wrong_token_is_refused(server) -> None:
    status, _body = _request("POST", "/refresh", {"X-Refresh-Token": "not-the-token"})
    assert status == 403


def test_a_cross_origin_post_is_refused(server) -> None:
    # The Origin check refuses outright rather than merely leaving the request
    # unauthenticated, so a page that somehow obtained a token still cannot use it.
    status, _body = _request(
        "POST", "/refresh",
        {"Origin": "https://evil.example", "X-Refresh-Token": _token(server)},
    )
    assert status == 403


def test_a_rebound_host_header_is_refused(server) -> None:
    # DNS rebinding: an attacker-controlled name resolving to 127.0.0.1 arrives with its own
    # Host. The loopback bind alone does not stop this; the Host allowlist does.
    status, _body = _request(
        "POST", "/refresh",
        {"Host": "attacker.test", "X-Refresh-Token": _token(server)},
    )
    assert status == 403


def test_the_preflight_grants_nothing(server) -> None:
    # No Access-Control-Allow-* headers, deliberately. A cross-origin preflight is meant to
    # fail, and that failure is what the custom-header requirement buys.
    request = urllib.request.Request(f"{BASE}/refresh", method="OPTIONS")
    with urllib.request.urlopen(request, timeout=10) as response:
        assert not any(h.lower().startswith("access-control-allow")
                       for h in response.headers.keys())


def test_unknown_paths_are_refused(server) -> None:
    for path in ("/../etc/passwd", "/vault/documents/x.md", "/anything"):
        status, _body = _request("GET", path)
        assert status == 404, path


def test_the_page_may_not_be_framed(server) -> None:
    request = urllib.request.Request(f"{BASE}/", method="GET")
    with urllib.request.urlopen(request, timeout=10) as response:
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["Referrer-Policy"] == "no-referrer"


def test_the_authorized_path_actually_works(server) -> None:
    # The control for every refusal above. Without it they would all pass on a broken route.
    status, body = _request("POST", "/refresh", {"X-Refresh-Token": _token(server)})
    assert status == 200, body
    assert "wrote graph.json" in json.loads(body)["summary"]


def test_the_served_graph_matches_the_committed_one(server) -> None:
    status, body = _request("GET", "/graph.json")
    assert status == 200
    assert json.loads(body) == json.loads((ROOT / "graph.json").read_text(encoding="utf-8"))


# ---- the audit, on this surface --------------------------------------------------

def test_a_graph_that_failed_its_floors_is_never_served() -> None:
    """The defect this replaces: `do_GET` called `run`, whose verdict is a field, and never
    read it. A vacuous extraction -- the failure every floor in the package exists to
    prevent -- came back at HTTP 200. `build` raises instead, so the handler cannot forget."""
    import tempfile

    from tools.vaultgraph.runner import AuditFailed, build

    with tempfile.TemporaryDirectory() as empty:
        with pytest.raises(AuditFailed):
            build(Path(empty))


def test_both_routes_refuse_rather_than_render_when_the_audit_fails() -> None:
    import tools.serve_vault as serve
    from tools.vaultgraph.runner import AuditFailed

    for route in ("/", "/graph.json"):
        handler = object.__new__(serve.Handler)
        answers: list[tuple[int, bytes]] = []
        handler.path = route
        handler._origin_is_local = lambda: True                     # noqa: SLF001
        handler._send = lambda status, body, ctype: answers.append((status, body))  # noqa: SLF001
        handler._refuse = serve.Handler._refuse.__get__(handler)    # noqa: SLF001

        original = serve.build
        serve.build = lambda _root: (_ for _ in ()).throw(AuditFailed(["floor: 0 < 63"]))
        try:
            handler.do_GET()
        finally:
            serve.build = original

        assert answers, f"{route} answered nothing"
        status, body = answers[0]
        assert status == 503, f"{route} served {status} on a failed audit"
        assert b"floor" in body


def test_a_drifted_plan_mirror_is_never_served() -> None:
    import tools.serve_vault as serve

    handler = object.__new__(serve.Handler)
    answers: list[tuple[int, bytes]] = []
    handler.path = "/"
    handler._origin_is_local = lambda: True                         # noqa: SLF001
    handler._send = lambda status, body, ctype: answers.append((status, body))  # noqa: SLF001
    handler._refuse = serve.Handler._refuse.__get__(handler)        # noqa: SLF001

    original = serve.mirror.check
    serve.mirror.check = lambda **_kwargs: (1, ["mirror drifted from its origin"])
    try:
        handler.do_GET()
    finally:
        serve.mirror.check = original

    assert answers
    status, body = answers[0]
    assert status == 503
    assert b"drifted" in body
