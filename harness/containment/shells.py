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

    config: Mapping[str, object] = field(default_factory=dict)
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
    executor_repo: str | None = None
    executor_commit_sha: str | None = None
    executor_resolved_through_redirect: bool | None = None


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


def _verdict(assertion_id: str, problems: Sequence[str], claim: str) -> Assertion:
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


def _check_c1(holes: Mapping[str, HoleValue], obs: ExecutorObservation) -> Assertion:
    """Persistence configured, and every observed event durable at end of run.

    **The premise inverted at O5.** The research note said persistence was opt-in and had to
    be asserted enabled; the field defaults to `"workspace/conversations"`, so it is on unless
    something sets it to `None`. The assertion is therefore "not disabled" rather than
    "enabled", and the two differ on every default configuration.

    The count half is unchanged and is the half D53 and plan:431 both insist on: persistence
    is verified by end-of-run event count, **not by a flag**. A flag says what was intended.
    """
    key = _as_key(holes["persistence_dir_key"])
    configured = obs.config.get(key, "<absent>")
    problems: list[str] = []
    if configured is None:
        problems.append(f"{key!r} is None; the conversation is explicitly not persisted")
    elif configured == "<absent>":
        problems.append(f"{key!r} is absent from the loaded configuration; its value is unknown")
    elif not str(configured).strip():
        problems.append(f"{key!r} is empty; a blank path is not a persistence directory")

    missing = obs.observed_event_ids - obs.durable_event_ids
    if missing:
        problems.append(f"{len(missing)} observed event id(s) absent from disk")
    if len(obs.durable_event_ids) < len(obs.observed_event_ids):
        problems.append(
            f"durable count {len(obs.durable_event_ids)} below observed "
            f"{len(obs.observed_event_ids)}; the read log is a subset of unknown size (F19)"
        )
    return _verdict("C1", problems, "persistence configured; every observed event durable")


def _check_c2(holes: Mapping[str, HoleValue], obs: ExecutorObservation) -> Assertion:
    """No compaction: no condenser configured, and zero condensation events in the stream.

    Two ways to be off, both legitimate: the field is `None`, or it holds the explicit
    no-op. A check accepting only one of them would fail a correctly configured executor,
    and a check accepting any value would pass a summarizing one.
    """
    key = _as_key(holes["condenser_key"])
    off_values = set(_as_names(holes["condenser_off_values"]))
    configured = obs.config.get(key)
    problems: list[str] = []
    if configured is not None and str(configured) not in off_values:
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
    policy = obs.config.get(policy_key)
    if policy is not None and str(policy) != required_policy:
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
        if obs.config.get(surface_key) is True:
            problems.append(f"{surface_key!r} is True; an interactive surface is enabled")

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


# ================================================================== the register of shells
#
# Every `source` is a path:line inside EXECUTOR_REPO at EXECUTOR_COMMIT.

_SERVER = "openhands-agent-server/openhands/agent_server"
_SDK = "openhands-sdk/openhands/sdk"

C1: Final = PremiseShell(
    assertion_id="C1",
    claim=(
        "Conversation persistence is configured, and every event the adaptor observed is "
        "present on disk at end of run"
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

SHELLS: Final[tuple[PremiseShell, ...]] = (C1, C2, C3, C5, C10)
