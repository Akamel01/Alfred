"""C1–C15 beyond the two probes, each paired with the control that stops it reading green.

**How this suite would be shown vacuous** (D57). Nearly every test here asserts an outcome
for a constructed input, so a probe that returned a constant would satisfy half of them. The
file is written so that each assertion has at least one *must fail* and one *must pass* case
over the same code path, and the shell tests additionally assert the thing that cannot be
faked: `test_no_shell_can_pass_while_a_hole_is_unread` runs every shell in the register
against an observation chosen to satisfy its check, and requires `NOT_EXECUTED` anyway.

Three tests carry the weight:

- `test_no_shell_can_pass_while_a_hole_is_unread` is the whole argument of ADR-0007 as one
  assertion. If it can be made to pass by filling nothing, the shells are decoration.
- `test_the_open_hole_worklist_is_not_empty` fails the day somebody deletes a hole instead
  of answering it — which is the cheapest way to make O5 look finished.
- `test_measurement_refuses_an_unverified_premise_that_build_admits` is the reason
  `premise_verified` crosses to the handle at all. Without it the flag is decorative.
"""

from __future__ import annotations

import json
from pathlib import Path
from dataclasses import replace
from uuid import uuid4

import pytest

from harness.containment.assertions import Assertion, AssertionOutcome, AssertionReport
from harness.containment.denylist import Denylist
from harness.containment.denylist import load as load_denylist
from harness.containment.handle import to_report, to_result
from harness.containment.inside import (
    MountObservation,
    assert_credentials_absent,
    assert_mounts_match,
    assert_no_archives_or_caches,
    assert_writable_set,
)
from harness.containment.patch_side import (
    assert_patch_carries_no_oracle,
    normalized_source_hash,
)
from harness.containment.reassert import REASSERTED, compare, reassert
from harness.containment.shells import (
    CANVAS_COMMIT,
    CANVAS_REPO,
    EXECUTOR_COMMIT,
    EXECUTOR_REPO,
    REDIRECTING_PATHS,
    SHELLS,
    UNREAD,
    ExecutorObservation,
    Hole,
    HoleKind,
    PremiseShell,
    evaluate,
    open_holes,
    unsourced_holes,
)
from harness.worker.port import (
    Admissibility,
    AssertionResult,
    ContainmentFailure,
    RunId,
    SandboxHandle,
    check_handle,
)
from harness.worker.port import AssertionOutcome as PortOutcome
from harness.worker.port import AssertionReport as PortReport

DENYLIST_PATH = Path(__file__).resolve().parents[2] / "policy" / "oracle-denylist.json"


@pytest.fixture(scope="module")
def denylist() -> Denylist:
    return load_denylist(DENYLIST_PATH)


# ========================================================== the shells (C1,C2,C3,C5,C10,C16)


def test_no_shell_can_pass_while_a_hole_is_unread() -> None:
    """ADR-0007 as a single assertion, and it survives O5.

    The holes are answered now, so this resets one and checks the refusal still holds. The
    observation is deliberately the *most favourable* available — empty everything, which is
    what a check reads as "nothing enabled, nothing emitted" and passes on. The shell must
    still report `NOT_EXECUTED`, because one name it would look for is unread again.

    Written against a reset rather than deleted with O5, because the executor will change and
    a hole will go back to UNREAD. The refusal has to hold then too.
    """
    favourable = ExecutorObservation()
    for shell in SHELLS:
        blinded = PremiseShell(
            assertion_id=shell.assertion_id,
            claim=shell.claim,
            holes=(Hole(name=shell.holes[0].name, kind=shell.holes[0].kind, question="?"),)
            + shell.holes[1:],
            check=shell.check,
        )
        result = evaluate(blinded, favourable)
        assert result.outcome is AssertionOutcome.NOT_EXECUTED, shell.assertion_id
        assert not result.premise_verified, shell.assertion_id


def test_the_shell_register_is_not_empty() -> None:
    """D57. The loop above would pass over an empty register."""
    assert len(SHELLS) >= 6
    assert {s.assertion_id for s in SHELLS} == {"C1", "C2", "C3", "C5", "C10", "C16"}


def test_every_shell_has_at_least_one_hole() -> None:
    """A shell with no holes is not a shell; it is an assertion that forgot to say so."""
    for shell in SHELLS:
        assert shell.holes, shell.assertion_id


def test_every_hole_is_answered() -> None:
    """O5 is discharged. Any hole going back to UNREAD fails here and reopens it."""
    assert open_holes() == ()


def test_every_answer_cites_a_source() -> None:
    """The control that replaces the worklist.

    An unread hole announces itself; an answered one with no citation does not. It reads as a
    fact and may be something somebody typed, which is the state O5 existed to leave behind.
    """
    assert unsourced_holes() == ()
    for shell in SHELLS:
        for hole in shell.holes:
            assert hole.source, f"{shell.assertion_id}.{hole.name}"


def test_a_hole_cannot_be_answered_without_a_source() -> None:
    with pytest.raises(ValueError, match="not a reading"):
        Hole(name="x", kind=HoleKind.CONFIG_KEY, question="?").filled("v", source="  ")


def test_the_pins_are_recorded_and_are_not_the_frontend() -> None:
    """ADR-0018. D38 names the repository that is now Agent Canvas, which is not the executor."""
    assert EXECUTOR_REPO.endswith("software-agent-sdk")
    assert len(EXECUTOR_COMMIT) == 40
    assert EXECUTOR_REPO != CANVAS_REPO
    assert EXECUTOR_COMMIT != CANVAS_COMMIT
    assert REDIRECTING_PATHS


def test_an_unread_hole_is_falsy_and_distinguishable_from_an_empty_answer() -> None:
    """`()` means the executor was read and has no such class. UNREAD means nobody looked."""
    unread = Hole(name="x", kind=HoleKind.EVENT_CLASS, question="?")
    answered_empty = unread.filled((), source="somewhere.py:1")
    assert not unread.read
    assert answered_empty.read
    assert not unread.value  # falsy, so `if hole.value:` cannot misread it as present
    assert not answered_empty.value  # also falsy — which is why `.read` exists at all
    assert unread.value is not answered_empty.value


def test_a_hole_cannot_be_filled_with_unread() -> None:
    with pytest.raises(ValueError, match="not filling it"):
        Hole(name="x", kind=HoleKind.CONFIG_KEY, question="?").filled(UNREAD, source="x.py:1")


def test_filling_an_unknown_hole_name_raises() -> None:
    """A typo that silently did nothing would leave a shell unread while looking filled."""
    shell = _shell("C2")
    with pytest.raises(KeyError, match="no such hole"):
        shell.with_holes(condenser_disable_key="x")


# --------------------------------------------------- the checks, against what O5 actually read


def _shell(assertion_id: str) -> PremiseShell:
    return next(s for s in SHELLS if s.assertion_id == assertion_id)


CLEAN = ExecutorObservation(
    config={
        "persistence_dir": "workspace/conversations",
        "delete_on_close": False,
        "condenser": None,
        "confirmation_policy": "NeverConfirm",
        "enable_vscode": False,
        "enable_vnc": False,
    },
    config_hash="h",
    harness_config_hash="h",
    durable_read_after_close=True,
    workspace_kind="DockerWorkspace",
    conversation_kind="RemoteConversation",
    container_id="c0ffee0000",
    executor_repo=EXECUTOR_REPO,
    executor_commit_sha=EXECUTOR_COMMIT,
    executor_resolved_through_redirect=True,
)


@pytest.mark.parametrize("assertion_id", ["C1", "C2", "C3", "C5", "C10", "C16"])
def test_every_shell_passes_on_a_correctly_configured_executor(assertion_id: str) -> None:
    """The must-pass half. Without it every failing case below is met by refusing everything."""
    result = evaluate(_shell(assertion_id), CLEAN)
    assert result.outcome is AssertionOutcome.PASSED, result.detail
    assert result.premise_verified


# ---- C1: the premise inverted at O5


def test_c1_fails_when_persistence_is_explicitly_disabled() -> None:
    """`persistence_dir` defaults to a path, so the hazard is an explicit None, not an absent key."""
    obs = replace(CLEAN, config={**CLEAN.config, "persistence_dir": None})
    result = evaluate(_shell("C1"), obs)
    assert result.outcome is AssertionOutcome.FAILED
    assert "not persisted" in result.detail


def test_c1_fails_when_the_key_is_absent_rather_than_assuming_the_default() -> None:
    """The loaded configuration is what is asserted, not the library's default."""
    config = {k: v for k, v in CLEAN.config.items() if k != "persistence_dir"}
    result = evaluate(_shell("C1"), replace(CLEAN, config=config))
    assert result.outcome is AssertionOutcome.FAILED
    assert "absent" in result.detail


def test_c1_fails_when_an_observed_event_is_not_durable() -> None:
    """The count half, which D53 insists on because a flag says only what was intended."""
    obs = replace(
        CLEAN,
        observed_event_ids=frozenset({"e1", "e2"}),
        durable_event_ids=frozenset({"e1"}),
    )
    result = evaluate(_shell("C1"), obs)
    assert result.outcome is AssertionOutcome.FAILED
    assert "F19" in result.detail or "absent from disk" in result.detail



def test_c1_fails_when_the_conversation_is_deleted_on_close() -> None:
    """ADR-0019. The default removes the conversation directory; C1 was reading it after."""
    obs = replace(CLEAN, config={**CLEAN.config, "delete_on_close": True})
    result = evaluate(_shell("C1"), obs)
    assert result.outcome is AssertionOutcome.FAILED
    assert "removed on close" in result.detail


def test_c1_fails_when_delete_on_close_is_absent_because_its_default_deletes() -> None:
    """The absent case and the True case are the same hazard: the library default is True."""
    config = {k: v for k, v in CLEAN.config.items() if k != "delete_on_close"}
    result = evaluate(_shell("C1"), replace(CLEAN, config=config))
    assert result.outcome is AssertionOutcome.FAILED
    assert "defaults to True" in result.detail


@pytest.mark.parametrize("ordering", [None, False])
def test_c1_fails_when_the_durable_read_was_not_taken_after_close(ordering: bool | None) -> None:
    """Deletion off is not enough: a read taken before close says nothing about what survives.

    `None` — the adaptor not saying — fails the same way as an explicit "before". An
    unstated ordering read as satisfactory is how this clause would quietly stop running.
    """
    result = evaluate(_shell("C1"), replace(CLEAN, durable_read_after_close=ordering))
    assert result.outcome is AssertionOutcome.FAILED
    assert "after close" in result.detail or "before close" in result.detail


# ---- C16: the assertion the other four assumed


HOST_SIDE = replace(
    CLEAN,
    workspace_kind="LocalWorkspace",
    conversation_kind="LocalConversation",
    container_id=None,
)


def test_c16_fails_on_a_host_side_workspace() -> None:
    result = evaluate(_shell("C16"), HOST_SIDE)
    assert result.outcome is AssertionOutcome.FAILED
    assert "host filesystem" in result.detail


@pytest.mark.parametrize("assertion_id", ["C1", "C2", "C3", "C10"])
def test_the_other_shells_pass_on_a_host_side_run_which_is_why_c16_exists(
    assertion_id: str,
) -> None:
    """The vacuity demonstration, and the whole argument for the assertion.

    Nothing about this observation is in a container. Every one of these four still reports
    `passed`, because each reads configuration keys and event classes that exist identically
    when the agent runs on the host. Four green assertions over an agent with no container
    around it — ADR-0007's third outcome, one layer above where the shells guard.
    """
    result = evaluate(_shell(assertion_id), HOST_SIDE)
    assert result.outcome is AssertionOutcome.PASSED, result.detail


@pytest.mark.parametrize("kind", ["DockerDevWorkspace", "APIRemoteWorkspace", "ApptainerWorkspace"])
def test_c16_rejects_container_kinds_outside_the_closed_set(kind: str) -> None:
    """A closed set of names, not a substring or a base class.

    `DockerDevWorkspace` subclasses `DockerWorkspace` and would pass an `isinstance` check
    while building its image on the fly, which is not the pinned image C5 assumes.
    """
    result = evaluate(_shell("C16"), replace(CLEAN, workspace_kind=kind))
    assert result.outcome is AssertionOutcome.FAILED
    assert kind in result.detail


def test_c16_fails_when_the_workspace_kind_was_not_reported() -> None:
    """Unreported is not benign: it is precisely the thing the assertion cannot infer."""
    result = evaluate(_shell("C16"), replace(CLEAN, workspace_kind=None))
    assert result.outcome is AssertionOutcome.FAILED
    assert "not reported" in result.detail


def test_c16_fails_on_a_container_workspace_driven_by_a_local_conversation() -> None:
    """The factory forbids this pairing; the factory is not the only constructor."""
    result = evaluate(_shell("C16"), replace(CLEAN, conversation_kind="LocalConversation"))
    assert result.outcome is AssertionOutcome.FAILED
    assert "Alfred's own process" in result.detail


@pytest.mark.parametrize("container_id", [None, "", "   "])
def test_c16_fails_without_a_container_id(container_id: str | None) -> None:
    """Both names above are self-reports. Without a container they describe an object graph."""
    result = evaluate(_shell("C16"), replace(CLEAN, container_id=container_id))
    assert result.outcome is AssertionOutcome.FAILED
    assert "no container id" in result.detail


# ---- C2: two ways to be off, three event classes


@pytest.mark.parametrize("off", [None, "NoOpCondenser", "NoOpCondenserSettings"])
def test_c2_accepts_both_spellings_of_off(off: object) -> None:
    """A check accepting only None would fail a correctly configured executor."""
    obs = replace(CLEAN, config={**CLEAN.config, "condenser": off})
    assert evaluate(_shell("C2"), obs).outcome is AssertionOutcome.PASSED


def test_c2_fails_on_a_configured_condenser() -> None:
    obs = replace(CLEAN, config={**CLEAN.config, "condenser": "LLMSummarizingCondenser"})
    result = evaluate(_shell("C2"), obs)
    assert result.outcome is AssertionOutcome.FAILED
    assert "condenser is configured" in result.detail


@pytest.mark.parametrize(
    "event_class", ["Condensation", "CondensationRequest", "CondensationSummaryEvent"]
)
def test_c2_catches_each_of_the_three_condensation_classes(event_class: str) -> None:
    """The research note named one of three. Each is checked separately, so a missed name shows."""
    obs = replace(CLEAN, stream_event_classes=("MessageAction", event_class))
    result = evaluate(_shell("C2"), obs)
    assert result.outcome is AssertionOutcome.FAILED
    assert "I16" in result.detail


def test_c2_fails_on_a_condensation_event_even_with_the_field_off() -> None:
    """The two conjuncts are independent findings once the vocabulary is right."""
    obs = replace(CLEAN, stream_event_classes=("Condensation",))
    assert obs.config["condenser"] is None
    assert evaluate(_shell("C2"), obs).outcome is AssertionOutcome.FAILED


# ---- C3: the conjunct that could not be implemented, and the surface nobody specified


def test_c3_fails_on_a_confirming_policy() -> None:
    obs = replace(CLEAN, config={**CLEAN.config, "confirmation_policy": "AlwaysConfirm"})
    result = evaluate(_shell("C3"), obs)
    assert result.outcome is AssertionOutcome.FAILED
    assert "NeverConfirm" in result.detail


def test_c3_catches_a_human_approval_that_emits_no_event() -> None:
    """The whole reason the specification's third conjunct was replaced.

    Approval emits nothing: rejection produces UserRejectObservation and acceptance is
    implicit on the second run() call. An event-counting check sees a clean stream here.
    """
    obs = replace(
        CLEAN,
        execution_statuses=("RUNNING", "WAITING_FOR_CONFIRMATION", "RUNNING", "FINISHED"),
        stream_event_classes=("MessageAction", "ActionEvent", "ObservationEvent"),
    )
    result = evaluate(_shell("C3"), obs)
    assert result.outcome is AssertionOutcome.FAILED
    assert "emits no event" in result.detail


def test_c3_catches_a_user_sourced_rejection() -> None:
    """A human rejecting proves a human was being asked, whatever the configuration says."""
    obs = replace(CLEAN, rejection_sources=("user",))
    result = evaluate(_shell("C3"), obs)
    assert result.outcome is AssertionOutcome.FAILED
    assert "rejection_source='user'" in result.detail


def test_c3_does_not_fire_on_alfreds_own_hook_block() -> None:
    """`rejection_source='hook'` is Alfred's PreToolUse block, not a human approval surface."""
    obs = replace(CLEAN, rejection_sources=("hook", "hook"))
    assert evaluate(_shell("C3"), obs).outcome is AssertionOutcome.PASSED


@pytest.mark.parametrize("surface", ["enable_vscode", "enable_vnc"])
def test_c3_catches_an_interactive_surface_enabled(surface: str) -> None:
    """`enable_vscode` defaults to True: a VS Code server inside the container, unless disabled."""
    obs = replace(CLEAN, config={**CLEAN.config, surface: True})
    result = evaluate(_shell("C3"), obs)
    assert result.outcome is AssertionOutcome.FAILED
    assert surface in result.detail


def test_c3_catches_the_surface_listening_even_when_configuration_says_off() -> None:
    """Configuration is an intention; a listening socket is the fact."""
    obs = replace(CLEAN, listening_ports=(8001,))
    result = evaluate(_shell("C3"), obs)
    assert result.outcome is AssertionOutcome.FAILED
    assert "listening" in result.detail


def test_c3_ignores_the_agent_servers_own_api_port() -> None:
    """8000 is the REST API Alfred drives. It is not a human surface."""
    obs = replace(CLEAN, listening_ports=(8000,))
    assert evaluate(_shell("C3"), obs).outcome is AssertionOutcome.PASSED


# ---- C5: the repository the plan named is not the executor


def test_c5_fails_on_the_frontend_repository() -> None:
    """D38 names this repository. At its HEAD it is Agent Canvas and holds no executor."""
    obs = replace(CLEAN, executor_repo=CANVAS_REPO, executor_commit_sha=CANVAS_COMMIT)
    result = evaluate(_shell("C5"), obs)
    assert result.outcome is AssertionOutcome.FAILED


def test_c5_fails_when_the_commit_was_not_resolved_through_the_redirect() -> None:
    obs = replace(CLEAN, executor_resolved_through_redirect=False)
    result = evaluate(_shell("C5"), obs)
    assert result.outcome is AssertionOutcome.FAILED
    assert "redirect" in result.detail


def test_c5_fails_on_a_drifted_commit() -> None:
    obs = replace(CLEAN, executor_commit_sha="f" * 40)
    assert evaluate(_shell("C5"), obs).outcome is AssertionOutcome.FAILED


# ---- C10: the channel the specification did not enumerate


def test_c10_fails_on_a_hoisted_configuration_file() -> None:
    obs = replace(CLEAN, config_files_found=("workspace/openhands_agent_server_config.json",))
    result = evaluate(_shell("C10"), obs)
    assert result.outcome is AssertionOutcome.FAILED
    assert "searched paths" in result.detail


def test_c10_catches_configuration_hoisted_through_the_environment() -> None:
    """The half that was not specified. `OH_*` variables are merged over the file.

    A container configured entirely through the environment leaves no file to find, so a
    search-path check alone reports a clean pass over a fully hoisted configuration.
    """
    obs = replace(CLEAN, config_env_names=("PATH", "OH_ENABLE_VSCODE", "OH_SESSION_API_KEYS_0"))
    result = evaluate(_shell("C10"), obs)
    assert result.outcome is AssertionOutcome.FAILED
    assert "environment variable" in result.detail


def test_c10_ignores_environment_variables_outside_the_prefix() -> None:
    obs = replace(CLEAN, config_env_names=("PATH", "HOME", "OHM_SOMETHING"))
    assert evaluate(_shell("C10"), obs).outcome is AssertionOutcome.PASSED


def test_c10_fails_when_the_hashes_differ() -> None:
    obs = replace(CLEAN, config_hash="a", harness_config_hash="b")
    assert evaluate(_shell("C10"), obs).outcome is AssertionOutcome.FAILED


# ================================================================================== C8


def test_c8_fails_on_a_secret_bearing_name() -> None:
    result = assert_credentials_absent({"PATH": "/usr/bin", "GITHUB_TOKEN": "x"})
    assert result.outcome is AssertionOutcome.FAILED
    assert "GITHUB_TOKEN" in result.detail


def test_c8_fails_on_a_credential_shaped_value_under_an_innocent_name() -> None:
    """The case the name list misses, and the one an exfiltration path would choose."""
    result = assert_credentials_absent({"PATH": "/usr/bin", "X": "ghp_" + "a" * 36})
    assert result.outcome is AssertionOutcome.FAILED
    assert "credential-shaped" in result.detail


def test_c8_never_puts_the_secret_into_the_detail() -> None:
    """A probe that reported the value would write the credential to the evidence chain."""
    secret = "ghp_" + "b" * 36
    result = assert_credentials_absent({"PATH": "/usr/bin", "X": secret})
    assert secret not in result.detail


def test_c8_passes_on_a_clean_environment() -> None:
    result = assert_credentials_absent({"PATH": "/usr/bin", "HOME": "/root", "LANG": "C"})
    assert result.outcome is AssertionOutcome.PASSED


def test_c8_is_not_executed_on_an_empty_environment() -> None:
    """The control. An empty environment is what a probe that failed to read one returns."""
    result = assert_credentials_absent({})
    assert result.outcome is AssertionOutcome.NOT_EXECUTED


# ================================================================================== C9


def test_c9_fails_on_an_extra_mount() -> None:
    spec = [MountObservation("/repo", read_only=False)]
    observed = [MountObservation("/repo", read_only=False), MountObservation("/etc/x", True)]
    result = assert_mounts_match(observed, spec)
    assert result.outcome is AssertionOutcome.FAILED
    assert "not specified" in result.detail


def test_c9_fails_on_a_mode_mismatch_which_is_the_quietest_of_the_three() -> None:
    spec = [MountObservation("/repo", read_only=True)]
    observed = [MountObservation("/repo", read_only=False)]
    result = assert_mounts_match(observed, spec)
    assert result.outcome is AssertionOutcome.FAILED
    assert "mode differs" in result.detail


def test_c9_passes_when_the_sets_match_mode_for_mode() -> None:
    spec = [MountObservation("/repo", read_only=False), MountObservation("/usr/lib", True)]
    assert assert_mounts_match(list(spec), list(spec)).outcome is AssertionOutcome.PASSED


@pytest.mark.parametrize(
    ("observed", "specified"),
    [([], [MountObservation("/repo", False)]), ([MountObservation("/repo", False)], [])],
    ids=["no-enumeration", "no-spec"],
)
def test_c9_is_not_executed_when_either_side_is_empty(
    observed: list[MountObservation], specified: list[MountObservation]
) -> None:
    assert assert_mounts_match(observed, specified).outcome is AssertionOutcome.NOT_EXECUTED


# ================================================================================= C12


def test_c12_fails_on_a_writable_interpreter() -> None:
    result = assert_writable_set(
        [MountObservation("/repo", False), MountObservation("/usr/lib/python3.12", False)],
        writable_roots=["/repo"],
        interpreter_paths=["/usr/lib/python3.12/bin/python3"],
    )
    assert result.outcome is AssertionOutcome.FAILED
    assert "writable" in result.detail


def test_c12_fails_on_a_writable_mount_outside_the_declared_roots() -> None:
    result = assert_writable_set(
        [MountObservation("/repo", False), MountObservation("/scratch", False)],
        writable_roots=["/repo"],
        interpreter_paths=[],
    )
    assert result.outcome is AssertionOutcome.FAILED
    assert "/scratch" in result.detail


def test_c12_takes_the_longest_covering_mount() -> None:
    """A read-only tree with a writable subtree mounted over it is writable at that subtree.

    The shorter path would report read-only and be wrong, which is a mid-run install into
    site-packages passing the assertion that exists to stop it.
    """
    result = assert_writable_set(
        [
            MountObservation("/repo", False),
            MountObservation("/usr", True),
            MountObservation("/usr/lib/python3.12/site-packages", False),
        ],
        writable_roots=["/repo"],
        interpreter_paths=["/usr/lib/python3.12/site-packages/python3"],
    )
    assert result.outcome is AssertionOutcome.FAILED


def test_c12_passes_on_a_read_only_interpreter_outside_the_writable_root() -> None:
    result = assert_writable_set(
        [MountObservation("/repo", False), MountObservation("/usr", True)],
        writable_roots=["/repo"],
        interpreter_paths=["/usr/bin/python3"],
    )
    assert result.outcome is AssertionOutcome.PASSED


def test_c12_fails_when_zero_interpreters_were_enumerated() -> None:
    """F15 again. A read-only assertion over no interpreters checked nothing."""
    result = assert_writable_set(
        [MountObservation("/repo", False)], writable_roots=["/repo"], interpreter_paths=[]
    )
    assert result.outcome is AssertionOutcome.FAILED
    assert "scanned nothing" in result.detail


def test_c12_is_not_executed_without_declared_roots() -> None:
    result = assert_writable_set(
        [MountObservation("/repo", False)], writable_roots=[], interpreter_paths=["/usr/bin/python3"]
    )
    assert result.outcome is AssertionOutcome.NOT_EXECUTED


# ================================================================================= C13


def test_c13_fails_on_a_wheel(tmp_path: Path) -> None:
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "thing-1.0-py3-none-any.whl").write_bytes(b"")
    result = assert_no_archives_or_caches([tmp_path])
    assert result.outcome is AssertionOutcome.FAILED
    assert "archives" in result.detail


def test_c13_fails_on_an_empty_resolver_cache_directory(tmp_path: Path) -> None:
    """An empty pip cache is a resolver configured to have one. Name, not contents."""
    (tmp_path / "outer").mkdir()
    (tmp_path / "outer" / "pip").mkdir()
    result = assert_no_archives_or_caches([tmp_path])
    assert result.outcome is AssertionOutcome.FAILED
    assert "caches" in result.detail


def test_c13_passes_on_a_clean_tree(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("x = 1\n")
    assert assert_no_archives_or_caches([tmp_path]).outcome is AssertionOutcome.PASSED


def test_c13_is_not_executed_on_no_roots() -> None:
    assert assert_no_archives_or_caches([]).outcome is AssertionOutcome.NOT_EXECUTED


def test_c13_is_not_executed_on_an_empty_tree(tmp_path: Path) -> None:
    """A walk that visited zero entries is what a wrong root produces."""
    assert assert_no_archives_or_caches([tmp_path]).outcome is AssertionOutcome.NOT_EXECUTED


def test_c13_is_not_executed_when_a_root_does_not_exist(tmp_path: Path) -> None:
    assert (
        assert_no_archives_or_caches([tmp_path / "nope"]).outcome is AssertionOutcome.NOT_EXECUTED
    )


# ================================================================================= C14


def _passed(assertion_id: str) -> Assertion:
    return Assertion(assertion_id, AssertionOutcome.PASSED, "ok")


def test_c14_passes_when_every_member_re_asserts() -> None:
    assert reassert([_passed(i) for i in REASSERTED]).outcome is AssertionOutcome.PASSED


def test_c14_is_not_executed_when_a_member_is_absent() -> None:
    """Absence is a failure, never a skip — and it is not the same as finding a problem."""
    result = reassert([_passed(i) for i in REASSERTED[:-1]])
    assert result.outcome is AssertionOutcome.NOT_EXECUTED
    assert REASSERTED[-1] in result.detail


def test_c14_fails_when_a_member_failed_at_the_end() -> None:
    results = [_passed(i) for i in REASSERTED[:-1]]
    results.append(Assertion(REASSERTED[-1], AssertionOutcome.FAILED, "a wheel appeared"))
    result = reassert(results)
    assert result.outcome is AssertionOutcome.FAILED
    assert "indeterminate" in result.detail


def test_c14_carries_an_unverified_premise_upward() -> None:
    """A fold reporting a clean premise over an unverified member would launder the state."""
    results = [_passed(i) for i in REASSERTED[:-1]]
    results.append(Assertion(REASSERTED[-1], AssertionOutcome.PASSED, "ok", premise_verified=False))
    assert reassert(results).premise_verified is False


def test_c14_compare_names_only_what_changed_during_the_run() -> None:
    boot = AssertionReport(tuple(_passed(i) for i in REASSERTED))
    end = AssertionReport(
        tuple(
            _passed(i) if i != "C13" else Assertion("C13", AssertionOutcome.FAILED, "appeared")
            for i in REASSERTED
        )
    )
    assert compare(boot, end) == ("C13",)


def test_c14_compare_is_silent_when_nothing_moved() -> None:
    boot = AssertionReport(tuple(_passed(i) for i in REASSERTED))
    assert compare(boot, boot) == ()


# ================================================================================= C15

_DIFF_HEADER = "--- a/{p}\n+++ b/{p}\n@@ -0,0 +1 @@\n"


def _diff(path: str, *added: str) -> str:
    return _DIFF_HEADER.format(p=path) + "".join(f"+{line}\n" for line in added)


def test_c15_fails_on_a_denied_dependency(denylist: Denylist) -> None:
    distribution = sorted(denylist.denied_distributions)[0]
    result = assert_patch_carries_no_oracle(_diff("pyproject.toml", f'  "{distribution}>=0.1",'), denylist)
    assert result.outcome is AssertionOutcome.FAILED
    assert "dependency" in result.detail


def test_c15_fails_on_a_denied_import(denylist: Denylist) -> None:
    module = sorted(denylist.denied_modules)[0]
    result = assert_patch_carries_no_oracle(_diff("src/metrics/ttc.py", f"import {module}"), denylist)
    assert result.outcome is AssertionOutcome.FAILED
    assert "import" in result.detail


def test_c15_fails_on_a_from_import_too(denylist: Denylist) -> None:
    module = sorted(denylist.denied_modules)[0]
    result = assert_patch_carries_no_oracle(
        _diff("src/metrics/ttc.py", f"    from {module} import measure"), denylist
    )
    assert result.outcome is AssertionOutcome.FAILED


def test_c15_fails_on_a_vendored_source_file(denylist: Denylist) -> None:
    """The clause the other two miss: a copy imports nothing denied and declares nothing."""
    body = "def ttc(a, b):\n    return a - b"
    digest = normalized_source_hash(body)
    result = assert_patch_carries_no_oracle(
        _diff("src/metrics/copied.py", *body.splitlines()),
        denylist,
        denied_source_hashes={digest: "crime/measure/time/ttc.py"},
    )
    assert result.outcome is AssertionOutcome.FAILED
    assert "vendored-source" in result.detail


def test_c15_normalization_survives_a_reformat() -> None:
    """Whitespace and comments are the reformat an agent produces without meaning to."""
    assert normalized_source_hash("def f(x):\n    return x  # note") == normalized_source_hash(
        "def   f(x):\n\n\treturn x"
    )


def test_c15_passes_on_an_ordinary_patch(denylist: Denylist) -> None:
    result = assert_patch_carries_no_oracle(
        _diff("src/metrics/ttc.py", "import numpy as np", "def ttc(a, b): return a - b"),
        denylist,
        denied_source_hashes={"0" * 64: "crime/measure/time/ttc.py"},
    )
    assert result.outcome is AssertionOutcome.PASSED
    assert result.premise_verified


def test_c15_says_so_when_clause_three_did_not_run(denylist: Denylist) -> None:
    """A two-clause check reporting a three-clause pass is the vacuity this avoids."""
    result = assert_patch_carries_no_oracle(_diff("src/x.py", "import numpy"), denylist)
    assert result.outcome is AssertionOutcome.PASSED
    assert result.premise_verified is False
    assert "2 of 3" in result.detail


def test_c15_is_not_executed_on_an_empty_diff(denylist: Denylist) -> None:
    assert (
        assert_patch_carries_no_oracle("", denylist).outcome is AssertionOutcome.NOT_EXECUTED
    )


def test_c15_is_not_executed_on_a_diff_with_no_added_lines(denylist: Denylist) -> None:
    diff = "--- a/x.py\n+++ b/x.py\n@@ -1 +0,0 @@\n-import numpy\n"
    assert (
        assert_patch_carries_no_oracle(diff, denylist).outcome is AssertionOutcome.NOT_EXECUTED
    )


def test_c15_ignores_context_and_removed_lines(denylist: Denylist) -> None:
    """Removing a denied import is the fix, not the offence."""
    module = sorted(denylist.denied_modules)[0]
    diff = f"--- a/x.py\n+++ b/x.py\n@@ -1,2 +1,1 @@\n-import {module}\n import numpy\n+import scipy\n"
    assert assert_patch_carries_no_oracle(diff, denylist).outcome is AssertionOutcome.PASSED


def test_c15_is_not_executed_against_an_empty_denylist() -> None:
    empty = Denylist(version=1, denied=(), permitted_substrate=(), sha256="0" * 64)
    result = assert_patch_carries_no_oracle(_diff("x.py", "import numpy"), empty)
    assert result.outcome is AssertionOutcome.NOT_EXECUTED


# ======================================== the crossing, and what the gate does with it


def _handle(*results: AssertionResult) -> SandboxHandle:
    return SandboxHandle(
        run_id=RunId(uuid4()),
        image_digest="sha256:" + "a" * 64,
        boot_report=PortReport(at="boot", results=results),
        mounts=(),
    )


def test_the_crossing_preserves_an_unverified_premise() -> None:
    """The whole reason this module exists: the flag used to die at the boundary."""
    result = to_result(
        Assertion("C2", AssertionOutcome.PASSED, "ok", premise_verified=False),
        executed_inside_container=False,
    )
    assert result.premise_verified is False
    assert result.outcome is PortOutcome.PASSED


def test_the_crossing_preserves_not_executed() -> None:
    result = to_result(
        Assertion("C1", AssertionOutcome.NOT_EXECUTED, "hole"), executed_inside_container=True
    )
    assert result.outcome is PortOutcome.NOT_EXECUTED


def test_the_report_marks_inside_and_outside_from_the_specification_table() -> None:
    report = to_report(
        [_passed("C6"), _passed("C4")], at="boot", inside=frozenset({"C6", "C7"})
    )
    by_id = report.by_id()
    assert by_id["C6"].executed_inside_container is True
    assert by_id["C4"].executed_inside_container is False


def test_measurement_refuses_an_unverified_premise_that_build_admits() -> None:
    """ADR-0007's admissibility split, and the reason the flag crosses the boundary."""
    handle = _handle(
        to_result(
            Assertion("C2", AssertionOutcome.PASSED, "ok", premise_verified=False),
            executed_inside_container=False,
        )
    )
    check_handle(handle, frozenset({"C2"}), admissibility=Admissibility.BUILD)
    with pytest.raises(ContainmentFailure, match="unverified premise"):
        check_handle(handle, frozenset({"C2"}), admissibility=Admissibility.MEASUREMENT)


def test_measurement_is_the_default() -> None:
    """A default of BUILD would admit a vacuous control every time a caller forgot."""
    handle = _handle(
        to_result(
            Assertion("C2", AssertionOutcome.PASSED, "ok", premise_verified=False),
            executed_inside_container=False,
        )
    )
    with pytest.raises(ContainmentFailure, match="unverified premise"):
        check_handle(handle, frozenset({"C2"}))


def test_a_verified_premise_is_admitted_as_a_measurement() -> None:
    """The must-pass half. Without it the refusal above is satisfied by refusing everything."""
    handle = _handle(
        to_result(Assertion("C6", AssertionOutcome.PASSED, "ok"), executed_inside_container=True)
    )
    check_handle(handle, frozenset({"C6"}), admissibility=Admissibility.MEASUREMENT)


def test_a_shell_never_reaches_dispatch() -> None:
    """End to end: an unread shell becomes not_executed, crosses, and the gate refuses."""
    assertion = evaluate(SHELLS[0], ExecutorObservation())
    handle = _handle(to_result(assertion, executed_inside_container=False))
    with pytest.raises(ContainmentFailure, match="did not pass"):
        check_handle(handle, frozenset({SHELLS[0].assertion_id}))


def test_the_committed_denylist_is_what_c15_runs_against(denylist: Denylist) -> None:
    """A suite that built its own denylist would never notice the committed one going empty."""
    assert denylist.denied_modules
    assert json.loads(DENYLIST_PATH.read_text())["version"] == denylist.version
