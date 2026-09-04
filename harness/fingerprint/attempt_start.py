"""Check A: the model that answers is the model the fingerprint declared, asserted at start.

Ticket #46 specified two enforcement checks for model routing. **Check P** — static policy
conformance — shipped as `scripts/lint_model_routing.py`. **Check A** — the fail-closed
assertion at attempt start — did not. `FactoryFingerprint.assert_matches` existed and
nothing called it, so P verified that two protected files agreed with each other while
nothing verified that reality agreed with either.

The rule is `loaded_context_length`'s, and the run-instrumentation specification already
states why in general form:

    a fingerprint field the server can change unobserved is not a fingerprint unless
    something checks it

and, for that one field, what follows:

    **Asserted against the fingerprint, not read from it.** … Mismatch is fail-closed: the
    attempt does not start.

Every field on a `FactoryFingerprint` has the same exposure and a worse one. A lane is a
process on a machine this side owns; an API-served model is a routing decision made by
somebody else, and `provider`, `model_id`, `api_version` and `routing_key` can all move
between one attempt and the next with nothing errored and nothing logged. An autonomy
grant is *"X% merge, Y wall-clock per success, on fingerprint Z"*, suspended by any
fingerprint change — so a substitution nobody observed does not suspend the grant, it
silently reassigns it to a model that never earned it.

------------------------------------------------------------------ prevented *and* visible

Refusing is half the job. A model swapped underneath a run that is merely refused shows up
as an attempt that did not happen, which is indistinguishable from an attempt that was
never scheduled. So the refusal carries a record: an `escalation` with
`primary_cause = fingerprint_drift`, `evaluated_at_turn = None` because no turn occurred,
and an `attempt_bundle_ref` over the canonical form of the differences. That bundle is what
makes the substitution auditable after the fact rather than only survivable in the moment.

Both fields are additions to the run-instrumentation specification's closed sets, recorded
in ADR-0054.

Inspector machinery (D20). This module reads no configuration and writes no row; it
compares two mappings and builds the refusal the caller records.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final, Mapping

from harness.acs.acs1 import acs_sha256
from harness.fingerprint.factory import FactoryFingerprint
from harness.fingerprint.record import FieldDiff, RecordDrift, UNDECLARED

#: The escalation cause this refusal carries. Added to the specification's closed set by
#: ADR-0054, because none of the eleven existing causes fits: `harness_fault` says this
#: side broke, and the whole point of the finding is that this side worked — it looked,
#: and what it found was somebody else's substitution.
CAUSE: Final = "fingerprint_drift"

#: The record type of the refusal bundle. Distinct from `factory_fingerprint`, because
#: ACS-1 takes the record type as its domain separator (ADR-0003): a bundle and a
#: fingerprint that coincidentally serialized alike must still hash apart.
BUNDLE_RECORD_TYPE: Final = "attempt_refusal_bundle"


class AttemptRefused(Exception):
    """The attempt does not start. Carries the record the caller must write.

    An exception rather than a returned status, deliberately: a returned status can be
    ignored by a caller that forgot to read it, and a caller that forgets this one starts
    an attempt on an undeclared model. Fail-closed means the default path on a mistake is
    refusal, and only a raise gives that.
    """

    def __init__(self, refusal: Refusal) -> None:
        self.refusal = refusal
        super().__init__(
            f"attempt refused — {refusal.summary}. The declared fingerprint is not what "
            "answered, so an attempt started here would be measured against an identity "
            "it does not have."
        )


@dataclass(frozen=True)
class Refusal:
    """The `escalation` record a refused start emits.

    Field names are the specification's, not this module's invention: `primary_cause`,
    `also_satisfied`, `evaluated_at_turn` and `attempt_bundle_ref` are the four the
    `escalation` record declares. `evaluated_at_turn` is `None` and that is the amendment
    ADR-0054 records — a refusal happens before turn zero, and writing `0` would say the
    first turn ran and reached this, which is a different event.
    """

    differences: tuple[FieldDiff, ...]
    attempt_bundle_ref: str
    primary_cause: str = CAUSE
    also_satisfied: tuple[str, ...] = ()
    evaluated_at_turn: int | None = None

    @property
    def summary(self) -> str:
        return "; ".join(str(diff) for diff in self.differences)

    def as_mapping(self) -> dict[str, Any]:
        return {
            "primary_cause": self.primary_cause,
            "also_satisfied": list(self.also_satisfied),
            "evaluated_at_turn": self.evaluated_at_turn,
            "attempt_bundle_ref": self.attempt_bundle_ref,
        }


def _bundle(declared: FactoryFingerprint, differences: tuple[FieldDiff, ...]) -> dict[str, Any]:
    """The structured bundle the escalation's `attempt_bundle_ref` addresses.

    It carries the declared fingerprint's hash rather than its fields. The hash is the
    identity, the fields are recoverable from the record that owns them, and copying them
    here would make a second place where a fingerprint's contents are written down.

    `UNDECLARED` is rendered as a string rather than dropped. A field the observation
    carried and the record never declared is the second direction of the comparison, and a
    bundle that omitted it would record "the model changed" for the case where the
    configuration surface *grew*, which is a different and more alarming event.
    """
    return {
        "declared_fingerprint_sha256": declared.fingerprint_sha256,
        "differences": [
            {
                "field": diff.field,
                "expected": "<undeclared>" if diff.expected is UNDECLARED else diff.expected,
                "observed": "<undeclared>" if diff.observed is UNDECLARED else diff.observed,
            }
            for diff in differences
        ],
    }


def begin_attempt(
    declared: FactoryFingerprint, observed: Mapping[str, Any]
) -> FactoryFingerprint:
    """Check A. Returns the declared record on a match; raises `AttemptRefused` otherwise.

    The return value is the declared record and not a new one, because there is nothing to
    build: agreement means the observation *is* the record, and handing back a second object
    would invite a caller to record the observation instead of the declaration. What the
    attempt is measured against is what was declared.
    """
    try:
        declared.assert_matches(observed)
    except RecordDrift as drift:
        differences = drift.differences
        bundle = _bundle(declared, differences)
        raise AttemptRefused(
            Refusal(
                differences=differences,
                attempt_bundle_ref=acs_sha256(BUNDLE_RECORD_TYPE, bundle),
            )
        ) from drift
    return declared
