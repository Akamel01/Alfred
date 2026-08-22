"""The verdict vocabulary's bindings: every other spelling answers to this module.

Three facts each had a second copy somewhere; the copies are what these tests bind:

1. **The database CHECK constraint** (`migrations/harness/evidence/versions/0001_evidence_base.py`,
   `ck_verdict_vocabulary`) is the runtime authority on what a verdict may be — the store
   deliberately refuses to re-validate in Python. Its word set must equal `VERDICTS`.
2. **The worker contract's forbidden field names** (`docs/tier1/worker-port-contract.md`,
   "Verdict-shaped fields") are restated as data in `harness/worker/port.py`. The doc is
   the authority; the port's frozenset must equal it.
3. **The two assertion-outcome enums** (containment probes vs the worker port) are
   deliberately separate vocabularies — see `harness/containment/handle.py` for why both
   exist — but must keep identical members. That binding lives beside handle.py in
   `test_outcome_binding.py`, not here.

A word added to any authority without updating its copy fails here, and vice versa.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import cast

import pytest

from harness.verdicts import (
    VERDICTS,
    VERDICT_FOR_VERIFICATION,
    UnmappedVerification,
    Verdict,
    verdict_for,
)

_ROOT = Path(__file__).resolve().parents[2]

# The five rows ADR-0006 specifies, restated here rather than read from the module under
# test. A test that derives its expectation from its subject asserts nothing.
EXPECTED: dict[str, str] = {
    "VERIFIED": "pass",
    "MISMATCH": "fail",
    "UNVERIFIABLE_SCHEMA_TOO_NEW": "indeterminate",
    "UNVERIFIABLE_SCHEMA_RETIRED": "indeterminate",
    "INVALID": "fail",
}


@pytest.mark.parametrize(("name", "verdict"), sorted(EXPECTED.items()))
def test_each_adr_0006_row(name: str, verdict: str) -> None:
    assert verdict_for(name) == verdict


def test_every_verdict_is_in_the_three_valued_vocabulary() -> None:
    assert set(VERDICT_FOR_VERIFICATION.values()) <= VERDICTS


def test_an_unmapped_name_raises_rather_than_defaulting() -> None:
    with pytest.raises(UnmappedVerification):
        verdict_for("UNVERIFIABLE_SCHEMA_SIDEWAYS")


def test_verdict_words_are_exactly_three() -> None:
    """Vacuity control for the bindings below: if VERDICTS itself drifts, they burn."""
    assert VERDICTS == {"pass", "fail", "indeterminate"}


def test_the_database_check_constraint_names_exactly_the_vocabulary() -> None:
    """The store does not validate in Python on purpose: the CHECK constraint is the
    authority ("the database is the one that is still true after a code change"). This
    binding keeps the migration's word list and this module from drifting apart."""
    text = (_ROOT / "migrations/harness/evidence/versions/0001_evidence_base.py").read_text()
    match = re.search(r'"verdict IN \(([^)]*)\)"', text)
    assert match, "ck_verdict_vocabulary not found in the evidence base migration"
    words = {w.strip().strip("'\"") for w in match.group(1).split(",")}
    assert words == VERDICTS


def test_the_worker_contract_field_names_match_the_ports_filter() -> None:
    """`worker-port-contract.md`'s forbidden-name list is the authority;
    `harness.worker.port.VERDICT_VOCABULARY` implements it. Neither may move alone."""
    from harness.worker.port import VERDICT_VOCABULARY

    doc = (_ROOT / "docs/tier1/worker-port-contract.md").read_text()
    section = re.search(
        r"## Verdict-shaped fields(.*?)(?=\n## |\Z)", doc, re.DOTALL
    )
    assert section, "'Verdict-shaped fields' section missing from the contract"
    names = set(re.findall(r"`([a-z_]+)`", cast("str", section.group(1))))
    assert names == set(VERDICT_VOCABULARY), (
        f"contract/doc mismatch: doc-only={sorted(names - set(VERDICT_VOCABULARY))} "
        f"code-only={sorted(set(VERDICT_VOCABULARY) - names)}"
    )


def test_the_type_is_the_frozenset_it_claims() -> None:
    """`Verdict` and `VERDICTS` are one vocabulary at two types. A static check would be
    nicer; this pins the runtime half of the claim."""
    verdicts: tuple[Verdict, ...] = ("pass", "fail", "indeterminate")
    assert set(verdicts) == VERDICTS
