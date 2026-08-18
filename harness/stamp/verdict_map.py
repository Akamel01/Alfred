"""ADR-0006's verdict table, as data rather than as prose.

The table maps what a stamp verifier concluded onto Alfred's three-valued failure
semantics. It lives here, outside the product tree, for one hard reason: D16/D39 forbid any
module under `src/` from returning the verdict vocabulary, and
`scripts/lint_verdict_boundary.py` enforces it. The verifier therefore returns its own
words and this file supplies the mapping.

**It names the vocabulary by string and imports nothing from `src`.** The dependency
direction in this repository is `src → harness` — `provenance.encoding` imports the ACS-1
encoder, and `pyproject.toml` puts `harness` on the path for exactly that. An import the
other way would close a cycle. What keeps the two sides honest instead is a bridge test in
`tests/` (which may import both) asserting that this table's key set equals
`StampVerification`'s value set **in both directions**: a member added there and not here
fails, and a key here naming nothing there fails too.

The table is written out rather than derived. A derived mapping — "anything starting
UNVERIFIABLE is indeterminate" — would silently classify a future arm nobody thought about.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Final

__all__ = ["VERDICT_WORDS", "VERDICT_FOR_VERIFICATION", "verdict_for"]

# Failure-semantics' three-valued vocabulary, quoted here as data. `indeterminate` is
# excluded from merge rate on both sides; it is not a capability signal.
VERDICT_WORDS: Final[frozenset[str]] = frozenset({"pass", "fail", "indeterminate"})

VERDICT_FOR_VERIFICATION: Final[MappingProxyType[str, str]] = MappingProxyType(
    {
        # Version known and implemented, digest matches.
        "VERIFIED": "pass",
        # Version known and implemented, digest differs. The only row that says tampering.
        "MISMATCH": "fail",
        # Above the verifier's highest known version. *Upgrade your verifier* — never
        # `fail`, because reporting "I cannot check this" as "this failed the check" is an
        # incident-grade misreport and the default behaviour of every naive hash comparison.
        "UNVERIFIABLE_SCHEMA_TOO_NEW": "indeterminate",
        # At or below the highest known, but not implemented. Should be unreachable while
        # retirement is forbidden; mapped so that reaching it is loud rather than a KeyError.
        "UNVERIFIABLE_SCHEMA_RETIRED": "indeterminate",
        # No locatable `stamp_schema_version`, or the document does not fit the version it
        # claims. Not an old stamp — there are none — so `fail`, never `indeterminate`.
        "INVALID": "fail",
    }
)


class UnmappedVerification(KeyError):
    """A verification outcome with no row. Never defaulted."""


def verdict_for(verification_name: str) -> str:
    """The verdict for one verification outcome, by name.

    Raises rather than defaulting. A default here would be a silent policy: the safe-looking
    choice (`indeterminate`) removes the row from the merge-rate denominator on both sides,
    which is how a misclassification stops being counted anywhere.
    """
    try:
        return VERDICT_FOR_VERIFICATION[verification_name]
    except KeyError as exc:
        raise UnmappedVerification(
            f"{verification_name!r} has no row in ADR-0006's verdict table; "
            f"known: {sorted(VERDICT_FOR_VERIFICATION)}"
        ) from exc
