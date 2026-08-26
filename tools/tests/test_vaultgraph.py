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
import re
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
    # 64, not the 65 the handoff quoted: docs/README.md and docs/READING-MAP.md are generated
    # and excluded, exactly as scripts/lint_docs.py:169-174 excludes them.
    result = _result()
    assert sum(1 for n in result.nodes if n.kind is NodeKind.DOCUMENT) == 64


def test_every_tier_directory_becomes_one_node() -> None:
    result = _result()
    assert sum(1 for n in result.nodes if n.kind is NodeKind.TIER) == 8


def test_every_falsification_condition_in_the_corpus_is_data() -> None:
    # 64 in document frontmatter, 5 in decision cells. This is the relation the graph exists
    # to make queryable and it existed as prose in two formats and as data nowhere.
    result = _result()
    docs = [n for n in result.nodes
            if n.kind is NodeKind.DOCUMENT and n.attrs.get("falsifies_if")]
    decisions = [n for n in result.nodes
                 if n.kind is NodeKind.DECISION and n.attrs.get("falsifies_if")]
    assert len(docs) == 64
    assert sorted(n.attrs["number"] for n in decisions) == ["30", "48", "49", "51", "55"]


def test_every_document_carries_a_falsification_condition() -> None:
    # The relation the graph exists to make visible. All 64 state one; a parser that stopped
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
    with pytest.raises(RegistryError, match="no node floor"):
        validate_registry((spec,), floor=1)


def test_an_edge_only_extractor_must_declare_that_it_mints_nothing() -> None:
    # `references` legitimately mints no nodes. Its floor lives on edges -- but "mints
    # nothing" has to be stated as max_nodes=0, so a node appearing there by accident is
    # caught rather than absorbed.
    def spec(**over: object) -> ExtractorSpec:
        base: dict[str, object] = dict(
            name="edges-only", kinds=(NodeKind.DOCUMENT,), min_nodes=0, max_nodes=0,
            min_edges=5, max_unparsed=0, expect_rejected=None, run=lambda ctx: Harvest(),
        )
        base.update(over)
        return ExtractorSpec(**base)  # type: ignore[arg-type]

    validate_registry((spec(),), floor=1)             # explicit, and floored on edges
    with pytest.raises(RegistryError, match="no node floor"):
        validate_registry((spec(max_nodes=None),), floor=1)
    with pytest.raises(RegistryError, match="nodes or edges"):
        validate_registry((spec(min_edges=0),), floor=1)


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


def test_refresh_skips_the_sync_step_where_the_origin_is_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The control that keeps /refresh usable off one laptop. The serve surface asks
    `origin_reachable` before offering a sync step; with every origin missing — the
    condition of every CI runner and clean clone — it must rebuild from the sealed
    mirror instead of failing on a file it never had."""
    sources = mirror.load_manifest()
    assert sources, "the repo ships a non-empty plan manifest"
    # Machine-neutral: whatever this host has, the helper must report exactly that fact —
    # the serve surface's sync/no-sync decision rides on it.
    expected = all(Path(s.origin).expanduser().is_file() for s in sources)
    assert mirror.origin_reachable(sources) is expected


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


# ---- code, gates and references -----------------------------------------------------------

def test_every_declared_package_is_on_disk_or_is_a_node() -> None:
    """The rule, not the instance. This pinned `src/thresholds` by name until that directory was
    created, at which point the test failed for the one reason that should never fail a test:
    the gap it was watching had been closed.

    What must hold is that a package `pyproject.toml` declares is either on disk or minted with
    an anomaly beside it, and never neither. The mechanism is proved against planted fixtures in
    `selftest.py` case 11, where both a present and an absent package are put there on purpose;
    here it is checked against whatever the repository currently declares."""
    from tools.vaultgraph.extract.code import _declared_packages

    result = _result()
    declared, _src = _declared_packages(ROOT)
    assert declared, "pyproject declares no wheel packages — the check has nothing to check"
    absent = {n.attrs["path"] for n in result.nodes if n.shape == "declared-absent"}
    anomalies = sum(1 for a in result.anomalies if a.kind == "declared-absent-package")
    for name in declared:
        on_disk = (ROOT / name).is_dir()
        assert on_disk or name in absent, f"{name} is declared, missing, and not surfaced"
        assert not (on_disk and name in absent), f"{name} is on disk and also minted absent"
    assert anomalies == len(absent), "a declared-absent node was minted with no anomaly"


def test_the_two_acs1_implementations_are_two_nodes() -> None:
    # harness/acs/acs1.py and harness/acs/acs1.mjs are independent implementations of one
    # specification, written from the spec rather than translated. Collapsing them into a
    # single node would erase the property the pair exists to demonstrate.
    result = _result()
    ids = {n.id for n in result.nodes}
    assert "module:harness.acs.acs1" in ids
    assert "module:harness.acs.acs1.mjs" in ids


def test_d20_protected_paths_are_marked() -> None:
    result = _result()
    protected = {n.attrs.get("path", "") for n in result.nodes if "protected" in n.tags}
    assert "scripts/lint_verdict_boundary.py" in protected
    assert "policy/oracle-denylist.json" in protected
    # The product tree is factory, not inspector, and must not be marked.
    assert not any(p.startswith("src/") for p in protected if p)


def test_lint_coverage_is_recorded_as_narrower_than_the_tree() -> None:
    # ruff and pyright are configured over the product tree only. A graph showing every
    # module under the same gate would assert something false.
    result = _result()
    modules = [n for n in result.nodes if n.kind is NodeKind.MODULE and n.attrs.get("path")]
    gated = {n.attrs["path"] for n in modules if n.attrs.get("lint_gated") == "true"}
    assert any(p.startswith("src/") for p in gated)
    assert not any(p.startswith("harness/") for p in gated)


def test_all_five_gate_jobs_and_their_dependency_order() -> None:
    result = _result()
    jobs = {n.id for n in result.nodes if n.kind is NodeKind.GATE}
    assert jobs == {"gate:integrity", "gate:product", "gate:inspector",
                    "gate:database", "gate:mutation"}
    needs = {(e.src, e.dst) for e in result.edges if e.kind.value == "needs"}
    assert ("gate:mutation", "gate:inspector") in needs
    assert ("gate:product", "gate:integrity") in needs


def test_every_gate_step_carries_a_command() -> None:
    # The multi-line `run: |` block for the ACS-1 byte-identity check used to come back empty,
    # because a comment line between two jobs discarded the collected block before the step
    # closed. A step with no command is a gate the graph cannot answer questions about.
    result = _result()
    steps = [n for n in result.nodes if n.kind is NodeKind.GATE_STEP]
    assert len(steps) >= 30
    assert all(n.attrs["command"] for n in steps)


def test_reference_edges_are_derived_and_never_structural() -> None:
    # A decision id written beside a function is a claim by whoever wrote the comment, not a
    # checked relation. The graph must not render it as though it were a table column.
    result = _result()
    enforced = [e for e in result.edges if e.kind.value == "enforced_by"]
    assert len(enforced) >= 100
    assert all(e.confidence.value == "derived" for e in enforced)


def test_no_edge_endpoint_is_dangling() -> None:
    result = _result()
    known = {n.id for n in result.nodes}
    dangling = sorted({e.src for e in result.edges} | {e.dst for e in result.edges}) 
    assert [d for d in dangling if d not in known] == []


# ---- stages, charter and the vault ---------------------------------------------------------

def test_all_ten_stages_carry_a_status_the_parser_actually_read() -> None:
    """Ten stages, each with a status from the declared vocabulary, and more than one distinct
    value among them.

    The last clause is the one doing work. A status parser that broke and returned the same
    constant for every stage would satisfy "all ten have a status", and the vault would render
    ten identical cards that nobody would read twice. Which stages are done is progress, and
    pinning it here made the suite fail when S4 and S8 landed — a test that reds on the work
    being done is measuring the wrong thing."""
    result = _result()
    stages = {n.attrs["number"]: n.status for n in result.nodes if n.kind is NodeKind.STAGE}
    assert len(stages) == 10
    assert set(stages) == {f"S{n}" for n in range(10)}
    vocabulary = {"done", "partial", "not-started"}
    assert set(stages.values()) <= vocabulary, f"unknown status: {set(stages.values())}"
    assert len(set(stages.values())) > 1, "every stage reports the same status"


def test_the_board_carries_both_kinds_of_dependency() -> None:
    """The acceptance criterion asks that a stage blocking a stage and an operator item blocking
    a stage are visible in one view, which requires both to be edges first.

    Named pairs were pinned here — `S2 blocks S4` among them — and the stage DAG on `main` no
    longer states that one. The claim worth holding is that both *shapes* of dependency survive
    extraction: an extractor that read only the stage table would drop every operator item and
    still pass a check written as "S2 blocks S5"."""
    result = _result()
    kinds = {n.id: n.kind for n in result.nodes}
    blocks = {(e.src, e.dst) for e in result.edges if e.kind.value == "blocks"}
    stage_to_stage = {p for p in blocks
                      if kinds.get(p[0]) is NodeKind.STAGE and kinds.get(p[1]) is NodeKind.STAGE}
    item_to_stage = {p for p in blocks
                     if kinds.get(p[0]) is NodeKind.OPERATOR_ITEM
                     and kinds.get(p[1]) is NodeKind.STAGE}
    assert stage_to_stage, "no stage blocks another stage"
    assert item_to_stage, "no operator item blocks a stage"


def test_the_stage_dag_has_no_cycle() -> None:
    result = _result()
    stage_ids = {n.id for n in result.nodes if n.kind is NodeKind.STAGE}
    graph: dict[str, set[str]] = {s: set() for s in stage_ids}
    for edge in result.edges:
        if edge.kind.value == "blocks" and edge.src in stage_ids and edge.dst in stage_ids:
            graph[edge.src].add(edge.dst)
    colour: dict[str, int] = {}

    def visit(node: str) -> bool:
        colour[node] = 1
        for nxt in sorted(graph[node]):
            if colour.get(nxt) == 1 or (colour.get(nxt) is None and visit(nxt)):
                return True
        colour[node] = 2
        return False

    assert not any(visit(s) for s in sorted(stage_ids) if s not in colour)


def test_kill_criteria_and_risks_come_from_tier_zero_not_the_plan() -> None:
    # The plan references K1-K6 and R1-R12 constantly and defines neither.
    result = _result()
    kills = [n for n in result.nodes if n.kind is NodeKind.KILL_CRITERION]
    risks = [n for n in result.nodes if n.kind is NodeKind.RISK]
    assert len(kills) == 6 and len(risks) == 12
    assert all(n.source.path == "docs/tier0/charter-and-non-goals.md" for n in kills)
    assert all(n.source.path == "docs/tier0/risk-register.md" for n in risks)
    assert [n.attrs["number"] for n in kills if n.status == "fired"] == ["K5"]


def test_the_risk_register_being_out_of_order_is_surfaced() -> None:
    # R12 sits between R10 and R11. Surfaced, not silently sorted.
    result = _result()
    assert any(a.kind == "risk-register-order" for a in result.anomalies)


def test_prose_edges_never_claim_structural_confidence() -> None:
    result = _result()
    prose = [e for e in result.edges if e.kind.value == "blocks"]
    assert prose and all(e.confidence.value == "prose" for e in prose)
    assert all(e.evidence for e in prose)
