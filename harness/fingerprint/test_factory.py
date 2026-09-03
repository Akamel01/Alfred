"""The factory fingerprint, and the two claims about it that a docstring cannot keep true.

The dangerous defect here is not a wrong hash. It is (a) a hash taken over a subset of the
fields, which passes every equality test while leaving the omitted fields free to change
under a measurement, and (b) the D19 group quietly drifting apart from `RunFingerprint`'s,
which would leave both records claiming to describe "what requalification reads" while
describing different things. Both get a test rather than a comment.
"""

from __future__ import annotations

import pytest

from harness.fingerprint.factory import (
    D19_FIELDS,
    FIELD_GROUPS,
    RECORD_TYPE,
    FactoryFingerprint,
    d19_is_shared,
    factory_fields,
)
from harness.fingerprint.record import FIELD_GROUPS as RUN_FIELD_GROUPS
from harness.fingerprint.record import RecordDrift, RecordIncomplete, RunFingerprint

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


# ---- the D19 group is one list, not two ------------------------------------------------


def test_the_d19_group_is_the_same_list_in_both_records() -> None:
    assert d19_is_shared()
    assert D19_FIELDS == RUN_FIELD_GROUPS["D19"]


def test_the_d19_fields_appear_on_both_dataclasses() -> None:
    # The shared *list* being equal is not enough: it must also name real fields on both.
    for name in D19_FIELDS:
        assert name in RunFingerprint.__dataclass_fields__
        assert name in FactoryFingerprint.__dataclass_fields__


def test_the_factory_record_carries_no_serving_field() -> None:
    """The reason this is a second record rather than a widened first one.

    `model_id` is deliberately NOT in this set even though `RunFingerprint` files it under
    `lane`. It names which model answered, which is a fact about both kinds of run. What
    cannot cross is the *serving configuration* — a quantization, a loaded context length, a
    parallel slot count. Those have no value for an API-served model, and inventing them here
    would put unverifiable values into a hash.
    """
    forbidden = {
        "quantization",
        "loaded_context_length",
        "parallel_slots",
        "quant_artifact_sha256",
        "inference_runtime_version",
        "server_version",
    }
    assert forbidden.isdisjoint(set(factory_fields()))
    # And the claim above about model_id, stated so it fails if someone removes it.
    assert "model_id" in factory_fields()
    assert "model_id" in RUN_FIELD_GROUPS["lane"]


# ---- construction is complete or it fails ----------------------------------------------


def test_a_valid_record_constructs() -> None:
    assert _record().capability_id == "capability:reviewer@1"


@pytest.mark.parametrize("name", list(_BASE))
def test_every_field_is_required(name: str) -> None:
    with pytest.raises(RecordIncomplete) as excinfo:
        _record(**{name: ""})
    assert name in str(excinfo.value)


@pytest.mark.parametrize("name", list(_BASE))
def test_no_field_may_be_a_non_string(name: str) -> None:
    with pytest.raises(RecordIncomplete):
        _record(**{name: 7})


@pytest.mark.parametrize("name", list(_BASE))
def test_no_field_may_be_inherit(name: str) -> None:
    # policy/model-routing.json forbids `inherit`, and this is the second place it must not
    # survive. It names whatever a session control currently says, which is not a value a
    # fingerprint can record; a grant measured on it would be suspended by a dropdown.
    with pytest.raises(RecordIncomplete) as excinfo:
        _record(**{name: "inherit"})
    assert "pinned" in str(excinfo.value)


# ---- the hash covers every field -------------------------------------------------------


def test_the_hash_is_stable_for_equal_records() -> None:
    assert _record().fingerprint_sha256 == _record().fingerprint_sha256


@pytest.mark.parametrize("name", list(_BASE))
def test_changing_any_field_moves_the_hash(name: str) -> None:
    # The subset-hash defect. A digest over ten of eleven fields passes every other test in
    # this file while leaving the eleventh free to change under a measurement.
    assert _record().fingerprint_sha256 != _record(**{name: "different"}).fingerprint_sha256


def test_the_record_type_differs_from_the_run_fingerprints() -> None:
    # ACS-1 takes the record type as its domain separator (ADR-0003). Two record types
    # sharing a separator is two records that can be substituted for each other.
    from harness.fingerprint.record import RECORD_TYPE as RUN_RECORD_TYPE

    assert RECORD_TYPE != RUN_RECORD_TYPE


# ---- comparison runs in both directions ------------------------------------------------


def test_an_identical_observation_produces_no_diff() -> None:
    assert _record().compare(_BASE) == ()


def test_a_changed_value_is_a_diff() -> None:
    diffs = _record().compare({**_BASE, "model_id": "gpt-5-nano"})
    assert len(diffs) == 1
    assert diffs[0].field == "model_id"


def test_a_field_the_observation_omits_is_a_diff() -> None:
    observed = {k: v for k, v in _BASE.items() if k != "api_version"}
    diffs = _record().compare(observed)
    assert [d.field for d in diffs] == ["api_version"]


def test_a_field_the_record_never_declared_is_also_a_diff() -> None:
    # The direction that gets forgotten. An executor reporting a field nobody declared is an
    # executor whose configuration surface grew under the measurement.
    diffs = _record().compare({**_BASE, "temperature": "0.7"})
    assert [d.field for d in diffs] == ["temperature"]


def test_assert_matches_raises_rather_than_warning() -> None:
    # This is check A from ticket #46: a mismatch means the attempt does not start.
    with pytest.raises(RecordDrift):
        _record().assert_matches({**_BASE, "model_id": "gpt-5-nano"})


def test_assert_matches_is_silent_on_agreement() -> None:
    _record().assert_matches(_BASE)


# ---- the groups account for every field ------------------------------------------------


def test_every_field_belongs_to_exactly_one_group() -> None:
    grouped = [name for group in FIELD_GROUPS.values() for name in group]
    assert sorted(grouped) == sorted(factory_fields())
    assert len(grouped) == len(set(grouped))
