"""Recovery of tool calls the serving layer rendered into the content channel.

Measured on the selected lane: 15–20% of tool calls — disproportionately the *final*
one — arrive as prose instead of through the tool-call channel, in two syntaxes:

    submit_answer
    {"value": 13.0994}

    submit_answer(10)

The JSON is valid; the channel is wrong. Without salvage the agent appears to stall
with no error at all: chain completion read 20% without it and 100% with it, on
identical model behaviour.

Two rules shape everything below.

**Salvage only unambiguous cases.** A named tool with a parseable JSON object that fits
its schema, or a *single-parameter* tool called positionally. Anything wider — a
two-parameter tool called positionally, two candidate calls in one message, arguments
that do not fit the schema — is the harness guessing at agent intent, which is how a
harness starts inventing agent actions. Those refuse, with a reason.

**Count, never absorb.** A salvaged call is a defect that happened. The rate is a
serving-quality signal that feeds lane selection, so `salvage_tool_call` returns a
result carrying an explicit salvaged flag and a refusal reason rather than an
`Optional` the caller can silently swallow. `SalvageCounter` accumulates the metric.

`bench/probe_agentic.py::parse_text_tool_call` is the reference this generalises: that
one is hard-wired to one probe's four tools and to a module-level name list, and falls
back to returning a zero-argument call whenever it sees a known name — which would read
a prose *mention* of a tool as a call to it. This module is generic over a tool schema
and refuses that case.

No third-party imports: the inspector must not depend on the supply chain it inspects.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from lane_fingerprint import LaneControlError

# ------------------------------------------------------------------------ reasons
# A refusal reason is a metric label, not prose. Stable strings, aggregated by the
# counter and reported per lane.

NO_CONTENT = "no_content"
NO_TOOL_NAME = "no_tool_name"
PROSE_MENTION_ONLY = "prose_mention_only"
UNKNOWN_TOOL = "unknown_tool"
MALFORMED_JSON = "malformed_json"
NOT_AN_OBJECT = "not_an_object"
ARGUMENTS_DO_NOT_MATCH_SCHEMA = "arguments_do_not_match_schema"
ARGUMENT_TYPE_MISMATCH = "argument_type_mismatch"
AMBIGUOUS_POSITIONAL = "ambiguous_positional"
UNPARSEABLE_POSITIONAL = "unparseable_positional"
MULTIPLE_CANDIDATES = "multiple_candidates"

# Syntax labels, so the metric can distinguish which serving defect produced the call.
SYNTAX_ENVELOPE = "name_arguments_envelope"
SYNTAX_NAME_OBJECT = "name_then_json_object"
SYNTAX_POSITIONAL = "positional"
SYNTAX_BARE_NAME = "bare_name_no_arguments"


# ------------------------------------------------------------------------- schema


@dataclass(frozen=True)
class ToolSpec:
    """The part of a tool schema this module needs, normalised."""

    name: str
    parameters: tuple[str, ...]
    required: tuple[str, ...]
    types: Mapping[str, str]

    @property
    def single_parameter(self) -> str | None:
        return self.parameters[0] if len(self.parameters) == 1 else None


_JSON_TYPES: dict[str, tuple[type, ...]] = {
    "string": (str,),
    "number": (int, float),
    "integer": (int,),
    "boolean": (bool,),
    "object": (dict,),
    "array": (list,),
    "null": (type(None),),
}


def tool_specs(tools: Iterable[Mapping[str, Any]]) -> tuple[ToolSpec, ...]:
    """Normalise OpenAI-style or flat tool schemas into `ToolSpec`s.

    A schema this cannot read raises rather than degrading to a looser match: salvage
    driven by a half-understood schema is salvage that guesses.
    """
    specs: list[ToolSpec] = []
    seen: set[str] = set()
    for tool in tools or ():
        if not isinstance(tool, Mapping):
            raise LaneControlError(f"tool schema entry is {type(tool).__name__}, not a mapping")
        body = tool.get("function") if isinstance(tool.get("function"), Mapping) else tool
        name = body.get("name")
        if not isinstance(name, str) or not name:
            raise LaneControlError(f"tool schema entry has no usable name: {tool!r}")
        if name in seen:
            raise LaneControlError(
                f"duplicate tool name {name!r} in schema — a call to it could not be "
                f"bound to one tool"
            )
        seen.add(name)
        params = body.get("parameters") or {}
        if not isinstance(params, Mapping):
            raise LaneControlError(f"tool {name!r} has non-mapping parameters")
        props = params.get("properties") or {}
        if not isinstance(props, Mapping):
            raise LaneControlError(f"tool {name!r} has non-mapping parameter properties")
        required = params.get("required") or []
        if not isinstance(required, Sequence) or isinstance(required, (str, bytes)):
            raise LaneControlError(f"tool {name!r} has a non-list `required`")
        types = {
            key: value.get("type")
            for key, value in props.items()
            if isinstance(value, Mapping) and isinstance(value.get("type"), str)
        }
        specs.append(ToolSpec(name, tuple(props), tuple(required), types))
    if not specs:
        raise LaneControlError("no tools supplied — there is nothing to salvage against")
    return tuple(specs)


# ------------------------------------------------------------------------- result


@dataclass(frozen=True)
class SalvagedCall:
    name: str
    arguments: dict[str, Any]
    syntax: str


@dataclass(frozen=True)
class SalvageResult:
    """Outcome of one inspection of a content-channel message.

    `salvaged` is the flag the caller counts; `reason` is why a refusal refused, as a
    stable metric label.
    """

    call: SalvagedCall | None
    reason: str = ""

    @property
    def salvaged(self) -> bool:
        return self.call is not None

    def __bool__(self) -> bool:
        return self.call is not None


def _ok(name: str, arguments: dict[str, Any], syntax: str) -> SalvageResult:
    return SalvageResult(SalvagedCall(name, arguments, syntax))


def _no(reason: str) -> SalvageResult:
    return SalvageResult(None, reason)


# ------------------------------------------------------------------------ parsing


_FENCE = re.compile(r"^[ \t]*```[A-Za-z0-9_+-]*[ \t]*$", re.MULTILINE)
_TOOL_TAGS = re.compile(r"</?(tool_call|tool_code|function_call)>", re.IGNORECASE)


def _strip_wrappers(content: str) -> str:
    """Remove markdown fences and tool-call tags. Nothing else is rewritten."""
    text = _FENCE.sub("", content)
    return _TOOL_TAGS.sub("", text)


def _match_close(text: str, open_idx: int) -> int:
    """Index just past the `)` matching the `(` at `open_idx`, or -1.

    Quote-aware, because a parenthesis inside a string argument is not a delimiter.
    """
    depth = 0
    quote = ""
    i = open_idx
    while i < len(text):
        ch = text[i]
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = ""
        elif ch in "\"'":
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return -1


def _top_level_comma(text: str) -> bool:
    depth = 0
    quote = ""
    i = 0
    while i < len(text):
        ch = text[i]
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = ""
        elif ch in "\"'":
            quote = ch
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif ch == "," and depth == 0:
            return True
        i += 1
    return False


def _validate(spec: ToolSpec, args: Mapping[str, Any]) -> str | None:
    """Return a refusal reason, or None if `args` is a valid call to `spec`."""
    unknown = set(args) - set(spec.parameters)
    if unknown:
        return ARGUMENTS_DO_NOT_MATCH_SCHEMA
    missing = set(spec.required) - set(args)
    if missing:
        return ARGUMENTS_DO_NOT_MATCH_SCHEMA
    for key, value in args.items():
        declared = spec.types.get(key)
        if declared is None:
            continue
        allowed = _JSON_TYPES.get(declared)
        if allowed is None:
            continue
        if declared in ("number", "integer") and isinstance(value, bool):
            return ARGUMENT_TYPE_MISMATCH
        if not isinstance(value, allowed):
            return ARGUMENT_TYPE_MISMATCH
    return None


def _from_object(spec: ToolSpec, obj: Any, syntax: str) -> SalvageResult:
    if not isinstance(obj, Mapping):
        return _no(NOT_AN_OBJECT)
    reason = _validate(spec, obj)
    if reason is not None:
        return _no(reason)
    return _ok(spec.name, dict(obj), syntax)


def _from_positional(spec: ToolSpec, raw: str) -> SalvageResult:
    """Bind a positional call. Single-parameter tools only, by construction."""
    raw = raw.strip()
    if not raw:
        # `name()`. Unambiguous only where the tool takes nothing (or nothing required).
        return _from_object(spec, {}, SYNTAX_POSITIONAL)
    param = spec.single_parameter
    if param is None:
        # Two or more parameters, or none declared: which slot the value fills is a
        # guess, and a guess is exactly what this module refuses to make.
        return _no(AMBIGUOUS_POSITIONAL)
    if _top_level_comma(raw):
        return _no(AMBIGUOUS_POSITIONAL)
    keyword = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*[=:]\s*(.+)$", raw, re.DOTALL)
    if keyword:
        if keyword.group(1) != param:
            return _no(ARGUMENTS_DO_NOT_MATCH_SCHEMA)
        raw = keyword.group(2).strip()
    try:
        value: Any = json.loads(raw)
    except json.JSONDecodeError:
        # A bare unquoted token is a string only where the parameter is one; anywhere
        # else the value cannot be reconstructed and the call is not recoverable.
        if spec.types.get(param) in (None, "string"):
            value = raw.strip("'\"")
        else:
            return _no(UNPARSEABLE_POSITIONAL)
    return _from_object(spec, {param: value}, SYNTAX_POSITIONAL)


def _envelope(text: str, by_name: Mapping[str, ToolSpec]) -> SalvageResult | None:
    """`{"name": ..., "arguments": {...}}` — the whole call as one JSON object."""
    start = text.find("{")
    if start == -1:
        return None
    try:
        obj, _ = json.JSONDecoder().raw_decode(text, start)
    except json.JSONDecodeError:
        return None
    if not isinstance(obj, dict) or "name" not in obj or "arguments" not in obj:
        return None
    name = obj["name"]
    if not isinstance(name, str):
        return _no(NOT_AN_OBJECT)
    spec = by_name.get(name)
    if spec is None:
        return _no(UNKNOWN_TOOL)
    inner = obj["arguments"]
    if isinstance(inner, str):
        try:
            inner = json.loads(inner) if inner.strip() else {}
        except json.JSONDecodeError:
            return _no(MALFORMED_JSON)
    return _from_object(spec, inner, SYNTAX_ENVELOPE)


def _candidates(text: str, specs: Sequence[ToolSpec]) -> list[tuple[ToolSpec, str, int]]:
    """Every `name` in `text` immediately followed by a call delimiter.

    "Immediately" means whitespace and at most one separating colon. A tool name in
    running prose is not a call to it, and that is the discriminator.
    """
    found: list[tuple[ToolSpec, str, int]] = []
    for spec in specs:
        pattern = re.compile(
            rf"(?<![A-Za-z0-9_]){re.escape(spec.name)}(?![A-Za-z0-9_])[ \t\r\n]*:?[ \t\r\n]*(?=[({{])"
        )
        for match in pattern.finditer(text):
            found.append((spec, text[match.end()], match.end()))
    return sorted(found, key=lambda item: item[2])


def _mentions_any(text: str, specs: Sequence[ToolSpec]) -> bool:
    return any(
        re.search(rf"(?<![A-Za-z0-9_]){re.escape(spec.name)}(?![A-Za-z0-9_])", text)
        for spec in specs
    )


def salvage_tool_call(
    content: str | None,
    tools: Iterable[Mapping[str, Any]],
) -> SalvageResult:
    """Recover a tool call rendered into the content channel, or refuse with a reason.

    Generic over `tools` — the same OpenAI-style schema list handed to the serving
    layer. Recovers exactly three shapes, all of which bind to one tool with no
    guessing:

    * `{"name": "t", "arguments": {...}}` — the call as a JSON envelope;
    * `t {...}` / `t\\n{...}` — a named tool followed by a JSON object fitting its
      schema;
    * `t(v)` — a **single-parameter** tool called positionally;

    plus a message that is nothing but the name of a tool taking no required argument.

    Everything else refuses. Notably: a two-parameter tool called positionally, two
    candidate calls in one message, arguments that do not fit the schema, malformed
    JSON, and a tool name appearing in prose.
    """
    specs = tool_specs(tools)
    by_name = {spec.name: spec for spec in specs}

    if not content or not content.strip():
        return _no(NO_CONTENT)
    text = _strip_wrappers(content)
    if not text.strip():
        return _no(NO_CONTENT)

    envelope = _envelope(text, by_name)
    if envelope is not None:
        return envelope

    results: list[SalvageResult] = []
    for spec, delimiter, index in _candidates(text, specs):
        if delimiter == "{":
            try:
                obj, _ = json.JSONDecoder().raw_decode(text, index)
            except json.JSONDecodeError:
                results.append(_no(MALFORMED_JSON))
                continue
            results.append(_from_object(spec, obj, SYNTAX_NAME_OBJECT))
        else:
            close = _match_close(text, index)
            if close == -1:
                results.append(_no(UNPARSEABLE_POSITIONAL))
                continue
            results.append(_from_positional(spec, text[index + 1: close - 1]))

    accepted = [r for r in results if r.salvaged]
    distinct = {
        (r.call.name, json.dumps(r.call.arguments, sort_keys=True, default=str))
        for r in accepted
    }
    if len(distinct) > 1:
        # Two different recoverable calls in one message. Choosing between them would
        # be the harness deciding what the agent meant.
        return _no(MULTIPLE_CANDIDATES)
    if accepted:
        return accepted[0]
    if results:
        return results[0]

    # A message that is nothing but a tool name, for a tool that needs no argument.
    bare = text.strip().strip("`\"'")
    spec = by_name.get(bare)
    if spec is not None and not spec.required:
        return _ok(spec.name, {}, SYNTAX_BARE_NAME)

    return _no(PROSE_MENTION_ONLY if _mentions_any(text, specs) else NO_TOOL_NAME)


# ------------------------------------------------------------------------ counting


@dataclass
class SalvageCounter:
    """Serving-quality metric. A salvaged call is a defect that happened.

    `inspected` counts content-channel messages examined — i.e. replies that arrived
    with no tool call in the tool-call channel — so `salvage_rate` is the share of
    those the serving layer mangled recoverably, and `refusals` is the shape of what it
    mangled unrecoverably.
    """

    inspected: int = 0
    salvaged: int = 0
    refusals: Counter = field(default_factory=Counter)

    def observe(self, result: SalvageResult) -> SalvageResult:
        self.inspected += 1
        if result.salvaged:
            self.salvaged += 1
        else:
            self.refusals[result.reason] += 1
        return result

    @property
    def salvage_rate(self) -> float | None:
        return self.salvaged / self.inspected if self.inspected else None

    def as_metrics(self) -> dict[str, Any]:
        return {
            "content_channel_messages": self.inspected,
            "text_channel_calls_salvaged": self.salvaged,
            "salvage_rate": self.salvage_rate,
            "refusals": dict(self.refusals),
        }
