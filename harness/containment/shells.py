"""Assertions whose premise nobody has read yet, and the holes O5 fills in.

C1, C2, C3, C5 and C10 rest on the **selected executor's own vocabulary** — the exact
configuration keys that disable persistence-off, condensation and the approval surface, the
exact event class names those features emit, the paths the executor searches for
configuration. None of it is in this repository and none of it has been read first-hand.

`sandbox-specification.md:125` argues such an assertion should be written to pass harmlessly,
because "an assertion that harmlessly passes on a feature that does not exist costs nothing."
**That is true for an absent feature and false for a misnamed one**, and ADR-0007 records why:
C2's two conjuncts and C3's three are not independent — each rests on the same vocabulary, so
one wrong name defeats all of them at once while the assertion reports `passed` with
compaction running upstream of a verdict. Fifteen green assertions that mean nothing are worse
than fifteen absent ones, because the green ones stop anybody looking.

So a shell **never passes.** An unread hole yields `NOT_EXECUTED`, which F25 makes a failure
and which `Worker.check_handle` already refuses to dispatch on. What a shell does provide is
the structure: the claim, the holes, and the check that runs the moment the holes are filled.
O5 is then a reading session that supplies **names**, not a design session.

## `UNREAD` is not an empty value

A hole holding `()` means *the executor was read and it has no such event class*. A hole
holding `UNREAD` means *nobody looked*. Collapsing them is the same defect as an optional
provenance field: the empty tuple is a finding, and absence is the ambiguity this removes.
`UNREAD` is a distinct sentinel so that the difference is visible at a glance and greppable
in one command:

    grep -rn UNREAD harness/containment/shells.py

Every occurrence that command prints is a question for the executor's source at the pinned
commit SHA, and the count going to zero is what discharges O5.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Final

from harness.containment.assertions import Assertion, AssertionOutcome

__all__ = [
    "SHELLS",
    "UNREAD",
    "ExecutorObservation",
    "Hole",
    "HoleKind",
    "PremiseShell",
    "Unread",
    "evaluate",
    "evaluate_all",
    "open_holes",
]


class Unread:
    """The sentinel for a hole nobody has filled. Distinct from every legitimate value.

    A singleton with a loud `repr`, and deliberately **not** `None`: `None` is a value some
    executor configuration could legitimately hold, and a hole whose unread state collides
    with a legal value is a hole that can be filled by accident.
    """

    _instance: Unread | None = None

    def __new__(cls) -> Unread:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "UNREAD(O5: read the executor at the pinned SHA)"

    def __bool__(self) -> bool:
        # Never truthy. `if hole.value:` must not read an unread hole as present.
        return False


UNREAD: Final = Unread()

type HoleValue = str | tuple[str, ...] | bool | Unread


class HoleKind(Enum):
    """What kind of fact the executor's source has to supply.

    Recorded per hole because the reading task differs: a configuration key is found in a
    settings model, an event class in a stream type union, a search path in a loader.
    """

    CONFIG_KEY = "config_key"
    CONFIG_VALUE = "config_value"
    EVENT_CLASS = "event_class"
    SEARCH_PATH = "search_path"
    REPO_FACT = "repo_fact"


@dataclass(frozen=True)
class Hole:
    """One fact about the executor that this repository does not know.

    `question` is written to be answerable by reading, not by inference — it names what to
    look for and, where the plan's research notes suggest a candidate, says so explicitly as
    a candidate rather than as an answer. A note that reads like an answer is how a research
    note becomes a premise nobody rechecks.
    """

    name: str
    kind: HoleKind
    question: str
    value: HoleValue = UNREAD
    candidate: str | None = None

    @property
    def read(self) -> bool:
        return not isinstance(self.value, Unread)

    def filled(self, value: HoleValue) -> Hole:
        """The same hole with an answer. Returns a new hole; nothing here is mutated."""
        if isinstance(value, Unread):
            raise ValueError(f"{self.name}: filling a hole with UNREAD is not filling it")
        return Hole(
            name=self.name,
            kind=self.kind,
            question=self.question,
            value=value,
            candidate=self.candidate,
        )


@dataclass(frozen=True)
class ExecutorObservation:
    """Everything the shells' checks read. Supplied by the adaptor, never guessed here.

    Defaults are the **empty** observation, not a benign one: a check handed this must not
    conclude anything comfortable from it. Each check states what it does with an empty
    field, and none of them treats emptiness as satisfaction unless the specification says
    a count of zero is the assertion (C1's event set and C2's condensation count).
    """

    config: Mapping[str, object] = field(default_factory=dict)
    config_hash: str | None = None
    harness_config_hash: str | None = None
    config_paths_searched: tuple[str, ...] = ()
    config_files_found: tuple[str, ...] = ()
    stream_event_classes: tuple[str, ...] = ()
    observed_event_ids: frozenset[str] = frozenset()
    durable_event_ids: frozenset[str] = frozenset()
    listening_ports: tuple[int, ...] = ()
    executor_commit_sha: str | None = None
    executor_resolved_through_redirect: bool | None = None


@dataclass(frozen=True)
class PremiseShell:
    """One containment assertion, its holes, and the check that runs once they are filled."""

    assertion_id: str
    claim: str
    holes: tuple[Hole, ...]
    check: Callable[[Mapping[str, HoleValue], ExecutorObservation], Assertion]

    def unread(self) -> tuple[str, ...]:
        return tuple(hole.name for hole in self.holes if not hole.read)

    def with_holes(self, **answers: HoleValue) -> PremiseShell:
        """The shell with some holes answered. This is what O5's session produces.

        An answer naming a hole that does not exist raises rather than being ignored: a
        typo'd hole name that silently did nothing would leave the shell unread while
        looking filled, which is the failure the whole module exists to prevent.
        """
        known = {hole.name for hole in self.holes}
        unknown = sorted(set(answers) - known)
        if unknown:
            raise KeyError(f"{self.assertion_id}: no such hole(s): {unknown}; known: {sorted(known)}")
        return PremiseShell(
            assertion_id=self.assertion_id,
            claim=self.claim,
            holes=tuple(
                hole.filled(answers[hole.name]) if hole.name in answers else hole
                for hole in self.holes
            ),
            check=self.check,
        )


def evaluate(shell: PremiseShell, observation: ExecutorObservation) -> Assertion:
    """Run a shell. **An unread hole is `NOT_EXECUTED` and the check is never called.**

    Not `FAILED`: nothing was checked, and reporting a failure would say the control ran and
    found a problem. Not `PASSED` under any circumstance — that is the entire point.
    `premise_verified` is False until every hole is read, so a report carries the distinction
    even for a shell that has since been filled and passed.
    """
    unread = shell.unread()
    if unread:
        return Assertion(
            assertion_id=shell.assertion_id,
            outcome=AssertionOutcome.NOT_EXECUTED,
            detail=(
                f"{len(unread)} unread premise hole(s): {', '.join(unread)}. "
                f"O5 — read the executor at the pinned SHA. Claim: {shell.claim}"
            ),
            premise_verified=False,
        )
    values = {hole.name: hole.value for hole in shell.holes}
    return shell.check(values, observation)


def evaluate_all(
    shells: Sequence[PremiseShell], observation: ExecutorObservation
) -> tuple[Assertion, ...]:
    return tuple(evaluate(shell, observation) for shell in shells)


def open_holes(shells: Sequence[PremiseShell] | None = None) -> tuple[str, ...]:
    """Every unread hole across the register, as `C3.approval_event_classes` handles.

    This is O5's worklist and the number that has to reach zero. A test asserts it is
    currently non-empty: a register reporting no open holes while the executor has not been
    read would mean the holes were removed rather than answered.
    """
    target = SHELLS if shells is None else shells
    return tuple(f"{s.assertion_id}.{name}" for s in target for name in s.unread())


# ============================================================================ the checks
#
# Each is a pure function of (filled holes, observation). They are written now, while the
# structure is the thing being designed, so that O5 supplies names and nothing else.


def _as_names(value: HoleValue) -> tuple[str, ...]:
    if isinstance(value, tuple):
        return value
    if isinstance(value, str):
        return (value,)
    raise TypeError(f"expected a name or names, got {value!r}")


def _as_key(value: HoleValue) -> str:
    if isinstance(value, str):
        return value
    raise TypeError(f"expected a single configuration key, got {value!r}")


def _check_c1(holes: Mapping[str, HoleValue], obs: ExecutorObservation) -> Assertion:
    """Per-event persistence on, and every observed event durable at end of run."""
    key = _as_key(holes["persistence_enabled_key"])
    enabled = obs.config.get(key)
    problems: list[str] = []
    if enabled is not True:
        problems.append(f"{key!r} is {enabled!r}, not True (persistence is opt-in)")

    # The count comparison is the half that catches a partial flush, and it is a subset
    # test rather than a length test: equal counts with different ids is not the same claim.
    missing = obs.observed_event_ids - obs.durable_event_ids
    if missing:
        problems.append(f"{len(missing)} observed event id(s) absent from disk")
    if len(obs.durable_event_ids) < len(obs.observed_event_ids):
        problems.append(
            f"durable count {len(obs.durable_event_ids)} below observed "
            f"{len(obs.observed_event_ids)}; the read log is a subset of unknown size (F19)"
        )
    return _verdict("C1", problems, "per-event persistence on; every observed event durable")


def _check_c2(holes: Mapping[str, HoleValue], obs: ExecutorObservation) -> Assertion:
    """No compaction: every condenser and summarizer off, and zero condensation events.

    The two conjuncts rest on the same vocabulary, which is exactly why ADR-0007 refuses to
    let this pass on unread holes: one wrong name defeats both at once.
    """
    problems: list[str] = []
    for key in _as_names(holes["condenser_disable_keys"]):
        value = obs.config.get(key)
        if value not in (False, None) and value != "":
            problems.append(f"{key!r} is {value!r}; a condenser is configured on")
    condensation = _as_names(holes["condensation_event_classes"])
    seen = sorted(set(obs.stream_event_classes) & set(condensation))
    if seen:
        problems.append(f"condensation-class events present in the stream: {seen} (I16)")
    return _verdict("C2", problems, "no condenser configured; zero condensation events")


def _check_c3(holes: Mapping[str, HoleValue], obs: ExecutorObservation) -> Assertion:
    """No second approval surface: no frontend served, approval mode off, no approval events."""
    problems: list[str] = []
    key = _as_key(holes["approval_mode_key"])
    value = obs.config.get(key)
    if value not in (False, None) and value != "":
        problems.append(f"{key!r} is {value!r}; a confirmation/approval mode is enabled")

    frontend_ports = tuple(
        int(port) for port in _as_names(holes["frontend_ports"]) if str(port).isdigit()
    )
    serving = sorted(set(obs.listening_ports) & set(frontend_ports))
    if serving:
        problems.append(f"the executor's own frontend is listening on {serving}")

    approvals = _as_names(holes["approval_event_classes"])
    seen = sorted(set(obs.stream_event_classes) & set(approvals))
    if seen:
        problems.append(
            f"approval-class events in the stream: {seen}; an approval landed in the "
            "executor's event stream and never in Alfred's evidence chain"
        )
    return _verdict("C3", problems, "no frontend served; approval mode off; zero approval events")


def _check_c5(holes: Mapping[str, HoleValue], obs: ExecutorObservation) -> Assertion:
    """Executor pinned by commit SHA resolved *through* the canonical-path redirect."""
    problems: list[str] = []
    pinned = _as_key(holes["pinned_commit_sha"])
    if obs.executor_commit_sha != pinned:
        problems.append(f"executor is at {obs.executor_commit_sha!r}, pinned to {pinned!r}")
    if obs.executor_resolved_through_redirect is not True:
        problems.append(
            "the commit was not resolved through the canonical-path redirect; a redirecting "
            "canonical path plus a repository with no tags is how a pin resolves to the "
            "redirect rather than through it"
        )
    return _verdict("C5", problems, "executor pinned by SHA, resolved through the redirect")


def _check_c10(holes: Mapping[str, HoleValue], obs: ExecutorObservation) -> Assertion:
    """Loaded configuration is the harness's, and no user or project config exists anywhere.

    The second conjunct is the one with a documented instance behind it: an SDK in this
    ecosystem treated an empty settings-source list as "unset" and loaded user configuration
    anyway. A hash comparison alone would have passed that, because the hoisted file *became*
    the loaded configuration.
    """
    problems: list[str] = []
    if obs.config_hash is None or obs.harness_config_hash is None:
        problems.append("a configuration hash is missing; the comparison cannot be made")
    elif obs.config_hash != obs.harness_config_hash:
        problems.append(
            f"loaded config hash {obs.config_hash} != harness-supplied {obs.harness_config_hash}"
        )

    searched = set(_as_names(holes["config_search_paths"])) | set(obs.config_paths_searched)
    hoisted = sorted(path for path in obs.config_files_found if path in searched)
    if hoisted:
        problems.append(f"configuration files exist at searched paths: {hoisted} (config hoisting)")
    if not searched:
        # D57 in miniature. A path set of zero makes the hoisting half unfalsifiable.
        problems.append("no configuration search paths are known; the hoisting check scanned none")
    return _verdict("C10", problems, "loaded config is the harness's; no config hoisted")


def _verdict(assertion_id: str, problems: Sequence[str], claim: str) -> Assertion:
    """Filled holes mean the check ran, so the outcome is `PASSED` or `FAILED` — never
    `NOT_EXECUTED`. `premise_verified=True` records that the vocabulary was read."""
    if problems:
        return Assertion(
            assertion_id=assertion_id,
            outcome=AssertionOutcome.FAILED,
            detail="; ".join(problems),
            premise_verified=True,
        )
    return Assertion(
        assertion_id=assertion_id,
        outcome=AssertionOutcome.PASSED,
        detail=claim,
        premise_verified=True,
    )


# ================================================================== the register of shells


C1: Final = PremiseShell(
    assertion_id="C1",
    claim=(
        "Per-event persistence enabled, and the durable event count at end of run is at "
        "least the count the adaptor observed, with every observed event id present on disk"
    ),
    holes=(
        Hole(
            name="persistence_enabled_key",
            kind=HoleKind.CONFIG_KEY,
            question=(
                "Which configuration key turns per-event persistence on? Persistence is "
                "opt-in, so the default is the hazard. Record the key's exact dotted path "
                "and the value that means enabled."
            ),
        ),
    ),
    check=_check_c1,
)

C2: Final = PremiseShell(
    assertion_id="C2",
    claim="No compaction: every condenser and summarizer disabled, zero condensation events",
    holes=(
        Hole(
            name="condenser_disable_keys",
            kind=HoleKind.CONFIG_KEY,
            question=(
                "Every configuration key that enables a condenser, summarizer, memory "
                "compressor or history truncator. All of them, not the one the docs "
                "mention: the assertion is that none is on, so a missed key is a hole."
            ),
        ),
        Hole(
            name="condensation_event_classes",
            kind=HoleKind.EVENT_CLASS,
            question=(
                "The event class names a condensation or summarization emits into the "
                "stream. An empty tuple is a legitimate answer meaning the executor emits "
                "no such class — record it as `()`, never leave it UNREAD."
            ),
        ),
    ),
    check=_check_c2,
)

C3: Final = PremiseShell(
    assertion_id="C3",
    claim="No second approval surface: frontend not served, approval mode off, no approval events",
    holes=(
        Hole(
            name="approval_mode_key",
            kind=HoleKind.CONFIG_KEY,
            question=(
                "The key for the executor's confirmation/approval mode, and the value that "
                "means disabled."
            ),
        ),
        Hole(
            name="frontend_ports",
            kind=HoleKind.CONFIG_VALUE,
            question=(
                "Which ports the executor's own frontend binds to when served. Needed as "
                "numbers: the socket scan compares against listening ports, not names."
            ),
        ),
        Hole(
            name="approval_event_classes",
            kind=HoleKind.EVENT_CLASS,
            question=(
                "The event class names an approval or confirmation emits. `()` if none "
                "exists — a real answer, not an unread hole."
            ),
        ),
    ),
    check=_check_c3,
)

C5: Final = PremiseShell(
    assertion_id="C5",
    claim="Executor pinned by commit SHA resolved through the canonical-path redirect",
    holes=(
        Hole(
            name="pinned_commit_sha",
            kind=HoleKind.REPO_FACT,
            question=(
                "The 40-hex commit the executor is pinned to, resolved by following the "
                "canonical-path redirect to the repository that actually serves it — not "
                "the redirect's own target listing. The repository has no tags to pin to, "
                "which is why this is a SHA and why the redirect matters."
            ),
        ),
    ),
    check=_check_c5,
)

C10: Final = PremiseShell(
    assertion_id="C10",
    claim="Loaded configuration equals the harness's; no user- or project-level config exists",
    holes=(
        Hole(
            name="config_search_paths",
            kind=HoleKind.SEARCH_PATH,
            question=(
                "Every path the executor searches for configuration, in order — user-level, "
                "project-level, environment-directed, and any implicit working-directory "
                "lookup. The documented instance in this ecosystem hoisted user "
                "configuration through a path an empty settings-source list did not disable."
            ),
        ),
    ),
    check=_check_c10,
)

# Ordered by assertion id so `open_holes()` reads as a worklist rather than as a set.
SHELLS: Final[tuple[PremiseShell, ...]] = (C1, C2, C3, C5, C10)
