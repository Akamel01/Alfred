"""The run fingerprint record: what a run was measured on, stated once and hashed.

Two containment assertions could not be written without this. C4 compares the runtime
image digest against a declared value and C11 compares the serving lane against one, and
until this module there was no declared value anywhere in the repository to compare
against — `runtime_image_digest` appeared in no Python file at all. Both were recorded as
blocked (ADR-0018, ADR-0019) rather than written as shells, because a shell whose only
hole is "the fingerprint" belongs on no worklist.

Three properties, and each answers a way a fingerprint stops being one:

1. **The hash is computed, never supplied.** `fingerprint_sha256` is derived from the
   fields through ACS-1 (`harness/acs/acs1.py`), the same encoder the result stamp and the
   evidence chain use, with its own vector suite and a JavaScript cross-check. A supplied
   hash is a claim about the fields; a computed one is a function of them.
2. **A missing field is an error, not a default.** A record that cannot state a field
   cannot assert on it, and a field defaulted at construction is a field that silently
   stops discriminating. This is `lane_fingerprint.FingerprintIncomplete` generalized: an
   assertion that cannot compare a field is not an assertion.
3. **Comparison runs in both directions.** A declared field the observation omits and an
   observed field the record never declared are both differences. The Worker port contract
   requires raising on the second direction too (`docs/tier1/worker-port-contract.md` §
   *Fingerprint obligations*), because an executor reporting a field nobody declared is an
   executor whose configuration surface grew under the measurement.

**What this module deliberately does not do is read anything.** It holds the declared
value and compares. Reading the live world is C4's and C11's job, and keeping the two apart
is what lets the comparison be tested without a container or a serving layer.

No third-party imports, and none from `src/`: the dependency runs the other way — the
product tree's provenance package imports this tree's ACS-1 encoder rather than
reimplementing it. The inspector must not depend on the supply chain it inspects.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any, Final, Mapping

from harness.acs.acs1 import acs_sha256

__all__ = [
    "FIELD_GROUPS",
    "UNDECLARED",
    "FieldDiff",
    "RecordDrift",
    "RecordIncomplete",
    "RunFingerprint",
    "RunFingerprintError",
    "fingerprint_fields",
]

#: The ACS-1 record type. Domain separation: a fingerprint and an evidence row with
#: coincidentally identical content must not produce the same digest.
RECORD_TYPE: Final = "run_fingerprint"


# ------------------------------------------------------------------------ errors


class RunFingerprintError(RuntimeError):
    """Base for every refusal here. Carries its error-taxonomy class."""

    taxonomy_class = "contract-violation"


class RecordIncomplete(RunFingerprintError):
    """A field the record needs is missing, empty, or out of range.

    Contract violation rather than infrastructure: nothing was read and nothing failed to
    read — the record as constructed cannot support the comparison it exists for.
    """


@dataclass(frozen=True)
class FieldDiff:
    """One field that differs. The single definition; `harness/lane` imports it.

    `expected is UNDECLARED` marks the second direction — a field the observation carried
    and the record never declared. It reads differently from a value mismatch and a caller
    that collapses the two loses the distinction between "the lane changed" and "the lane
    grew a knob nobody knew about".
    """

    field: str
    expected: Any
    observed: Any

    def __str__(self) -> str:
        if self.expected is UNDECLARED:
            return f"{self.field}: undeclared, observed {self.observed!r}"
        if self.observed is UNDECLARED:
            return f"{self.field}: expected {self.expected!r}, not observed at all"
        return f"{self.field}: expected {self.expected!r}, observed {self.observed!r}"


class _Undeclared:
    """A sentinel distinct from `None`, because `None` is a value an executor can report."""

    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover — repr is for failure messages
        return "<undeclared>"


UNDECLARED: Final = _Undeclared()


class RecordDrift(RunFingerprintError):
    """The observation is not the record the run was dispatched against."""

    def __init__(self, differences: tuple[FieldDiff, ...]) -> None:
        self.differences = differences
        detail = "; ".join(str(d) for d in differences)
        super().__init__(
            f"run fingerprint drift — {detail}. The run is not being measured on the "
            f"configuration it was dispatched against."
        )


# ------------------------------------------------------------------------ the record


#: Presentation order and, more importantly, the decision each field answers to. A reader
#: asking "why is this field here" gets the answer from the grouping rather than from the
#: commit that added it.
FIELD_GROUPS: Final[Mapping[str, tuple[str, ...]]] = {
    # D19: what tiered requalification reads to decide which component moved.
    "D19": (
        "capability_id",
        "model_version",
        "prompt_version",
        "tool_version",
        "context_strategy_version",
    ),
    # D40: the fields a measurement is not comparable across.
    "D40": (
        "quant_artifact_sha256",
        "inference_runtime_version",
        "server_version",
        "orchestrator_sha",
        "harness_identity",
        "lockfile_sha256",
        "criterion_set_version",
    ),
    # The serving lane. C11 asserts these against the live server.
    "lane": (
        "model_id",
        "quantization",
        "loaded_context_length",
        "parallel_slots",
    ),
    # The worker's own contribution. Every one is a field something else can change
    # without notice; `runtime_image_digest` is what C4 asserts.
    "worker": (
        "executor_name",
        "executor_commit_sha",
        "adaptor_version",
        "runtime_image_digest",
        "oracle_denylist_version",
        "tool_description_sha256",
        "seed_layer_order_sha256",
    ),
}

#: Fields whose value is a count and whose floor is meaningful. `parallel_slots` at 1 and
#: above 1 are different lanes: cross-request prefix reuse is 140x at 1 and 1.0x above it.
_POSITIVE_INTS: Final = ("loaded_context_length", "parallel_slots", "criterion_set_version")


@dataclass(frozen=True)
class RunFingerprint:
    """Everything a run was measured on. Constructed complete or not at all."""

    # D19.
    capability_id: str
    model_version: str
    prompt_version: str
    tool_version: str
    context_strategy_version: str
    # D40. The quantization *artifact* hash, never the quant name — imatrix variants share
    # names, and a 4-bit and a 6-bit quant of the same weights are different models for
    # grant purposes.
    quant_artifact_sha256: str
    inference_runtime_version: str
    server_version: str
    orchestrator_sha: str
    harness_identity: str
    lockfile_sha256: str
    criterion_set_version: int
    # Lane.
    model_id: str
    quantization: str
    loaded_context_length: int
    parallel_slots: int
    # Worker port.
    executor_name: str
    executor_commit_sha: str
    adaptor_version: str
    runtime_image_digest: str
    oracle_denylist_version: str
    # A tuple rather than one hash: descriptions change behaviour without names changing,
    # and a single digest over all of them cannot say which tool moved.
    tool_description_sha256: tuple[str, ...]
    seed_layer_order_sha256: str

    def __post_init__(self) -> None:
        problems: list[str] = []
        for name in fingerprint_fields():
            value = getattr(self, name)
            if name == "tool_description_sha256":
                if not isinstance(value, tuple):
                    problems.append(f"{name} is {type(value).__name__}, not a tuple")
                elif not value:
                    # A run declaring no tool descriptions cannot detect a description
                    # change, which is the entire reason the field exists.
                    problems.append(f"{name} is empty")
                elif any(not isinstance(v, str) or not v.strip() for v in value):
                    problems.append(f"{name} contains an empty or non-string entry")
                continue
            if name in _POSITIVE_INTS:
                # bool before int, for the same reason ACS-1 orders them that way.
                if isinstance(value, bool) or not isinstance(value, int):
                    problems.append(f"{name} is {type(value).__name__}, not an int")
                elif value < 1:
                    problems.append(f"{name} is {value}, which is below its floor of 1")
                continue
            if not isinstance(value, str):
                problems.append(f"{name} is {type(value).__name__}, not a str")
            elif not value.strip():
                problems.append(f"{name} is empty")
        if problems:
            raise RecordIncomplete(
                "run fingerprint cannot be constructed — "
                + "; ".join(problems)
                + ". A record that cannot state a field cannot assert on it."
            )

    # ---------------------------------------------------------------- serialization

    def as_mapping(self) -> dict[str, Any]:
        """The record as plain data, for hashing and for the register row.

        The tuple becomes a list because ACS-1 encodes sequences and not tuples
        specifically; the two canonicalize identically, so nothing is lost.
        """
        out: dict[str, Any] = {}
        for name in fingerprint_fields():
            value = getattr(self, name)
            out[name] = list(value) if isinstance(value, tuple) else value
        return out

    @property
    def fingerprint_sha256(self) -> str:
        """Derived, never stored. See property 1 in the module docstring."""
        return acs_sha256(RECORD_TYPE, self.as_mapping())

    # ------------------------------------------------------------------ comparison

    def compare(self, observed: Mapping[str, Any]) -> tuple[FieldDiff, ...]:
        """Every difference between this record and an observation, in both directions.

        Returns rather than raises, so a caller that wants to report all differences can,
        and `assert_matches` is the raising form. Order is declaration order, then the
        undeclared keys sorted — deterministic, because a diff list that reorders between
        runs is one nobody can diff.
        """
        diffs: list[FieldDiff] = []
        for name in fingerprint_fields():
            expected = getattr(self, name)
            if name not in observed:
                diffs.append(FieldDiff(name, expected, UNDECLARED))
                continue
            seen = observed[name]
            if isinstance(expected, tuple) and isinstance(seen, list):
                seen = tuple(seen)
            if not _equal(expected, seen):
                diffs.append(FieldDiff(name, expected, observed[name]))
        declared = set(fingerprint_fields())
        for name in sorted(k for k in observed if k not in declared):
            diffs.append(FieldDiff(name, UNDECLARED, observed[name]))
        return tuple(diffs)

    def assert_matches(self, observed: Mapping[str, Any]) -> None:
        """Raise `RecordDrift` on any difference. Nothing is warned about."""
        diffs = self.compare(observed)
        if diffs:
            raise RecordDrift(diffs)


def fingerprint_fields() -> tuple[str, ...]:
    """Declaration order, taken from the dataclass rather than from a second list.

    A hand-maintained field list beside a dataclass is a list that will disagree with it,
    and the direction it disagrees in is a field that stops being hashed.
    """
    return tuple(f.name for f in fields(RunFingerprint))


def _equal(expected: Any, observed: Any) -> bool:
    """Equality that does not let Python's bool/int identity paper over a difference."""
    if isinstance(expected, bool) != isinstance(observed, bool):
        return False
    return expected == observed
