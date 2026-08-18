#!/usr/bin/env python3
"""Build Alfred's knowledge graph and the Obsidian vault derived from it.

    python3 tools/gen_vault.py                # build graph.json (and, from stage 4, vault/)
    python3 tools/gen_vault.py --check        # fail if the committed output is stale or edited
    python3 tools/gen_vault.py --self-test    # prove the vacuity guards fire

Lives in `tools/` and not `scripts/` deliberately. `scripts/`, `.github/workflows/`, `policy/`,
`migrations/roles/` and `harness/` are inspector machinery under D20 — agents may improve the
factory and never the inspector. A generator landed in `scripts/` would trigger major-fix #8:
line-by-line human review plus a mandatory ADR, for a documentation tool that needs neither.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.vaultgraph import mirror                          # noqa: E402
from tools.vaultgraph.runner import run                      # noqa: E402
from tools.vaultgraph.selftest import self_test               # noqa: E402
from tools.vaultgraph.render import vault as render_vault      # noqa: E402
from tools.vaultgraph.serialize import (                       # noqa: E402
    build_payload, compare_tree, dumps, write_tree,
)
from tools.vaultgraph.textio import ROOT                      # noqa: E402

GRAPH = ROOT / "graph.json"
ARTIFACT = ROOT / "docs-graph.html"


def _report(result, *, verbose: bool) -> None:
    for report in sorted(result.reports, key=lambda r: r.name):
        ceiling = "" if report.max_nodes is None else f"/{report.max_nodes}"
        print(
            f"  {report.name:<16} scanned {report.scanned:>4}  "
            f"nodes {report.nodes:>4}{ceiling} (floor {report.min_nodes})  "
            f"edges {report.edges:>4} (floor {report.min_edges})  "
            f"unparsed {report.unparsed}/{report.max_unparsed}"
        )
    for anomaly in result.anomalies:
        print(f"  ANOMALY {anomaly.kind}: {anomaly.detail}")
    if verbose:
        for item in result.unparsed:
            print(f"  UNPARSED {item.source}: {item.text[:80]} — {item.reason}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="compare against the committed output; write nothing")
    parser.add_argument("--sync-plan", action="store_true", dest="sync_plan",
                        help="re-copy the plan file into plan/ and re-stamp its manifest")
    parser.add_argument("--require-origin", action="store_true", dest="require_origin",
                        help="with --check, treat an absent plan origin as a failure")
    parser.add_argument("--self-test", action="store_true", dest="selftest",
                        help="run the planted fixtures that prove the guards fire")
    parser.add_argument("--graph-only", action="store_true", dest="graph_only",
                        help="write graph.json and skip the vault")
    parser.add_argument("--verbose", action="store_true", help="list every unparsed item")
    args = parser.parse_args(argv)

    if args.selftest:
        return self_test()

    if args.sync_plan:
        code, message = mirror.sync()
        print(message)
        return code

    # Mirror integrity first. A graph built from a corrupted or drifted snapshot is worse than
    # no graph, because its source pointers still look like they resolve.
    mirror_code, mirror_messages = mirror.check(require_origin=args.require_origin)
    for message in mirror_messages:
        print(f"  {message}")
    if mirror_code:
        return mirror_code

    result = run(ROOT)
    _report(result, verbose=args.verbose)

    if not result.ok:
        for failure in result.failures:
            print(f"FAIL {failure}")
        print(f"\n{len(result.failures)} extraction failure(s) — no output written")
        return 1

    sources = mirror.load_manifest()
    inputs = {f"{s.id}_sha256": s.sha256 for s in sources}
    inputs.update({f"{s.id}_mirror": s.mirror for s in sources})
    content = dumps(build_payload(result, inputs))

    tree = (
        {} if args.graph_only
        else render_vault.build(result.nodes, result.edges, result.anomalies, result.unparsed)
    )
    if not args.graph_only:
        tree["docs-graph.html"] = render_vault.artifact(
            result.nodes, result.edges, result.anomalies, result.unparsed
        )

    if args.check:
        problems: list[str] = []
        if not GRAPH.exists():
            problems.append("missing: graph.json")
        elif GRAPH.read_text(encoding="utf-8") != content:
            problems.append("differs: graph.json")
        problems.extend(compare_tree(ROOT, tree))
        if problems:
            for problem in problems[:20]:
                print(f"  {problem}")
            if len(problems) > 20:
                print(f"  ... and {len(problems) - 20} more")
            print(
                f"ERROR the vault is stale or hand-edited ({len(problems)} problem(s)) — "
                "run python3 tools/gen_vault.py"
            )
            return 1
        print(
            f"OK vault current ({len(result.nodes)} nodes, {len(result.edges)} edges, "
            f"{len(tree)} notes)"
        )
        return 0

    GRAPH.write_text(content, encoding="utf-8", newline="\n")
    written, removed = write_tree(ROOT, tree)
    print(
        f"OK wrote graph.json ({len(result.nodes)} nodes, {len(result.edges)} edges) "
        f"and {len(tree)} vault notes ({written} changed, {removed} orphan(s) removed)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
