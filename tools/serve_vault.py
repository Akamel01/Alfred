#!/usr/bin/env python3
"""A local surface where the refresh button actually refreshes.

    python3 tools/serve_vault.py            # http://127.0.0.1:8787
    python3 tools/serve_vault.py --port 9001

The published artifact cannot do this. No runtime capability grants a page repository access,
so its refresh control would be a button that lies about what it does — it ships a frozen
snapshot instead, and this is where a real regeneration lives. Same `graph.json`, two
renderers; the difference is honest in both.

Stdlib `http.server`, not FastAPI. D13 names FastAPI as the product stack but it is not an
installed dependency, and pulling one through the supply-chain policy and a technology
selection record for a localhost surface with one route buys nothing.

## Why this is more careful than a dev server usually is

A local server with a state-changing POST is reachable from **any page the operator's browser
visits**. A plain HTML form can cross-post to `127.0.0.1` without a preflight and without
reading the response, which is enough to make a machine run a generator on a stranger's cue.
Four controls, and none of them is the origin check alone:

* **Loopback bind.** `127.0.0.1`, never `0.0.0.0`. Not reachable off the machine at all.
* **A per-run token in a custom header.** A custom header forces a CORS preflight, which a
  cross-origin page cannot satisfy without this server agreeing — and it never does. The token
  is minted per run and exists only in the page this server rendered.
* **Host allowlist.** `Host:` must be loopback, which is what stops DNS rebinding — an
  attacker-controlled name resolving to 127.0.0.1 arrives with its own Host and is refused.
* **Origin allowlist.** A cross-origin `Origin` is refused outright rather than merely
  unauthenticated.

Everything served is generated in memory. Nothing is read from disk by request path, so there
is no traversal surface to get wrong.
"""

from __future__ import annotations

import argparse
import json
import secrets
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.vaultgraph import mirror                              # noqa: E402
from tools.vaultgraph.render import html as render_html          # noqa: E402
from tools.vaultgraph.runner import AuditFailed, build             # noqa: E402
from tools.vaultgraph.serialize import build_payload, dumps      # noqa: E402
from tools.vaultgraph.stamp import stamp                         # noqa: E402
from tools.vaultgraph.textio import ROOT                         # noqa: E402

HOST = "127.0.0.1"
DEFAULT_PORT = 8787
TOKEN = secrets.token_urlsafe(24)

#: Regenerating touches the working tree, so one at a time. Two overlapping runs would race
#: on every file the generator writes.
_LOCK = threading.Lock()


def _loopback(hostname: str) -> bool:
    host = hostname.rsplit(":", 1)[0].strip("[]")
    return host in ("127.0.0.1", "localhost", "::1")


class Handler(BaseHTTPRequestHandler):
    server_version = "AlfredVaultGraph/1"
    protocol_version = "HTTP/1.1"

    # ---- plumbing ------------------------------------------------------

    def log_message(self, fmt: str, *args: object) -> None:
        sys.stderr.write(f"  {self.address_string()} {fmt % args}\n")

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        # This page embeds a token and triggers a repository read. Nothing may frame it, and
        # no referrer may carry its URL onward.
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _refuse(self, status: int, reason: str) -> None:
        self._send(status, json.dumps({"error": reason}).encode("utf-8"), "application/json")

    def _origin_is_local(self) -> bool:
        if not _loopback(self.headers.get("Host", "")):
            return False
        origin = self.headers.get("Origin")
        return origin is None or _loopback(origin.split("://", 1)[-1])

    # ---- routes --------------------------------------------------------

    def _build(self):
        """The graph, or None having already answered with why there is none.

        The same two gates the CLI applies, in the same order and for the same reasons: a
        graph built from a drifted snapshot carries source pointers that still look like
        they resolve, and a graph that failed its floors is the vacuous result every
        extractor declares a floor to prevent. Serving either at 200 makes this surface a
        way to read output the committed surface would refuse to write."""
        code, messages = mirror.check()
        if code:
            self._refuse(503, "plan mirror integrity failed:\n  " + "\n  ".join(messages))
            return None
        try:
            return build(ROOT)
        except AuditFailed as failed:
            self._refuse(503, "extraction failed its floors:\n  " + "\n  ".join(failed.failures))
            return None

    def do_GET(self) -> None:  # noqa: N802 - the base class names it
        if not self._origin_is_local():
            self._refuse(403, "this surface answers loopback requests only")
            return
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            result = self._build()
            if result is None:
                return
            page = render_html.render(
                result.nodes, result.edges, result.anomalies, result.unparsed,
                live_token=TOKEN,
            )
            self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")
            return
        if path == "/stamp":
            # Deliberately unauthenticated and deliberately not behind the refresh token. It
            # changes nothing, reads no file content, and answers one hash -- the token exists
            # to stop a stranger's page *running the generator*, and spending it here would
            # only mean the page had to prove itself to ask a question it already knows the
            # answer to. The loopback bind and the Host allowlist still apply.
            self._send(200, json.dumps({"stamp": stamp(ROOT)}).encode("utf-8"),
                       "application/json")
            return
        if path == "/graph.json":
            result = self._build()
            if result is None:
                return
            body = dumps(build_payload(result, mirror.graph_inputs())).encode("utf-8")
            self._send(200, body, "application/json")
            return
        self._refuse(404, "no such path")

    def do_POST(self) -> None:  # noqa: N802
        if not self._origin_is_local():
            self._refuse(403, "this surface answers loopback requests only")
            return
        if self.path.split("?", 1)[0] != "/refresh":
            self._refuse(404, "no such path")
            return
        # The token lives only in the page this server rendered. Requiring it in a custom
        # header is what forces a preflight that no cross-origin page can satisfy.
        if not secrets.compare_digest(self.headers.get("X-Refresh-Token", ""), TOKEN):
            self._refuse(403, "missing or stale refresh token — reload this page")
            return
        if not _LOCK.acquire(blocking=False):
            self._refuse(409, "a regeneration is already running")
            return
        try:
            code, summary = regenerate()
        finally:
            _LOCK.release()
        if code:
            self._refuse(500, summary)
            return
        self._send(200, json.dumps({"summary": summary}).encode("utf-8"), "application/json")

    def do_OPTIONS(self) -> None:  # noqa: N802
        # Deliberately no Access-Control-Allow-* headers. A cross-origin preflight is meant to
        # fail here; that failure is the control.
        self._send(204, b"", "text/plain")


def regenerate() -> tuple[int, str]:
    """Sync the plan mirror, then rebuild — as a subprocess, so this surface runs exactly what
    CI runs rather than a second code path that can drift from it.

    The sync step is offered only where the live origin exists. On any other machine
    (every CI runner) `sync` rightly refuses — there is nothing to copy from — and
    rebuilding from the committed, seal-verified mirror is both sufficient and the
    documented semantics: absence of the origin is never itself a failure.
    """
    steps: list[tuple[str, list[str]]] = []
    if mirror.origin_reachable(mirror.load_manifest()):
        steps.append(("plan mirror", [sys.executable, "tools/gen_vault.py", "--sync-plan"]))
    steps.append(("vault", [sys.executable, "tools/gen_vault.py"]))
    lines: list[str] = []
    for label, command in steps:
        finished = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        tail = (finished.stdout.strip().splitlines() or ["(no output)"])[-1]
        if finished.returncode:
            detail = (finished.stderr.strip() or finished.stdout.strip()).splitlines()
            return finished.returncode, f"{label} failed: {(detail or ['unknown'])[-1]}"
        lines.append(tail)
    return 0, lines[-1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args(argv)

    server = ThreadingHTTPServer((HOST, args.port), Handler)
    print(f"Alfred register graph · http://{HOST}:{args.port}")
    print("  Regenerate re-reads the repository. Ctrl-C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
