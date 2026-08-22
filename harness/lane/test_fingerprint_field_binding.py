"""Three spellings of "the lane's fields", and the two-schema reality between them.

`harness/fingerprint/record.py` `FIELD_GROUPS["lane"]` is what a run hashes: four fields,
including `parallel_slots`. `harness/lane/lane_fingerprint.py` `FINGERPRINT_FIELDS` is
what the serving layer publishes and the lane module compares: six fields — `engine`,
`arch` and `max_context_length` that the record does not carry, and no `parallel_slots`.
These are **two schemas, deliberately**: the slot count is a launch-time property the
serving API does not publish (`docs/tier4/sandbox-specification.md` row C11, ADR-0020),
so it is asserted from an explicit argument in `harness/containment/lane.py` instead, and
the three API-reported fields cross into the lane module through
`expectation_from`, which selects exactly the record's lane group minus that one field.

Neither list derives from the other at runtime — each is restated beside its own schema —
so this test freezes the *relationship*: what `expectation_from` must select from a real
record, that everything it selects is comparable by the lane module, and the exact
partition between the two field sets. Any member moving on either side fails here first.

If you add a lane field: decide which schema it belongs to (or both), touch every side
this file names, and update this test's partition.
"""

from __future__ import annotations

from harness.containment.lane import expectation_from
from harness.fingerprint.record import FIELD_GROUPS, RunFingerprint
from harness.lane.lane_fingerprint import FINGERPRINT_FIELDS

_BASE = {
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
    "runtime_image_digest": "sha256:" + "0" * 64,
    "oracle_denylist_version": "denylist-3",
    "tool_description_sha256": ("a" * 64, "b" * 64),
    "seed_layer_order_sha256": "s" * 64,
}


def _record(**overrides: object) -> RunFingerprint:
    return RunFingerprint(**{**_BASE, **overrides})  # type: ignore[arg-type]


def test_expectation_selects_the_lane_group_minus_parallel_slots() -> None:
    """The computed relationship: `expectation_from` reads exactly those record fields."""
    record = _record()
    expected = expectation_from(record)
    assert set(expected) == set(FIELD_GROUPS["lane"]) - {"parallel_slots"}
    assert expected == {
        "model_id": record.model_id,
        "quantization": record.quantization,
        "loaded_context_length": record.loaded_context_length,
    }
    # And it moves with the record, so a changed dispatch cannot wear a stale expectation.
    assert (
        expectation_from(_record(loaded_context_length=28_672))["loaded_context_length"]
        == 28_672
    )


def test_every_selected_field_is_comparable_by_the_lane_module() -> None:
    """A selected field `assert_fingerprint` could not compare would be an unread conjunct."""
    assert set(FIELD_GROUPS["lane"]) - {"parallel_slots"} <= set(FINGERPRINT_FIELDS)


def test_the_two_schemas_partition_exactly_as_declared() -> None:
    """The partition itself is the contract; any drift on either side lands here."""
    shared = {"model_id", "quantization", "loaded_context_length"}
    record_only = {"parallel_slots"}
    lane_module_only = {"engine", "arch", "max_context_length"}

    lane_group = set(FIELD_GROUPS["lane"])
    lane_fields = set(FINGERPRINT_FIELDS)
    assert lane_group & lane_fields == shared
    assert lane_group - lane_fields == record_only
    assert lane_fields - lane_group == lane_module_only


def test_neither_schema_collapses() -> None:
    """Vacuity guard (D57): empty groups agree with anything and pin nothing."""
    assert FIELD_GROUPS["lane"]
    assert FINGERPRINT_FIELDS
