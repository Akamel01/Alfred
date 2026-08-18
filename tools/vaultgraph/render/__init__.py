"""Renderers. Downstream of one extraction, and structurally unable to reach it.

Nothing under `render/` may import from `extract/`. A layering check in `--self-test` asserts
that transitively, using the same BFS technique `scripts/lint_verdict_boundary.py` uses on the
verdict boundary -- a one-hop check would miss `render.note -> helpers -> extract.decisions`.
"""

from __future__ import annotations

__all__ = ["canvas", "dataview", "note", "vault"]
