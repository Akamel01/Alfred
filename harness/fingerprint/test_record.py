"""The run fingerprint record, and the control that the hash covers every field.

The dangerous defect here is not a wrong hash — a wrong hash fails everything loudly. It
is a hash taken over a *subset* of the fields, which passes every equality test in this
file while leaving the omitted fields free to change under a measurement. So the last
test in the first section changes each field in turn and requires the digest to move.
"""

from __future__ import annotations

import pytest

from harness.fingerprint.record import (
    FIELD_GROUPS,
    UNDECLARED,
    RecordDrift,
    RecordIncomplete,
    RunFingerprint,
    fingerprint_fields,
)

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


# ------------------------------------------------------------------------ the hash


def test_the_hash_is_stable_for_the_same_fields() -> None:
    assert _record().fingerprint_sha256 == _record().fingerprint_sha256


def test_the_hash_is_not_stored_and_cannot_be_supplied() -> None:
    """A supplied hash is a claim about the fields; a computed one is a function of them."""
    assert "fingerprint_sha256" not in fingerprint_fields()
    with pytest.raises(TypeError):
        RunFingerprint(**_BASE, fingerprint_sha256="deadbeef")  # type: ignore[arg-type]


def test_every_field_is_covered_by_the_hash() -> None:
    """The control. A digest over a subset passes every other test in this file.

    Each field is perturbed to a value of its own type and the digest must move. A field
    the hash does not read is a field that can change under a measurement without the
    fingerprint saying so, which is the exact failure `loaded_context_length` already cost
    once.
    """
    baseline = _record().fingerprint_sha256
    for name in fingerprint_fields():
        current = _BASE[name]
        if isinstance(current, tuple):
            perturbed: object = current + ("c" * 64,)
        elif isinstance(current, int):
            perturbed = current + 1
        else:
            perturbed = f"{current}-moved"
        assert _record(**{name: perturbed}).fingerprint_sha256 != baseline, (
            f"{name} does not participate in the digest"
        )


def test_the_field_groups_account_for_every_field() -> None:
    """The groups are documentation, and documentation drifts unless something reads it."""
    grouped = tuple(name for group in FIELD_GROUPS.values() for name in group)
    assert sorted(grouped) == sorted(fingerprint_fields())
    assert len(set(grouped)) == len(grouped), "a field is claimed by two groups"


# ----------------------------------------------------------------- construction refuses


@pytest.mark.parametrize(
    "override, fragment",
    [
        ({"capability_id": ""}, "capability_id is empty"),
        ({"capability_id": "   "}, "capability_id is empty"),
        ({"model_id": None}, "model_id is NoneType"),
        ({"loaded_context_length": 0}, "below its floor"),
        ({"parallel_slots": 0}, "below its floor"),
        ({"criterion_set_version": 0}, "below its floor"),
        ({"parallel_slots": True}, "parallel_slots is bool"),
        ({"loaded_context_length": "262144"}, "loaded_context_length is str"),
        ({"tool_description_sha256": ()}, "tool_description_sha256 is empty"),
        ({"tool_description_sha256": ("",)}, "empty or non-string entry"),
        ({"tool_description_sha256": ["a" * 64]}, "not a tuple"),
    ],
)
def test_an_incomplete_record_cannot_be_constructed(
    override: dict[str, object], fragment: str
) -> None:
    with pytest.raises(RecordIncomplete, match=fragment):
        _record(**override)


def test_every_problem_is_reported_at_once() -> None:
    """One error per construction would make fixing a record an N-round game."""
    with pytest.raises(RecordIncomplete) as caught:
        _record(capability_id="", model_id="", parallel_slots=0)
    message = str(caught.value)
    assert "capability_id" in message and "model_id" in message and "parallel_slots" in message


def test_a_complete_record_is_constructed() -> None:
    """The positive control: without it every test above passes on a class that always raises."""
    assert _record().runtime_image_digest.startswith("sha256:")


# ------------------------------------------------------------------------ comparison


def test_a_matching_observation_reports_no_difference() -> None:
    record = _record()
    assert record.compare(record.as_mapping()) == ()
    record.assert_matches(record.as_mapping())


def test_a_changed_value_is_a_difference() -> None:
    record = _record()
    observed = record.as_mapping() | {"loaded_context_length": 28_672}
    diffs = record.compare(observed)
    assert [d.field for d in diffs] == ["loaded_context_length"]
    with pytest.raises(RecordDrift, match="28672"):
        record.assert_matches(observed)


def test_a_field_the_observation_omits_is_a_difference() -> None:
    """Not a pass. An unobserved field was not compared, and nothing that was not compared
    can have agreed."""
    record = _record()
    observed = record.as_mapping()
    del observed["runtime_image_digest"]
    diffs = record.compare(observed)
    assert [d.field for d in diffs] == ["runtime_image_digest"]
    assert diffs[0].observed is UNDECLARED
    assert "not observed at all" in str(diffs[0])


def test_a_field_the_record_never_declared_is_a_difference() -> None:
    """The second direction, which the Worker port contract requires: an executor
    reporting a field nobody declared is an executor whose surface grew."""
    record = _record()
    diffs = record.compare(record.as_mapping() | {"speculative_decoding": "on"})
    assert [d.field for d in diffs] == ["speculative_decoding"]
    assert diffs[0].expected is UNDECLARED
    assert "undeclared" in str(diffs[0])


def test_bool_and_int_are_not_the_same_observation() -> None:
    """Python says `True == 1`. A lane serving one slot and a lane reporting a flag are
    not the same lane."""
    record = _record()
    diffs = record.compare(record.as_mapping() | {"parallel_slots": True})
    assert [d.field for d in diffs] == ["parallel_slots"]


def test_a_list_and_a_tuple_of_the_same_hashes_agree() -> None:
    """The record holds a tuple and every serialization round-trip yields a list. A
    difference reported here would be a difference in the encoding, not in the lane."""
    record = _record()
    assert record.compare(record.as_mapping()) == ()
    assert record.as_mapping()["tool_description_sha256"] == list(_BASE["tool_description_sha256"])


def test_all_differences_are_reported_not_just_the_first() -> None:
    record = _record()
    observed = record.as_mapping() | {"model_id": "other", "quantization": "Q8_0", "extra": "x"}
    assert [d.field for d in record.compare(observed)] == ["model_id", "quantization", "extra"]


# ------------------------------------------------- the register carries every field


def _declared_columns() -> set[str]:
    """Column names from the control migrations, read from source rather than a database.

    An AST read rather than a live schema so this control runs in every environment. A
    drift guard that only runs where Postgres does is a drift guard that stops running.
    """
    import ast
    from pathlib import Path

    columns: set[str] = set()
    versions = Path(__file__).resolve().parents[2] / "migrations/harness/control/versions"
    for path in sorted(versions.glob("*.py")):
        for node in ast.walk(ast.parse(path.read_text())):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "Column"
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                columns.add(node.args[0].value)
    return columns


def test_every_record_field_has_a_column_in_the_register() -> None:
    """A record field with no column is a field the register cannot answer *what changed* on.

    D19's tiered requalification is a decision about which component moved, and it reads
    the columns. A field that lives only in Python is a field the decision cannot see.
    """
    columns = _declared_columns()
    assert columns, "the migration read found no columns; this control did not run"
    missing = sorted(set(fingerprint_fields()) - columns)
    assert not missing, f"run fingerprint fields with no column: {missing}"
