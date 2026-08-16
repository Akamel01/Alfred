"""Tests for the two lane controls, with the negative controls that make them tests.

A test that still passes when the feature is deleted is not a test. So every guard here
is paired with a **mutant** — a deliberately weakened reimplementation of the same
control, standing in for the code as it would be with the guard removed — and the test
asserts the mutant misses exactly the case the real control catches. That is what makes
these fixtures discriminating rather than decorative:

* `_mutant_assert_fingerprint` checks the model id only, which is what "record the
  fingerprint and trust it" amounts to; it passes a lane that silently reloaded at
  28,672 while the real control aborts.
* `_mutant_salvage` is the probe's fallback shape — any known tool name anywhere in the
  content yields a call; it reads a prose mention as a call and binds a two-parameter
  positional call by guessing, both of which the real control refuses.

    python3 -m pytest harness/lane -q
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from lane_fingerprint import (
    FINGERPRINT_FIELDS,
    FingerprintDrift,
    FingerprintIncomplete,
    FingerprintUnavailable,
    LaneControlError,
    assert_fingerprint,
    read_fingerprint,
)
from lane_salvage import (
    AMBIGUOUS_POSITIONAL,
    ARGUMENTS_DO_NOT_MATCH_SCHEMA,
    ARGUMENT_TYPE_MISMATCH,
    MALFORMED_JSON,
    MULTIPLE_CANDIDATES,
    NO_CONTENT,
    PROSE_MENTION_ONLY,
    SYNTAX_BARE_NAME,
    SYNTAX_ENVELOPE,
    SYNTAX_NAME_OBJECT,
    SYNTAX_POSITIONAL,
    UNKNOWN_TOOL,
    UNPARSEABLE_POSITIONAL,
    SalvageCounter,
    salvage_tool_call,
    tool_specs,
)

MODEL = "qwen3-next-80b-a3b-instruct"

# The fingerprint a run was dispatched against: a model loaded at 262,144.
DISPATCHED = {
    "model_id": MODEL,
    "engine": "gguf",
    "quantization": "Q4_K_M",
    "arch": "qwen3",
    "loaded_context_length": 262144,
    "max_context_length": 262144,
}

# The same lane after an idle gap: auto-unloaded, JIT-reloaded at defaultContextLength.
# Nothing errored when this happened; the probes just returned 0/10.
RELOADED = {**DISPATCHED, "loaded_context_length": 28672}


def _fetch(fingerprint: dict[str, Any]):
    return lambda model: dict(fingerprint)


TOOLS = [
    {"type": "function", "function": {
        "name": "list_scenarios",
        "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {
        "name": "describe_scenario",
        "parameters": {"type": "object", "properties": {
            "scenario_id": {"type": "string"}}, "required": ["scenario_id"]}}},
    {"type": "function", "function": {
        "name": "get_state",
        "parameters": {"type": "object", "properties": {
            "scenario_id": {"type": "string"},
            "agent_index": {"type": "integer"},
            "step": {"type": "integer"}},
            "required": ["scenario_id", "agent_index", "step"]}}},
    {"type": "function", "function": {
        "name": "submit_answer",
        "parameters": {"type": "object", "properties": {
            "value": {"type": "number"}}, "required": ["value"]}}},
]


# ============================================================ fingerprint: positives


def test_matching_fingerprint_returns_what_was_verified() -> None:
    observed = assert_fingerprint(MODEL, DISPATCHED, fetch=_fetch(DISPATCHED))
    assert observed == DISPATCHED
    assert observed is not DISPATCHED  # a copy, not the expectation handed back


def test_every_fingerprint_field_is_compared() -> None:
    # Each field on its own must be able to abort a run; a fingerprint with fields
    # nothing reads is a fingerprint with fields that can drift unnoticed.
    for field_name in FINGERPRINT_FIELDS:
        if field_name == "model_id":
            continue
        drifted = {**DISPATCHED, field_name: "CHANGED"}
        with pytest.raises(FingerprintDrift) as exc:
            assert_fingerprint(MODEL, DISPATCHED, fetch=_fetch(drifted))
        assert [d.field for d in exc.value.differences] == [field_name]


# =================================================== fingerprint: NEGATIVE CONTROLS


def _mutant_assert_fingerprint(model: str, expected: dict, *, fetch) -> dict:
    """The control as it behaves without the guard: identity checked, config trusted.

    This is not a strawman — it is what "read the fingerprint at run start and record
    it" does, and it is the code path that let a lane serving 28,672 be measured as a
    capability regression.
    """
    observed = fetch(model)
    if observed["model_id"] != expected["model_id"]:
        raise FingerprintDrift(model, ())
    return observed


def test_context_length_drift_aborts_the_run() -> None:
    """The defect this control exists for: same model, silently different context."""
    with pytest.raises(FingerprintDrift) as exc:
        assert_fingerprint(MODEL, DISPATCHED, fetch=_fetch(RELOADED))
    diff = exc.value.differences[0]
    assert diff.field == "loaded_context_length"
    assert (diff.expected, diff.observed) == (262144, 28672)


def test_mutant_without_the_guard_misses_the_context_drift() -> None:
    """Negative control for the test above.

    With the guard removed the identical fixture passes, so the fixture is not what
    catches the drift — the guard is.
    """
    assert _mutant_assert_fingerprint(MODEL, DISPATCHED, fetch=_fetch(RELOADED)) == RELOADED


def test_unreadable_fingerprint_is_not_a_pass() -> None:
    """A check that did not run and a check that passed are different outcomes."""
    def boom(model: str):
        raise ConnectionError("connection refused")

    with pytest.raises(FingerprintUnavailable):
        assert_fingerprint(MODEL, DISPATCHED, fetch=boom)


def test_mutant_without_fail_closed_reading_would_swallow_the_error() -> None:
    """Negative control: the fail-open form returns a verdict-shaped value instead."""
    def lenient(model: str, expected: dict, *, fetch):
        try:
            return fetch(model)
        except Exception:
            return dict(expected)  # the failure mode: assume it matched

    def boom(model: str):
        raise ConnectionError("connection refused")

    assert lenient(MODEL, DISPATCHED, fetch=boom) == DISPATCHED


def test_expectation_omitting_context_length_is_rejected() -> None:
    """An expectation that cannot detect the defect is an error, not a narrower check."""
    partial = {"model_id": MODEL, "engine": "gguf"}
    with pytest.raises(FingerprintIncomplete):
        assert_fingerprint(MODEL, partial, fetch=_fetch(RELOADED))


def test_empty_expectation_is_rejected() -> None:
    with pytest.raises(FingerprintIncomplete):
        assert_fingerprint(MODEL, {}, fetch=_fetch(DISPATCHED))


def test_field_absent_from_observation_cannot_be_called_a_match() -> None:
    truncated = {k: v for k, v in DISPATCHED.items() if k != "loaded_context_length"}
    with pytest.raises(FingerprintIncomplete):
        assert_fingerprint(MODEL, DISPATCHED, fetch=_fetch(truncated))


def test_expectation_for_a_different_model_is_rejected() -> None:
    with pytest.raises(FingerprintIncomplete):
        assert_fingerprint("some-other-model", DISPATCHED, fetch=_fetch(DISPATCHED))


def test_bool_and_int_do_not_compare_equal() -> None:
    with pytest.raises(FingerprintDrift):
        assert_fingerprint(
            MODEL,
            {**DISPATCHED, "engine": 1},
            fetch=_fetch({**DISPATCHED, "engine": True}),
        )


def test_string_context_length_is_drift_not_coercion() -> None:
    """The control does not repair a mistyped expectation into a match."""
    with pytest.raises(FingerprintDrift):
        assert_fingerprint(
            MODEL,
            {**DISPATCHED, "loaded_context_length": "262144"},
            fetch=_fetch(DISPATCHED),
        )


def test_reader_returning_a_non_mapping_is_unavailable() -> None:
    with pytest.raises(FingerprintUnavailable):
        assert_fingerprint(MODEL, DISPATCHED, fetch=lambda m: ["not", "a", "mapping"])


def test_lane_errors_from_the_reader_propagate_unchanged() -> None:
    def unloaded(model: str):
        raise FingerprintUnavailable("model is present but not loaded")

    with pytest.raises(FingerprintUnavailable, match="not loaded"):
        assert_fingerprint(MODEL, DISPATCHED, fetch=unloaded)


# ------------------------------------------------------------- reading the lane


class _FakeResponse:
    def __init__(self, payload: Any) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *exc: Any) -> bool:
        return False


def _patch_urlopen(monkeypatch, payload: Any) -> None:
    import lane_fingerprint

    monkeypatch.setattr(
        lane_fingerprint.urllib.request,
        "urlopen",
        lambda url, timeout=None: _FakeResponse(payload),
    )


def test_read_fingerprint_projects_the_serving_payload(monkeypatch) -> None:
    _patch_urlopen(monkeypatch, {"data": [{
        "id": MODEL, "state": "loaded", "compatibility_type": "gguf",
        "quantization": "Q4_K_M", "arch": "qwen3",
        "loaded_context_length": 262144, "max_context_length": 262144}]})
    assert read_fingerprint(MODEL) == DISPATCHED


def test_read_fingerprint_refuses_a_model_that_is_not_loaded(monkeypatch) -> None:
    _patch_urlopen(monkeypatch, {"data": [{"id": MODEL, "state": "not-loaded"}]})
    with pytest.raises(FingerprintUnavailable, match="not loaded"):
        read_fingerprint(MODEL)


def test_read_fingerprint_refuses_an_absent_model(monkeypatch) -> None:
    _patch_urlopen(monkeypatch, {"data": []})
    with pytest.raises(FingerprintUnavailable, match="not served"):
        read_fingerprint(MODEL)


def test_read_fingerprint_refuses_a_payload_it_cannot_read(monkeypatch) -> None:
    _patch_urlopen(monkeypatch, {"unexpected": True})
    with pytest.raises(FingerprintUnavailable):
        read_fingerprint(MODEL)


# ================================================================= salvage: shapes


def test_name_then_json_object_is_salvaged() -> None:
    """The observed shape, verbatim."""
    result = salvage_tool_call('submit_answer\n{"value": 13.0994}', TOOLS)
    assert result.salvaged
    assert result.call.name == "submit_answer"
    assert result.call.arguments == {"value": 13.0994}
    assert result.call.syntax == SYNTAX_NAME_OBJECT


def test_single_parameter_positional_call_is_salvaged() -> None:
    """The second observed shape, verbatim."""
    result = salvage_tool_call("submit_answer(10)", TOOLS)
    assert result.call.arguments == {"value": 10}
    assert result.call.syntax == SYNTAX_POSITIONAL


def test_envelope_form_is_salvaged() -> None:
    content = 'Here you go: {"name": "get_state", "arguments": {"scenario_id": "S-1", ' \
              '"agent_index": 0, "step": 3}}'
    result = salvage_tool_call(content, TOOLS)
    assert result.call.name == "get_state"
    assert result.call.arguments["step"] == 3
    assert result.call.syntax == SYNTAX_ENVELOPE


def test_envelope_with_stringified_arguments_is_salvaged() -> None:
    content = '{"name": "submit_answer", "arguments": "{\\"value\\": 4.5}"}'
    assert salvage_tool_call(content, TOOLS).call.arguments == {"value": 4.5}


def test_fenced_and_tagged_calls_are_salvaged() -> None:
    content = '<tool_call>\n```json\nsubmit_answer\n{"value": 1}\n```\n</tool_call>'
    assert salvage_tool_call(content, TOOLS).call.arguments == {"value": 1}


def test_bare_name_of_a_zero_argument_tool_is_salvaged() -> None:
    result = salvage_tool_call("list_scenarios", TOOLS)
    assert result.call == salvage_tool_call("`list_scenarios`", TOOLS).call
    assert result.call.syntax == SYNTAX_BARE_NAME


def test_keyword_positional_call_matching_the_parameter_is_salvaged() -> None:
    assert salvage_tool_call("submit_answer(value=10)", TOOLS).call.arguments == {"value": 10}


def test_multi_parameter_tool_called_by_name_and_object_is_salvaged() -> None:
    """Width is only a problem for positional calls; a named object binds itself."""
    content = 'get_state {"scenario_id": "S-2", "agent_index": 1, "step": 0}'
    assert salvage_tool_call(content, TOOLS).call.arguments["scenario_id"] == "S-2"


# ====================================================== salvage: NEGATIVE CONTROLS


def _mutant_salvage(content: str, tools) -> tuple[str, dict] | None:
    """Salvage without the ambiguity guards: any known name anywhere is a call.

    This is the shape a looser implementation takes — including the reference probe's
    fallback, which returns a zero-argument call whenever it recognises a name. It is
    here to prove the assertions below discriminate.
    """
    names = [spec.name for spec in tool_specs(tools)]
    for name in names:
        idx = content.find(name)
        if idx == -1:
            continue
        paren = content.find("(", idx)
        if paren != -1:
            close = content.find(")", paren)
            raw = content[paren + 1:close]
            return name, {"first_param": raw}
        return name, {}
    return None


def test_two_parameter_positional_call_is_not_salvaged() -> None:
    """Which value fills which slot is a guess, so the harness does not make it."""
    result = salvage_tool_call('get_state("S-1", 0, 3)', TOOLS)
    assert not result.salvaged
    assert result.reason == AMBIGUOUS_POSITIONAL


def test_mutant_would_have_guessed_the_two_parameter_binding() -> None:
    """Negative control for the test above."""
    assert _mutant_salvage('get_state("S-1", 0, 3)', TOOLS) is not None


def test_prose_mentioning_a_tool_name_is_not_a_call() -> None:
    content = ("I now have everything I need, so I will call submit_answer with the "
               "value 13.0994 and finish.")
    result = salvage_tool_call(content, TOOLS)
    assert not result.salvaged
    assert result.reason == PROSE_MENTION_ONLY


def test_mutant_would_have_read_the_prose_mention_as_a_call() -> None:
    """Negative control for the test above.

    A harness that salvages this has begun inventing agent actions: it would report a
    `submit_answer` the agent never made.
    """
    content = ("I now have everything I need, so I will call submit_answer with the "
               "value 13.0994 and finish.")
    assert _mutant_salvage(content, TOOLS) == ("submit_answer", {})


def test_prose_mentioning_a_zero_argument_tool_is_not_a_call() -> None:
    content = "First I should probably use list_scenarios, then work through each one."
    assert salvage_tool_call(content, TOOLS).reason == PROSE_MENTION_ONLY


def test_malformed_json_is_not_salvaged() -> None:
    result = salvage_tool_call('submit_answer\n{"value": 13.09', TOOLS)
    assert not result.salvaged
    assert result.reason == MALFORMED_JSON


def test_arguments_outside_the_schema_are_not_salvaged() -> None:
    assert salvage_tool_call(
        'submit_answer {"answer": 13.0994}', TOOLS).reason == ARGUMENTS_DO_NOT_MATCH_SCHEMA


def test_missing_required_argument_is_not_salvaged() -> None:
    assert salvage_tool_call(
        "submit_answer()", TOOLS).reason == ARGUMENTS_DO_NOT_MATCH_SCHEMA
    assert salvage_tool_call(
        'get_state {"scenario_id": "S-1"}', TOOLS).reason == ARGUMENTS_DO_NOT_MATCH_SCHEMA


def test_wrong_argument_type_is_not_salvaged() -> None:
    assert salvage_tool_call(
        'submit_answer {"value": "thirteen"}', TOOLS).reason == ARGUMENT_TYPE_MISMATCH
    assert salvage_tool_call(
        'submit_answer {"value": true}', TOOLS).reason == ARGUMENT_TYPE_MISMATCH


def test_unparseable_positional_value_for_a_numeric_parameter_is_not_salvaged() -> None:
    assert salvage_tool_call(
        "submit_answer(thirteen)", TOOLS).reason == UNPARSEABLE_POSITIONAL


def test_keyword_naming_a_different_parameter_is_not_salvaged() -> None:
    assert salvage_tool_call(
        "submit_answer(answer=10)", TOOLS).reason == ARGUMENTS_DO_NOT_MATCH_SCHEMA


def test_two_different_candidate_calls_are_not_salvaged() -> None:
    content = 'describe_scenario {"scenario_id": "S-1"}\nsubmit_answer {"value": 2}'
    assert salvage_tool_call(content, TOOLS).reason == MULTIPLE_CANDIDATES


def test_a_repeated_identical_call_is_still_one_call() -> None:
    content = 'submit_answer {"value": 2}\nsubmit_answer {"value": 2}'
    assert salvage_tool_call(content, TOOLS).call.arguments == {"value": 2}


def test_envelope_naming_an_unknown_tool_is_not_salvaged() -> None:
    content = '{"name": "rm_rf", "arguments": {"path": "/"}}'
    assert salvage_tool_call(content, TOOLS).reason == UNKNOWN_TOOL


def test_bare_json_object_with_no_tool_name_is_not_salvaged() -> None:
    """Inferring the tool from the argument keys alone is guessing at intent."""
    assert not salvage_tool_call('{"value": 13.0994}', TOOLS).salvaged


def test_empty_content_is_not_salvaged() -> None:
    assert salvage_tool_call("", TOOLS).reason == NO_CONTENT
    assert salvage_tool_call(None, TOOLS).reason == NO_CONTENT
    assert salvage_tool_call("   \n ", TOOLS).reason == NO_CONTENT


def test_a_substring_of_a_tool_name_is_not_that_tool() -> None:
    assert not salvage_tool_call('my_get_state {"scenario_id": "S-1"}', TOOLS).salvaged
    assert not salvage_tool_call('get_state_v2 {"scenario_id": "S-1"}', TOOLS).salvaged


def test_parenthesis_inside_a_string_argument_does_not_end_the_call() -> None:
    tools = [{"name": "note", "parameters": {
        "type": "object", "properties": {"text": {"type": "string"}},
        "required": ["text"]}}]
    result = salvage_tool_call('note("a (nested) remark")', tools)
    assert result.call.arguments == {"text": "a (nested) remark"}


def test_salvage_is_generic_over_the_schema() -> None:
    """Nothing about the module is bound to one probe's tool list."""
    tools = [{"type": "function", "function": {
        "name": "apply_patch",
        "parameters": {"type": "object", "properties": {"diff": {"type": "string"}},
                       "required": ["diff"]}}}]
    assert salvage_tool_call("apply_patch(--- a/x)", tools).call.arguments == {"diff": "--- a/x"}
    assert not salvage_tool_call("submit_answer(10)", tools).salvaged


# ================================================================ schema handling


def test_unreadable_tool_schema_raises_rather_than_matching_loosely() -> None:
    with pytest.raises(LaneControlError):
        salvage_tool_call("submit_answer(1)", [{"description": "no name"}])
    with pytest.raises(LaneControlError):
        salvage_tool_call("submit_answer(1)", [])
    with pytest.raises(LaneControlError):
        tool_specs([{"name": "t", "parameters": {}}, {"name": "t", "parameters": {}}])


def test_tool_specs_reads_flat_and_openai_shapes_alike() -> None:
    flat = tool_specs([{"name": "submit_answer", "parameters": {
        "type": "object", "properties": {"value": {"type": "number"}},
        "required": ["value"]}}])
    nested = tool_specs([TOOLS[3]])
    assert flat == nested
    assert flat[0].single_parameter == "value"
    assert tool_specs([TOOLS[2]])[0].single_parameter is None


# ======================================================================= counting


def test_counter_reports_salvage_as_a_serving_quality_metric() -> None:
    counter = SalvageCounter()
    contents = [
        'submit_answer\n{"value": 1}',          # salvaged
        "submit_answer(2)",                      # salvaged
        'get_state("S-1", 0, 3)',                # refused: ambiguous
        "I will call submit_answer shortly.",    # refused: prose
    ]
    for content in contents:
        counter.observe(salvage_tool_call(content, TOOLS))

    metrics = counter.as_metrics()
    assert metrics["content_channel_messages"] == 4
    assert metrics["text_channel_calls_salvaged"] == 2
    assert metrics["salvage_rate"] == 0.5
    assert metrics["refusals"] == {AMBIGUOUS_POSITIONAL: 1, PROSE_MENTION_ONLY: 1}


def test_counter_rate_is_none_before_anything_is_inspected() -> None:
    assert SalvageCounter().salvage_rate is None


def test_result_is_falsy_when_nothing_was_salvaged() -> None:
    """The caller cannot mistake a refusal for a call, in either idiom."""
    assert not salvage_tool_call("nothing here", TOOLS)
    assert bool(salvage_tool_call("submit_answer(1)", TOOLS)) is True
