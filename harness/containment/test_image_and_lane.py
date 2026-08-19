"""C4 and C11 — the two rows that were blocked on a fingerprint record, and their controls.

Both are written the same way and for the same reason: **the caller must not be able to
tell "nothing was checked" from "everything agreed" by whether a value came back.** So
every path that reads nothing lands on `NOT_EXECUTED`, which F25 makes a failure, and each
row carries a positive control — without one, a check that refused unconditionally would
satisfy every negative test here.
"""

from __future__ import annotations

from typing import Any, Mapping

import pytest

from harness.containment.assertions import AssertionOutcome
from harness.containment.image import ImageObservation, assert_runtime_image
from harness.containment.lane import assert_lane_fingerprint, expectation_from
from harness.fingerprint.record import RunFingerprint
from harness.lane.lane_fingerprint import FingerprintUnavailable

_DIGEST = "sha256:" + "0" * 64

_BASE: dict[str, Any] = {
    "capability_id": "cap-1",
    "model_version": "qwen3-coder-30b@2026-07",
    "prompt_version": "p-3",
    "tool_version": "t-2",
    "context_strategy_version": "cs-1",
    "quant_artifact_sha256": "q" * 64,
    "inference_runtime_version": "llama.cpp-b4200",
    "server_version": "lmstudio-0.3.20",
    "orchestrator_sha": "o" * 40,
    "harness_identity": "alfred-harness-1",
    "lockfile_sha256": "l" * 64,
    "criterion_set_version": 1,
    "model_id": "qwen3-coder-30b",
    "quantization": "Q4_K_M",
    "loaded_context_length": 262_144,
    "parallel_slots": 1,
    "executor_name": "software-agent-sdk",
    "executor_commit_sha": "d460d1a0b6bd35e054ad146c6078205df4686387",
    "adaptor_version": "adaptor-0.1",
    "runtime_image_digest": _DIGEST,
    "oracle_denylist_version": "denylist-3",
    "tool_description_sha256": ("a" * 64,),
    "seed_layer_order_sha256": "s" * 64,
}


def _record(**overrides: Any) -> RunFingerprint:
    return RunFingerprint(**{**_BASE, **overrides})


# ------------------------------------------------------------------------------ C4


def test_c4_passes_on_the_declared_image() -> None:
    """The positive control."""
    result = assert_runtime_image(ImageObservation(_DIGEST, True, False, 4), _record())
    assert result.outcome is AssertionOutcome.PASSED
    assert result.observed["runtime_image_digest"] == _DIGEST


def test_c4_fails_on_a_digest_that_moved_under_the_same_tag() -> None:
    """Tag drift and a silent rebuild both leave the tag identical and the bytes different."""
    result = assert_runtime_image(
        ImageObservation("sha256:" + "1" * 64, True, False, 4), _record()
    )
    assert result.outcome is AssertionOutcome.FAILED
    assert "fingerprint declares" in result.detail


def test_c4_fails_when_the_image_is_not_mirrored_locally() -> None:
    result = assert_runtime_image(ImageObservation(_DIGEST, False, False, 4), _record())
    assert result.outcome is AssertionOutcome.FAILED
    assert "not mirrored" in result.detail


def test_c4_fails_when_the_pull_happened_inside_the_sandbox_netns() -> None:
    """A pull from inside means a registry host was reachable from the sandbox."""
    result = assert_runtime_image(ImageObservation(_DIGEST, True, True, 4), _record())
    assert result.outcome is AssertionOutcome.FAILED
    assert "reachable from the sandbox" in result.detail


def test_c4_reports_every_failing_conjunct_at_once() -> None:
    result = assert_runtime_image(
        ImageObservation("sha256:" + "2" * 64, False, True, 4), _record()
    )
    assert result.outcome is AssertionOutcome.FAILED
    assert result.detail.count(";") == 2


def test_c4_is_not_executed_when_the_pull_location_was_never_read() -> None:
    """`None` is not `False`. An unread conjunct is unexecuted, not satisfied."""
    result = assert_runtime_image(ImageObservation(_DIGEST, True, None, 4), _record())
    assert result.outcome is AssertionOutcome.NOT_EXECUTED
    assert result.observed["pulled_in_sandbox_netns"] == "unread"


def test_c4_control_an_empty_image_store_does_not_read_as_agreement() -> None:
    """D57. A scan that enumerated zero images is the observation a broken probe produces."""
    result = assert_runtime_image(ImageObservation(_DIGEST, True, False, 0), _record())
    assert result.outcome is AssertionOutcome.NOT_EXECUTED


def test_c4_control_no_inspection_at_all_is_not_a_pass() -> None:
    result = assert_runtime_image(None, _record())
    assert result.outcome is AssertionOutcome.NOT_EXECUTED
    assert "never compared" in result.detail


def test_c4_records_its_values_whatever_the_outcome() -> None:
    """`reassert.compare` needs the values to tell the same image from one of the same kind."""
    failed = assert_runtime_image(ImageObservation("sha256:" + "3" * 64, True, False, 4), _record())
    assert failed.observed["runtime_image_digest"] == "sha256:" + "3" * 64


# ----------------------------------------------------------------------------- C11


def _serving(**overrides: Any) -> Mapping[str, Any]:
    payload = {
        "model_id": _BASE["model_id"],
        "quantization": _BASE["quantization"],
        "loaded_context_length": _BASE["loaded_context_length"],
    }
    payload.update(overrides)
    return payload


def test_c11_passes_when_all_four_fields_agree() -> None:
    """The positive control."""
    result = assert_lane_fingerprint(
        _record(), fetch=lambda _: _serving(), observed_parallel_slots=1
    )
    assert result.outcome is AssertionOutcome.PASSED
    assert result.observed["parallel_slots"] == "1"


def test_c11_fails_on_the_defect_the_lane_control_was_written_for() -> None:
    """A model loaded at 262,144 found serving at 28,672 after an idle gap."""
    result = assert_lane_fingerprint(
        _record(),
        fetch=lambda _: _serving(loaded_context_length=28_672),
        observed_parallel_slots=1,
    )
    assert result.outcome is AssertionOutcome.FAILED
    assert "28672" in result.observed["lane_drift"]


def test_c11_fails_when_the_slot_count_differs() -> None:
    """Prefix reuse is 140x at one slot and 1.0x above it: a different lane, same model id."""
    result = assert_lane_fingerprint(
        _record(), fetch=lambda _: _serving(), observed_parallel_slots=4
    )
    assert result.outcome is AssertionOutcome.FAILED
    assert "disable cross-request prefix reuse" in result.detail


def test_c11_is_not_executed_when_the_slot_count_was_not_supplied() -> None:
    """The serving API does not publish it, and a guessed key would pass on a field
    nobody read."""
    result = assert_lane_fingerprint(_record(), fetch=lambda _: _serving())
    assert result.outcome is AssertionOutcome.NOT_EXECUTED
    assert result.observed["parallel_slots"] == "unread"


def test_c11_control_an_unreadable_lane_is_not_a_pass() -> None:
    """F25 through the lane module's own vocabulary: unreadable is treated as unexecuted."""

    def _unreachable(_: str) -> Mapping[str, Any]:
        raise FingerprintUnavailable("cannot reach the lane")

    result = assert_lane_fingerprint(
        _record(), fetch=_unreachable, observed_parallel_slots=1
    )
    assert result.outcome is AssertionOutcome.NOT_EXECUTED


def test_c11_control_a_lane_missing_a_declared_field_is_not_a_pass() -> None:
    """The lane module raises `FingerprintIncomplete` on a field it cannot compare."""
    result = assert_lane_fingerprint(
        _record(),
        fetch=lambda _: {"model_id": _BASE["model_id"], "loaded_context_length": 262_144},
        observed_parallel_slots=1,
    )
    assert result.outcome is AssertionOutcome.NOT_EXECUTED


def test_c11_expectation_omits_the_field_the_serving_api_does_not_publish() -> None:
    """Declaring `parallel_slots` to the lane module would report an unread field as a
    contract violation instead of as the unread conjunct it is."""
    assert "parallel_slots" not in expectation_from(_record())
    assert set(expectation_from(_record())) == {
        "model_id", "quantization", "loaded_context_length"
    }


@pytest.mark.parametrize("field", ["model_id", "quantization"])
def test_c11_fails_on_any_declared_field_that_moved(field: str) -> None:
    result = assert_lane_fingerprint(
        _record(), fetch=lambda _: _serving(**{field: "moved"}), observed_parallel_slots=1
    )
    assert result.outcome is AssertionOutcome.FAILED
