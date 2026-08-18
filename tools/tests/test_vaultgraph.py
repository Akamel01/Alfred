"""The generator's own guards, asserted from outside the generator.

`--self-test` proves the vacuity guards fire and ships that proof with the code. This suite
proves the things a planted fixture cannot: that the real repo produces the counts the design
claims, that two builds agree byte for byte, and that `--check` fails on each of the three
ways committed output can go wrong (stale, deleted, hand-edited).

**How this suite would be shown vacuous** (D57): every count assertion here is an equality
against a number this repo actually holds today, so a regex that stopped matching would fail
rather than pass quieter. `test_registry_rejects_a_floorless_extractor` is the control for the
registry validation itself — remove the `min_nodes <= 0` clause from `protocol.validate_registry`
and it goes red.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from tools.vaultgraph.model import Minter, MintError, NodeKind, SourceRef  # noqa: E402
from tools.vaultgraph.protocol import (  # noqa: E402
    ExtractorSpec,
    Harvest,
    RegistryError,
    validate_registry,
)
from tools.vaultgraph.runner import run  # noqa: E402
from tools.vaultgraph.selftest import self_test  # noqa: E402
from tools.vaultgraph.serialize import build_payload, dumps  # noqa: E402


def _result():
    return run(ROOT)


# ---- counts against the real repo -------------------------------------------------------

def test_the_register_yields_sixty_three_documents() -> None:
    # 63, not the 65 the handoff quoted: docs/README.md and docs/READING-MAP.md are generated
    # and excluded, exactly as scripts/lint_docs.py:169-174 excludes them.
    result = _result()
    assert sum(1 for n in result.nodes if n.kind is NodeKind.DOCUMENT) == 63


def test_every_tier_directory_becomes_one_node() -> None:
    result = _result()
    assert sum(1 for n in result.nodes if n.kind is NodeKind.TIER) == 8


def test_every_document_carries_a_falsification_condition() -> None:
    # The relation the graph exists to make visible. All 63 state one; a parser that stopped
    # reading frontmatter would drop this to zero and this assertion is what would say so.
    result = _result()
    docs = [n for n in result.nodes if n.kind is NodeKind.DOCUMENT]
    assert docs and all(n.attrs["falsifies_if"] for n in docs)


def test_every_source_pointer_resolves_to_a_real_file() -> None:
    result = _result()
    for node in result.nodes:
        target = ROOT / node.source.path
        assert target.exists(), f"{node.id} points at {node.source}"


def test_the_extraction_reports_no_failures() -> None:
    assert _result().failures == []


# ---- determinism -------------------------------------------------------------------------

def test_two_builds_are_byte_identical() -> None:
    assert dumps(build_payload(run(ROOT), {})) == dumps(build_payload(run(ROOT), {}))


def test_no_absolute_path_reaches_the_output() -> None:
    assert str(ROOT) not in dumps(build_payload(run(ROOT), {}))


@pytest.mark.parametrize("seed", ["0", "1"])
def test_output_is_stable_across_hash_seeds(seed: str) -> None:
    # A same-process double build cannot catch a set reaching output; two seeds can.
    probe = (
        "import sys; sys.path.insert(0, '.');"
        "from tools.vaultgraph.runner import run;"
        "from tools.vaultgraph.serialize import build_payload, dumps;"
        "from tools.vaultgraph.textio import ROOT;"
        "sys.stdout.write(dumps(build_payload(run(ROOT), {})))"
    )
    out = subprocess.run(
        [sys.executable, "-c", probe], cwd=ROOT, capture_output=True, text=True, check=True,
        env={"PYTHONHASHSEED": seed, "PATH": "/usr/bin:/bin"},
    ).stdout
    assert out == dumps(build_payload(run(ROOT), {}))


def test_graph_json_is_valid_json_and_carries_its_schema_version() -> None:
    payload = json.loads(dumps(build_payload(run(ROOT), {})))
    assert payload["schema_version"] == 1
    assert payload["nodes"] == sorted(payload["nodes"], key=lambda n: n["id"])


# ---- --check catches all three ways output goes wrong -------------------------------------

def _cli(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "tools/gen_vault.py", *args], cwd=cwd, capture_output=True, text=True
    )


def test_check_passes_on_committed_output() -> None:
    _cli(cwd=ROOT)
    assert _cli("--check", cwd=ROOT).returncode == 0


def test_check_fails_on_a_hand_edited_graph(tmp_path: Path) -> None:
    graph = ROOT / "graph.json"
    original = graph.read_text(encoding="utf-8")
    try:
        graph.write_text(original.replace('"schema_version": 1', '"schema_version": 2'), encoding="utf-8")
        assert _cli("--check", cwd=ROOT).returncode == 1
    finally:
        graph.write_text(original, encoding="utf-8")


def test_check_fails_when_output_is_missing() -> None:
    graph = ROOT / "graph.json"
    original = graph.read_text(encoding="utf-8")
    try:
        graph.unlink()
        assert _cli("--check", cwd=ROOT).returncode == 1
    finally:
        graph.write_text(original, encoding="utf-8")


# ---- the guards themselves ----------------------------------------------------------------

def test_self_test_passes() -> None:
    assert self_test() == 0


def test_registry_rejects_a_floorless_extractor() -> None:
    spec = ExtractorSpec(
        name="floorless", kinds=(NodeKind.DOCUMENT,), min_nodes=0, max_nodes=None,
        min_edges=0, max_unparsed=0, expect_rejected=None, run=lambda ctx: Harvest(),
    )
    with pytest.raises(RegistryError, match="no floor"):
        validate_registry((spec,), floor=1)


def test_registry_rejects_duplicate_names() -> None:
    spec = ExtractorSpec(
        name="twice", kinds=(NodeKind.DOCUMENT,), min_nodes=1, max_nodes=None,
        min_edges=0, max_unparsed=0, expect_rejected=None, run=lambda ctx: Harvest(),
    )
    with pytest.raises(RegistryError, match="duplicate"):
        validate_registry((spec, spec), floor=1)


def test_ids_differing_only_by_case_are_refused() -> None:
    # One file on macOS, two on Linux. The vault must not depend on which machine built it.
    minter = Minter()
    minter.mint(NodeKind.DECISION, "D1", SourceRef("f.md", 1))
    with pytest.raises(MintError, match="case-insensitively"):
        minter.mint(NodeKind.DECISION, "d1", SourceRef("f.md", 2))


# ---- the plan mirror ----------------------------------------------------------------------

from tools.vaultgraph import mirror  # noqa: E402


def test_the_mirror_matches_its_manifest() -> None:
    code, messages = mirror.check()
    assert code == 0, messages


def test_an_absent_origin_is_not_a_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    # CI, a clean clone, and anyone else's machine all have no ~/.claude/plans. Absence is
    # never a failure; drift always is. Without this the vault stops building off one laptop.
    monkeypatch.setattr(mirror, "origin_path", lambda source: Path("/nonexistent/plan.md"))
    code, messages = mirror.check()
    assert code == 0
    assert any("origin absent" in m for m in messages)


def test_an_absent_origin_fails_only_when_the_operator_asks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mirror, "origin_path", lambda source: Path("/nonexistent/plan.md"))
    assert mirror.check(require_origin=True)[0] == 1


def test_a_drifted_origin_fails(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    drifted = tmp_path / "drifted.md"
    drifted.write_text("not the plan", encoding="utf-8")
    monkeypatch.setattr(mirror, "origin_path", lambda source: drifted)
    code, messages = mirror.check()
    assert code == 1
    assert any("drifted" in m for m in messages)


def test_the_manifest_carries_no_timestamp() -> None:
    # A capture time is unverifiable metadata that would break the manifest's own byte
    # determinism to record something nothing checks.
    raw = (ROOT / "plan" / "manifest.json").read_text(encoding="utf-8")
    assert "captured" not in raw and "timestamp" not in raw


# ---- decisions ----------------------------------------------------------------------------

def test_all_fifty_seven_decisions_are_extracted() -> None:
    result = _result()
    numbers = sorted(
        int(n.attrs["number"]) for n in result.nodes if n.kind is NodeKind.DECISION
    )
    assert numbers == list(range(1, 58))


def test_the_decision_shapes_are_split_as_the_plan_writes_them() -> None:
    # 48 table rows (D1-D38 plus the blank-line-separated D48-D57), 3 headings (D39-D41),
    # 6 bold-lead paragraphs (D42-D47).
    result = _result()
    shapes: dict[str, int] = {}
    for node in result.nodes:
        if node.kind is NodeKind.DECISION:
            shapes[node.shape] = shapes.get(node.shape, 0) + 1
    assert shapes == {"table-row": 48, "heading": 3, "bold-paragraph": 6}


def test_restatements_fold_into_occurrences_rather_than_new_nodes() -> None:
    result = _result()
    by_number = {n.attrs["number"]: n for n in result.nodes if n.kind is NodeKind.DECISION}
    assert len(by_number["45"].occurrences) == 2   # amended, then finalized
    assert len(by_number["47"].occurrences) == 1   # amended
    assert len(by_number["17"].occurrences) == 1   # the superseded decision's own chapter


def test_all_twelve_amendments_are_extracted() -> None:
    result = _result()
    assert sum(1 for n in result.nodes if n.kind is NodeKind.AMENDMENT) == 12
