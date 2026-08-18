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


def run_walker(export_path: Path, anchor_path: Path | None = None) -> WalkResult:
    """Run the JavaScript re-walk and parse its verdict.

    Shelling out to `node` rather than reimplementing the walk in Python is the entire
    point. A Python re-walk of a Python-written chain checks the chain against the encoder
    that produced it, which is not a check.
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

    line = completed.stdout.strip()
    # `OK <table>/<chain>: <n> rows, one path, head <prefix>, anchor <state>`
    try:
        rows = int(line.split(": ", 1)[1].split(" rows", 1)[0])
        head = line.split("head ", 1)[1].split(",", 1)[0].strip()
        state = line.rsplit("anchor ", 1)[1].strip()
    except (IndexError, ValueError) as exc:
        raise AnchorError(f"walker output not understood: {line!r}") from exc
    return WalkResult(length=rows, head_sha256=head, anchor_state=state)


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
