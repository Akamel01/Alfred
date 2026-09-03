#!/usr/bin/env python3
"""Topology lint — TOP001-TOP009 per orchestration-canvas-spec §6.

Checks `orchestration/topology.json` against `policy/node-palette.json`:

  TOP001 unique node ids
  TOP002 edge references valid nodes
  TOP003 source port declared in palette
  TOP004 target port declared in palette
  TOP005 contract legal for endpoint kinds
  TOP006 no duplicate edges
  TOP007 multiplicity/cycle rules (cycles forbidden for delegates-to, reviews, feeds)
  TOP008 palette conformance (all nodes from palette)
  TOP009 schema version present

Exit 0 clean, 1 on violation. `--self-test` plants each rule and proves it fires.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any

from _lintkit import REPO_ROOT, Findings, self_test_exit, vacuity_guard

PALETTE_PATH: Path = Path("policy/node-palette.json")
TOPOLOGY_PATH: Path = Path("orchestration/topology.json")
BINDINGS_PATH: Path = Path("policy/role-bindings.json")

# Contracts where cycles are forbidden. hands-off-to allows feedback loops.
CYCLE_FORBIDDEN: frozenset[str] = frozenset({"delegates-to", "reviews", "feeds"})
ALL_CONTRACTS: frozenset[str] = frozenset({"delegates-to", "hands-off-to", "reviews", "feeds"})


def _load_json(path: Path, base: Path = REPO_ROOT) -> tuple[dict[str, Any] | None, str | None]:
    full = base / path
    if not full.is_file():
        return None, f"missing file: {path}"
    try:
        data = json.loads(full.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, f"{path} does not parse: {exc}"
    return data, None


def _palette_map(palette: dict[str, Any]) -> dict[str, dict[str, Any]]:
    nodes: list[dict[str, Any]] = palette.get("nodes", [])
    return {entry["id"]: entry for entry in nodes if "id" in entry}


def _detect_cycle(edges: list[dict[str, Any]], contract: str, node_ids: set[str]) -> list[str]:
    """Return violations for cycles in subgraph of *contract*."""
    adj: dict[str, list[str]] = defaultdict(list)
    for e in edges:
        if e.get("contract") == contract:
            src = e.get("source", "")
            dst = e.get("target", "")
            if src in node_ids and dst in node_ids:
                adj[src].append(dst)

    visited: set[str] = set()
    stack: set[str] = set()
    violations: list[str] = []

    def dfs(node: str, trail: list[str]) -> None:
        visited.add(node)
        stack.add(node)
        trail.append(node)
        for nxt in adj.get(node, []):
            if nxt not in visited:
                dfs(nxt, trail)
            elif nxt in stack:
                # found cycle, report trail
                idx = trail.index(nxt) if nxt in trail else 0
                cycle = trail[idx:] + [nxt]
                violations.append(
                    f"TOP007 cycle forbidden for contract {contract!r}: {' -> '.join(cycle)}"
                )
        trail.pop()
        stack.remove(node)

    for nid in sorted(node_ids):
        if nid not in visited:
            dfs(nid, [])
    return violations


def check_topology(base: Path = REPO_ROOT) -> Findings:
    findings = Findings()
    palette_data, palette_err = _load_json(PALETTE_PATH, base)
    topology_data, topo_err = _load_json(TOPOLOGY_PATH, base)

    if palette_err is not None:
        findings.violations.append(palette_err)
        return findings
    if topo_err is not None:
        findings.violations.append(topo_err)
        return findings

    assert palette_data is not None and topology_data is not None

    # TOP009 version present
    if "version" not in topology_data:
        findings.violations.append("TOP009 topology missing 'version' field")
    elif not isinstance(topology_data["version"], int):
        findings.violations.append("TOP009 topology 'version' must be int")
    elif topology_data["version"] != 1:
        findings.violations.append(f"TOP009 topology version {topology_data['version']!r} != 1")

    if "version" not in palette_data:
        findings.violations.append("TOP009 palette missing 'version' field")
    elif palette_data["version"] != 1:
        findings.violations.append(f"TOP009 palette version {palette_data['version']!r} != 1")

    nodes: list[dict[str, Any]] = topology_data.get("nodes", [])  # type: ignore[assignment]
    edges: list[dict[str, Any]] = topology_data.get("edges", [])  # type: ignore[assignment]

    if not isinstance(nodes, list):
        findings.violations.append("TOP008 topology 'nodes' must be list")
        nodes = []
    if not isinstance(edges, list):
        findings.violations.append("TOP006 topology 'edges' must be list")
        edges = []

    findings.scanned = len(nodes) + len(edges)
    if findings.scanned == 0:
        # let vacuity guard handle, but also report
        return findings

    palette_by_id = _palette_map(palette_data)
    valid_kinds = set(palette_by_id.keys())

    # TOP001 unique node ids + build map kind by id
    seen: set[str] = set()
    duplicates: set[str] = set()
    id_to_kind: dict[str, str] = {}
    id_to_node: dict[str, dict[str, Any]] = {}
    for n in nodes:
        nid = n.get("id", "")
        kind = n.get("kind", "")
        if not nid:
            findings.violations.append("TOP001 node missing 'id'")
            continue
        if nid in seen:
            duplicates.add(nid)
        seen.add(nid)
        id_to_kind[nid] = kind
        id_to_node[nid] = n

        # TOP008 palette conformance
        if kind not in valid_kinds:
            findings.violations.append(f"TOP008 node {nid!r} kind {kind!r} not in palette")

    for dup in sorted(duplicates):
        findings.violations.append(f"TOP001 duplicate node id {dup!r}")

    node_ids = seen

    # TOP006 duplicate edges
    edge_keys: dict[tuple[str, str, str, str, str], int] = {}
    for e in edges:
        src = e.get("source", "")
        tgt = e.get("target", "")
        sp = e.get("source_port", "")
        tp = e.get("target_port", "")
        ct = e.get("contract", "")
        key = (src, sp, tgt, tp, ct)
        if key in edge_keys:
            findings.violations.append(
                f"TOP006 duplicate edge {e.get('id', '')!r}: same source:{sp} target:{tp} contract:{ct}"
            )
        else:
            edge_keys[key] = 1

    # Per-edge checks
    for e in edges:
        eid = e.get("id", "<no-id>")
        src = e.get("source", "")
        tgt = e.get("target", "")
        sp = e.get("source_port", "")
        tp = e.get("target_port", "")
        ct = e.get("contract", "")

        # TOP002 references
        if src not in node_ids:
            findings.violations.append(f"TOP002 edge {eid!r} source {src!r} not in nodes")
            continue
        if tgt not in node_ids:
            findings.violations.append(f"TOP002 edge {eid!r} target {tgt!r} not in nodes")
            continue

        src_kind = id_to_kind.get(src, "")
        tgt_kind = id_to_kind.get(tgt, "")
        src_entry = palette_by_id.get(src_kind)
        tgt_entry = palette_by_id.get(tgt_kind)

        # If palette missing, already reported TOP008, skip port checks
        if src_entry is None or tgt_entry is None:
            continue

        src_out: set[str] = set(src_entry.get("ports", {}).get("out", []))
        tgt_in: set[str] = set(tgt_entry.get("ports", {}).get("in", []))

        # TOP003
        if sp not in src_out:
            findings.violations.append(
                f"TOP003 edge {eid!r} source_port {sp!r} not in {src_kind!r} out {sorted(src_out)}"
            )
        # TOP004
        if tp not in tgt_in:
            findings.violations.append(
                f"TOP004 edge {eid!r} target_port {tp!r} not in {tgt_kind!r} in {sorted(tgt_in)}"
            )
        # TOP005 contract legal
        if ct not in ALL_CONTRACTS:
            findings.violations.append(f"TOP005 edge {eid!r} contract {ct!r} unknown")
        else:
            if ct not in src_out or ct not in tgt_in:
                findings.violations.append(
                    f"TOP005 edge {eid!r} contract {ct!r} not legal for {src_kind!r}->{tgt_kind!r} "
                    f"(source out {sorted(src_out)}, target in {sorted(tgt_in)})"
                )

        # Also check that source_port/target_port match contract when contract is known
        # (lenient: if ports are contract names, they should equal contract; but allow generic port names
        # only if they are in palette sets — already covered above)
        # No extra TOP code for mismatch; TOP003/004/005 cover it.

    # TOP007 cycles
    for contract in sorted(CYCLE_FORBIDDEN):
        violations = _detect_cycle(edges, contract, node_ids)
        findings.violations.extend(violations)

    return findings


# ---------------------------------------------------------------------- self-test


# ------------------------------------------------------------------- role bindings (TOP010-013)


def check_bindings(base: Path = REPO_ROOT) -> Findings:
    """TOP010-TOP013. The palette says which roles exist; the bindings say which ones run.

    This is a two-file invariant, which is why it extends this lint rather than living in a
    new one: a separate file would either duplicate the palette loader or leave the
    cross-check unowned.

    TOP010 every palette kind has a `bindable` value, and every `bindable` key is a real kind.
    TOP011 `bindable` agrees with the palette's own category. Stated explicitly *and* derived,
           then compared: an explicit `never` is a statement a reviewer sees in the diff, and
           deriving it from `category` is an inference that breaks silently the day a
           non-agent kind is added outside the operator category. Two independent expressions
           of one fact, checked against each other, is not two homes for it.
    TOP012 every binding names a kind whose `bindable` is `agent`, exactly once.
    TOP013 a binding with no agents states why. An empty `agents` list is a real answer --
           no ECC agent may hold validation authority -- but an unexplained one is an
           omission wearing the same shape.
    """
    findings = Findings()
    palette_data, palette_err = _load_json(PALETTE_PATH, base)
    bindings_data, bindings_err = _load_json(BINDINGS_PATH, base)

    if palette_err is not None:
        findings.violations.append(palette_err)
        return findings
    if bindings_err is not None:
        findings.violations.append(bindings_err)
        return findings

    assert palette_data is not None and bindings_data is not None

    kinds = _palette_map(palette_data)
    declared: dict[str, Any] = bindings_data.get("bindable_by_kind") or bindings_data.get("kinds") or {}
    bindings: list[dict[str, Any]] = bindings_data.get("bindings", [])  # type: ignore[assignment]
    findings.scanned = len(kinds) + len(bindings)

    legal = {"agent", "unbound", "never"}

    # TOP010 -- both directions.
    for kind_id in sorted(kinds):
        if kind_id not in declared:
            findings.violations.append(f"TOP010 palette kind {kind_id!r} has no bindable value")
    for kind_id in sorted(declared):
        if kind_id not in kinds:
            findings.violations.append(f"TOP010 bindable names {kind_id!r}, which is not a palette kind")
        elif declared[kind_id] not in legal:
            findings.violations.append(
                f"TOP010 kind {kind_id!r} bindable {declared[kind_id]!r} not in {sorted(legal)}"
            )

    # TOP011 -- explicit against derived.
    for kind_id, value in sorted(declared.items()):
        node = kinds.get(kind_id)
        if node is None or value not in legal:
            continue
        is_operator = node.get("category") == "operator"
        if is_operator and value != "never":
            findings.violations.append(
                f"TOP011 kind {kind_id!r} is category 'operator' but bindable is {value!r}, not 'never'"
            )
        if not is_operator and value == "never":
            findings.violations.append(
                f"TOP011 kind {kind_id!r} is bindable 'never' but category is "
                f"{node.get('category')!r}, not 'operator'"
            )

    # TOP012 -- one binding per agent-bindable kind.
    seen: dict[str, int] = {}
    for binding in bindings:
        kind_id = binding.get("kind")
        if not isinstance(kind_id, str):
            findings.violations.append("TOP012 a binding has no 'kind'")
            continue
        seen[kind_id] = seen.get(kind_id, 0) + 1
        if declared.get(kind_id) != "agent":
            findings.violations.append(
                f"TOP012 binding for {kind_id!r} whose bindable is "
                f"{declared.get(kind_id)!r}, not 'agent'"
            )
    for kind_id, count in sorted(seen.items()):
        if count > 1:
            findings.violations.append(f"TOP012 kind {kind_id!r} has {count} bindings, expected 1")
    for kind_id, value in sorted(declared.items()):
        if value == "agent" and kind_id not in seen:
            findings.violations.append(f"TOP012 kind {kind_id!r} is bindable 'agent' but has no binding")

    # TOP013 -- an empty roster is an answer only when it says why.
    for binding in bindings:
        kind_id = binding.get("kind", "<unnamed>")
        if not binding.get("agents") and not binding.get("unbound_reason"):
            findings.violations.append(
                f"TOP013 binding {kind_id!r} names no agents and gives no unbound_reason"
            )

    return findings


def _valid_palette() -> dict[str, Any]:
    """Minimal palette for self-test: covers cases needed."""
    return {
        "version": 1,
        "nodes": [
            {"id": "planner", "label": "Planner", "description": "p", "ports": {"in": [], "out": ["delegates-to"]}, "defaults": {}, "icon": "x", "category": "planning"},
            {"id": "code-writer", "label": "CW", "description": "c", "ports": {"in": ["delegates-to", "reviews"], "out": ["hands-off-to"]}, "defaults": {}, "icon": "x", "category": "execution"},
            {"id": "reviewer", "label": "Rev", "description": "r", "ports": {"in": ["hands-off-to"], "out": ["reviews"]}, "defaults": {}, "icon": "x", "category": "review"},
            {"id": "researcher", "label": "Res", "description": "r", "ports": {"in": ["delegates-to"], "out": ["hands-off-to"]}, "defaults": {}, "icon": "x", "category": "execution"},
            {"id": "drafter", "label": "Draft", "description": "d", "ports": {"in": ["delegates-to", "hands-off-to"], "out": ["hands-off-to"]}, "defaults": {}, "icon": "x", "category": "execution"},
        ],
    }


def _valid_topology() -> dict[str, Any]:
    return {
        "version": 1,
        "metadata": {"created_at": "2026-08-26T00:00:00Z", "updated_at": "2026-08-26T00:00:00Z", "author": "operator", "description": "test"},
        "nodes": [
            {"id": "n1", "kind": "planner", "label": "Planner", "position": {"x": 0, "y": 0}},
            {"id": "n2", "kind": "code-writer", "label": "CW", "position": {"x": 100, "y": 0}},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "source_port": "delegates-to", "target": "n2", "target_port": "delegates-to", "contract": "delegates-to", "label": ""},
        ],
    }


def _write_fixture(root: Path, palette: dict[str, Any] | None, topology: dict[str, Any] | None) -> None:
    if palette is not None:
        p = root / PALETTE_PATH
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(palette), encoding="utf-8")
    if topology is not None:
        t = root / TOPOLOGY_PATH
        t.parent.mkdir(parents=True, exist_ok=True)
        t.write_text(json.dumps(topology), encoding="utf-8")


def _write_bindings(root: Path, palette: dict[str, Any], bindings: dict[str, Any]) -> None:
    p = root / PALETTE_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(palette), encoding="utf-8")
    b = root / BINDINGS_PATH
    b.parent.mkdir(parents=True, exist_ok=True)
    b.write_text(json.dumps(bindings), encoding="utf-8")


def _binding_palette() -> dict[str, Any]:
    """Palette for the binding checks: one agent-bindable kind and one operator kind.

    The operator kind is the point -- TOP011 compares the explicit `bindable` against the
    category, and a fixture with no operator kind cannot exercise either direction of it.
    """
    palette = _valid_palette()
    palette["nodes"].append({
        "id": "evidence-store", "label": "Evidence", "description": "e",
        "ports": {"in": [], "out": []}, "defaults": {}, "icon": "x", "category": "operator",
    })
    return palette


def _valid_bindings() -> dict[str, Any]:
    return {
        "version": 1,
        "kinds": {
            "planner": "agent",
            "code-writer": "unbound",
            "reviewer": "unbound",
            "researcher": "unbound",
            "drafter": "unbound",
            "evidence-store": "never",
        },
        "bindings": [
            {"kind": "planner", "capability_id": "capability:planner@1",
             "agents": [{"agent": "planner", "harness": "claude-code"}]},
        ],
    }


def self_test() -> int:
    failures: list[str] = []

    with tempfile.TemporaryDirectory() as raw:
        scratch = Path(raw)

        # control: valid palette + valid topology must be clean
        clean = scratch / "clean"
        _write_fixture(clean, _valid_palette(), _valid_topology())
        ctrl = check_topology(base=clean)
        if ctrl.violations:
            failures.append(f"control fired on clean: {ctrl.violations}")

        # TOP001 duplicate node id
        case = scratch / "top001"
        topo = _valid_topology()
        topo["nodes"] = [
            {"id": "n1", "kind": "planner", "label": "Planner", "position": {"x": 0, "y": 0}},
            {"id": "n1", "kind": "code-writer", "label": "CW", "position": {"x": 100, "y": 0}},
        ]
        _write_fixture(case, _valid_palette(), topo)
        if not any("TOP001" in v for v in check_topology(base=case).violations):
            failures.append("TOP001 did not fire on duplicate node id")

        # TOP002 edge references missing node
        case = scratch / "top002"
        topo = _valid_topology()
        topo["edges"][0]["target"] = "n9"
        _write_fixture(case, _valid_palette(), topo)
        if not any("TOP002" in v for v in check_topology(base=case).violations):
            failures.append("TOP002 did not fire on missing target")

        # TOP003 source port not in palette
        case = scratch / "top003"
        topo = _valid_topology()
        topo["edges"][0]["source_port"] = "reviews"
        _write_fixture(case, _valid_palette(), topo)
        if not any("TOP003" in v for v in check_topology(base=case).violations):
            failures.append("TOP003 did not fire on bad source_port")

        # TOP004 target port not in palette
        case = scratch / "top004"
        topo = _valid_topology()
        topo["edges"][0]["target_port"] = "hands-off-to"
        _write_fixture(case, _valid_palette(), topo)
        if not any("TOP004" in v for v in check_topology(base=case).violations):
            failures.append("TOP004 did not fire on bad target_port")

        # TOP005 contract not legal for pair
        case = scratch / "top005"
        topo = _valid_topology()
        # planner delegates-to code-writer is legal, change to reviews which is not
        topo["edges"][0]["contract"] = "reviews"
        topo["edges"][0]["source_port"] = "delegates-to"  # keep ports valid for TOP003/004 to isolate TOP005
        topo["edges"][0]["target_port"] = "delegates-to"
        _write_fixture(case, _valid_palette(), topo)
        # Purposely make contract illegal: planner out delegates-to only, so reviews illegal
        if not any("TOP005" in v for v in check_topology(base=case).violations):
            failures.append("TOP005 did not fire on illegal contract for pair")

        # TOP006 duplicate edge
        case = scratch / "top006"
        topo = _valid_topology()
        topo["edges"] = [topo["edges"][0], topo["edges"][0].copy()]
        topo["edges"][1]["id"] = "e2"
        _write_fixture(case, _valid_palette(), topo)
        if not any("TOP006" in v for v in check_topology(base=case).violations):
            failures.append("TOP006 did not fire on duplicate edge")

        # TOP007 cycle forbidden for delegates-to
        case = scratch / "top007"
        topo = {
            "version": 1,
            "metadata": {"created_at": "2026-08-26T00:00:00Z", "updated_at": "2026-08-26T00:00:00Z", "author": "operator", "description": "cycle"},
            "nodes": [
                {"id": "n1", "kind": "planner", "label": "Planner", "position": {"x": 0, "y": 0}},
                {"id": "n2", "kind": "code-writer", "label": "CW", "position": {"x": 100, "y": 0}},
                {"id": "n3", "kind": "researcher", "label": "R", "position": {"x": 200, "y": 0}},
            ],
            "edges": [
                {"id": "e1", "source": "n1", "source_port": "delegates-to", "target": "n2", "target_port": "delegates-to", "contract": "delegates-to", "label": ""},
                {"id": "e2", "source": "n2", "source_port": "hands-off-to", "target": "n3", "target_port": "hands-off-to", "contract": "hands-off-to", "label": ""},
            ],
        }
        # For cycle we need delegates-to that cycles: add planner->code-writer and code-writer->planner but code-writer cannot delegates-to planner (planner in []), so use planner self-loop via two planners?
        # Simpler: two planners delegating to each other via code-writer intermediary not possible due to kind restrictions.
        # So plant a direct reviews cycle: reviewer->code-writer and code-writer via ??? Instead plant delegates-to cycle using two code-writer nodes that can be both source? But code-writer out is hands-off-to not delegates-to, so cannot form delegates-to cycle.
        # Use reviews cycle: reviewer->code-writer and then make code-writer a reviewer? Not valid.
        # For test, we can make palette that allows cycle: use planner -> planner? But palette says planner in [] so cannot be target. So for self-test we need a custom palette where delegates-to allows cycle.
        # Instead test feeds cycle with nodes that support it: we need a palette where nodes can both feed.
        # Simpler: create palette where a.kind out delegates-to and in delegates-to, enabling cycle.
        palette_cycle = {
            "version": 1,
            "nodes": [
                {"id": "a", "label": "A", "description": "a", "ports": {"in": ["delegates-to"], "out": ["delegates-to"]}, "defaults": {}, "icon": "x", "category": "planning"},
                {"id": "b", "label": "B", "description": "b", "ports": {"in": ["delegates-to"], "out": ["delegates-to"]}, "defaults": {}, "icon": "x", "category": "planning"},
            ],
        }
        topo_cycle = {
            "version": 1,
            "metadata": {"created_at": "2026-08-26T00:00:00Z", "updated_at": "2026-08-26T00:00:00Z", "author": "operator", "description": "cycle"},
            "nodes": [
                {"id": "n1", "kind": "a", "label": "A1", "position": {"x": 0, "y": 0}},
                {"id": "n2", "kind": "b", "label": "B1", "position": {"x": 100, "y": 0}},
            ],
            "edges": [
                {"id": "e1", "source": "n1", "source_port": "delegates-to", "target": "n2", "target_port": "delegates-to", "contract": "delegates-to", "label": ""},
                {"id": "e2", "source": "n2", "source_port": "delegates-to", "target": "n1", "target_port": "delegates-to", "contract": "delegates-to", "label": ""},
            ],
        }
        _write_fixture(case, palette_cycle, topo_cycle)
        if not any("TOP007" in v for v in check_topology(base=case).violations):
            failures.append("TOP007 did not fire on delegates-to cycle")
        # Verify hands-off-to cycle is allowed (no violation)
        case2 = scratch / "top007-allow"
        palette_allow = {
            "version": 1,
            "nodes": [
                {"id": "a", "label": "A", "description": "a", "ports": {"in": ["hands-off-to"], "out": ["hands-off-to"]}, "defaults": {}, "icon": "x", "category": "execution"},
                {"id": "b", "label": "B", "description": "b", "ports": {"in": ["hands-off-to"], "out": ["hands-off-to"]}, "defaults": {}, "icon": "x", "category": "execution"},
            ],
        }
        _write_fixture(case2, palette_allow, topo_cycle)
        # Change contract to hands-off-to for both edges
        topo_allow = {
            "version": 1,
            "metadata": {"created_at": "2026-08-26T00:00:00Z", "updated_at": "2026-08-26T00:00:00Z", "author": "operator", "description": "cycle-allow"},
            "nodes": topo_cycle["nodes"],
            "edges": [
                {"id": "e1", "source": "n1", "source_port": "hands-off-to", "target": "n2", "target_port": "hands-off-to", "contract": "hands-off-to", "label": ""},
                {"id": "e2", "source": "n2", "source_port": "hands-off-to", "target": "n1", "target_port": "hands-off-to", "contract": "hands-off-to", "label": ""},
            ],
        }
        _write_fixture(case2, palette_allow, topo_allow)
        if any("TOP007" in v for v in check_topology(base=case2).violations):
            failures.append("TOP007 fired on hands-off-to cycle which should be allowed")

        # TOP008 palette conformance
        case = scratch / "top008"
        topo = _valid_topology()
        topo["nodes"][0]["kind"] = "unknown-kind"
        _write_fixture(case, _valid_palette(), topo)
        if not any("TOP008" in v for v in check_topology(base=case).violations):
            failures.append("TOP008 did not fire on unknown kind")

        # TOP009 missing version
        case = scratch / "top009"
        topo = _valid_topology()
        del topo["version"]
        _write_fixture(case, _valid_palette(), topo)
        if not any("TOP009" in v for v in check_topology(base=case).violations):
            failures.append("TOP009 did not fire on missing version")

        # vacuity guard: empty topology should report scanned 0
        case = scratch / "empty"
        _write_fixture(case, _valid_palette(), {"version": 1, "metadata": {}, "nodes": [], "edges": []})
        if check_topology(base=case).scanned != 0:
            failures.append("empty topology did not report zero scanned")

        # ---- role bindings TOP010-TOP013 ------------------------------------------------

        # control: valid palette + valid bindings must be clean
        case = scratch / "bind-clean"
        _write_bindings(case, _binding_palette(), _valid_bindings())
        ctrl_b = check_bindings(base=case)
        if ctrl_b.violations:
            failures.append(f"binding control fired on clean: {ctrl_b.violations}")

        # TOP010 a palette kind with no bindable value
        case = scratch / "top010a"
        b = _valid_bindings()
        del b["kinds"]["drafter"]
        _write_bindings(case, _binding_palette(), b)
        if not any("TOP010" in v for v in check_bindings(base=case).violations):
            failures.append("TOP010 did not fire on a kind with no bindable value")

        # TOP010 the reverse direction: a bindable naming no palette kind
        case = scratch / "top010b"
        b = _valid_bindings()
        b["kinds"]["ghost-kind"] = "unbound"
        _write_bindings(case, _binding_palette(), b)
        if not any("TOP010" in v for v in check_bindings(base=case).violations):
            failures.append("TOP010 did not fire on a bindable naming no palette kind")

        # TOP011 an operator kind declared bindable
        case = scratch / "top011a"
        b = _valid_bindings()
        b["kinds"]["evidence-store"] = "agent"
        _write_bindings(case, _binding_palette(), b)
        if not any("TOP011" in v for v in check_bindings(base=case).violations):
            failures.append("TOP011 did not fire on an operator kind declared bindable")

        # TOP011 the reverse direction: 'never' on a non-operator kind
        case = scratch / "top011b"
        b = _valid_bindings()
        b["kinds"]["drafter"] = "never"
        _write_bindings(case, _binding_palette(), b)
        if not any("TOP011" in v for v in check_bindings(base=case).violations):
            failures.append("TOP011 did not fire on 'never' outside the operator category")

        # TOP012 a binding for a kind that is not bindable 'agent'
        case = scratch / "top012a"
        b = _valid_bindings()
        b["bindings"].append({"kind": "drafter", "agents": [{"agent": "x", "harness": "y"}]})
        _write_bindings(case, _binding_palette(), b)
        if not any("TOP012" in v for v in check_bindings(base=case).violations):
            failures.append("TOP012 did not fire on a binding for a non-agent kind")

        # TOP012 a kind bindable 'agent' with no binding
        case = scratch / "top012b"
        b = _valid_bindings()
        b["bindings"] = []
        _write_bindings(case, _binding_palette(), b)
        if not any("TOP012" in v for v in check_bindings(base=case).violations):
            failures.append("TOP012 did not fire on an agent kind with no binding")

        # TOP013 an empty agent roster with no stated reason
        case = scratch / "top013"
        b = _valid_bindings()
        b["bindings"][0]["agents"] = []
        _write_bindings(case, _binding_palette(), b)
        if not any("TOP013" in v for v in check_bindings(base=case).violations):
            failures.append("TOP013 did not fire on an empty roster with no unbound_reason")

        # TOP013 negative control: an empty roster WITH a reason is legal
        case = scratch / "top013-ok"
        b = _valid_bindings()
        b["bindings"][0]["agents"] = []
        b["bindings"][0]["unbound_reason"] = "no agent may hold this authority"
        _write_bindings(case, _binding_palette(), b)
        if any("TOP013" in v for v in check_bindings(base=case).violations):
            failures.append("TOP013 fired on an empty roster that stated its reason")

    return self_test_exit(
        failures,
        "OK self-test — TOP001 duplicate id, TOP002 missing ref, TOP003 bad source_port, "
        "TOP004 bad target_port, TOP005 illegal contract, TOP006 duplicate edge, "
        "TOP007 cycle forbidden/allowed, TOP008 unknown kind, TOP009 missing version, "
        "TOP010 unbindable/unknown kind both directions, TOP011 category disagreement both "
        "directions, TOP012 binding/bindable mismatch both directions, TOP013 unexplained "
        "empty roster with its paired control; control clean\n",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint orchestration topology TOP001-TOP009")
    parser.add_argument("--check", action="store_true", help="check files (default)")
    parser.add_argument("--self-test", action="store_true", help="plant violations and verify each check fires")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    findings = check_topology()
    bindings = check_bindings()
    for violation in [*findings.violations, *bindings.violations]:
        sys.stdout.write(f"{violation}\n")
    if vacuity_guard(findings.scanned, "VACUOUS topology: scanned 0 nodes+edges\n"):
        return 1
    if vacuity_guard(bindings.scanned, "VACUOUS bindings: scanned 0 kinds+bindings\n"):
        return 1
    if findings.violations or bindings.violations:
        return 1
    sys.stdout.write(
        f"OK topology — {findings.scanned} nodes+edges, all TOP001-TOP009 satisfied; "
        f"bindings — {bindings.scanned} kinds+bindings, all TOP010-TOP013 satisfied\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
