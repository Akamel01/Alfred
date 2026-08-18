"""The restore drill and the independent re-walk, each with the control that matters.

**How this suite would be shown vacuous** (D57). The drill's comparisons all pass on a
restore that copied nothing, if the source was also empty — so the drill is seeded first
and `test_drill_restores_a_seeded_chain` asserts a non-trivial row count. The walker's
refusals would all pass against a walker that threw unconditionally, so
`test_walker_accepts_a_sound_chain` is what keeps the accepting path reachable.

The two tests that carry the weight:

- `test_walker_rejects_a_chain_the_python_encoder_signed_wrongly` is the whole argument for
  a second implementation. A tampered digest that Python would happily re-derive from its
  own encoder must fail in Node.
- `test_walker_rejects_a_restore_that_lost_the_anchored_head` is the only non-self-
  referential comparison in the drill. A truncated restore is internally perfect.
"""

from __future__ import annotations

import json
import subprocess
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psycopg
import pytest

from harness.db.cluster import ThrowawayCluster, throwaway_cluster
from harness.evidence.anchor import Anchor, AnchorError, derive, run_walker
from harness.evidence.export import export_chain
from harness.evidence.restore_drill import DrillError, run_drill
from harness.evidence.store import EvidenceStore

pytestmark = pytest.mark.db

ORG = uuid.UUID("018f0000-0000-7000-8000-0000000000a1")
PROJECT = uuid.UUID("018f0000-0000-7000-8000-0000000000a2")
RECORD_TYPE = "alfred.run.task_start.v1"


def _seed(cluster: ThrowawayCluster, chain: str, *, n: int) -> str:
    """Write `n` linked rows and return the head digest."""
    with psycopg.connect(cluster.url("alfred_harness")) as conn:
        store = EvidenceStore(conn)
        head = ""
        for index in range(n):
            head = store.append_run_record(
                chain_id=chain,
                org_id=ORG,
                project_id=PROJECT,
                task_id=uuid.uuid4(),
                record_type=RECORD_TYPE,
                body={"seq": index, "note": "seeded for the drill"},
                schema_version=1,
                emitted_at=datetime.now(UTC),
                monotonic_ns=1000 * index,
            ).sha256
        conn.commit()
    return head


def _export(cluster: ThrowawayCluster, chain: str, destination: Path) -> int:
    with psycopg.connect(cluster.url("alfred_harness")) as conn:
        return export_chain(conn, table="run_record", chain_id=chain, destination=destination)


def _chain_id(name: str) -> str:
    return f"{name}-{uuid.uuid4().hex[:8]}"


# ------------------------------------------------------------------- the JS walker


def test_walker_accepts_a_sound_chain(cluster: ThrowawayCluster, tmp_path: Path) -> None:
    """The control. Without it, every refusal below is met by a walker that always throws."""
    chain = _chain_id("sound")
    head = _seed(cluster, chain, n=5)
    export = tmp_path / "chain.json"
    assert _export(cluster, chain, export) == 5

    result = run_walker(export)
    assert result.length == 5
    assert head.startswith(result.head_sha256)


def test_walker_rejects_a_chain_the_python_encoder_signed_wrongly(
    cluster: ThrowawayCluster, tmp_path: Path
) -> None:
    """The argument for a second implementation, made against a real export.

    A row's `body_sha256` is altered in the exported file while its `sha256` is left
    alone — the shape a tamper takes when the toolchain that rewrote the row also
    recomputed nothing. Node must refuse it, and Node has never seen the Python encoder.
    """
    chain = _chain_id("tampered")
    _seed(cluster, chain, n=4)
    export = tmp_path / "chain.json"
    _export(cluster, chain, export)

    payload = json.loads(export.read_text(encoding="utf-8"))
    payload["rows"][2]["body_sha256"] = "0" * 64
    export.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(AnchorError, match="recomputes to"):
        run_walker(export)


def test_walker_rejects_a_second_genesis(cluster: ThrowawayCluster, tmp_path: Path) -> None:
    """Totality, at the position a plain unique index does not cover."""
    chain = _chain_id("twogenesis")
    _seed(cluster, chain, n=3)
    export = tmp_path / "chain.json"
    _export(cluster, chain, export)

    payload = json.loads(export.read_text(encoding="utf-8"))
    orphan = dict(payload["rows"][0])
    orphan["id"] = str(uuid.uuid4())
    payload["rows"].append(orphan)
    export.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(AnchorError, match="duplicate digest|branches"):
        run_walker(export)


def test_walker_rejects_an_island(cluster: ThrowawayCluster, tmp_path: Path) -> None:
    """A row removed from the middle leaves a tail whose every link recomputes."""
    chain = _chain_id("island")
    _seed(cluster, chain, n=5)
    export = tmp_path / "chain.json"
    _export(cluster, chain, export)

    payload = json.loads(export.read_text(encoding="utf-8"))
    by_prev = {row["prev_sha256"]: row for row in payload["rows"]}
    middle = by_prev[by_prev[None]["sha256"]]
    payload["rows"] = [row for row in payload["rows"] if row["id"] != middle["id"]]
    export.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(AnchorError, match="do not form one path"):
        run_walker(export)


def test_walker_rejects_an_empty_export(tmp_path: Path) -> None:
    """A walker handed zero rows reports what a walker that found nothing wrong reports."""
    export = tmp_path / "empty.json"
    export.write_text(
        json.dumps({"table": "run_record", "chain_id": "x", "rows": []}), encoding="utf-8"
    )
    with pytest.raises(AnchorError, match="zero rows"):
        run_walker(export)


def test_walker_rejects_a_restore_that_lost_the_anchored_head(
    cluster: ThrowawayCluster, tmp_path: Path
) -> None:
    """The only comparison that is not self-referential.

    The export is truncated to its first three rows. Every remaining link recomputes, the
    walk is total over what is present, and the chain is internally perfect — which is
    exactly what a competent attacker would arrange. Only the anchor notices.
    """
    chain = _chain_id("truncated")
    head = _seed(cluster, chain, n=6)
    export = tmp_path / "chain.json"
    _export(cluster, chain, export)
    anchor = derive(export, full_head=head)

    payload = json.loads(export.read_text(encoding="utf-8"))
    order: list[dict[str, Any]] = []
    by_prev = {row["prev_sha256"]: row for row in payload["rows"]}
    cursor = by_prev.get(None)
    while cursor is not None:
        order.append(cursor)
        cursor = by_prev.get(cursor["sha256"])
    payload["rows"] = order[:3]
    export.write_text(json.dumps(payload), encoding="utf-8")

    anchor_path = tmp_path / "anchor.json"
    anchor_path.write_text(anchor.to_json(), encoding="utf-8")

    # The control first: without the anchor the truncated chain is accepted.
    assert run_walker(export).length == 3
    with pytest.raises(AnchorError, match="not reachable"):
        run_walker(export, anchor_path)


def test_anchor_refuses_a_head_the_walker_disagrees_with(
    cluster: ThrowawayCluster, tmp_path: Path
) -> None:
    chain = _chain_id("disagree")
    _seed(cluster, chain, n=3)
    export = tmp_path / "chain.json"
    _export(cluster, chain, export)
    with pytest.raises(AnchorError, match="disagrees"):
        derive(export, full_head="f" * 64)


# ------------------------------------------------------------------------ the drill


def test_drill_refuses_to_restore_into_its_source(cluster: ThrowawayCluster, tmp_path: Path) -> None:
    """A drill whose failure mode is the incident is not a drill."""
    with pytest.raises(DrillError, match="refusing"):
        run_drill(
            source=cluster,
            target=cluster,
            table="run_record",
            chain_id="x",
            anchor=Anchor("run_record", "x", "0" * 64, 0, "now"),
            workspace=tmp_path,
        )


# Deliberately unmarked. A `slow` marker here would be a switch for turning the only
# end-to-end restore check off, and the drill costs one extra throwaway cluster — about
# fifteen seconds against a gate whose absence is unrecoverable data loss.
def test_drill_restores_a_seeded_chain(cluster: ThrowawayCluster, tmp_path: Path) -> None:
    """D-synthetic end to end: dump, restore into a second cluster, compare four ways.

    Two findings are *expected* and asserted for rather than tolerated — no artifact rows
    exist yet, and no Tier 0 recovery objective is stated. Both are recorded as findings
    rather than skipped, because an unexercised check reports what a clean check reports.
    """
    chain = _chain_id("drill")
    head = _seed(cluster, chain, n=8)
    export = tmp_path / "source-chain.json"
    _export(cluster, chain, export)
    anchor = derive(export, full_head=head)

    with throwaway_cluster() as target:
        report = run_drill(
            source=cluster,
            target=target,
            table="run_record",
            chain_id=chain,
            anchor=anchor,
            workspace=tmp_path,
        )

    assert report.walk_length == 8
    assert report.walk_anchor_state == "equal"
    assert report.row_counts["run_record"][0] == report.row_counts["run_record"][1]
    assert report.row_counts["run_record"][1] >= 8
    assert all(report.key_sets_equal.values())

    expected = {"artifact resolution was not exercised", "recovery objective"}
    for fragment in expected:
        assert any(fragment in finding for finding in report.findings), report.findings
    assert len(report.findings) == len(expected), report.findings


def test_node_is_available() -> None:
    """The walker needs stock Node and nothing else. If it is missing, say so loudly.

    A drill that silently degrades to a Python re-walk when Node is absent is a drill that
    checks the encoder against itself on exactly the machines nobody looked at.
    """
    completed = subprocess.run(["node", "--version"], capture_output=True, text=True, check=False)
    assert completed.returncode == 0, "node is required for the independent chain re-walk"
