"""The plan file lives outside the repo. This mirrors it in, and makes drift mechanical.

The plan carrying D1-D57, A1-A12, the phases, the ports and the invariants lives at
`~/.claude/plans/`. Reading it from there directly would make the vault unbuildable from a
clean clone and would make every plan-derived `source` pointer resolve to a path outside
version control -- which is the one acceptance criterion that path could not meet.

So it is mirrored. **Byte-verbatim, never transformed.** A structured extraction committed to
the repo would be a second authored artifact that drifts; a byte copy has nothing to keep in
sync by hand, only bytes to re-copy. What makes the copy self-maintaining is that nobody has
to remember it:

* `--sync-plan` re-copies and re-stamps. One command, no judgement.
* `--check` is location-aware. Where the origin is present and has drifted, it fails. Where
  the origin is absent -- CI, a clean clone, anyone else's machine -- it verifies the mirror
  against its own manifest and passes. **Absence is never a failure; drift always is.**
* The safety property does not come from the sync. It comes from the exact counts the
  plan-derived extractors pin: a sync that broke a shape fails the build with
  `plan_decisions: 55 nodes, expected 57`. The failure *is* the review trigger.

No timestamp in the manifest. A capture time is unverifiable metadata that would break the
manifest's own byte-determinism to record something nothing checks.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from .textio import ROOT

MIRROR_DIR = ROOT / "plan"
MANIFEST = MIRROR_DIR / "manifest.json"

#: Stored with `~` unexpanded so no home path enters the repository.
DEFAULT_ORIGIN = "~/.claude/plans/handoff-autonomous-software-engineering-fizzy-dahl.md"
MIRROR_NAME = "handoff-autonomous-software-engineering-fizzy-dahl.md"


@dataclass(frozen=True, slots=True)
class Source:
    id: str
    origin: str
    mirror: str
    sha256: str
    bytes: int
    lines: int


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _measure(raw: bytes) -> tuple[str, int, int]:
    """Hash the raw bytes, not normalized text. A hash of folded line endings would not
    detect the rewrite it exists to detect."""
    text = raw.decode("utf-8").replace("\r\n", "\n")
    return _digest(raw), len(raw), len(text.split("\n"))


def load_manifest() -> list[Source]:
    if not MANIFEST.exists():
        return []
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return [Source(**entry) for entry in payload["sources"]]


def dump_manifest(sources: list[Source]) -> str:
    payload = {
        "schema_version": 1,
        "sources": [
            {
                "id": s.id, "origin": s.origin, "mirror": s.mirror,
                "sha256": s.sha256, "bytes": s.bytes, "lines": s.lines,
            }
            for s in sorted(sources, key=lambda s: s.id)
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def origin_path(source: Source) -> Path:
    return Path(source.origin).expanduser()


def origin_reachable(sources: list[Source]) -> bool:
    """True when every declared origin exists on this machine.

    The serve surface's refresh asks this before offering a sync step: syncing copies
    FROM the live plan, so on any machine without it — every CI runner — there is
    nothing to copy and `sync` rightly refuses. Refusing to rebuild too would make
    refresh unusable off the operator's laptop; rebuilding from the committed mirror is
    exactly what "absence is never a failure" buys, because the manifest seal still
    guarantees the bytes being rebuilt from.
    """
    return all(origin_path(s).is_file() for s in sources)


def sync(origin: str = DEFAULT_ORIGIN, source_id: str = "handoff-plan") -> tuple[int, str]:
    """Copy the origin in verbatim and re-stamp the manifest. The only mode that writes."""
    live = Path(origin).expanduser()
    if not live.is_file():
        return 1, f"ERROR origin not found: {origin}"

    raw = live.read_bytes()
    sha, size, lines = _measure(raw)
    MIRROR_DIR.mkdir(exist_ok=True)
    (MIRROR_DIR / MIRROR_NAME).write_bytes(raw)

    others = [s for s in load_manifest() if s.id != source_id]
    entry = Source(
        id=source_id, origin=origin, mirror=f"plan/{MIRROR_NAME}",
        sha256=sha, bytes=size, lines=lines,
    )
    MANIFEST.write_text(dump_manifest([*others, entry]), encoding="utf-8", newline="\n")
    return 0, f"OK synced {source_id} ({lines} lines, {size} bytes, sha256 {sha[:12]})"


def check(*, require_origin: bool = False) -> tuple[int, list[str]]:
    """Integrity always; drift only where the origin is reachable."""
    messages: list[str] = []
    sources = load_manifest()
    if not sources:
        return 1, ["ERROR plan manifest is missing or empty — run --sync-plan"]

    failed = False
    for source in sources:
        mirrored = ROOT / source.mirror
        if not mirrored.is_file():
            messages.append(f"ERROR mirror missing: {source.mirror}")
            failed = True
            continue

        raw = mirrored.read_bytes()
        sha, size, lines = _measure(raw)
        if (sha, size, lines) != (source.sha256, source.bytes, source.lines):
            messages.append(
                f"ERROR {source.mirror} does not match its manifest — corrupted or hand-edited"
            )
            failed = True
            continue

        live = origin_path(source)
        if live.is_file():
            if _digest(live.read_bytes()) != source.sha256:
                messages.append(
                    f"ERROR {source.id}: the live plan has drifted from the mirror — run "
                    "--sync-plan, rebuild, and review the count deltas"
                )
                failed = True
            else:
                messages.append(f"OK {source.id} mirror matches the live origin")
        elif require_origin:
            messages.append(f"ERROR {source.id}: origin absent and --require-origin was given")
            failed = True
        else:
            messages.append(
                f"OK {source.id} mirror integrity verified "
                "(origin absent, as expected off the operator's machine)"
            )
    return (1 if failed else 0), messages


def graph_inputs() -> dict[str, str]:
    """What `graph.json` records about the sources it was built from.

    One function rather than one per caller: the CLI and the local surface both stamp this,
    and when they each built it their own way they disagreed — the server omitted the mirror
    path, so a graph served live differed from the committed one in a field neither had any
    reason to differ in.
    """
    sources = load_manifest()
    inputs = {f"{s.id}_sha256": s.sha256 for s in sources}
    inputs.update({f"{s.id}_mirror": s.mirror for s in sources})
    return inputs
