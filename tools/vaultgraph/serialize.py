"""Canonical JSON. The rules here are the whole of the determinism guarantee.

Byte-identical output on re-run comes from four properties and nothing else:

* every collection is sorted before it is written — nodes by id, edges by a total key that
  includes the evidence string, so two edges differing only in evidence still order stably;
* `sort_keys=True`, so no dict insertion order reaches the file;
* nothing derived from wall clock, hostname, `id()`, `hash()`, `uuid` or `random` is written;
* every path is repo-relative, via the single choke point in `textio.rel`.

`ensure_ascii=False` because the corpus is full of en-dashes and U+2212 minus signs and
escaping them makes the file unreadable in a diff. The choice matters less than the fact that
it is fixed.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from .model import Edge, Node
from .protocol import Anomaly, Rejected, Unparsed
from .runner import RunResult

SCHEMA_VERSION = 1


def _node_key(node: Node) -> str:
    return node.id


def _edge_key(edge: Edge) -> tuple[str, str, str, str, int, str]:
    return (
        edge.kind.value,
        edge.src,
        edge.dst,
        edge.source.path,
        edge.source.line,
        edge.evidence,
    )


def _flag_key(item: Unparsed | Rejected) -> tuple[str, str, int, str]:
    return (item.extractor, item.source.path, item.source.line, item.text)


def _anomaly_key(item: Anomaly) -> tuple[str, str]:
    return (item.kind, item.detail)


def build_payload(result: RunResult, inputs: dict[str, str]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for node in result.nodes:
        counts[node.kind.value] = counts.get(node.kind.value, 0) + 1
    edge_counts: dict[str, int] = {}
    for edge in result.edges:
        edge_counts[edge.kind.value] = edge_counts.get(edge.kind.value, 0) + 1

    return {
        "schema_version": SCHEMA_VERSION,
        "generator": "tools/vaultgraph",
        "inputs": dict(sorted(inputs.items())),
        "counts": dict(sorted(counts.items())),
        "edge_counts": dict(sorted(edge_counts.items())),
        "extractors": [asdict(r) for r in sorted(result.reports, key=lambda r: r.name)],
        "nodes": [asdict(n) for n in sorted(result.nodes, key=_node_key)],
        "edges": [asdict(e) for e in sorted(result.edges, key=_edge_key)],
        "unparsed": [asdict(u) for u in sorted(result.unparsed, key=_flag_key)],
        "rejected": [asdict(r) for r in sorted(result.rejected, key=_flag_key)],
        "anomalies": [asdict(a) for a in sorted(result.anomalies, key=_anomaly_key)],
    }


def dumps(payload: dict[str, Any]) -> str:
    """The one serialization. A trailing newline so the file ends like every other text file
    in the repo and `git diff` does not report `\\ No newline at end of file` forever."""
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
