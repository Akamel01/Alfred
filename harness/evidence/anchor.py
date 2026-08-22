"""The chain head, recorded off-machine, and derived by the implementation that is not Python.

D43 anchors the chain head off-machine daily. The anchor is the **only comparison in the
restore drill that is not self-referential**: without it a drill proves the dump is
internally consistent, which a competent attacker would also arrange. Its authority comes
from having been written at a time before any compromise and from living somewhere the
live machine cannot reach — not from anything about how it is computed.

**It is nonetheless computed by the JavaScript walker rather than by Python.** If Python
derived the head, an encoder defect would produce a wrong anchor and a later restore
would agree with it perfectly. Deriving it from the independent implementation means the
anchor and the check that consults it were produced by the same non-Python reading, which
is the reading the product's claim rests on.

**Anchor retention bounds what this can prove.** A compromise predating every anchor in
retention is invisible to this mechanism, and no amount of chaining changes that. The
anchor bounds tamper-detection to the anchor's own retention window and no further.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

WALKER: Final = Path(__file__).resolve().parent / "verify_chain.mjs"
ANCHOR_FORMAT_VERSION: Final = 1

# The walker's stdout protocol (ADR-0014: JSONL is transport, not derivation — the
# re-walk stays an implementation that did not write the chain). One JSON object per
# line; every field name is fixed here so a walker that drifts fails this parser instead
# of being reinterpreted by it.
EVENT_FIELDS: Final[frozenset[str]] = frozenset({"walk", "head", "anchor", "error"})
EVENT_KEYS: Final[dict[str, frozenset[str]]] = {
    "walk": frozenset({"table", "chain_id", "rows"}),
    "head": frozenset({"sha"}),
    "anchor": frozenset({"state"}),
    "error": frozenset({"message"}),
}
ANCHOR_STATES: Final[frozenset[str]] = frozenset(
    {"absent", "equal", "reachable-and-extended"}
)


class AnchorError(RuntimeError):
    """The anchor could not be derived or verified. Fail closed."""


@dataclass(frozen=True)
class Anchor:
    table: str
    chain_id: str
    head_sha256: str
    length: int
    anchored_at: str

    def to_json(self) -> str:
        return json.dumps(
            {
                "anchor_format_version": ANCHOR_FORMAT_VERSION,
                "table": self.table,
                "chain_id": self.chain_id,
                "head_sha256": self.head_sha256,
                "length": self.length,
                "anchored_at": self.anchored_at,
            },
            indent=2,
            sort_keys=True,
        )


@dataclass(frozen=True)
class WalkResult:
    length: int
    head_sha256: str
    anchor_state: str


def _parse_verdict(stdout: str) -> WalkResult:
    """Dispatch the walker's JSONL verdict, refusing anything unrecognized.

    Fail closed by construction: a line that is not JSON, not an object, of an unknown
    type, carrying unexpected fields, repeated, or missing entirely is an `AnchorError`,
    never an ignored line — a verdict assembled from partial output would be a verdict
    the walker never issued. The head arrives truncated to 16 characters because
    `derive` checks the caller's full digest against it.
    """
    seen: dict[str, dict[str, object]] = {}
    for raw in stdout.splitlines():
        if not raw.strip():
            continue
        try:
            event = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise AnchorError(f"walker line is not JSON: {raw!r}") from exc
        if not isinstance(event, dict):
            raise AnchorError(f"walker line is not an event object: {raw!r}")
        kind = event.get("type")
        if not isinstance(kind, str) or kind not in EVENT_FIELDS:
            raise AnchorError(f"walker emitted an unrecognized event: {raw!r}")
        if set(event) - {"type"} != set(EVENT_KEYS[kind]):
            raise AnchorError(f"walker event {kind!r} has unexpected fields: {raw!r}")
        if kind in seen:
            raise AnchorError(f"walker repeated its {kind!r} event: {raw!r}")
        seen[kind] = event

    if "error" in seen:
        message = seen["error"]["message"]
        raise AnchorError(f"walker refused the chain: {message}")

    missing = (EVENT_FIELDS - {"error"}) - seen.keys()
    if missing:
        raise AnchorError(
            f"walker verdict incomplete; no {sorted(missing)} event in {stdout.strip()!r}"
        )

    walk_event = seen["walk"]
    rows = walk_event["rows"]
    if not isinstance(rows, int) or isinstance(rows, bool):
        raise AnchorError(f"walker 'rows' is not an integer: {walk_event['rows']!r}")
    for kind, field in (("walk", "table"), ("walk", "chain_id"), ("head", "sha")):
        if not isinstance(seen[kind][field], str):
            raise AnchorError(f"walker {kind}.{field} is not a string: {seen[kind][field]!r}")
    state = seen["anchor"]["state"]
    if not isinstance(state, str) or state not in ANCHOR_STATES:
        raise AnchorError(f"walker anchor state is not recognized: {state!r}")

    return WalkResult(
        length=rows,
        head_sha256=str(seen["head"]["sha"]),
        anchor_state=state,
    )


def run_walker(export_path: Path, anchor_path: Path | None = None) -> WalkResult:
    """Run the JavaScript re-walk and parse its typed verdict.

    Shelling out to `node` rather than reimplementing the walk in Python is the entire
    point. A Python re-walk of a Python-written chain checks the chain against the encoder
    that produced it, which is not a check. The walker reports one JSON event per line on
    stdout; a nonzero exit is a refusal regardless of what stdout carries.
    """
    argv = ["node", str(WALKER), str(export_path)]
    if anchor_path is not None:
        argv.append(str(anchor_path))
    try:
        completed = subprocess.run(argv, capture_output=True, text=True, timeout=300, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AnchorError(f"could not run the JavaScript walker: {exc}") from exc

    if completed.returncode != 0:
        raise AnchorError(
            f"chain re-walk failed: {(completed.stderr or completed.stdout).strip()}"
        )
    return _parse_verdict(completed.stdout)


def derive(export_path: Path, *, full_head: str) -> Anchor:
    """Build an anchor from a fresh export, with the walker as the authority on the walk.

    `full_head` is supplied by the caller because the walker prints a truncated prefix for
    readability; the anchor must carry the whole digest, and a truncated anchor is a
    weaker claim that nothing would notice. The walker still decides the *length* and
    whether the chain walks at all, and the caller's head is required to agree with the
    prefix the walker printed.
    """
    exported = json.loads(export_path.read_text(encoding="utf-8"))
    result = run_walker(export_path)
    if not full_head.startswith(result.head_sha256):
        raise AnchorError(
            f"caller's head {full_head} disagrees with the walker's {result.head_sha256}"
        )
    return Anchor(
        table=str(exported["table"]),
        chain_id=str(exported["chain_id"]),
        head_sha256=full_head,
        length=result.length,
        anchored_at=datetime.now(UTC).isoformat(),
    )
