"""The bridge between `ResultStampV1` and its published vector (ADR-0004, ADR-0006).

`harness/acs/gen_vectors.py` writes the stamp vectors by hand, in the neutral tagged form,
importing nothing from `src` — a specification generated from the implementation it
specifies states nothing. That independence leaves a gap: the vector pins the *encoding* of
a ten-key document, and nothing pins that `ResultStampV1.to_acs()` actually emits that
document. CI's byte-identical-regeneration gate would keep passing while the model drifted
away from its own specification.

This file closes it, from the one place that may import both trees. It rebuilds each
`stamp-v1-*` / `stamped-result-v1-*` / `upstream-config-v1` case from the model and asserts
the canonical bytes and the digest match the committed vector exactly.

**Vacuity control.** Every assertion below is per-case, so an empty or renamed vector
section would pass all of them for free. `test_the_stamp_vector_section_is_not_empty` fails
on a count of zero, and `test_every_expected_case_id_is_present` fails when a case this file
knows about has left `vectors.json` — a check that scanned nothing fails rather than
passing (D57).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

import pytest

from metrics.reasons import Reason
from metrics.value import defined, undefined
from provenance.encoding import canonicalize
from provenance.stamp import (
    RECORD_TYPE_STAMP,
    RECORD_TYPE_STAMPED_RESULT,
    AssumptionSet,
    ResultStampV1,
    StampedResult,
    Tolerance,
)
from provenance.upstream import (
    RECORD_TYPE_UPSTREAM_CONFIG,
    CorpusUpstream,
    SimulatedUpstream,
    UnknownReason,
    UnknownUpstream,
    UpstreamToolchain,
    unknown_upstream,
)
from provenance.verify import verify_stamp

VECTORS: Final = json.loads(
    (Path(__file__).resolve().parents[1] / "harness" / "acs" / "vectors.json").read_text()
)

COMMIT: Final = "0" * 39 + "a"

CORPUS: Final = CorpusUpstream(
    corpus_name="CommonRoad",
    corpus_version="2020a",
    scenario_id="ZAM_Urban-7_1_S-2",
    corpus_digest="2" * 64,
)

_BASELINE_WITH_ENTRIES: Final = AssumptionSet(
    name="baseline",
    version="1.0.0",
    entries={"horizon_s": 10.0, "extrapolation": "constant_velocity"},
)
_BASELINE_EMPTY: Final = AssumptionSet(name="baseline", version="1.0.0")
_TOLERANCE: Final = Tolerance(atol=1e-9, rtol=1e-6)


def _stamp(
    upstream: UpstreamToolchain, *, assumptions: AssumptionSet = _BASELINE_EMPTY
) -> ResultStampV1:
    return ResultStampV1(
        metric_id="ttc",
        metric_version="1.0.0",
        code_commit=COMMIT,
        assumption_set=assumptions,
        input_hash="1" * 64,
        tolerance=_TOLERANCE,
        upstream=upstream,
    )


# The cases this file claims to cover, and the model that must reproduce each. Keyed by
# vector id so a renamed or deleted vector fails loudly rather than silently reducing
# coverage — the failure mode that let an oracle image tag stop being checked.
STAMP_CASES: Final[dict[str, ResultStampV1]] = {
    "stamp-v1-corpus": _stamp(CORPUS, assumptions=_BASELINE_WITH_ENTRIES),
    "stamp-v1-simulated-minimal": _stamp(
        SimulatedUpstream(tool_name="ExampleSim", tool_version="2024 R2", config_digest="3" * 64)
    ),
    "stamp-v1-simulated-full": _stamp(
        SimulatedUpstream(
            tool_name="ExampleSim",
            tool_version="2024 R2",
            config_digest="3" * 64,
            tool_build="7.3.0-hotfix4",
            config_ref="s3://alfred-configs/run-41.yaml",
        )
    ),
    "stamp-v1-unknown": _stamp(unknown_upstream(UnknownReason.UPSTREAM_NOT_RECORDED)),
}

RESULT_CASES: Final[dict[str, StampedResult]] = {
    "stamped-result-v1-defined": StampedResult(value=defined(2.4), stamp=_stamp(CORPUS)),
    "stamped-result-v1-undefined": StampedResult(
        value=undefined(Reason.NO_CONFLICT_AREA), stamp=_stamp(CORPUS)
    ),
}


def _encode_case(case_id: str) -> dict[str, str]:
    found = [c for c in VECTORS["encode"] if c["id"] == case_id]
    if not found:
        pytest.fail(f"vector {case_id!r} is absent from vectors.json")
    return found[0]


# ------------------------------------------------------------------- vacuity controls


def test_the_stamp_vector_section_is_not_empty() -> None:
    """A count of zero fails. Every other test here is per-case and would pass on nothing."""
    covered = [c for c in VECTORS["encode"] if c["record_type"].startswith("alfred.")]
    assert len(covered) >= len(STAMP_CASES) + len(RESULT_CASES) + 1


def test_every_expected_case_id_is_present() -> None:
    present = {c["id"] for c in VECTORS["encode"]}
    expected = set(STAMP_CASES) | set(RESULT_CASES) | {"upstream-config-v1"}
    assert expected <= present, f"vectors gone missing: {sorted(expected - present)}"


# ------------------------------------------------------------ the model matches the vector


@pytest.mark.parametrize("case_id", sorted(STAMP_CASES))
def test_the_model_reproduces_the_published_stamp_vector(case_id: str) -> None:
    vector = _encode_case(case_id)
    stamp = STAMP_CASES[case_id]

    assert vector["record_type"] == RECORD_TYPE_STAMP
    # Bytes first, digest second. A digest match with different bytes is impossible, but the
    # byte comparison is what a reader can act on when it fails.
    assert canonicalize(stamp.to_acs()).hex() == vector["canonical_hex"]
    assert stamp.digest() == vector["sha256"]


@pytest.mark.parametrize("case_id", sorted(RESULT_CASES))
def test_the_model_reproduces_the_published_stamped_result_vector(case_id: str) -> None:
    vector = _encode_case(case_id)
    result = RESULT_CASES[case_id]
    assert vector["record_type"] == RECORD_TYPE_STAMPED_RESULT
    assert canonicalize(result.to_acs()).hex() == vector["canonical_hex"]
    assert result.content_hash() == vector["sha256"]


def test_the_upstream_config_record_type_is_the_allocated_one() -> None:
    """ADR-0006 allocates `alfred.upstream_config`; the vector must use that exact tag."""
    assert _encode_case("upstream-config-v1")["record_type"] == RECORD_TYPE_UPSTREAM_CONFIG


# ----------------------------------------------- the published digest actually verifies


@pytest.mark.parametrize("case_id", sorted(STAMP_CASES))
def test_the_published_vector_verifies_through_the_two_stage_read(case_id: str) -> None:
    """The reader and the specification agree, not merely the writer and the specification."""
    vector = _encode_case(case_id)
    result = verify_stamp(STAMP_CASES[case_id].to_acs(), vector["sha256"])
    assert result.verified, result.detail
    assert result.document_schema_version == 1


def test_the_ten_keys_are_exactly_the_ten_keys() -> None:
    """ADR-0006 freezes the key set. Spelled out rather than counted."""
    assert sorted(STAMP_CASES["stamp-v1-corpus"].to_acs()) == [
        "acs_version",
        "assumption_set",
        "code_commit",
        "input_hash",
        "metric_id",
        "metric_version",
        "reason_codebook_version",
        "stamp_schema_version",
        "tolerance",
        "upstream",
    ]


def test_the_unknown_arm_reason_travels_as_a_name() -> None:
    document = STAMP_CASES["stamp-v1-unknown"].to_acs()
    arm = document["upstream"]
    assert isinstance(arm, dict)
    assert arm["reason"] == UnknownReason.UPSTREAM_NOT_RECORDED.name
    assert b"UPSTREAM_NOT_RECORDED" in canonicalize(document)


def test_an_absent_optional_is_not_an_emitted_null() -> None:
    """`absent` and `declared blank` must not canonicalize to the same bytes."""
    minimal = STAMP_CASES["stamp-v1-simulated-minimal"].to_acs()
    arm = minimal["upstream"]
    assert isinstance(arm, dict)
    assert "tool_build" not in arm
    assert "config_ref" not in arm
    assert minimal != STAMP_CASES["stamp-v1-simulated-full"].to_acs()


def test_the_unknown_arm_is_the_only_one_that_fails_the_storage_duty() -> None:
    for case_id, stamp in STAMP_CASES.items():
        expected = not isinstance(stamp.upstream, UnknownUpstream)
        assert stamp.discharges_storage_duty is expected, case_id
