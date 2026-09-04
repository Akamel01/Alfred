"""Check A: a planted substitution must refuse to start, and its control must proceed.

The failure this file exists to catch is not a wrong hash. It is the check reporting green
because it never ran — which is what the tree looked like before this module landed:
`assert_matches` existed and nothing called it, so `scripts/lint_model_routing.py` verified
that two protected files agreed with each other and nothing verified that reality agreed
with either.

So every test here is a pair. A plant, and the control that must stay quiet beside it.
"""

from __future__ import annotations

import pytest

from harness.acs.acs1 import acs_sha256
from harness.fingerprint.attempt_start import (
    BUNDLE_RECORD_TYPE,
    CAUSE,
    AttemptRefused,
    begin_attempt,
)
from harness.fingerprint.factory import FactoryFingerprint

_BASE = {
    "capability_id": "capability:reviewer@1",
    "model_version": "claude-opus-5@2026-05-01",
    "prompt_version": "p-3",
    "tool_version": "t-2",
    "context_strategy_version": "cs-1",
    "provider": "anthropic",
    "model_id": "claude-opus-5",
    "api_version": "2026-05-01",
    "routing_key": "capability:reviewer@1",
    "harness_identity": "claude-code",
    "orchestrator_sha": "a" * 40,
}


def _record(**overrides: object) -> FactoryFingerprint:
    return FactoryFingerprint(**{**_BASE, **overrides})  # type: ignore[arg-type]


# ---- the control: an observation that agrees starts ------------------------------------


def test_a_matching_observation_starts_the_attempt() -> None:
    declared = _record()
    assert begin_attempt(declared, declared.as_mapping()) is declared


def test_the_returned_record_is_the_declared_one_not_a_rebuild() -> None:
    """Agreement means the observation *is* the record.

    Handing back a second object built from the observation would invite a caller to
    record what it saw rather than what it declared, and the two are the same only for as
    long as the check keeps passing.
    """
    declared = _record()
    returned = begin_attempt(declared, declared.as_mapping())
    assert returned.fingerprint_sha256 == declared.fingerprint_sha256


# ---- the plants: every field, in both directions ---------------------------------------


@pytest.mark.parametrize("field", sorted(_BASE))
def test_any_substituted_field_refuses_the_start(field: str) -> None:
    """Every field, not just `model_id`.

    A check written for the field somebody had in mind is a check that passes on the field
    somebody did not. `api_version` moving is a provider re-pointing a stable alias;
    `routing_key` moving is this side's own policy changing the resolution without moving
    the capability. Both are substitutions and neither looks like one.
    """
    declared = _record()
    observed = {**declared.as_mapping(), field: "substituted"}
    with pytest.raises(AttemptRefused) as raised:
        begin_attempt(declared, observed)
    assert [diff.field for diff in raised.value.refusal.differences] == [field]


def test_a_field_the_record_never_declared_also_refuses() -> None:
    """The second direction, which is the one that gets forgotten.

    A field the observation carried and the record never declared means the configuration
    surface grew under the measurement. It reads as a smaller event than a changed value
    and is a larger one: nobody chose it, so nobody is watching it.
    """
    declared = _record()
    observed = {**declared.as_mapping(), "reasoning_effort": "high"}
    with pytest.raises(AttemptRefused) as raised:
        begin_attempt(declared, observed)
    assert [diff.field for diff in raised.value.refusal.differences] == ["reasoning_effort"]


def test_a_missing_field_refuses_rather_than_defaulting() -> None:
    declared = _record()
    observed = {k: v for k, v in declared.as_mapping().items() if k != "provider"}
    with pytest.raises(AttemptRefused):
        begin_attempt(declared, observed)


# ---- the refusal is a record, not only a raise ------------------------------------------


def test_the_refusal_carries_the_escalation_fields_the_specification_names() -> None:
    declared = _record()
    with pytest.raises(AttemptRefused) as raised:
        begin_attempt(declared, {**declared.as_mapping(), "model_id": "cheaper"})
    emitted = raised.value.refusal.as_mapping()
    assert emitted["primary_cause"] == CAUSE
    assert emitted["also_satisfied"] == []
    assert emitted["attempt_bundle_ref"]


def test_the_turn_is_none_and_never_zero() -> None:
    """A refusal happens before turn zero.

    `evaluated_at_turn = 0` would say the first turn ran and reached this. That is a
    different event, and the two must not be the same row — the same reason
    `human_review_ms` is null rather than 0 when its instrument did not run.
    """
    declared = _record()
    with pytest.raises(AttemptRefused) as raised:
        begin_attempt(declared, {**declared.as_mapping(), "model_id": "cheaper"})
    assert raised.value.refusal.evaluated_at_turn is None


def test_the_bundle_hash_is_over_the_differences_and_moves_with_them() -> None:
    """Two different substitutions must not address the same bundle.

    A bundle reference that collapsed distinct substitutions would make the audit trail
    say "a substitution happened" without saying which — which is the difference between
    evidence and a rumour.
    """
    declared = _record()
    refs = []
    for substitute in ("cheaper", "different"):
        with pytest.raises(AttemptRefused) as raised:
            begin_attempt(declared, {**declared.as_mapping(), "model_id": substitute})
        refs.append(raised.value.refusal.attempt_bundle_ref)
    assert refs[0] != refs[1]


def test_the_bundle_carries_the_declared_hash_and_not_its_fields() -> None:
    """The hash is the identity; copying the fields would make a second home for them."""
    declared = _record()
    with pytest.raises(AttemptRefused) as raised:
        begin_attempt(declared, {**declared.as_mapping(), "model_id": "cheaper"})
    expected = acs_sha256(
        BUNDLE_RECORD_TYPE,
        {
            "declared_fingerprint_sha256": declared.fingerprint_sha256,
            "differences": [
                {"field": "model_id", "expected": "claude-opus-5", "observed": "cheaper"}
            ],
        },
    )
    assert raised.value.refusal.attempt_bundle_ref == expected


def test_the_bundle_record_type_is_not_the_fingerprints() -> None:
    """ACS-1 takes the record type as its domain separator (ADR-0003)."""
    from harness.fingerprint.factory import RECORD_TYPE

    assert BUNDLE_RECORD_TYPE != RECORD_TYPE
