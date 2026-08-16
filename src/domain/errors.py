"""Error taxonomy (docs/tier1/failure-semantics.md).

Five classes, and every raised error type maps to exactly one. An unclassified
error is itself a contract violation and halts the run, so the mapping is a
property the test suite asserts rather than a convention.

Degeneracy is *not* an error. A scenario with no conflict is ordinary input and
is answered with `Undefined(reason)`; exceptions are reserved for caller bugs —
wrong units, unsorted timestamps, mismatched array lengths.
"""

from __future__ import annotations

from enum import Enum

__all__ = [
    "AlfredError",
    "ContractViolation",
    "ErrorClass",
    "ExhaustionError",
    "InfrastructureError",
    "LengthMismatch",
    "PolicyViolation",
    "SelfPairing",
    "UnitsViolation",
    "UnsortedTimestamps",
    "error_class_of",
]


class ErrorClass(Enum):
    """The five taxonomy classes. `value` is the stable wire name."""

    INFRASTRUCTURE = "infrastructure"
    POLICY_VIOLATION = "policy_violation"
    CRITERION_FAILURE = "criterion_failure"
    EXHAUSTION = "exhaustion"
    CONTRACT_VIOLATION = "contract_violation"


class AlfredError(Exception):
    """Base for every error Alfred raises deliberately.

    Subclasses declare `error_class`; `error_class_of` refuses anything that does
    not, which is what makes "unclassified error halts the run" checkable.
    """

    error_class: ErrorClass = ErrorClass.CONTRACT_VIOLATION


class InfrastructureError(AlfredError):
    """Model server down, DB connection lost, disk full. Harness-owned."""

    error_class = ErrorClass.INFRASTRUCTURE


class PolicyViolation(AlfredError):
    """Protected-path write, non-allowlisted egress, held-out read from the agent
    role. Terminates the run and is never retried: retrying is indistinguishable
    from searching for a formulation the check does not catch."""

    error_class = ErrorClass.POLICY_VIOLATION


class ExhaustionError(AlfredError):
    """Turn cap, wall-clock cap, iteration cap, no monotone progress."""

    error_class = ErrorClass.EXHAUSTION


class ContractViolation(AlfredError):
    """A caller bug. Never used to signal degeneracy."""

    error_class = ErrorClass.CONTRACT_VIOLATION


class UnitsViolation(ContractViolation):
    """A quantity supplied in the wrong unit, or a non-finite input coordinate."""


class UnsortedTimestamps(ContractViolation):
    """E20 — unsorted or duplicate timestamps."""


class LengthMismatch(ContractViolation):
    """Parallel arrays of differing length."""


class SelfPairing(ContractViolation):
    """E25 — ego paired against itself."""


def error_class_of(error: BaseException) -> ErrorClass:
    """The taxonomy class of `error`.

    Raises `ContractViolation` for anything outside the taxonomy, which is the
    behaviour the "no unclassified error" rule requires: an unknown error is not
    silently bucketed into a plausible class.
    """
    if isinstance(error, AlfredError):
        return error.error_class
    raise ContractViolation(f"error type is outside the taxonomy: {type(error).__name__}")
