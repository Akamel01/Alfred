"""D-synthetic: dump one cluster, restore into another, and check four ways.

**Two drills, and conflating them is the failure** (§6 of the harness self-test
specification). *D-synthetic* runs in CI on every change and proves the **mechanism**.
*D-production* restores the actual off-machine backup and proves the **artifact**; it
cannot run in CI, which has no access to the off-machine target. This module is
D-synthetic, and a green run here is not "restore verified" for Phase 0 exit.

**Never destroy the live cluster.** The drill restores into a *second* throwaway cluster
and touches the source only to read from it. A drill whose failure mode is the incident is
not a drill.

**Data-only, into a cluster whose schema came from the migrations.** Deliberate, and the
argument is not convenience: it separates "the schema is what the migrations say" from
"the rows are what the backup holds". A restore that brings its own schema can bring back
a *different* schema — an evidence table with a column dropped, or a check constraint
missing — and every row would land in it without complaint.

**Comparison three is done by JavaScript, not here.** The specification lists four
comparisons: row counts, primary-key set equality, per-row content hash against the stored
digest, and the full chain re-walk. The third recomputes a digest, so doing it in Python
would check the encoder that wrote it against itself. Both digest comparisons therefore
run in `verify_chain.mjs`, and this module does the two that are not digest claims.

**Wall-clock is recorded and the absence of a recovery objective is a finding.** No Tier 0
document states one as of 2026-08-17, so the drill reports the number and says the
objective is missing. It does not skip the check, and it does not invent a threshold.
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final

import psycopg

from harness.db.cluster import SUPERUSER, ThrowawayCluster
from harness.evidence.anchor import Anchor, run_walker
from harness.evidence.export import export_chain

EVIDENCE_TABLES: Final = ("run_record", "verdict", "operator_action", "artifact", "defect_escape")

# Stated nowhere in the register as of 2026-08-17. Recorded as absent rather than guessed:
# a threshold invented by the thing being measured is not an objective.
RECOVERY_OBJECTIVE_S: Final[float | None] = None


class DrillError(RuntimeError):
    """The drill could not be carried out. Never reported as a passing restore."""


@dataclass
class DrillReport:
    restore_wall_clock_s: float = 0.0
    row_counts: dict[str, tuple[int, int]] = field(default_factory=dict)
    key_sets_equal: dict[str, bool] = field(default_factory=dict)
    walk_length: int = 0
    walk_anchor_state: str = "absent"
    artifacts_checked: int = 0
    findings: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.findings


def _docker_exec(container: str, argv: list[str], *, password: str, stdin: str | None = None) -> str:
    completed = subprocess.run(
        ["docker", "exec", "-i", "-e", f"PGPASSWORD={password}", container, *argv],
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise DrillError(f"{' '.join(argv[:2])} failed: {completed.stderr.strip()[:600]}")
    return completed.stdout


def dump_evidence(source: ThrowawayCluster) -> str:
    """Data-only dump of the evidence schema. Reads the source; never writes to it."""
    return _docker_exec(
        source.container,
        [
            "pg_dump", "--data-only", "--schema=evidence", "--no-owner", "--no-privileges",
            "-U", SUPERUSER, "-d", source.dbname,
        ],
        password=source.superuser_password,
    )


def restore_evidence(target: ThrowawayCluster, dump: str) -> float:
    """Load the dump into a *different* cluster. Returns wall-clock seconds."""
    started = time.monotonic()
    _docker_exec(
        target.container,
        ["psql", "-v", "ON_ERROR_STOP=1", "-U", SUPERUSER, "-d", target.dbname],
        password=target.superuser_password,
        stdin=dump,
    )
    return time.monotonic() - started


def _counts_and_keys(conn: psycopg.Connection[Any]) -> dict[str, tuple[int, frozenset[str]]]:
    result: dict[str, tuple[int, frozenset[str]]] = {}
    with conn.cursor() as cur:
        for table in EVIDENCE_TABLES:
            # Identifier is a module constant, never input.
            cur.execute(f"SELECT id FROM evidence.{table}")
            keys = frozenset(str(row[0]) for row in cur.fetchall())
            result[table] = (len(keys), keys)
    return result


def run_drill(
    *,
    source: ThrowawayCluster,
    target: ThrowawayCluster,
    table: str,
    chain_id: str,
    anchor: Anchor,
    workspace: Path,
    artifact_root: Path | None = None,
) -> DrillReport:
    """Dump, restore, and compare. Returns a report; findings make it a failure."""
    if source.container == target.container:
        # The one line that must never be relaxed: a drill that restores over its own
        # source has a failure mode identical to the incident it is rehearsing for.
        raise DrillError("refusing to restore into the source cluster")

    report = DrillReport()
    dump = dump_evidence(source)
    report.restore_wall_clock_s = restore_evidence(target, dump)

    with (
        psycopg.connect(source.url(SUPERUSER)) as before,
        psycopg.connect(target.url(SUPERUSER)) as after,
    ):
        original = _counts_and_keys(before)
        restored = _counts_and_keys(after)

        # 1 — row counts. Catches truncation.
        for name in EVIDENCE_TABLES:
            report.row_counts[name] = (original[name][0], restored[name][0])
            if original[name][0] != restored[name][0]:
                report.findings.append(
                    f"{name}: {original[name][0]} rows before, {restored[name][0]} after"
                )

        # 2 — primary-key set equality. Catches a missing row masked by an extra one,
        # which equal counts do not notice.
        for name in EVIDENCE_TABLES:
            equal = original[name][1] == restored[name][1]
            report.key_sets_equal[name] = equal
            if not equal:
                missing = len(original[name][1] - restored[name][1])
                extra = len(restored[name][1] - original[name][1])
                report.findings.append(f"{name}: {missing} row(s) missing, {extra} extra")

        # 4 (and 3, which it subsumes) — the independent re-walk against the anchor.
        export_path = workspace / "restored-chain.json"
        anchor_path = workspace / "anchor.json"
        exported_rows = export_chain(after, table=table, chain_id=chain_id, destination=export_path)
        anchor_path.write_text(anchor.to_json(), encoding="utf-8")
        walk = run_walker(export_path, anchor_path)
        report.walk_length = walk.length
        report.walk_anchor_state = walk.anchor_state
        if walk.length != exported_rows:
            report.findings.append(
                f"walk visited {walk.length} of {exported_rows} exported rows"
            )

        # Artifact resolution. A restore bringing back rows and not artifacts leaves a
        # chain of references to nothing, and row counts do not notice.
        with after.cursor() as cur:
            cur.execute("SELECT content_sha256 FROM evidence.artifact")
            digests = [str(row[0]) for row in cur.fetchall()]

    if digests:
        if artifact_root is None:
            report.findings.append(
                f"{len(digests)} artifact row(s) restored with no artifact root to resolve against"
            )
        else:
            for digest in digests:
                if not (artifact_root / digest).is_file():
                    report.findings.append(f"artifact {digest} does not resolve to bytes")
                else:
                    report.artifacts_checked += 1
    else:
        # Not a pass. An unexercised check reports what a clean check reports, and this
        # one will stay unexercised until the artifact store exists.
        report.findings.append(
            "FINDING: no artifact rows in the restore, so artifact resolution was not exercised"
        )

    if RECOVERY_OBJECTIVE_S is None:
        report.findings.append(
            f"FINDING: restore took {report.restore_wall_clock_s:.2f}s and no Tier 0 "
            f"recovery objective exists to compare it against"
        )
    elif report.restore_wall_clock_s > RECOVERY_OBJECTIVE_S:
        report.findings.append(
            f"restore took {report.restore_wall_clock_s:.2f}s against an objective of "
            f"{RECOVERY_OBJECTIVE_S:.2f}s"
        )

    return report
