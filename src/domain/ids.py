"""Typed, sortable identifiers (cross-stage invariant I4).

UUIDv7 (RFC 9562): 48-bit big-endian Unix millisecond timestamp, then version and
variant bits, then randomness. Sortable by creation time, which is what makes it
usable as a Postgres primary key without a separate ordering column.

Distinct `NewType` per entity so `pyright --strict` refuses a `ScenarioId` where a
`TrackId` belongs. The runtime representation is one `uuid.UUID` for all of them;
the separation is entirely static, which is exactly where ID-confusion bugs are
cheap to prevent and expensive to find.
"""

from __future__ import annotations

import os
import time
from typing import NewType
from uuid import UUID

__all__ = [
    "ArtifactId",
    "EvidenceId",
    "RunId",
    "ScenarioId",
    "StampId",
    "TrackId",
    "uuid7",
]

ScenarioId = NewType("ScenarioId", UUID)
TrackId = NewType("TrackId", UUID)
RunId = NewType("RunId", UUID)
StampId = NewType("StampId", UUID)
EvidenceId = NewType("EvidenceId", UUID)
ArtifactId = NewType("ArtifactId", UUID)


def uuid7(*, timestamp_ms: int | None = None, random_bytes: bytes | None = None) -> UUID:
    """A UUIDv7.

    Both sources of non-determinism are injectable so a replayed run can pin them.
    Reproducibility is the product: an ID generator that can only read the wall
    clock puts a non-replayable value into every record it stamps.
    """
    ms = time.time_ns() // 1_000_000 if timestamp_ms is None else timestamp_ms
    if not 0 <= ms < 2**48:
        raise ValueError(f"UUIDv7 timestamp out of the 48-bit range: {ms}")
    rand = os.urandom(10) if random_bytes is None else random_bytes
    if len(rand) != 10:
        raise ValueError(f"UUIDv7 needs exactly 10 random bytes, got {len(rand)}")

    raw = bytearray(ms.to_bytes(6, "big") + rand)
    raw[6] = (raw[6] & 0x0F) | 0x70  # version 7
    raw[8] = (raw[8] & 0x3F) | 0x80  # RFC 9562 variant
    return UUID(bytes=bytes(raw))


def uuid7_timestamp_ms(value: UUID) -> int:
    """The embedded millisecond timestamp. Raises if `value` is not a v7."""
    if value.version != 7:
        raise ValueError(f"not a UUIDv7: version {value.version}")
    return int.from_bytes(value.bytes[:6], "big")
