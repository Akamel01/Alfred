"""What has been released, append-only. Rollback needs a past to roll back to.

A rollback is only meaningful against a recorded previous release. Without a ledger the
command has no target, and the failure mode is the dangerous one: "rollback succeeded"
when nothing was ever deployed, because there was nothing to disagree with.

Append-only for the same reason evidence is (D43): a deploy history that can be rewritten
cannot answer "what was serving when that number was computed", which is the question a
recall under D27 actually asks.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

Action = Literal["deploy", "rollback"]


class LedgerError(RuntimeError):
    """The ledger cannot answer the question asked of it."""


@dataclass(frozen=True)
class Entry:
    release_id: str
    image_ref: str
    source_digest: str
    action: Action
    # Seconds since the epoch, supplied by the caller rather than read here, so a test can
    # be deterministic without the ledger owning a clock.
    at: float


class Ledger:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, entry: Entry) -> None:
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(entry), sort_keys=True) + "\n")

    def entries(self) -> tuple[Entry, ...]:
        if not self.path.is_file():
            return ()
        out: list[Entry] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                out.append(Entry(**json.loads(line)))
        return tuple(out)

    def current(self) -> Entry | None:
        entries = self.entries()
        return entries[-1] if entries else None

    def rollback_target(self) -> Entry:
        """The release to return to: the last one that is not the one now serving.

        Scanned by `release_id` rather than by position, because a rollback is itself an
        entry — taking "the second to last row" would, after one rollback, name the
        release that was just rolled *away from* and oscillate between two versions
        forever while reporting success each time.
        """
        entries = self.entries()
        if not entries:
            raise LedgerError(
                "no release has ever been deployed; there is nothing to roll back to. "
                "Reported as a failure rather than a no-op: a rollback that succeeds "
                "against an empty history is the check passing with nothing to check."
            )
        serving = entries[-1].release_id
        for entry in reversed(entries[:-1]):
            if entry.release_id != serving:
                return entry
        raise LedgerError(
            f"every recorded release is {serving!r}; a rollback would deploy what is "
            "already serving and report success without changing anything"
        )
