"""A UUIDv7 for the evidence plane, independent of `src/domain/ids.py` (I4, issue #80).

**Why this is not an import.** `harness/` is the protected inspector (D20): an agent may
edit `src/domain/`, and `src/domain/ids.py` is where the product's `uuid7()` lives.
Importing that function into `harness/evidence/store.py` — the module that mints every
evidence row's primary key — would put agent-writable code on a path a protected writer
executes. An agent could then weaken `uuid7()` (drop the version bits, widen the timestamp
window, make it deterministic) without touching a single file `policy/protected-paths.json`
names, which is the D20 collapse by another route: the boundary is supposed to be *what
executes*, not *which file changed*. `scripts/lint_verdict_boundary.py`'s R check already
forbids this in one direction — no verdict-writing module (`harness.evidence`,
`harness.criterion`) reaches the agent-writable tree — and this module keeps that true by
not needing the import at all.

**Why a second implementation is acceptable here and is not silent.** Two copies of a
26-line function can drift, and drift here is worse than most duplication because a
diverged generator would silently start producing keys the other side does not recognize
as sortable. Left as a comment, "these two agree" is exactly the kind of claim
`harness/fingerprint/factory.py`'s `d19_is_shared()` exists to stop being a comment, and
`harness/verdicts/__init__.py`'s bridge test is the precedent for where the check runs: not
inside either protected/agent-writable module, but in `tests/domain/test_ids.py`, the one
place that may import both trees for verification without either tree depending on the
other at runtime. A future change to either side that breaks agreement fails that test,
which is collected by the same product test job CI already runs — not a new job that could
be quietly skipped.

**What this buys and what it costs.** Bought: the fence stays exactly as strict as before —
no new edge in the import graph out of `harness.evidence` or `harness.oracle`. Cost: two
implementations of RFC 9562 UUIDv7 that must be kept in step by hand, and nothing but the
bridge test enforces that. Do not remove `tests/domain/test_ids.py` to make an unrelated
change pass; it is load-bearing in the same way `d19_is_shared()` is.

RFC 9562: 48-bit big-endian Unix millisecond timestamp, then a 4-bit version field set to
7, then 12 bits of randomness, then a 2-bit variant field set to `10`, then 62 more bits of
randomness. Sortable by creation time, which is the property `harness/evidence/store.py`'s
serial, single-writer chain and `harness/oracle/load.py`'s heldout loader are both built to
use.
"""

from __future__ import annotations

import os
import time
from uuid import UUID

__all__ = ["uuid7"]


def uuid7(*, timestamp_ms: int | None = None, random_bytes: bytes | None = None) -> UUID:
    """A UUIDv7. `timestamp_ms` and `random_bytes` are injectable for the bridge test in
    `tests/domain/test_ids.py` and for any future replay of a fixed evidence chain — both
    harness concerns, not product ones, which is one more reason this is not simply
    re-exported from `src`.
    """
    millis = time.time_ns() // 1_000_000 if timestamp_ms is None else timestamp_ms
    if not 0 <= millis < 2**48:
        raise ValueError(f"UUIDv7 timestamp out of the 48-bit range: {millis}")
    entropy = os.urandom(10) if random_bytes is None else random_bytes
    if len(entropy) != 10:
        raise ValueError(f"UUIDv7 needs exactly 10 random bytes, got {len(entropy)}")

    fields = bytearray(millis.to_bytes(6, byteorder="big") + entropy)
    fields[6] = (fields[6] & 0x0F) | 0x70  # version 7, high nibble of byte 6
    fields[8] = (fields[8] & 0x3F) | 0x80  # RFC 9562 variant, top two bits of byte 8
    return UUID(bytes=bytes(fields))
