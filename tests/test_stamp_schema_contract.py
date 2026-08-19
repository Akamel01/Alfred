"""ADR-0006's enforcement clauses, as executable checks with their own controls.

The ADR's Consequences list names four things CI must assert:

1. `stamp_schema_version` is present, top-level and integer in every emitted stamp.
2. No stamp model makes an `upstream` arm's required field optional.
3. Every superseded schema version's vectors still pass.
4. The record type is not versioned.

(3) is discharged by `tests/test_stamp_v1_vectors.py` together with the byte-identical
regeneration gate; the other three are here. Each is written as a function over the
encoder registry, and each ships a **planted-violation control** — a deliberately wrong model
handed to the same function, which must be rejected. A check with no planted violation
reports the same thing whether it works or not, which is the argument
`scripts/lint_verdict_boundary.py --self-test` already makes for itself.

Every check also fails on an empty scan. A check that examined zero models is not a passing
check (D57).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final, Literal

import pytest
from pydantic import ValidationError

from domain.base import AlfredModel
from domain.errors import ContractViolation
from provenance.encoding import AcsValue, canonicalize
from provenance.stamp import RECORD_TYPE_STAMP, AssumptionSet, ResultStampV1, Tolerance
from provenance.upstream import (
    CorpusUpstream,
    SimulatedUpstream,
    UnknownReason,
    UnknownUpstream,
    unknown_upstream,
)
from provenance.verify import (
    HIGHEST_KNOWN_SCHEMA,
    SCHEMA_VERSION_KEY,
    encoder_for,
    known_schema_versions,
)

REPO_ROOT: Final = Path(__file__).resolve().parents[1]
SRC: Final = REPO_ROOT / "src"

_ARMS: Final = (SimulatedUpstream, CorpusUpstream, UnknownUpstream)

# The fields ADR-0006 marks Required on each arm. Restated here rather than read from the
# models: a test that derives its expectation from its subject asserts nothing.
_REQUIRED_BY_ARM: Final[dict[str, frozenset[str]]] = {
    "simulated": frozenset({"tool_name", "tool_version", "config_digest"}),
    "corpus": frozenset({"corpus_name", "corpus_version", "scenario_id", "corpus_digest"}),
    "unknown": frozenset({"reason"}),
}

_OPTIONAL_BY_ARM: Final[dict[str, frozenset[str]]] = {
    "simulated": frozenset({"tool_build", "config_ref"}),
    "corpus": frozenset(),
    "unknown": frozenset(),
}


def _sample(encoder: type[ResultStampV1]) -> ResultStampV1:
    return encoder(
        metric_id="ttc",
        metric_version="1.0.0",
        code_commit="0" * 39 + "a",
        assumption_set=AssumptionSet(name="baseline", version="1.0.0"),
        input_hash="1" * 64,
        tolerance=Tolerance(atol=1e-9, rtol=1e-6),
        upstream=CorpusUpstream(
            corpus_name="CommonRoad",
            corpus_version="2020a",
            scenario_id="ZAM_Urban-7_1_S-2",
            corpus_digest="2" * 64,
        ),
    )


# ============================================================ 1. the pinned version key


class SchemaVersionViolation(AssertionError):
    """The planted-violation controls below expect exactly this."""


def check_schema_version_is_locatable(document: dict[str, AcsValue]) -> None:
    """The check, factored out so a deliberately wrong document can be fed to it."""
    if SCHEMA_VERSION_KEY not in document:
        raise SchemaVersionViolation(f"{SCHEMA_VERSION_KEY!r} is not a key of the document")
    value = document[SCHEMA_VERSION_KEY]
    if isinstance(value, bool) or not isinstance(value, int):
        raise SchemaVersionViolation(f"{SCHEMA_VERSION_KEY!r} is {type(value).__name__}, not int")
    if value < 1:
        raise SchemaVersionViolation(f"{SCHEMA_VERSION_KEY!r} is {value}, below 1")
    # Inside the preimage. A schema version outside the digest is a claim anyone can rewrite.
    if SCHEMA_VERSION_KEY.encode() not in canonicalize(document):
        raise SchemaVersionViolation(f"{SCHEMA_VERSION_KEY!r} is not in the canonical bytes")


def test_the_encoder_registry_is_not_empty() -> None:
    """D57. Every check below iterates the registry and would pass on an empty one."""
    versions = known_schema_versions()
    assert len(versions) >= 1
    assert max(versions) == HIGHEST_KNOWN_SCHEMA


@pytest.mark.parametrize("version", known_schema_versions())
def test_every_emitted_stamp_carries_the_pinned_version_key(version: int) -> None:
    encoder = encoder_for(version)
    assert encoder is not None
    document = _sample(encoder).to_acs()
    check_schema_version_is_locatable(document)
    assert document[SCHEMA_VERSION_KEY] == version


@pytest.mark.parametrize(
    ("planted", "why"),
    [
        ({"metric_id": "ttc"}, "the key is absent"),
        ({SCHEMA_VERSION_KEY: "1"}, "the version is a string"),
        ({SCHEMA_VERSION_KEY: True}, "the version is a bool, which is an int in Python"),
        ({SCHEMA_VERSION_KEY: 0}, "the version is below 1"),
        ({"stamp": {SCHEMA_VERSION_KEY: 1}}, "the version is nested rather than top-level"),
    ],
)
def test_the_version_check_rejects_a_planted_violation(
    planted: dict[str, AcsValue], why: str
) -> None:
    """The control. Without it this check reports the same thing whether it works or not."""
    with pytest.raises(SchemaVersionViolation):
        check_schema_version_is_locatable(planted)
        pytest.fail(f"the check accepted a document where {why}")


def test_the_version_is_pinned_by_the_model_not_merely_defaulted() -> None:
    """A model that accepted any integer would let a v1 document claim to be v2."""
    with pytest.raises((ContractViolation, ValidationError)):
        _ = ResultStampV1(
            metric_id="ttc",
            metric_version="1.0.0",
            code_commit="0" * 39 + "a",
            assumption_set=AssumptionSet(name="baseline", version="1.0.0"),
            input_hash="1" * 64,
            tolerance=Tolerance(atol=1e-9, rtol=1e-6),
            upstream=unknown_upstream(UnknownReason.UPSTREAM_NOT_RECORDED),
            stamp_schema_version=2,
        )


# ==================================================== 2. no required arm field is optional


class OptionalityViolation(AssertionError):
    pass


def check_required_fields_are_required(arm: type[AlfredModel], required: frozenset[str]) -> None:
    fields = arm.model_fields
    missing = required - set(fields)
    if missing:
        raise OptionalityViolation(f"{arm.__name__} is missing {sorted(missing)}")
    for name in sorted(required):
        if not fields[name].is_required():
            raise OptionalityViolation(
                f"{arm.__name__}.{name} is optional; ADR-0006 rejects an optional "
                "provenance field, which is the specific weakness it declines SSP for"
            )


@pytest.mark.parametrize("arm", _ARMS, ids=lambda a: a.__name__)
def test_no_arm_makes_a_required_field_optional(arm: type[AlfredModel]) -> None:
    kind = str(arm.model_fields["kind"].default)
    required = _REQUIRED_BY_ARM[kind]
    assert required, f"{kind} has no required fields declared in this test"
    check_required_fields_are_required(arm, required)


@pytest.mark.parametrize("arm", _ARMS, ids=lambda a: a.__name__)
def test_the_optional_set_is_exactly_what_the_adr_permits(arm: type[AlfredModel]) -> None:
    """An arm that grew a new optional field silently is the drift this catches."""
    kind = str(arm.model_fields["kind"].default)
    actual_optional = {
        name
        for name, field in arm.model_fields.items()
        if name != "kind" and not field.is_required()
    }
    assert actual_optional == set(_OPTIONAL_BY_ARM[kind])


def test_the_optionality_check_rejects_a_planted_violation() -> None:
    class LaxSimulated(AlfredModel):
        kind: Literal["simulated"] = "simulated"
        tool_name: str = "ExampleSim"
        tool_version: str | None = None
        config_digest: str | None = None

    with pytest.raises(OptionalityViolation):
        check_required_fields_are_required(LaxSimulated, _REQUIRED_BY_ARM["simulated"])


def test_the_optionality_check_rejects_a_missing_field() -> None:
    class TruncatedCorpus(AlfredModel):
        kind: Literal["corpus"] = "corpus"
        corpus_name: str = "CommonRoad"

    with pytest.raises(OptionalityViolation):
        check_required_fields_are_required(TruncatedCorpus, _REQUIRED_BY_ARM["corpus"])


# ============================================================ 3. the record type is not versioned


def test_the_stamp_record_type_carries_no_version() -> None:
    """Cross-version collision is complete from the content; a second place to bump is a
    second place to drift (ADR-0006, "Cross-version collision is structurally impossible")."""
    assert RECORD_TYPE_STAMP == "alfred.result_stamp"
    assert not RECORD_TYPE_STAMP.endswith(tuple(f".v{n}" for n in range(1, 10)))
    assert not any(character.isdigit() for character in RECORD_TYPE_STAMP)


def test_no_versioned_record_type_appears_anywhere_in_the_product_tree() -> None:
    scanned = 0
    offenders: list[str] = []
    for path in sorted(SRC.rglob("*.py")):
        scanned += 1
        if f"{RECORD_TYPE_STAMP}.v" in path.read_text():
            offenders.append(str(path.relative_to(REPO_ROOT)))
    # D57: a scan of zero files is not a pass.
    assert scanned > 0, "the product tree scan found no files"
    assert not offenders, f"a versioned record type appears in {offenders}"


def test_the_two_stamp_record_types_are_distinct_from_the_upstream_one() -> None:
    vectors = json.loads((REPO_ROOT / "harness" / "acs" / "vectors.json").read_text())
    tags = {c["record_type"] for c in vectors["encode"] if c["record_type"].startswith("alfred.")}
    assert {"alfred.result_stamp", "alfred.stamped_result", "alfred.upstream_config"} <= tags


# ==================================== the unknown arm is visible rather than silent (decision 6)


def test_the_unknown_arm_cannot_be_reached_without_naming_a_reason() -> None:
    with pytest.raises(ValidationError):
        UnknownUpstream()  # pyright: ignore[reportCallIssue] — the missing reason is the point


def test_the_unknown_arm_refuses_a_reason_outside_the_closed_set() -> None:
    with pytest.raises(ValidationError):
        UnknownUpstream(reason="UPSTREAM_WHATEVER")  # pyright: ignore[reportArgumentType] — an invented name is the point


def test_no_product_module_constructs_the_unknown_arm() -> None:
    """`unknown` is defect-grade. Nothing in the factory may reach for it by default.

    The defining module is excluded because it must name the class to declare it. Every
    other product module naming it is a path that can silently emit a stamp which does not
    discharge the buyer's storage duty.
    """
    definer = SRC / "provenance" / "upstream.py"
    scanned = 0
    offenders: list[str] = []
    for path in sorted(SRC.rglob("*.py")):
        if path == definer:
            continue
        scanned += 1
        text = path.read_text()
        if "UnknownUpstream(" in text or "unknown_upstream(" in text:
            offenders.append(str(path.relative_to(REPO_ROOT)))
    assert scanned > 0, "the product tree scan found no files besides the definer"
    assert not offenders, f"the unknown upstream arm is constructed in {offenders}"


def test_the_reason_codebook_is_a_closed_set_of_names() -> None:
    """Names on the wire, never integers, never reused, never repurposed (ADR-0002)."""
    assert {member.name for member in UnknownReason} == {
        "UPSTREAM_NOT_RECORDED",
        "UPSTREAM_TOOL_UNDECLARED",
        "UPSTREAM_CONFIG_UNAVAILABLE",
    }
    for member in UnknownReason:
        assert member.value == member.name
