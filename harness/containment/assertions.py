"""Three outcomes for a containment assertion, and the third is the dangerous one.

`passed` and `failed` are obvious. **`not_executed` is the value the whole vocabulary
exists for.** An assertion that did not run has not passed, and the single most common way
a containment control fails is by not running at all — a probe that raised before it
started, an assertion skipped because its precondition was missing, a check whose result
was never collected. Collapsing it into `passed` turns a missing control into a green one;
collapsing it into `failed` is safe but loses the distinction an operator needs to fix it.

So the vocabulary is three-valued and `require_all_passed` treats `not_executed` exactly
as `failed`, which is F25 stated as code.

**An assertion may also pass vacuously, and this module cannot detect that.** ADR-0007:
an assertion resting on a *misnamed* config key or event class reports `passed` while the
control it names does nothing — executed, passed, and vacuous. That is a third outcome
beyond these three and it is not representable here, deliberately: representing it would
require the assertion to know something it cannot know from inside. What this module can
do is carry the `premise_verified` flag so a report says which of its assertions rest on a
premise nobody has checked first-hand, and `AssertionReport.unverified_premises` is what a
reader consults before quoting a green report as evidence.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum


class AssertionOutcome(Enum):
    PASSED = "passed"
    FAILED = "failed"
    # Never read as passed. F25.
    NOT_EXECUTED = "not_executed"


class ContainmentFailure(RuntimeError):
    """A required assertion did not pass. The run does not start."""


@dataclass(frozen=True)
class Assertion:
    """One containment claim and what became of it.

    `premise_verified=False` marks an assertion whose subject has not been inspected
    first-hand — a config key read from documentation rather than from source, an event
    class named in a research note. Such an assertion passes harmlessly if the feature
    does not exist, which costs nothing; what it cannot do is distinguish that from a
    feature that exists under a different name, which costs every measurement taken under
    it.
    """

    assertion_id: str
    outcome: AssertionOutcome
    detail: str
    premise_verified: bool = True
    # The values the check actually read, as strings, keyed by what they are. `detail` is
    # prose for a human; this is for `reassert.compare`, which needs to tell "the same
    # container" from "a container of the same kind" — a distinction no outcome carries and
    # no prose can be diffed for. Empty means the check reported none, which `value_blind`
    # names rather than reading as "nothing changed".
    #
    # A dict on a frozen dataclass: `Assertion` is not hashable in practice and nothing in
    # this tree hashes one. Kept as a Mapping rather than a tuple of pairs because it crosses
    # to `AssertionResult.observed`, which is a Mapping, and one conversion is enough.
    observed: Mapping[str, str] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.outcome is AssertionOutcome.PASSED


@dataclass(frozen=True)
class AssertionReport:
    """Everything one boot asserted. Carried on the sandbox handle."""

    assertions: tuple[Assertion, ...]

    def by_id(self, assertion_id: str) -> Assertion | None:
        return next((a for a in self.assertions if a.assertion_id == assertion_id), None)

    @property
    def unverified_premises(self) -> tuple[str, ...]:
        return tuple(a.assertion_id for a in self.assertions if not a.premise_verified)

    def require_all_passed(self, *, required: tuple[str, ...]) -> None:
        """Refuse unless every required assertion is present and `passed`.

        Absence is a failure, not a skip. `Worker.dispatch` refuses on a handle whose
        report is missing a required assertion for the same reason it refuses on a failed
        one: an assertion nobody ran and an assertion nobody wrote are indistinguishable
        from here, and both mean the control was not applied.
        """
        problems: list[str] = []
        for assertion_id in required:
            found = self.by_id(assertion_id)
            if found is None:
                problems.append(f"{assertion_id}: absent from the report")
            elif not found.passed:
                problems.append(f"{assertion_id}: {found.outcome.value} — {found.detail}")
        if problems:
            raise ContainmentFailure("; ".join(problems))
