"""The global reason codebook (ADR-0001 consequences, ADR-0002).

One enum for the whole system. Codes enumerate *kinds of degeneracy*, not
metrics x kinds — a single `NO_CONFLICT_AREA` serves every conflict-point
measure — which is why `uint8` is enough and why growth is sublinear in the
number of metrics.

Two facts about the integer, both load-bearing:

* It is a **private in-memory encoding**. The wire format and the
  content-addressed hash carry the *name* (ADR-0002), so renumbering within a
  new codebook version is a code change and not a re-derivation of stored
  results.
* `0` means defined, permanently, and `255` is `UNKNOWN_CODE`. A reader that
  meets a code it does not know maps it to 255 and **never** to 0. Decoding an
  unrecognized reason as "defined" would reintroduce the plausible-wrong
  failure the whole representation exists to prevent, this time through the
  deserializer rather than through the metric.
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import IntEnum
from types import MappingProxyType
from typing import Final

from domain.errors import ContractViolation

__all__ = [
    "ALLOCATION_CEILING",
    "DEFINED_CODE",
    "FROZEN_CODEBOOK",
    "REASON_CODEBOOK_VERSION",
    "UNKNOWN_CODE",
    "CodebookError",
    "Reason",
    "allocated_reasons",
    "check_codebook",
    "decode_reason",
    "reason_from_name",
    "reason_name",
]


class Reason(IntEnum):
    """Global degeneracy codebook, version 1.

    Names are stable and never reused for a different meaning. Integers are
    stable within a codebook version.
    """

    DEFINED = 0

    # The seven the Edge Case and Degeneracy Specification's 30 rows reduce to.
    NO_CONFLICT_AREA = 1  # E7  — paths never intersect; no conflict point exists
    SINGLE_OCCUPANCY = 2  # E8  — only one agent ever enters the conflict area
    INSUFFICIENT_SAMPLES = 3  # E16/E17 — not enough samples for the derivative
    NO_RELATIVE_MOTION = 4  # E6  — measure requires motion; there is none
    NO_DATA = 5  # E23 — zero-length trajectory
    NO_COUNTERPART = 6  # E24 — pairwise measure, one agent in the scenario
    UPSTREAM_UNDEFINED = 7  # composition: an input was undefined

    UNKNOWN_CODE = 255


DEFINED_CODE: Final[int] = 0
UNKNOWN_CODE: Final[int] = 255

REASON_CODEBOOK_VERSION: Final[int] = 1

# The build fails here rather than at 254 (ADR-0002). A ceiling discovered at
# exhaustion is an emergency; a ceiling discovered at 80% is a scheduled decision
# with an ADR attached. It also fences off the mechanical hazard that numpy wraps
# uint8 arithmetic silently — 254 + 3 evaluates to 1 with no error — so a naive
# allocator cannot collide with a live code instead of failing.
ALLOCATION_CEILING: Final[int] = 200

# The frozen record of what has ever been allocated. `check_codebook` asserts the
# enum still agrees with it, which is the checkable form of "names are stable and
# never reused": renaming a member, renumbering one, or reusing a retired name all
# fail here rather than silently changing the meaning of a stored result.
FROZEN_CODEBOOK: Final[Mapping[str, int]] = MappingProxyType(
    {
        "DEFINED": 0,
        "NO_CONFLICT_AREA": 1,
        "SINGLE_OCCUPANCY": 2,
        "INSUFFICIENT_SAMPLES": 3,
        "NO_RELATIVE_MOTION": 4,
        "NO_DATA": 5,
        "NO_COUNTERPART": 6,
        "UPSTREAM_UNDEFINED": 7,
        "UNKNOWN_CODE": 255,
    }
)


class CodebookError(ContractViolation):
    """The codebook violates an ADR-0002 invariant. Fails the build, not a run."""


def allocated_reasons() -> Mapping[str, int]:
    """Name → integer for every member, including the two reserved ones."""
    return MappingProxyType({member.name: int(member.value) for member in Reason})


def _allocatable(codes: Mapping[str, int]) -> dict[str, int]:
    """The codes that count against the ceiling: everything but 0 and 255."""
    return {name: code for name, code in codes.items() if code not in (DEFINED_CODE, UNKNOWN_CODE)}


def check_codebook(
    codes: Mapping[str, int] | None = None,
    frozen: Mapping[str, int] | None = None,
) -> None:
    """Assert every ADR-0002 invariant. Raises `CodebookError` on the first breach.

    Both mappings are arguments so the guards are testable without waiting for the
    condition they guard against: a ceiling check that can only be exercised by
    actually allocating 200 codes, or a drift check that can only be exercised by
    committing a renumbering, is a guard nobody has ever run.
    """
    mapping = allocated_reasons() if codes is None else dict(codes)
    reference = FROZEN_CODEBOOK if frozen is None and codes is None else frozen

    if mapping.get("DEFINED") != DEFINED_CODE:
        raise CodebookError("DEFINED must be allocated to 0 in every codebook version")
    if mapping.get("UNKNOWN_CODE") != UNKNOWN_CODE:
        raise CodebookError("UNKNOWN_CODE must be allocated to 255 in every codebook version")

    seen: dict[int, str] = {}
    for name, code in mapping.items():
        if not 0 <= code <= 255:
            raise CodebookError(f"reason code {name}={code} does not fit uint8")
        if name != name.upper() or not name.replace("_", "").isalnum():
            raise CodebookError(f"reason name is not a stable upper-snake identifier: {name!r}")
        if code in seen:
            raise CodebookError(
                f"reason codes are not bijective: {seen[code]} and {name} both hold {code}"
            )
        seen[code] = name

    for name, code in _allocatable(mapping).items():
        if code in (DEFINED_CODE, UNKNOWN_CODE):  # pragma: no cover — excluded by _allocatable
            raise CodebookError(f"{name} allocates a reserved code")

    allocated = len(_allocatable(mapping))
    if allocated >= ALLOCATION_CEILING:
        raise CodebookError(
            f"{allocated} reason codes allocated; the ceiling is {ALLOCATION_CEILING} "
            f"of 254 usable. Widening to uint16 is a pure code change (ADR-0002) but "
            f"needs an ADR, not a merge."
        )

    if reference is not None and mapping != dict(reference):
        raise CodebookError(
            "the enum no longer matches FROZEN_CODEBOOK: a name or integer changed. "
            "Names are stable and never reused; integers are stable within a codebook "
            "version, so this needs a codebook version bump and an ADR."
        )


def decode_reason(code: int) -> Reason:
    """Decode a stored integer. Unrecognized codes become `UNKNOWN_CODE`, never `DEFINED`.

    This is the single most important line in the module. Every other choice in
    ADR-0001 is defeated if an unknown code decodes to 0.
    """
    if not 0 <= code <= 255:
        raise CodebookError(f"reason code {code} does not fit uint8")
    try:
        return Reason(code)
    except ValueError:
        return Reason.UNKNOWN_CODE


def reason_name(code: int) -> str:
    """The wire name for a stored integer. Unknown integers name themselves `UNKNOWN_CODE`."""
    return decode_reason(code).name


def reason_from_name(name: str) -> Reason:
    """Decode a wire name. An unrecognized name is `UNKNOWN_CODE`, symmetrically.

    A future version's name reaching an older reader is the same hazard as a
    future version's integer, and gets the same answer.
    """
    try:
        return Reason[name]
    except KeyError:
        return Reason.UNKNOWN_CODE
