"""The executor-premise assertions, and the source read that filled their holes (O5).

C1, C2, C3, C5 and C10 rest on the selected executor's own vocabulary. Until 2026-08-18 none
of it had been read first-hand, every hole below held `UNREAD`, and every one of these
assertions reported `not_executed` — which F25 makes a failure and which `check_handle`
refuses to dispatch on. **A shell with an unread hole never passes**, and that remains true
of any hole reset to `UNREAD` in the future.

O5 read the source. What it found changed more than five names — see ADR-0018 — and the
corrections are recorded here beside the values they correct, because a research note that
quietly becomes a constant is how a premise stops being rechecked.

## Every filled hole cites a source

`Hole.source` is a `path:line` inside the pinned tree, and a hole cannot be filled without
one. The control that matters after O5 is no longer "is anything unread" but **"can each
answer be re-verified"**: a constant with no citation is indistinguishable from a guess
somebody typed, which is precisely the state O5 existed to leave behind.

    grep -rn UNREAD harness/containment/shells.py

Zero occurrences means every hole is answered. `unsourced_holes()` is the check that they
were answered by reading rather than by inference, and CI asserts it is empty.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Final

from harness.containment.assertions import Assertion, AssertionOutcome

__all__ = [
    "C17",
    "ConfigContractViolation",
    "ConfigValue",
    "CANVAS_COMMIT",
    "CANVAS_REPO",
    "EXECUTOR_COMMIT",
    "EXECUTOR_REPO",
    "REDIRECTING_PATHS",
    "SHELLS",
    "UNREAD",
    "ExecutorObservation",
    "Hole",
    "HoleKind",
    "PremiseShell",
    "Unread",
    "evaluate",
    "evaluate_all",
    "validated_config",
    "open_holes",
    "unsourced_holes",
]

# ------------------------------------------------------------------------ the pins
#
# Resolved 2026-08-18 by following the redirect rather than trusting the canonical path,
# which is C5's whole point. Recorded rather than fabricated (this repository has caught a
# fabricated digest before).

EXECUTOR_REPO: Final = "https://github.com/OpenHands/software-agent-sdk"
EXECUTOR_COMMIT: Final = "d460d1a0b6bd35e054ad146c6078205df4686387"

# NOT the executor. `OpenHands/OpenHands` is "Agent Canvas", a TypeScript/React/Electron
# control centre; at this commit it holds eight Python files, all CI scripts and test mocks.
# Pinned here only so that a future reader who finds this name in D38 can see it was checked
# and rejected rather than overlooked (ADR-0018).
CANVAS_REPO: Final = "https://github.com/OpenHands/OpenHands"
CANVAS_COMMIT: Final = "1916c9046c4e6a1e081be1ba06e278d182a40133"

# Both 301 to `OpenHands/OpenHands`, verified 2026-08-18. Neither is the executor, and
# pinning *to* a redirect rather than *through* it is the C5 hazard exactly.
REDIRECTING_PATHS: Final[tuple[str, ...]] = (
    "https://github.com/OpenDevin/OpenDevin",
    "https://github.com/All-Hands-AI/OpenHands",
)


class Unread:
    """The sentinel for a hole nobody has filled. Distinct from every legitimate value.

    A singleton with a loud `repr`, and deliberately **not** `None`: `None` is a value some
    executor configuration could legitimately hold — `persistence_dir` and `Agent.condenser`
    both use it to mean something specific — so a hole whose unread state collided with it
    could be filled by accident.
    """

    _instance: Unread | None = None

    def __new__(cls) -> Unread:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "UNREAD(read the executor at the pinned SHA)"

    def __bool__(self) -> bool:
        # Never truthy. `if hole.value:` must not read an unread hole as present.
        return False


UNREAD: Final = Unread()

type HoleValue = str | tuple[str, ...] | bool | Unread


class HoleKind(Enum):
    CONFIG_KEY = "config_key"
    CONFIG_VALUE = "config_value"
    EVENT_CLASS = "event_class"
    SEARCH_PATH = "search_path"
    REPO_FACT = "repo_fact"


@dataclass(frozen=True)
class Hole:
    """One fact about the executor, the question that finds it, and where it was read."""

    name: str
    kind: HoleKind
    question: str
    value: HoleValue = UNREAD
    source: str | None = None
    correction: str | None = None

    @property
    def read(self) -> bool:
        return not isinstance(self.value, Unread)

    def filled(self, value: HoleValue, *, source: str, correction: str | None = None) -> Hole:
        """The same hole with an answer and a citation. `source` is not optional.

        A constant with no citation cannot be re-verified, and after O5 that is the only
        failure mode left: not an unread hole, but an answered one nobody can check.
        """
        if isinstance(value, Unread):
            raise ValueError(f"{self.name}: filling a hole with UNREAD is not filling it")
        if not source.strip():
            raise ValueError(f"{self.name}: an answer without a source is not a reading")
        return Hole(
            name=self.name,
            kind=self.kind,
            question=self.question,
            value=value,
            source=source,
            correction=correction or self.correction,
        )


@dataclass(frozen=True)
class ExecutorObservation:
    """Everything the checks read. Supplied by the adaptor, never guessed here.

    Defaults are the **empty** observation, not a benign one. Each check states what it does
    with an empty field and none treats emptiness as satisfaction unless the specification
    says a count of zero is the assertion.
    """

    config: Mapping[str, ConfigValue] = field(default_factory=dict)
    config_hash: str | None = None
    harness_config_hash: str | None = None
    config_files_found: tuple[str, ...] = ()
    # `OH_*` names present in the container's environment. A second configuration channel
    # that overrides the file, and therefore a second hoisting channel (C10).
    config_env_names: tuple[str, ...] = ()
    stream_event_classes: tuple[str, ...] = ()
    observed_event_ids: frozenset[str] = frozenset()
    durable_event_ids: frozenset[str] = frozenset()
    # `rejection_source` values seen on UserRejectObservation. "user" means a human sat in
    # the loop; "hook" is Alfred's own PreToolUse block and is not an approval surface.
    rejection_sources: tuple[str, ...] = ()
    # Every ConversationExecutionStatus the conversation passed through. The observable
    # substitute for an approval event, because approval emits none.
    execution_statuses: tuple[str, ...] = ()
    listening_ports: tuple[int, ...] = ()
    # Whether the durable read was taken *after* the conversation was closed. `None` means
    # the adaptor did not say, which C1 treats as a problem rather than as "probably fine":
    # the client deletes the conversation on close by default, so a read of unknown ordering
    # is a read that may have happened before the directory was removed.
    durable_read_after_close: bool | None = None
    # The `kind` tag of the workspace and the class of the conversation actually in use.
    # `kind` is the class name (`utils/models.py:199`), so these are compared as names.
    workspace_kind: str | None = None
    conversation_kind: str | None = None
    # The container the adaptor started. Without one, the two names above describe an object
    # graph with nothing behind it.
    container_id: str | None = None
    executor_repo: str | None = None
    executor_commit_sha: str | None = None
    executor_resolved_through_redirect: bool | None = None

    # The argv the container was actually started with, read from outside. C17's subject.
    # Empty means the adaptor did not read it, which C17 reports as `not_executed` rather
    # than as an unhardened launch: an argv nobody read says nothing about the flags on it.
    container_launch_args: tuple[str, ...] = ()
    # Host-side bindings for every published port, as `docker` reports them -- for example
    # `0.0.0.0:8010->8000/tcp`. The direction S6's egress work does not cover.
    published_port_bindings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        # Refuse at the boundary, not inside a check. An adaptor sending an arbitrary object
        # would otherwise reach a reader that renders it with `str()` and compares a repr --
        # a comparison that can only fail, for a reason no report can explain.
        validated_config(self.config)


@dataclass(frozen=True)
class PremiseShell:
    assertion_id: str
    claim: str
    holes: tuple[Hole, ...]
    check: Callable[[Mapping[str, HoleValue], ExecutorObservation], Assertion]

    def unread(self) -> tuple[str, ...]:
        return tuple(hole.name for hole in self.holes if not hole.read)

    def unsourced(self) -> tuple[str, ...]:
        return tuple(hole.name for hole in self.holes if hole.read and not hole.source)

    def with_holes(self, **answers: HoleValue) -> PremiseShell:
        """Answer holes without a citation. Test-only: `filled` is the real path.

        An answer naming a hole that does not exist raises rather than being ignored — a
        typo'd name that silently did nothing would leave a shell unread while looking filled.
        """
        known = {hole.name for hole in self.holes}
        unknown = sorted(set(answers) - known)
        if unknown:
            raise KeyError(
                f"{self.assertion_id}: no such hole(s): {unknown}; known: {sorted(known)}"
            )
        return PremiseShell(
            assertion_id=self.assertion_id,
            claim=self.claim,
            holes=tuple(
                hole.filled(answers[hole.name], source="<test>") if hole.name in answers else hole
                for hole in self.holes
            ),
            check=self.check,
        )


def evaluate(shell: PremiseShell, observation: ExecutorObservation) -> Assertion:
    """Run a shell. **An unread hole is `NOT_EXECUTED` and the check is never called.**

    Not `FAILED`: nothing was checked, and a failure would claim the control ran and found a
    problem. Never `PASSED` under any observation — that is the entire point, and it stays
    true for any hole reset to `UNREAD` by a future executor change.
    """
    unread = shell.unread()
    if unread:
        return Assertion(
            assertion_id=shell.assertion_id,
            outcome=AssertionOutcome.NOT_EXECUTED,
            detail=(
                f"{len(unread)} unread premise hole(s): {', '.join(unread)}. "
                f"Read the executor at {EXECUTOR_COMMIT[:12]}. Claim: {shell.claim}"
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
    """Unread holes, as `C3.approval_mode_key` handles. Empty since O5."""
    target = SHELLS if shells is None else shells
    return tuple(f"{s.assertion_id}.{name}" for s in target for name in s.unread())


def unsourced_holes(shells: Sequence[PremiseShell] | None = None) -> tuple[str, ...]:
    """Answered holes with no citation — the control that matters after O5.

    An unread hole announces itself. An answered one with no source does not: it reads as a
    fact and may be a guess somebody typed, which is the state O5 existed to leave behind.
    """
    target = SHELLS if shells is None else shells
    return tuple(f"{s.assertion_id}.{name}" for s in target for name in s.unsourced())


# ============================================================================ the checks


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


# ------------------------------------------------- reading the adaptor's configuration
#
# `ExecutorObservation.config` was `Mapping[str, object]`: adaptor-supplied, unvalidated, and
# with no agreed serialization. Before these helpers each check invented its own reading and
# they disagreed — C1 refused to assume a library default, C2 assumed one; C3 compared with
# `is True` while C2 compared with `str(...)`. Three green assertions over live hazards came
# out of that, and none of them was a mistake anyone could see by reading one check alone.
# Six of the seven findings in the containment self-review were that one root cause.
#
# The discipline is one sentence: **absent is unknown, uninterpretable is a finding, and
# neither is a pass.**
#
# The reading was made consistent first; the *contract* is typed here. `ConfigValue` is the
# closed JSON-shaped union an adaptor may send, and `validated_config` refuses anything
# outside it at the boundary rather than letting it reach a check that will read it with
# `str()` and get a repr.
#
# **Why a union and not a model.** The keys are not knowable in advance: every one of them is
# a hole, answered by reading the executor, and a different executor answers differently. A
# model enumerating today's keys would have to be edited by anyone adding a hole, and the
# check would then be typed against the harness's expectations rather than against what the
# adaptor may legally send. Typing the *values* removes `object` without pretending the key
# set is closed.
#
# **What this does not do.** It does not make a wrong value right, and it does not validate
# that a key means what the hole says it means. A string where a boolean belongs still reaches
# `_as_flag`, which still reports it as uninterpretable. This closes the serialization half of
# the finding: a value that could not survive a round trip through JSON cannot enter.


# A value an adaptor may legally send. Recursive, so nested configuration is covered; closed,
# so an arbitrary Python object is not a configuration value. `None` is in the union because
# the SDK uses it meaningfully — `persistence_dir: None` is how persistence is switched off,
# and C1 distinguishes it from absent.
type ConfigValue = str | int | float | bool | None | Sequence["ConfigValue"] | Mapping[str, "ConfigValue"]


class ConfigContractViolation(TypeError):
    """The adaptor sent a configuration value with no agreed serialization.

    A refusal at the boundary rather than a finding inside a check. A check reading an
    arbitrary object would render it with `str()` and compare a repr — which is a comparison
    that can only ever fail, and fails for a reason the report cannot explain.
    """


def validated_config(raw: Mapping[str, object], *, _path: str = "") -> dict[str, ConfigValue]:
    """Every value in the closed union, or raise naming the path that is not.

    Booleans are checked before integers throughout: `bool` is a subclass of `int` in Python
    and an `isinstance(value, int)` test accepts `True`, which is how a flag becomes the
    number 1 somewhere downstream.
    """
    out: dict[str, ConfigValue] = {}
    for key, value in raw.items():
        if not isinstance(key, str):
            raise ConfigContractViolation(f"configuration key {key!r} is not a string")
        out[key] = _validated_value(value, f"{_path}{key}")
    return out


def _validated_value(value: object, path: str) -> ConfigValue:
    if value is None or isinstance(value, (str, bool, int, float)):
        if isinstance(value, float) and (value != value or value in (float("inf"), float("-inf"))):
            # NaN and the infinities have no JSON spelling. Admitting them here would put a
            # value in the configuration that cannot survive being written down.
            raise ConfigContractViolation(f"{path}: {value!r} has no serialization")
        return value
    if isinstance(value, Mapping):
        return validated_config({str(k): v for k, v in value.items()}, _path=f"{path}.")  # pyright: ignore[reportUnknownArgumentType]
    if isinstance(value, (str, bytes)):
        raise ConfigContractViolation(f"{path}: bytes are not a configuration value")
    if isinstance(value, Sequence):
        return [_validated_value(item, f"{path}[{i}]") for i, item in enumerate(value)]  # pyright: ignore[reportUnknownArgumentType, reportUnknownVariableType]
    raise ConfigContractViolation(
        f"{path}: {type(value).__name__} is not a configuration value; the adaptor must send "
        "something that survives a round trip through JSON"
    )


class Absent:
    """The sentinel for a key the loaded configuration does not carry.

    Not the string `"<absent>"`, which was the previous spelling: a configuration value may
    legitimately *be* that string, and `persistence_dir: "<absent>"` reported "absent from
    the loaded configuration". The same argument as `Unread` against `None`, made twice in
    one file because the second time it was made with a string.
    """

    _instance: Absent | None = None

    def __new__(cls) -> Absent:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "ABSENT(the loaded configuration does not carry this key)"

    def __bool__(self) -> bool:
        return False


ABSENT: Final = Absent()

# What the three JSON-ish channels spell a boolean as. `load_config` merges `OH_*` environment
# variables over the file (C10), and an environment variable is a string — so a check that
# accepted only Python `True` would pass an enabled VS Code server on every environment-configured
# container, which is exactly the surface C3 exists to close.
_TRUE_SPELLINGS: Final[frozenset[str]] = frozenset({"true", "1", "yes", "on"})
_FALSE_SPELLINGS: Final[frozenset[str]] = frozenset({"false", "0", "no", "off"})


def _read(obs: ExecutorObservation, key: str) -> ConfigValue | Absent:
    """One configuration value, or `ABSENT`. Never conflates absent with any real value."""
    return obs.config.get(key, ABSENT)


def _as_flag(value: object) -> bool | None:
    """A configuration value as a boolean, or `None` when it does not spell one.

    `None` is *uninterpretable*, and every caller treats it as a problem rather than as
    either polarity. A value nobody can read is not a value that says "off".
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value) if value in (0, 1) else None
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in _TRUE_SPELLINGS:
            return True
        if lowered in _FALSE_SPELLINGS:
            return False
    return None


def _flag_problem(key: str, value: object, *, required: bool, why: str) -> str | None:
    """The shared boolean clause: absent, uninterpretable, or the wrong polarity.

    `why` is the consequence of the wrong polarity, so each caller supplies its own sentence
    and the three failure shapes stay identical across checks.
    """
    if isinstance(value, Absent):
        return f"{key!r} is absent from the loaded configuration; its value is unknown ({why})"
    flag = _as_flag(value)
    if flag is None:
        return (
            f"{key!r} is {value!r}, which does not spell a boolean; an unreadable value is "
            "not a value that says off"
        )
    if flag is not required:
        return f"{key!r} is {value!r}; expected {required}. {why}"
    return None


def _verdict(
    assertion_id: str,
    problems: Sequence[str],
    claim: str,
    observed: Mapping[str, str] | None = None,
) -> Assertion:
    """`observed` is attached to **both** outcomes on purpose.

    A failed assertion's values are exactly what a reader needs to see, and `reassert.compare`
    reads observations across boot and end regardless of outcome — attaching them only to the
    pass would make a value diff impossible in the one case where something is already wrong.
    """
    values = dict(observed or {})
    if problems:
        return Assertion(
            assertion_id=assertion_id,
            outcome=AssertionOutcome.FAILED,
            detail="; ".join(problems),
            premise_verified=True,
            observed=values,
        )
    return Assertion(
        assertion_id=assertion_id,
        outcome=AssertionOutcome.PASSED,
        detail=claim,
        premise_verified=True,
        observed=values,
    )


def _check_c1(holes: Mapping[str, HoleValue], obs: ExecutorObservation) -> Assertion:
    """Persistence configured, and every observed event durable at end of run.

    **The premise inverted at O5.** The research note said persistence was opt-in and had to
    be asserted enabled; the field defaults to `"workspace/conversations"`, so it is on unless
    something sets it to `None`. The assertion is therefore "not disabled" rather than
    "enabled", and the two differ on every default configuration.

    The count half is unchanged and is the half D53 and plan:431 both insist on: persistence
    is verified by end-of-run event count, **not by a flag**. A flag says what was intended.

    **The fourth clause exists because the third was being read against a directory the
    default configuration deletes** (ADR-0019). `Conversation(...)` defaults
    `delete_on_close=True`; on close the client issues `DELETE /conversations/{id}` and the
    server `safe_rmtree`s the conversation directory. The workspace survives, the event log
    does not. So two things are asserted, and neither alone is enough: deletion is off, *and*
    the durable read was taken after close. Deletion off with a read taken before close still
    proves nothing about what survives the run, and a read after close under
    `delete_on_close=True` is a read of an empty directory that C1 would report as a missing
    event count rather than as the configuration error it is.
    """
    key = _as_key(holes["persistence_dir_key"])
    configured = _read(obs, key)
    problems: list[str] = []
    if configured is None:
        problems.append(f"{key!r} is None; the conversation is explicitly not persisted")
    elif isinstance(configured, Absent):
        problems.append(f"{key!r} is absent from the loaded configuration; its value is unknown")
    elif not str(configured).strip():
        problems.append(f"{key!r} is empty; a blank path is not a persistence directory")

    delete_key = _as_key(holes["delete_on_close_key"])
    delete_problem = _flag_problem(
        delete_key,
        _read(obs, delete_key),
        required=False,
        why=(
            "it defaults to True, the conversation directory is removed on close, and a "
            "durable read then proves nothing about what survives the run"
        ),
    )
    if delete_problem:
        problems.append(delete_problem)

    if obs.durable_read_after_close is not True:
        problems.append(
            "the durable read was not stated to have been taken after close"
            if obs.durable_read_after_close is None
            else "the durable read was taken before close; deletion happens at close"
        )

    missing = obs.observed_event_ids - obs.durable_event_ids
    if missing:
        problems.append(f"{len(missing)} observed event id(s) absent from disk")
    if len(obs.durable_event_ids) < len(obs.observed_event_ids):
        problems.append(
            f"durable count {len(obs.durable_event_ids)} below observed "
            f"{len(obs.observed_event_ids)}; the read log is a subset of unknown size (F19)"
        )
    return _verdict(
        "C1",
        problems,
        "persistence configured; deletion on close off; every observed event durable "
        "on a read taken after close",
    )


def _check_c2(holes: Mapping[str, HoleValue], obs: ExecutorObservation) -> Assertion:
    """No compaction: no condenser configured, and zero condensation events in the stream.

    Two ways to be off, both legitimate: the field is `None`, or it holds the explicit
    no-op. A check accepting only one of them would fail a correctly configured executor,
    and a check accepting any value would pass a summarizing one.
    """
    key = _as_key(holes["condenser_key"])
    off_values = set(_as_names(holes["condenser_off_values"]))
    configured = _read(obs, key)
    problems: list[str] = []
    if isinstance(configured, Absent):
        # C1 refuses to read an absent key as the library's default and this used to do the
        # opposite for the same class of fact. The default happens to be `None`, which is
        # off, which is what made the asymmetry survive: the check was right by coincidence
        # for the one executor whose default nobody had changed.
        problems.append(
            f"{key!r} is absent from the loaded configuration; its value is unknown, and the "
            "library default is not what is being asserted"
        )
    elif configured is not None and str(configured) not in off_values:
        problems.append(
            f"{key!r} is {configured!r}; a condenser is configured "
            f"(off is None or one of {sorted(off_values)})"
        )

    condensation = _as_names(holes["condensation_event_classes"])
    seen = sorted(set(obs.stream_event_classes) & set(condensation))
    if seen:
        problems.append(f"condensation-class events present in the stream: {seen} (I16)")
    return _verdict("C2", problems, "no condenser configured; zero condensation events")


def _check_c3(holes: Mapping[str, HoleValue], obs: ExecutorObservation) -> Assertion:
    """No second approval surface, and no interactive surface into the execution plane.

    **The specification's third conjunct could not be implemented as worded, and this is its
    replacement.** It asked for "zero approval-class events in the stream". There are none to
    count: rejection emits `UserRejectObservation`, and acceptance is *implicit* — the second
    `run()` call executes the pending actions and emits nothing. So a human could approve
    every action in a run and the stream would carry zero approval-class events. The original
    conjunct would have reported `passed` over exactly the hazard C3 exists to prevent.

    Three observable things replace it, and together they are stronger than what was asked:
    the policy is `NeverConfirm`; the conversation never entered the waiting state, which is
    persisted; and no rejection carries `rejection_source="user"`, since a human rejecting
    proves a human was being asked.

    The fourth clause was not in the specification at all. The agent server runs a **VS Code
    server inside the container, enabled by default** — an arbitrary file-edit and
    code-execution surface for a human, whose use lands in no event stream at any layer. C3
    was written against a chat frontend with an approval button; this is worse, and it is on
    unless turned off.
    """
    problems: list[str] = []

    policy_key = _as_key(holes["confirmation_policy_key"])
    required_policy = _as_key(holes["confirmation_policy_off_value"])
    policy = _read(obs, policy_key)
    if isinstance(policy, Absent):
        problems.append(
            f"{policy_key!r} is absent from the loaded configuration; the default is "
            f"{required_policy}, and the default is not what is being asserted"
        )
    elif policy is not None and str(policy) != required_policy:
        problems.append(f"{policy_key!r} is {policy!r}, not {required_policy!r}")

    waiting = _as_key(holes["waiting_status_name"])
    if waiting in obs.execution_statuses:
        problems.append(
            f"the conversation entered {waiting}; a human was asked to approve an action, "
            "and the approval itself emits no event"
        )

    if "user" in obs.rejection_sources:
        problems.append(
            "a rejection carries rejection_source='user'; a human rejecting proves a human "
            "was being asked, whatever the configuration says"
        )

    for surface_key in _as_names(holes["interactive_surface_keys"]):
        surface_problem = _flag_problem(
            surface_key,
            _read(obs, surface_key),
            required=False,
            why=(
                "an interactive surface into the execution plane is enabled, and anything a "
                "human does through it lands in no event stream at any layer"
            ),
        )
        if surface_problem:
            problems.append(surface_problem)

    surface_ports = tuple(
        int(port) for port in _as_names(holes["interactive_surface_ports"]) if port.isdigit()
    )
    serving = sorted(set(obs.listening_ports) & set(surface_ports))
    if serving:
        problems.append(f"an interactive surface is listening on {serving}")

    return _verdict(
        "C3",
        problems,
        "NeverConfirm; never waited for confirmation; no user rejection; no interactive surface",
    )


def _check_c5(holes: Mapping[str, HoleValue], obs: ExecutorObservation) -> Assertion:
    """Executor pinned by commit SHA in the repository the redirect actually leads to.

    Both halves are load-bearing and the first is the one O5 found broken: the repository the
    plan named by URL no longer contains an executor at all.
    """
    problems: list[str] = []
    repo = _as_key(holes["executor_repo"])
    pinned = _as_key(holes["pinned_commit_sha"])
    if obs.executor_repo != repo:
        problems.append(f"executor came from {obs.executor_repo!r}, pinned to {repo!r}")
    if obs.executor_commit_sha != pinned:
        problems.append(f"executor is at {obs.executor_commit_sha!r}, pinned to {pinned!r}")
    if obs.executor_resolved_through_redirect is not True:
        problems.append(
            "the commit was not resolved through the canonical-path redirect; two historical "
            f"paths still 301 here ({', '.join(REDIRECTING_PATHS)}) and pinning to a redirect "
            "rather than through it is this assertion's whole subject"
        )
    return _verdict("C5", problems, f"executor pinned at {pinned[:12]} in {repo}")


def _check_c10(holes: Mapping[str, HoleValue], obs: ExecutorObservation) -> Assertion:
    """Loaded configuration is the harness's, and nothing hoisted it — from a file or the
    environment.

    **The environment half was not in the specification.** The loader reads a JSON file and
    then merges `OH_*` environment variables *over* it. A check that enumerated search paths
    and found no file would pass a container whose entire configuration arrived through
    environment variables — which is the same defect as the documented SDK case, through the
    channel nobody enumerated.
    """
    problems: list[str] = []
    if obs.config_hash is None or obs.harness_config_hash is None:
        problems.append("a configuration hash is missing; the comparison cannot be made")
    elif obs.config_hash != obs.harness_config_hash:
        problems.append(
            f"loaded config hash {obs.config_hash} != harness-supplied {obs.harness_config_hash}"
        )

    searched = set(_as_names(holes["config_search_paths"]))
    if not searched:
        problems.append("no configuration search paths are known; the hoisting check scanned none")
    hoisted = sorted(path for path in obs.config_files_found if path in searched)
    if hoisted:
        problems.append(f"configuration files exist at searched paths: {hoisted}")

    prefix = _as_key(holes["config_env_prefix"])
    overrides = sorted(name for name in obs.config_env_names if name.startswith(f"{prefix}_"))
    if overrides:
        problems.append(
            f"{len(overrides)} {prefix}_* environment variable(s) override the configuration "
            f"file: {overrides[:10]}"
        )
    return _verdict("C10", problems, "loaded config is the harness's; nothing hoisted")



def _check_c16(holes: Mapping[str, HoleValue], obs: ExecutorObservation) -> Assertion:
    """The agent is running in the container at all.

    **Every other executor-premise assertion assumes this and none of them checks it**
    (ADR-0019). `Workspace(working_dir=...)` with no `host` returns a `LocalWorkspace`, which
    executes on the host filesystem, while `BaseWorkspace`'s own docstring calls every
    workspace "sandboxed". On a host-side run C1, C2, C3 and C10 all still pass: each reads
    configuration keys and event classes that exist identically in the local case. That is
    four green assertions over an agent with no container around it, which is ADR-0007's
    third outcome one layer above where the shells were built to guard.

    Three clauses, and each covers a different way of being wrong:

    1. **The workspace kind is a container kind**, matched against a closed set of names
       rather than a substring or a base class. `kind` is the class name, so a subclass is a
       different name — deliberately, because `DockerDevWorkspace` *builds the image on the
       fly* from a base image and is therefore not the pinned-image premise C5 and the
       layer-1 closure check are written against.
    2. **The conversation is the remote one.** A container-backed workspace paired with a
       local conversation would run the loop in Alfred's own process; the factory does not
       allow it today, but the factory is not the only constructor and this asserts the
       outcome rather than trusting the route to it.
    3. **A container id was recorded.** Without one the first two clauses describe an object
       graph and nothing else: a `workspace_kind` string is a self-report, and a self-report
       with no container behind it is the failure this assertion exists to catch.
    """
    problems: list[str] = []

    allowed = set(_as_names(holes["container_workspace_kinds"]))
    host_kind = _as_key(holes["host_workspace_kind"])
    kind = obs.workspace_kind
    if kind is None:
        problems.append(
            "the workspace kind was not reported; the assertion cannot tell a container from "
            "the host, which is the one thing it exists to tell"
        )
    elif kind == host_kind:
        problems.append(
            f"the workspace is {host_kind!r}, which executes on the host filesystem; the "
            "agent is not in a container and every other C assertion passes anyway"
        )
    elif kind not in allowed:
        problems.append(f"workspace kind {kind!r} is not one of {sorted(allowed)}")

    required_conversation = _as_key(holes["remote_conversation_class"])
    if obs.conversation_kind is None:
        problems.append("the conversation class was not reported")
    elif obs.conversation_kind != required_conversation:
        problems.append(
            f"the conversation is {obs.conversation_kind!r}, not {required_conversation!r}; "
            "the agent loop is running in Alfred's own process"
        )

    if not (obs.container_id or "").strip():
        problems.append(
            "no container id was recorded; the workspace kind is a self-report and nothing "
            "behind it was observed"
        )

    return _verdict(
        "C16",
        problems,
        f"workspace kind {obs.workspace_kind}; {required_conversation}; container "
        f"{(obs.container_id or '')[:12]}",
        # The container id is the reason `compare` reads values at all: two passes over two
        # different containers are indistinguishable by outcome. Recorded in full, not
        # truncated as the prose is — a diff over a 12-character prefix is a diff over a
        # prefix.
        observed={
            "workspace_kind": obs.workspace_kind or "<unreported>",
            "conversation_kind": obs.conversation_kind or "<unreported>",
            "container_id": obs.container_id or "<unreported>",
        },
    )



# Loopback, by every spelling `docker port` emits. A binding anywhere else publishes the
# agent server on an interface something other than this machine can reach.
_LOOPBACK: Final[frozenset[str]] = frozenset({"127.0.0.1", "::1", "localhost"})

# Alfred's launch requirements, not the executor's. Kept out of the hole register on purpose:
# a hole is a fact about the executor that had to be read, and these are policy this project
# chose. Mixing them would let a policy change look like a re-reading of somebody's source.
_REQUIRED_LAUNCH_FLAGS: Final[tuple[tuple[str, str], ...]] = (
    ("--cap-drop", "no capability is dropped, so in-container privilege is whatever the image grants"),
    ("--network", "egress uses the default bridge, which is open"),
)


def _bind_host(binding: str) -> str:
    """The host address out of `0.0.0.0:8010->8000/tcp`. Empty when it does not parse.

    Unparseable is returned as empty and treated as a finding by the caller rather than as
    loopback: a binding whose shape nobody recognizes is not a binding anybody checked.
    """
    left = binding.split("->", 1)[0].strip()
    if not left:
        return ""
    # IPv6 bindings arrive bracketed: `[::1]:8010`. Strip the brackets before splitting on
    # the port, or every IPv6 address parses as its own first hextet.
    if left.startswith("["):
        closing = left.find("]")
        return left[1:closing] if closing != -1 else ""
    parts = left.rsplit(":", 1)
    return parts[0] if len(parts) == 2 else ""


def _check_c17(holes: Mapping[str, HoleValue], obs: ExecutorObservation) -> Assertion:
    """The ingress surface and the launch posture — the half of ADR-0019 nothing covered.

    ADR-0019 recorded four unhardened defaults and left open which were Alfred's to assert and
    which S6's host-level `nftables` work already covered. **Two of them are Alfred's, and the
    reason is direction.** S6's default-drop is egress: it stops the container reaching out.
    Points 1 and 2 are the other way round and the other layer:

    1. **Ingress.** The agent server's `session_api_keys` defaults empty and "empty list
       implies the server will be unsecured"; `DockerWorkspace` then sets `api_key = None`
       outright. The server is told to bind `0.0.0.0` and is published with
       `-p {host_port}:8000`, which Docker binds on **all** host interfaces. That is an
       unauthenticated remote-code-execution endpoint reachable off-box, and no egress rule
       touches it. Two clauses, because either alone is insufficient: authentication is
       required, **and** the published binding must be loopback. An authenticated endpoint on
       `0.0.0.0` is one credential away, and a loopback binding with no credential trusts every
       process on the host.

    2. **Launch flags.** The SDK's own `docker run` argument list carries no `--cap-drop`, no
       `--read-only`, no `--security-opt`, no user namespace and no `--network`. These are
       readable from outside the sandbox, which is where this assertion already runs, so they
       are assertable rather than merely regrettable.

    **What is deliberately not here.** The agent user's `NOPASSWD:ALL` sudo is baked into the
    image, not chosen at launch, so no runtime flag can assert it away and reading the argv
    would never see it. It belongs to S6's layer-1 image-build closure check, and this
    docstring is the only place that split is currently written down outside the ADR.

    **Vacuity control.** An unread argv and an unread binding list are `not_executed`, never a
    pass — an assertion over an argv nobody collected would report the same thing on a
    hardened launch and an unhardened one, which is the shape D57 and F25 exist to reject.
    """
    unread: list[str] = []
    if not obs.container_launch_args:
        unread.append("container_launch_args")
    if not obs.published_port_bindings:
        unread.append("published_port_bindings")
    if unread:
        return Assertion(
            assertion_id="C17",
            outcome=AssertionOutcome.NOT_EXECUTED,
            detail=(
                f"nothing read for {', '.join(unread)}; the launch posture cannot be told "
                "from an argv and a binding list nobody collected"
            ),
        )

    problems: list[str] = []

    key = _as_key(holes["server_auth_key"])
    configured = _read(obs, key)
    if isinstance(configured, Absent):
        problems.append(f"{key!r} is absent from the loaded configuration; its value is unknown")
    elif configured is None:
        problems.append(
            f"{key!r} is None; DockerWorkspace sets it outright and the server is then unsecured"
        )
    elif isinstance(configured, (str, bytes)):
        if not configured.strip():
            problems.append(f"{key!r} is blank; a blank key is not a key")
    elif isinstance(configured, Sequence) and not configured:
        problems.append(
            f"{key!r} is empty; an empty list means the server runs unauthenticated, and it "
            "is the default"
        )

    off_box = sorted(
        binding for binding in obs.published_port_bindings if _bind_host(binding) not in _LOOPBACK
    )
    if off_box:
        problems.append(
            f"{len(off_box)} published port binding(s) are not loopback: {off_box[:5]}; "
            "the agent server is reachable from outside this machine"
        )

    argv = " ".join(obs.container_launch_args)
    for flag, consequence in _REQUIRED_LAUNCH_FLAGS:
        if flag not in obs.container_launch_args:
            problems.append(f"{flag} absent from the launch; {consequence}")
    if "--network" in obs.container_launch_args:
        index = obs.container_launch_args.index("--network")
        value = obs.container_launch_args[index + 1] if index + 1 < len(obs.container_launch_args) else ""
        if value in ("", "bridge", "default"):
            problems.append(
                f"--network is {value!r}, which is the default bridge; naming the flag is not "
                "the same as leaving the default network"
            )

    return _verdict(
        "C17",
        problems,
        "server authenticated; every published binding on loopback; launch hardened",
        observed={
            "published_port_bindings": ",".join(obs.published_port_bindings),
            # The full argv, not a summary. `reassert.compare` needs to tell a container
            # relaunched with different flags from one launched the same way twice, and a
            # summary of the flags this check happens to look at cannot show a flag it does not.
            "container_launch_args": argv,
        },
    )


# ================================================================== the register of shells
#
# Every `source` is a path:line inside EXECUTOR_REPO at EXECUTOR_COMMIT.

_SERVER = "openhands-agent-server/openhands/agent_server"
_SDK = "openhands-sdk/openhands/sdk"
_WORKSPACE = "openhands-workspace/openhands/workspace"

C1: Final = PremiseShell(
    assertion_id="C1",
    claim=(
        "Conversation persistence is configured, the conversation is not deleted on close, "
        "and every event the adaptor observed is present on disk on a read taken after close"
    ),
    holes=(
        Hole(
            name="persistence_dir_key",
            kind=HoleKind.CONFIG_KEY,
            question="Which configuration key controls conversation persistence, and what disables it?",
        ).filled(
            "persistence_dir",
            source=f"{_SERVER}/models.py:134",
            correction=(
                "The research note said persistence is opt-in and must be asserted enabled. "
                "It is `str | None` defaulting to 'workspace/conversations' — on unless "
                "explicitly set to None. The assertion is 'not disabled', not 'enabled'."
            ),
        ),
        Hole(
            name="delete_on_close_key",
            kind=HoleKind.CONFIG_KEY,
            question="Which key decides whether the persisted conversation survives the run?",
        ).filled(
            "delete_on_close",
            source=f"{_SDK}/conversation/conversation.py:142",
            correction=(
                "Not in the specification, and it falsified C1 as written (ADR-0019). It "
                "defaults to **True** in every constructor path; on close the client issues "
                "DELETE /conversations/{id} "
                f"({_SDK}/conversation/impl/remote_conversation.py:1729-1739) and the server "
                "safe_rmtree's the conversation directory "
                f"({_SERVER}/conversation_service.py:1725-1731). The workspace is preserved; "
                "the event log is not. C1 was reading a directory the default removes."
            ),
        ),
    ),
    check=_check_c1,
)

C2: Final = PremiseShell(
    assertion_id="C2",
    claim="No condenser configured, and zero condensation-class events in the stream",
    holes=(
        Hole(
            name="condenser_key",
            kind=HoleKind.CONFIG_KEY,
            question="Which field carries the condenser?",
        ).filled("condenser", source=f"{_SDK}/agent/base.py:265"),
        Hole(
            name="condenser_off_values",
            kind=HoleKind.CONFIG_VALUE,
            question="Which values mean no compaction? `None` is handled separately.",
        ).filled(
            ("NoOpCondenser", "NoOpCondenserSettings"),
            source=f"{_SDK}/context/condenser/no_op_condenser.py:7",
            correction=(
                "Two ways to be off, not one: the field is None, or it holds the explicit "
                "no-op. `PipelineCondenser` composes others, so a non-null value is never "
                "safe by inspection of the field name alone."
            ),
        ),
        Hole(
            name="condensation_event_classes",
            kind=HoleKind.EVENT_CLASS,
            question="Which event classes does condensation or summarization emit?",
        ).filled(
            ("Condensation", "CondensationRequest", "CondensationSummaryEvent"),
            source=f"{_SDK}/event/condenser.py:11,99,120",
            correction=(
                "The research note named only CondensationSummaryEvent, which is the third "
                "of three. Naming one of three is the misnamed-key hazard with two extra "
                "chances to occur."
            ),
        ),
    ),
    check=_check_c2,
)

C3: Final = PremiseShell(
    assertion_id="C3",
    claim=(
        "No approval surface and no interactive surface: NeverConfirm, never waited for "
        "confirmation, no user-sourced rejection, no VS Code or VNC server"
    ),
    holes=(
        Hole(
            name="confirmation_policy_key",
            kind=HoleKind.CONFIG_KEY,
            question="Which key carries the confirmation policy?",
        ).filled("confirmation_policy", source=f"{_SERVER}/models.py:153"),
        Hole(
            name="confirmation_policy_off_value",
            kind=HoleKind.CONFIG_VALUE,
            question="Which policy arm means never ask a human?",
        ).filled(
            "NeverConfirm",
            source=f"{_SDK}/security/confirmation_policy.py:35",
            correction="A polymorphic policy object, not a boolean. Arms: AlwaysConfirm, NeverConfirm, ConfirmRisky.",
        ),
        Hole(
            name="waiting_status_name",
            kind=HoleKind.CONFIG_VALUE,
            question="Which execution status means the agent is waiting for a human to approve?",
        ).filled(
            "WAITING_FOR_CONFIRMATION",
            source=f"{_SDK}/conversation/state.py:54",
            correction=(
                "This replaces the specification's 'zero approval-class events'. There is no "
                "approve-side event: rejection emits UserRejectObservation, acceptance is "
                "implicit on the second run() call and emits nothing. The persisted status is "
                "the only observable trace that a human was asked."
            ),
        ),
        Hole(
            name="interactive_surface_keys",
            kind=HoleKind.CONFIG_KEY,
            question="Which keys enable an interactive human surface inside the container?",
        ).filled(
            ("enable_vscode", "enable_vnc"),
            source=f"{_SERVER}/config.py:304,321",
            correction=(
                "Not in the specification at all. `enable_vscode` defaults to **True**: a full "
                "VS Code server runs inside the agent container unless disabled, and anything "
                "a human does there lands in no event stream at any layer."
            ),
        ),
        Hole(
            name="interactive_surface_ports",
            kind=HoleKind.CONFIG_VALUE,
            question="Which ports do those surfaces bind?",
        ).filled(
            ("8001",),
            source=f"{_SERVER}/config.py:309",
            correction="vscode_port default 8001. The agent server's own REST API is 8000 and is Alfred's channel, not a human surface.",
        ),
    ),
    check=_check_c3,
)

C5: Final = PremiseShell(
    assertion_id="C5",
    claim="Executor pinned by commit SHA in the repository the redirect actually leads to",
    holes=(
        Hole(
            name="executor_repo",
            kind=HoleKind.REPO_FACT,
            question="Which repository actually contains the executor?",
        ).filled(
            EXECUTOR_REPO,
            source="resolved 2026-08-18; see ADR-0018",
            correction=(
                "D38 names OpenHands/OpenHands. At 1916c904 that repository is 'Agent Canvas', "
                "a TypeScript/React/Electron control centre with eight Python files, all CI "
                "scripts and test mocks. The executor is a different repository."
            ),
        ),
        Hole(
            name="pinned_commit_sha",
            kind=HoleKind.REPO_FACT,
            question="Which commit is the executor pinned to?",
        ).filled(
            EXECUTOR_COMMIT,
            source="git ls-remote --symref, default branch HEAD at read time, 2026-08-18",
            correction=(
                "The specification says the repository has no tags to pin to. It has tags; "
                "v1.14.0 was the most recent at read time. HEAD was chosen deliberately so "
                "that the vocabulary read is the vocabulary pinned, not because none existed."
            ),
        ),
    ),
    check=_check_c5,
)

C10: Final = PremiseShell(
    assertion_id="C10",
    claim="Loaded configuration equals the harness's, with nothing hoisted from a file or the environment",
    holes=(
        Hole(
            name="config_search_paths",
            kind=HoleKind.SEARCH_PATH,
            question="Every path the agent server searches for configuration.",
        ).filled(
            ("workspace/openhands_agent_server_config.json",),
            source=f"{_SERVER}/config.py:26,27,441",
            correction=(
                "One file path, selected by the OPENHANDS_AGENT_SERVER_CONFIG_PATH "
                "environment variable and otherwise this default."
            ),
        ),
        Hole(
            name="config_env_prefix",
            kind=HoleKind.CONFIG_KEY,
            question="Which environment-variable prefix configures the server?",
        ).filled(
            "OH",
            source=f"{_SERVER}/config.py:25,446-450",
            correction=(
                "Not in the specification. `load_config` merges OH_* environment variables "
                "**over** the file, so a container configured entirely through the "
                "environment would pass a search-path check that found no file."
            ),
        ),
    ),
    check=_check_c10,
)

C16: Final = PremiseShell(
    assertion_id="C16",
    claim=(
        "The agent executes inside the container: a container-backed workspace kind, the "
        "remote conversation, and a recorded container id"
    ),
    holes=(
        Hole(
            name="container_workspace_kinds",
            kind=HoleKind.CONFIG_VALUE,
            question="Which workspace kinds put the agent in a container Alfred controls?",
        ).filled(
            ("DockerWorkspace",),
            source=f"{_WORKSPACE}/docker/workspace.py:53",
            correction=(
                "A closed set of one, and the exclusions are the point. `DockerDevWorkspace` "
                f"({_WORKSPACE}/docker/dev_workspace.py:10) builds the image on the fly from a "
                "base image, which is not the pinned image C5 and the layer-1 closure check "
                "assume. `APIRemoteWorkspace` and `OpenHandsCloudWorkspace` "
                f"({_WORKSPACE}/remote_api/workspace.py:19, {_WORKSPACE}/cloud/workspace.py:53) "
                "put the run on somebody else's machine, which D35 forbids outright. "
                "`ApptainerWorkspace` is a container but not one this specification's mount, "
                "egress and writable-set assertions were written against."
            ),
        ),
        Hole(
            name="host_workspace_kind",
            kind=HoleKind.CONFIG_VALUE,
            question="Which workspace kind runs the agent on the host?",
        ).filled(
            "LocalWorkspace",
            source=f"{_SDK}/workspace/local.py:17",
            correction=(
                "Named separately from 'not in the allowed set' so the failure says which "
                "way it went wrong. It is also **the default**: `Workspace(working_dir=...)` "
                f"with no host returns it ({_SDK}/workspace/workspace.py:36-49), while "
                f"`BaseWorkspace`'s docstring ({_SDK}/workspace/base.py:27-33) calls every "
                "workspace sandboxed."
            ),
        ),
        Hole(
            name="remote_conversation_class",
            kind=HoleKind.CONFIG_VALUE,
            question="Which conversation class runs the agent loop in the container rather than in-process?",
        ).filled(
            "RemoteConversation",
            source=f"{_SDK}/conversation/conversation.py:155,192",
            correction=(
                "The factory selects it from the workspace type and refuses `persistence_dir` "
                "for it — which is why C1 cites the **server-side** persistence_dir "
                f"({_SERVER}/models.py:134) and not this one. The same name at two layers "
                "with opposite requirements; unifying them would break C1 green-side."
            ),
        ),
    ),
    check=_check_c16,
)

C17: Final = PremiseShell(
    assertion_id="C17",
    claim=(
        "The agent server requires authentication, every published port is bound to loopback, "
        "and the container was launched with capabilities dropped and off the default network"
    ),
    holes=(
        Hole(
            name="server_auth_key",
            kind=HoleKind.CONFIG_KEY,
            question="Which configuration key authenticates the agent server, and what leaves it open?",
        ).filled(
            "session_api_keys",
            source=f"{_SERVER}/config.py:223-232,33-44",
            correction=(
                "It defaults to an empty list, and the field's own documentation says an "
                "empty list implies the server will be unsecured. `DockerWorkspace` then "
                f"sets `api_key = None` outright ({_WORKSPACE}/docker/workspace.py:278), so "
                "the default path is unauthenticated twice over. Read at O5 and recorded in "
                "ADR-0019; not re-read here, and the citation is what makes that checkable."
            ),
        ),
    ),
    check=_check_c17,
)

SHELLS: Final[tuple[PremiseShell, ...]] = (C1, C2, C3, C5, C10, C16, C17)
