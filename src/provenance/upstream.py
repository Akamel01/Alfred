"""`UpstreamToolchain` — who produced the trajectory, and under what setup (ADR-0006).

The stamp names *Alfred's* `metric_version` and `code_commit`. D48's buyer's mandated
duty under EU 2022/1426 Annex III Part 4 is storage of the **upstream** toolchain version
and traceability from M&S output back to setup. An artifact digest of a trajectory file is
neither: it identifies the output, not the producer.

```json
{"kind": "simulated", "tool_name": "...", "tool_version": "...", "config_digest": "..."}
{"kind": "corpus",    "corpus_name": "...", "corpus_version": "...", "scenario_id": "..."}
{"kind": "unknown",   "reason": "UPSTREAM_NOT_RECORDED"}
```

The third use of the tagged-union pattern, after three-valued verdicts and `MetricValue`.
Three claims that read informally as "no simulator" are held apart, and **absence is
forbidden**: no default, no `| None`. An optional provenance field is the specific weakness
ADR-0006 rejects SSP Layered Standard Traceability for inheriting.

**Alfred's container never observes the simulator.** Every field on the `simulated` arm is
*declared* by whoever ran the run. The stamp makes the declaration tamper-evident because
it sits inside the digest; it does not make it true. D30's phrase "upstream toolchain
identity" reads "as declared" (ADR-0006, "The honest limit").
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Annotated, Final, Literal

from pydantic import Field, TypeAdapter, field_validator

from domain.base import AlfredModel
from domain.errors import ContractViolation

__all__ = [
    "RECORD_TYPE_UPSTREAM_CONFIG",
    "UPSTREAM_TOOLCHAIN_ADAPTER",
    "CorpusUpstream",
    "SimulatedUpstream",
    "UnknownReason",
    "UnknownUpstream",
    "UpstreamToolchain",
    "corpus_upstream",
    "unknown_upstream",
]

# The domain-separation tag allocated by ADR-0006 for the canonicalized upstream
# configuration document. Distinct from `alfred.result_stamp`: the digest commits to a
# configuration, and the configuration is not a stamp.
RECORD_TYPE_UPSTREAM_CONFIG: Final[str] = "alfred.upstream_config"

_SHA256_HEX: Final = re.compile(r"\A[0-9a-f]{64}\Z")


class UnknownReason(Enum):
    """Why the upstream toolchain could not be determined.

    A small closed set of **names**. ADR-0002's discipline: names on the wire, never
    integers, never reused, never repurposed. It needs no version of its own and no
    `stamp_schema_version` bump to grow, because adding an allowed value changes no
    existing stamp's digest — only removing or repurposing a name would, and both are
    forbidden.

    A verifier meeting a name it does not know applies ADR-0002's `255 UNKNOWN_CODE` rule:
    the digest still verifies, because it is computed over the name string — but the
    verifier **must not** report "upstream known".
    """

    UPSTREAM_NOT_RECORDED = "UPSTREAM_NOT_RECORDED"
    UPSTREAM_TOOL_UNDECLARED = "UPSTREAM_TOOL_UNDECLARED"
    UPSTREAM_CONFIG_UNAVAILABLE = "UPSTREAM_CONFIG_UNAVAILABLE"


def _digest(value: str) -> str:
    if not _SHA256_HEX.match(value):
        raise ContractViolation(f"digest must be 64 lowercase hex, got {value!r}")
    return value


class SimulatedUpstream(AlfredModel):
    """A simulator produced the trajectory. Identity plus setup, both required."""

    kind: Literal["simulated"] = "simulated"

    tool_name: str = Field(min_length=1, description="The simulator's identity, as declared.")

    # Free-form, and **deliberately not** validated as MAJOR.MINOR.PATCH. `metric_version`
    # is semverish because Alfred controls it; a vendor ships `2024 R2` or `7.3.0-hotfix4`,
    # and forcing a grammar here would force a lie into the one field the regulation names.
    # The asymmetry against `ResultStampV1.metric_version` is deliberate — do not unify them.
    tool_version: str = Field(min_length=1, description="As the vendor writes it. No grammar.")

    config_digest: str = Field(
        description=(
            "ACS-1 digest under RECORD_TYPE_UPSTREAM_CONFIG over the canonicalized "
            "configuration document. A real run's configuration is large and vendor-shaped; "
            "inlining it would put an un-normalizable document inside every stamp's preimage."
        )
    )

    tool_build: str | None = Field(
        default=None, description="Commit or build id where the vendor publishes one; most do not."
    )

    # Optional in the schema, required by policy wherever re-derivation is claimed. The
    # digest commits; the ref retrieves. A digest with no retrievable preimage proves
    # nothing was altered and lets nobody reproduce anything.
    config_ref: str | None = Field(default=None, description="Locator for the stored config.")

    @field_validator("config_digest")
    @classmethod
    def _config_digest(cls, value: str) -> str:
        return _digest(value)

    @field_validator("tool_build", "config_ref")
    @classmethod
    def _no_empty_optional(cls, value: str | None) -> str | None:
        # An empty string is not "absent"; it is a declared blank, which reads as a value
        # to every consumer and to the digest. Absence has a spelling already.
        if value is not None and not value.strip():
            raise ContractViolation("an optional upstream field is absent or non-blank, not empty")
        return value


class CorpusUpstream(AlfredModel):
    """The trajectory came from a published corpus, not from a simulator run.

    "Not applicable" is expressed as this *positive* arm, never as a negative tag. A bare
    `{"kind":"not_applicable"}` is indistinguishable from laziness: a reviewer asking "not
    applicable because what?" gets nothing back. This arm names what *is* there, so the
    claim is checkable.
    """

    kind: Literal["corpus"] = "corpus"
    corpus_name: str = Field(min_length=1)
    corpus_version: str = Field(min_length=1)
    scenario_id: str = Field(min_length=1)
    corpus_digest: str

    @field_validator("corpus_digest")
    @classmethod
    def _corpus_digest(cls, value: str) -> str:
        return _digest(value)


class UnknownUpstream(AlfredModel):
    """There *was* an upstream toolchain and Alfred could not determine it.

    A defect-grade state: a stamp carrying this arm does not discharge the buyer's storage
    duty. `ResultStampV1.discharges_storage_duty` is `False` for it, and the reason is
    mandatory — there is no bare constructor and no default, so the arm cannot be reached
    by accident. That is the whole difference between this and the `| None` ADR-0006 refuses.
    """

    kind: Literal["unknown"] = "unknown"
    reason: UnknownReason


type UpstreamToolchain = Annotated[
    SimulatedUpstream | CorpusUpstream | UnknownUpstream, Field(discriminator="kind")
]

UPSTREAM_TOOLCHAIN_ADAPTER: TypeAdapter[UpstreamToolchain] = TypeAdapter(UpstreamToolchain)


# ------------------------------------------------------------------- constructors


def corpus_upstream(
    *, corpus_name: str, corpus_version: str, scenario_id: str, corpus_digest: str
) -> CorpusUpstream:
    return CorpusUpstream(
        corpus_name=corpus_name,
        corpus_version=corpus_version,
        scenario_id=scenario_id,
        corpus_digest=corpus_digest,
    )


def unknown_upstream(reason: UnknownReason) -> UnknownUpstream:
    """The only way to build the `unknown` arm, and it will not let you omit the reason.

    Keyword-free and typed: a caller cannot reach this arm by passing a string it made up,
    and cannot reach it at all without naming which of the three failures occurred.
    """
    return UnknownUpstream(reason=reason)
