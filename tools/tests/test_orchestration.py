"""Orchestration palette binding + topology validation.

Palette: 21 entries, version 1, every id unique kebab-case, ports from contract set,
category legal. Topology: production file passes lint; planted violations fail.
Mirrors `test_protected_binding.py` style: the binding pins the direction that drifts
silently — palette declares, topology must use it.
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import lint_topology  # type: ignore[import-not-found]

PALETTE_PATH = ROOT / "policy" / "node-palette.json"
TOPOLOGY_PATH = ROOT / "orchestration" / "topology.json"

LEGAL_CONTRACTS = {"delegates-to", "hands-off-to", "reviews", "feeds"}
LEGAL_CATEGORIES = {"planning", "execution", "review", "operator"}
KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def test_palette_has_21_entries_version_1() -> None:
    data = json.loads(PALETTE_PATH.read_text(encoding="utf-8"))
    assert data["version"] == 1
    assert len(data["nodes"]) == 21


def test_palette_ids_unique_and_kebab_case() -> None:
    data = json.loads(PALETTE_PATH.read_text(encoding="utf-8"))
    ids = [n["id"] for n in data["nodes"]]
    assert len(ids) == len(set(ids)), f"duplicate ids: {ids}"
    for nid in ids:
        assert KEBAB.match(nid), f"{nid!r} not kebab-case"


def test_palette_entry_schema() -> None:
    data = json.loads(PALETTE_PATH.read_text(encoding="utf-8"))
    for entry in data["nodes"]:
        assert "id" in entry and "label" in entry and "description" in entry
        assert "ports" in entry and "in" in entry["ports"] and "out" in entry["ports"]
        assert "category" in entry and entry["category"] in LEGAL_CATEGORIES
        for contract in entry["ports"]["in"] + entry["ports"]["out"]:
            assert contract in LEGAL_CONTRACTS, f"{entry['id']} has unknown contract {contract!r}"
        # defaults keys must be out:<contract>
        for key in entry.get("defaults", {}):
            assert key.startswith("out:"), f"{entry['id']} defaults key {key!r} must start with 'out:'"
            assert key.removeprefix("out:") in LEGAL_CONTRACTS


def test_palette_bijective_no_extra_spellings() -> None:
    """Every palette id is a stable single spelling; no duplicates case-insensitive."""
    data = json.loads(PALETTE_PATH.read_text(encoding="utf-8"))
    folded: dict[str, str] = {}
    for nid in [n["id"] for n in data["nodes"]]:
        low = nid.casefold()
        assert low not in folded, f"case collision {nid!r} vs {folded[low]!r}"
        folded[low] = nid


def test_topology_production_passes() -> None:
    findings = lint_topology.check_topology(base=ROOT)
    assert findings.violations == [], f"production topology should pass: {findings.violations}"
    assert findings.scanned == 15  # 8 nodes + 7 edges


def test_topology_validation_happy_and_fail_paths() -> None:
    # duplicate node id
    with tempfile.TemporaryDirectory() as raw:
        scratch = Path(raw)
        palette = json.loads(PALETTE_PATH.read_text(encoding="utf-8"))
        topo = json.loads(TOPOLOGY_PATH.read_text(encoding="utf-8"))
        topo["nodes"] = topo["nodes"] + [topo["nodes"][0].copy()]  # duplicate first
        (scratch / "policy").mkdir(parents=True, exist_ok=True)
        (scratch / "orchestration").mkdir(parents=True, exist_ok=True)
        (scratch / "policy" / "node-palette.json").write_text(json.dumps(palette), encoding="utf-8")
        (scratch / "orchestration" / "topology.json").write_text(json.dumps(topo), encoding="utf-8")
        findings = lint_topology.check_topology(base=scratch)
        assert any("TOP001" in v for v in findings.violations), "should catch duplicate node id"

    # unknown kind
    with tempfile.TemporaryDirectory() as raw:
        scratch = Path(raw)
        palette = json.loads(PALETTE_PATH.read_text(encoding="utf-8"))
        topo = json.loads(TOPOLOGY_PATH.read_text(encoding="utf-8"))
        topo["nodes"][0]["kind"] = "ghost-kind"
        (scratch / "policy").mkdir(parents=True, exist_ok=True)
        (scratch / "orchestration").mkdir(parents=True, exist_ok=True)
        (scratch / "policy" / "node-palette.json").write_text(json.dumps(palette), encoding="utf-8")
        (scratch / "orchestration" / "topology.json").write_text(json.dumps(topo), encoding="utf-8")
        findings = lint_topology.check_topology(base=scratch)
        assert any("TOP008" in v for v in findings.violations)

    # missing version
    with tempfile.TemporaryDirectory() as raw:
        scratch = Path(raw)
        palette = json.loads(PALETTE_PATH.read_text(encoding="utf-8"))
        topo = json.loads(TOPOLOGY_PATH.read_text(encoding="utf-8"))
        del topo["version"]
        (scratch / "policy").mkdir(parents=True, exist_ok=True)
        (scratch / "orchestration").mkdir(parents=True, exist_ok=True)
        (scratch / "policy" / "node-palette.json").write_text(json.dumps(palette), encoding="utf-8")
        (scratch / "orchestration" / "topology.json").write_text(json.dumps(topo), encoding="utf-8")
        findings = lint_topology.check_topology(base=scratch)
        assert any("TOP009" in v for v in findings.violations)
