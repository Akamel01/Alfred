"""The harness's verdict vocabulary: the words, the stamp bridge table, one home.

`pass`, `fail`, `indeterminate` — failure-semantics' three-valued vocabulary — used to be
spelled out in four places across `harness/`: the criterion runner declared a `Literal`,
the evidence store carried a dead frozenset beside a database CHECK constraint that is the
real authority, this module's predecessor held the bridge table, and the worker port kept a
negative filter. Four spellings meant four places to drift; this module is now the only
one that names them.

**It lives here, outside the product tree, for one hard reason:** D16/D39 forbid any module
under `src/` from returning the verdict vocabulary, and `scripts/lint_verdict_boundary.py`
enforces it. The stamp verifier therefore returns its own words and `verdict_for` supplies
the mapping onto these.

**It imports nothing from `src`.** The dependency direction in this repository is
`src → harness` — `provenance.encoding` imports the ACS-1 encoder, and `pyproject.toml`
puts `harness` on the path for exactly that. An import the other way would close a cycle.
What keeps the two sides honest instead is a bridge test in `tests/` (which may import
both) asserting that the table's key set equals `StampVerification`'s value set **in both
directions**: a member added there and not here fails, and a key here naming nothing there
fails too.

**The bridge table is written out rather than derived.** A derived mapping — "anything
starting UNVERIFIABLE is indeterminate" — would silently classify a future arm nobody
thought about.

**Binding tests travel with this module** (`test_verdicts.py`): the migration's CHECK
constraint text must equal `VERDICTS`, and the worker contract's forbidden field-name list
must equal `harness.worker.port.VERDICT_VOCABULARY`. A word added anywhere without its
authority fails here first.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Final, Literal

__all__ = [
    "VERDICTS",
    "Verdict",
    "VERDICT_FOR_VERIFICATION",
    "UnmappedVerification",
    "verdict_for",
]

# Failure-semantics' three-valued vocabulary, quoted here as data. `indeterminate` is
# excluded from merge rate on both sides; it is not a capability signal.
VERDICTS: Final[frozenset[str]] = frozenset({"pass", "fail", "indeterminate"})

type Verdict = Literal["pass", "fail", "indeterminate"]

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


def verdict_for(verification_name: str) -> Verdict:
    """The verdict for one verification outcome, by name.

    Raises rather than defaulting. A default here would be a silent policy: the safe-looking
    choice (`indeterminate`) removes the row from the merge-rate denominator on both sides,
    which is how a misclassification stops being counted anywhere.
    """
    try:
        return VERDICT_FOR_VERIFICATION[verification_name]  # type: ignore[no-any-return]
    except KeyError as exc:
        raise UnmappedVerification(
            f"{verification_name!r} has no row in ADR-0006's verdict table; "
            f"known: {sorted(VERDICT_FOR_VERIFICATION)}"
        ) from exc
