"""The two assertion-outcome enums are bound, though deliberately separate.

`harness/containment/assertions.AssertionOutcome` (what a probe concluded) and
`harness.worker.port.AssertionOutcome` (what travels on `SandboxHandle`) are two
vocabularies on purpose — the port's type carries where a claim ran and what it observed,
and `handle.py` exists to cross between them losslessly. But their *members* must stay
identical: handle.py's mapping is written out member-by-member precisely so that the first
divergence is loud. That divergence used to be guarded only by an unreachable-at-runtime
branch; this test makes it loud at commit time instead.

If you add a member: decide whether it belongs on both sides, extend both and the mapping
in `handle.py`, and this test passes again.
"""

from __future__ import annotations

import pytest

from harness.containment.assertions import AssertionOutcome as ProbeOutcome
from harness.worker.port import AssertionOutcome as PortOutcome


def test_the_two_outcome_enums_have_identical_members() -> None:
    assert {m.name for m in ProbeOutcome} == {m.name for m in PortOutcome}


@pytest.mark.parametrize("probe_member", list(ProbeOutcome))
def test_every_probe_member_has_the_same_value_on_both_sides(probe_member: ProbeOutcome) -> None:
    port_member = PortOutcome[probe_member.name]
    assert port_member.value == probe_member.value
