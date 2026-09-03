"""The factory fingerprint: what an *agent* run was measured on, as opposed to a lane.

`RunFingerprint` cannot describe a factory agent, and the reason is structural rather than
an omission. Its `lane` and D40 groups are self-hosted-inference fields — `quantization`,
`loaded_context_length`, `parallel_slots`, `quant_artifact_sha256`,
`inference_runtime_version`, `server_version`. None of them has a value for a model served
over an API, and `record.py` forbids the obvious patch in its own words:

    A missing field is an error, not a default. A record that cannot state a field cannot
    assert on it, and a field defaulted at construction is a field that silently stops
    discriminating.

Making six fields nullable to admit factory runs would weaken the record for the product
runs it was built for. So this is a second record rather than a widened first one.

**What it shares, and why that is the whole point.** The D19 group is imported from
`record.py` rather than restated: `capability_id`, `model_version`, `prompt_version`,
`tool_version`, `context_strategy_version`. Those five describe an agent, not a GPU, and
they are already *"what tiered requalification reads to decide which component moved."* A
second copy of that list is a list that will disagree with the first, and the direction it
disagrees in is a field that stops being hashed.

**Why a factory run needs a fingerprint at all.** The glossary binds an autonomy grant to
one: *"X% merge, Y wall-clock per success, on fingerprint Z"*, **suspended by any
fingerprint change**. Without this record a factory merge rate is a number with no declared
identity behind it, and `policy/role-bindings.json`'s claim that a binding edit is a
requalification event has nothing to attach to.

The three properties `record.py` names as what stops a fingerprint from being one are kept
verbatim: the hash is computed and never supplied, a missing field is an error rather than a
default, and comparison runs in both directions.

**Deliberately no lane group and no quantization.** An API-served model has no serving lane
this side can assert on, and inventing fields to make the two records look alike would put
values in a hash that nothing can check. What replaces them is the identity the provider
actually exposes.

Inspector machinery (D20). This module reads nothing; it holds the declared value and
compares.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any, Final, Mapping

from harness.acs.acs1 import acs_sha256
from harness.fingerprint.record import FIELD_GROUPS as RUN_FIELD_GROUPS
from harness.fingerprint.record import (
    UNDECLARED,
    FieldDiff,
    RecordDrift,
    RecordIncomplete,
)

#: Distinct from `run_fingerprint`, and that distinction is load-bearing: ACS-1 takes the
#: record type as its domain separator (ADR-0003), so a factory record and a lane record
#: with coincidentally equal fields still hash differently. Two record types sharing a
#: separator is two records that can be substituted for each other.
RECORD_TYPE: Final = "factory_fingerprint"

#: Taken from `RunFingerprint` rather than retyped. The D19 group has one definition.
D19_FIELDS: Final[tuple[str, ...]] = RUN_FIELD_GROUPS["D19"]

#: The API-served identity. It replaces the lane and quantization groups, and every field
#: here is one a provider can change without telling anyone.
SERVED_FIELDS: Final[tuple[str, ...]] = (
    "provider",
    "model_id",
    "api_version",
    "routing_key",
    "harness_identity",
    "orchestrator_sha",
)

FIELD_GROUPS: Final[Mapping[str, tuple[str, ...]]] = {
    "D19": D19_FIELDS,
    "served": SERVED_FIELDS,
}


@dataclass(frozen=True)
class FactoryFingerprint:
    """Everything a factory agent run was measured on. Constructed complete or not at all."""

    # D19 — shared verbatim with RunFingerprint.
    capability_id: str
    model_version: str
    prompt_version: str
    tool_version: str
    context_strategy_version: str
    # Served identity. `routing_key` is the capability_id the model was resolved through;
    # it is recorded separately from `capability_id` because a routing policy change can
    # move the model without moving the capability, and a record that cannot tell those
    # apart cannot say which component moved.
    provider: str
    model_id: str
    api_version: str
    routing_key: str
    harness_identity: str
    orchestrator_sha: str

    def __post_init__(self) -> None:
        problems: list[str] = []
        for name in factory_fields():
            value = getattr(self, name)
            if not isinstance(value, str):
                problems.append(f"{name} is {type(value).__name__}, not a str")
            elif not value.strip():
                problems.append(f"{name} is empty")
            elif value == "inherit":
                # policy/model-routing.json forbids it, and this is the second place it must
                # not survive: `inherit` names whatever a session control currently says,
                # which is not a value a fingerprint can record. A grant measured on it would
                # be suspended by someone changing a dropdown.
                problems.append(f"{name} is 'inherit', which is not a pinned identity")
        if problems:
            raise RecordIncomplete(
                "factory fingerprint cannot be constructed — "
                + "; ".join(problems)
                + ". A record that cannot state a field cannot assert on it."
            )

    # ---------------------------------------------------------------- serialization

    def as_mapping(self) -> dict[str, Any]:
        return {name: getattr(self, name) for name in factory_fields()}

    @property
    def fingerprint_sha256(self) -> str:
        """Derived, never stored. A supplied hash is a claim; a computed one is a function."""
        return acs_sha256(RECORD_TYPE, self.as_mapping())

    # ------------------------------------------------------------------ comparison

    def compare(self, observed: Mapping[str, Any]) -> tuple[FieldDiff, ...]:
        """Every difference, in both directions.

        The second direction is the one that gets forgotten: a field the observation carried
        and this record never declared means the configuration surface grew under the
        measurement.
        """
        diffs: list[FieldDiff] = []
        for name in factory_fields():
            expected = getattr(self, name)
            if name not in observed:
                diffs.append(FieldDiff(name, expected, UNDECLARED))
                continue
            # Plain equality, deliberately: `record.py` needs `_equal` because
            # `tool_description_sha256` is a tuple that arrives as a list. Every field here
            # is a str, so importing a private helper to compare strings would buy nothing
            # and couple this module to the other's internals.
            if expected != observed[name]:
                diffs.append(FieldDiff(name, expected, observed[name]))
        declared = set(factory_fields())
        for name in sorted(k for k in observed if k not in declared):
            diffs.append(FieldDiff(name, UNDECLARED, observed[name]))
        return tuple(diffs)

    def assert_matches(self, observed: Mapping[str, Any]) -> None:
        """Raise `RecordDrift` on any difference. This is check A from ticket #46.

        The rule is `loaded_context_length`'s, for the same reason the run-instrumentation
        specification gives it: a fingerprint field the server can change unobserved is not a
        fingerprint unless something checks it. A mismatch means the attempt does not start.
        """
        diffs = self.compare(observed)
        if diffs:
            raise RecordDrift(diffs)


def factory_fields() -> tuple[str, ...]:
    """Declaration order, taken from the dataclass rather than from a second list."""
    return tuple(f.name for f in fields(FactoryFingerprint))


def d19_is_shared() -> bool:
    """The D19 group here is the D19 group there — checked, not asserted in a comment.

    `record.py` owns the list. If a sixth D19 field is added to `RunFingerprint` and not
    here, the two records stop being comparable on exactly the thing tiered requalification
    reads, and a docstring saying "shared verbatim" would still read true. This is the
    callable form of that claim, and `test_factory.py` fails on it.
    """
    return D19_FIELDS == RUN_FIELD_GROUPS["D19"]
