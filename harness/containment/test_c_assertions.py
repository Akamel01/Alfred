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
import sys
from dataclasses import replace
from pathlib import Path
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
from harness.containment.oracle_absence import probe
from harness.containment.patch_side import (
    assert_patch_carries_no_oracle,
    imported_top_level_names,
    normalized_source_hash,
)
from harness.containment.reassert import (
    REASSERTED,
    DriftKind,
    compare,
    drifted_ids,
    reassert,
    value_blind,
)
from harness.containment.shells import (
    C1,
    C17,
    CANVAS_COMMIT,
    ConfigContractViolation,
    ConfigKeyConfusion,
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
    confusable_config_keys,
    evaluate,
    named_config_keys,
    open_holes,
    unsourced_holes,
    validated_config,
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
    assert len(SHELLS) >= 7
    assert {s.assertion_id for s in SHELLS} == {"C1", "C2", "C3", "C5", "C10", "C16", "C17"}


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

# C17's subject. Defined beside `CLEAN` rather than in the C17 section below because the C14
# coverage assertion needs it too: C17 is a member of `REASSERTED`, so the launch posture has
# to be built the way the adaptor builds it in both places, from one definition.
_HARDENED_ARGV = ("docker", "run", "--cap-drop", "ALL", "--network", "none", "img")
_LOOPBACK_BINDING = ("127.0.0.1:8010->8000/tcp",)

CLEAN_LAUNCH = replace(
    CLEAN,
    config={**CLEAN.config, "session_api_keys": ["k"]},
    container_launch_args=_HARDENED_ARGV,
    published_port_bindings=_LOOPBACK_BINDING,
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



# ---- how every check reads the adaptor's configuration
#
# `ExecutorObservation.config` is `Mapping[str, object]` with no schema. Before these tests
# each check invented its own reading and they disagreed, which produced three green
# assertions over live hazards. The discipline, asserted here across every check that reads
# configuration: absent is unknown, uninterpretable is a finding, and neither is a pass.


@pytest.mark.parametrize("spelling", [True, 1, "true", "True", "TRUE", " on ", "yes"])
def test_c3_catches_an_interactive_surface_however_the_channel_spells_true(
    spelling: object,
) -> None:
    """The most serious of the review findings, and the one with a live hazard behind it.

    `enable_vscode` defaults to True and puts a VS Code server inside the agent container.
    The check compared with `is True`, so it passed on every spelling but the Python one —
    and C10's whole finding is that configuration also arrives through `OH_*` environment
    variables, where every value is a string.
    """
    obs = replace(CLEAN, config={**CLEAN.config, "enable_vscode": spelling})
    result = evaluate(_shell("C3"), obs)
    assert result.outcome is AssertionOutcome.FAILED, result.detail
    assert "enable_vscode" in result.detail


@pytest.mark.parametrize("spelling", [False, 0, "false", "FALSE", "off", "no"])
def test_c3_accepts_every_spelling_of_off(spelling: object) -> None:
    """The control. Without it the test above is satisfied by a check that refuses everything."""
    obs = replace(CLEAN, config={**CLEAN.config, "enable_vscode": spelling})
    assert evaluate(_shell("C3"), obs).outcome is AssertionOutcome.PASSED


def test_c3_fails_on_a_value_that_does_not_spell_a_boolean() -> None:
    """An unreadable value is not a value that says off."""
    obs = replace(CLEAN, config={**CLEAN.config, "enable_vnc": "maybe"})
    result = evaluate(_shell("C3"), obs)
    assert result.outcome is AssertionOutcome.FAILED
    assert "does not spell a boolean" in result.detail


@pytest.mark.parametrize(
    ("assertion_id", "key"),
    [
        ("C1", "persistence_dir"),
        ("C1", "delete_on_close"),
        ("C2", "condenser"),
        ("C3", "confirmation_policy"),
        ("C3", "enable_vscode"),
        ("C3", "enable_vnc"),
    ],
)
def test_no_check_reads_an_absent_key_as_the_library_default(
    assertion_id: str, key: str
) -> None:
    """C1 refused to assume a default and C2 assumed one, for the same class of fact.

    C2's default happens to be `None`, which is off, which is what let the asymmetry survive:
    the check was right by coincidence for the one executor whose default nobody had changed.
    """
    config = {k: v for k, v in CLEAN.config.items() if k != key}
    result = evaluate(_shell(assertion_id), replace(CLEAN, config=config))
    assert result.outcome is AssertionOutcome.FAILED, result.detail
    assert key in result.detail


def test_a_configuration_value_may_be_the_string_the_sentinel_used_to_be() -> None:
    """The absent sentinel is a singleton, not `"<absent>"`.

    `shells.py` builds `Unread` precisely so a sentinel cannot collide with a real value, and
    then spelled a second sentinel as a string two hundred lines later. A directory named
    `<absent>` is absurd; a check that cannot tell one from a missing key is the point.
    """
    obs = replace(CLEAN, config={**CLEAN.config, "persistence_dir": "<absent>"})
    result = evaluate(_shell("C1"), obs)
    assert result.outcome is AssertionOutcome.PASSED, result.detail

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


def test_the_reassertion_set_is_stated_not_derived() -> None:
    """The set is closed and written down. D57: the loops below pass over an empty tuple.

    Pinned as a literal rather than as a length, because the failure this guards against is a
    member quietly leaving — which shrinks the set without breaking anything that reads it.
    """
    assert REASSERTED == ("C7", "C9", "C12", "C13", "C16", "C17")


def test_c14_passes_when_every_member_re_asserts() -> None:
    assert reassert([_passed(i) for i in REASSERTED]).outcome is AssertionOutcome.PASSED


def test_c14_fails_when_the_container_is_gone_at_the_end_of_the_run() -> None:
    """Why C16 is in the set. `docker run` carries `--rm`: a container that exited mid-run
    leaves nothing behind, so the adaptor has no container id and C16 fails at the end while
    having passed at boot. That is `indeterminate`, not a verdict about the agent.
    """
    end = [_passed(i) for i in REASSERTED if i != "C16"]
    end.append(evaluate(_shell("C16"), replace(CLEAN, container_id=None)))
    result = reassert(end)
    assert result.outcome is AssertionOutcome.FAILED
    assert "indeterminate" in result.detail
    boot = AssertionReport(tuple(_passed(i) for i in REASSERTED))
    assert drifted_ids(compare(boot, AssertionReport(tuple(end)))) == ("C16",)


def test_c14_compare_sees_a_container_swapped_for_another_of_the_same_kind() -> None:
    """The case that made `compare` read values. Two passes, two different containers.

    Nothing about the outcomes moved — both ends are `passed`, both are `DockerWorkspace`,
    both are `RemoteConversation`. The run moved underneath a control that an outcome-level
    comparison would have called clean.
    """
    boot = evaluate(_shell("C16"), replace(CLEAN, container_id="aaaaaaaaaaaa"))
    end = evaluate(_shell("C16"), replace(CLEAN, container_id="bbbbbbbbbbbb"))
    assert boot.outcome is end.outcome is AssertionOutcome.PASSED

    drifts = compare(AssertionReport((boot,)), AssertionReport((end,)))
    assert [(d.kind, d.key) for d in drifts] == [(DriftKind.VALUE, "container_id")]
    assert drifts[0].boot == "aaaaaaaaaaaa"
    assert drifts[0].end == "bbbbbbbbbbbb"


def test_c14_compare_records_the_container_id_in_full_not_the_prose_prefix() -> None:
    """`detail` truncates the id to twelve characters; a diff over a prefix is a prefix diff."""
    long_id = "c" * 64
    result = evaluate(_shell("C16"), replace(CLEAN, container_id=long_id))
    assert result.observed["container_id"] == long_id


def test_c14_catches_a_relaunch_that_reopened_the_ingress_surface() -> None:
    """Why C17 is in the set. The drift kinds are the assertion, not the outcomes.

    A container relaunched mid-run with the port republished on `0.0.0.0` and `--cap-drop`
    gone passes C17 at boot — the gate that would have refused it has already run — and is
    never re-checked without this. `drifted_ids` naming C17 is what fails if C17 leaves
    `REASSERTED`; the `VALUE` kinds on both keys are what fails if the check stops reading
    the argv, which an outcome-level pass/fail pair cannot tell apart from a real relaunch.
    """
    boot = evaluate(_shell("C17"), CLEAN_LAUNCH)
    end = evaluate(
        _shell("C17"),
        replace(
            CLEAN_LAUNCH,
            container_launch_args=("docker", "run", "img"),
            published_port_bindings=("0.0.0.0:8010->8000/tcp",),
        ),
    )
    assert boot.outcome is AssertionOutcome.PASSED
    assert end.outcome is AssertionOutcome.FAILED

    drifts = compare(AssertionReport((boot,)), AssertionReport((end,)))
    assert drifted_ids(drifts) == ("C17",)
    assert {(d.kind, d.key) for d in drifts} == {
        (DriftKind.OUTCOME, None),
        (DriftKind.VALUE, "container_launch_args"),
        (DriftKind.VALUE, "published_port_bindings"),
    }
    assert reassert([_passed(i) for i in REASSERTED if i != "C17"] + [end]).outcome is (
        AssertionOutcome.FAILED
    )


def test_c14_sees_a_relaunch_that_kept_the_posture_and_changed_the_argv() -> None:
    """The case an outcome comparison cannot express, for C17 rather than for C16.

    Both ends pass: capabilities dropped, off the default network, loopback binding. The
    container is a different container all the same — a different image, a different
    `--cap-drop` value — and the run moved underneath a control that never noticed. This is
    the reason C17 records the **full** argv rather than a summary of the flags the check
    happens to look at: a summary cannot show a flag it does not summarize.
    """
    boot = evaluate(_shell("C17"), CLEAN_LAUNCH)
    end = evaluate(
        _shell("C17"),
        replace(
            CLEAN_LAUNCH,
            container_launch_args=("docker", "run", "--cap-drop", "NET_RAW", "--network", "none", "other"),
        ),
    )
    assert boot.outcome is end.outcome is AssertionOutcome.PASSED
    drifts = compare(AssertionReport((boot,)), AssertionReport((end,)))
    assert [(d.kind, d.key) for d in drifts] == [(DriftKind.VALUE, "container_launch_args")]


def test_c14_reports_not_executed_when_the_relaunched_posture_was_not_read() -> None:
    """F25 through the new member. An end-of-run C17 over an argv nobody collected is
    `not_executed`, and a fold that read that as a pass would be the quietest way for the
    re-assertion to stop running."""
    end = [_passed(i) for i in REASSERTED if i != "C17"]
    end.append(evaluate(_shell("C17"), replace(CLEAN_LAUNCH, container_launch_args=())))
    result = reassert(end)
    assert result.outcome is AssertionOutcome.NOT_EXECUTED
    assert "C17" in result.detail


def test_c14_compare_reports_an_observation_that_stopped_being_made() -> None:
    """The quiet kind. A key-wise diff over *shared* keys sees nothing here.

    A check that stopped observing and a check that observed no change are the same shape
    from outside, which is the whole reason this is a named kind rather than a silence.
    """
    boot = Assertion("C9", AssertionOutcome.PASSED, "ok", observed={"mounts": "/repo:rw"})
    end = Assertion("C9", AssertionOutcome.PASSED, "ok", observed={})
    drifts = compare(AssertionReport((boot,)), AssertionReport((end,)))
    assert [(d.kind, d.key) for d in drifts] == [(DriftKind.OBSERVATION_LOST, "mounts")]


def test_c14_compare_reports_an_observation_that_appeared() -> None:
    """The mirror, reported rather than judged benign on the reader's behalf."""
    boot = Assertion("C9", AssertionOutcome.PASSED, "ok", observed={})
    end = Assertion("C9", AssertionOutcome.PASSED, "ok", observed={"mounts": "/repo:rw"})
    drifts = compare(AssertionReport((boot,)), AssertionReport((end,)))
    assert [(d.kind, d.key) for d in drifts] == [(DriftKind.OBSERVATION_APPEARED, "mounts")]


def test_c14_compare_reports_an_assertion_present_at_only_one_end() -> None:
    """`reassert` refuses on end-side absence; boot-side absence was caught by nothing."""
    only_end = compare(AssertionReport(()), AssertionReport((_passed("C13"),)))
    assert [d.kind for d in only_end] == [DriftKind.MISSING_AT_BOOT]
    only_boot = compare(AssertionReport((_passed("C13"),)), AssertionReport(()))
    assert [d.kind for d in only_boot] == [DriftKind.MISSING_AT_END]


def test_c14_compare_reads_values_on_a_failing_outcome_too() -> None:
    """Attaching observations only to the pass would blind the diff where it matters most."""
    boot = Assertion("C13", AssertionOutcome.PASSED, "clean", observed={"archives": "0"})
    end = Assertion("C13", AssertionOutcome.FAILED, "a wheel appeared", observed={"archives": "1"})
    kinds = {(d.kind, d.key) for d in compare(AssertionReport((boot,)), AssertionReport((end,)))}
    assert kinds == {(DriftKind.OUTCOME, None), (DriftKind.VALUE, "archives")}


def test_value_blind_names_what_was_compared_on_its_outcome_alone() -> None:
    """D57 for this comparison. An empty `compare` over these ids is not evidence of stillness."""
    reports = AssertionReport(tuple(_passed(i) for i in REASSERTED))
    assert compare(reports, reports) == ()
    assert value_blind(reports, reports) == REASSERTED


def test_every_reasserted_member_records_observations(
    denylist: Denylist, tmp_path: Path
) -> None:
    """The coverage assertion, run against the real implementations rather than fixtures.

    `value_blind` names what could only be compared by outcome. This is the other side of it:
    every member of the closed set is built here the way the adaptor builds it, and each one
    must return something to compare. A member added later without observations makes
    `value_blind` non-empty in production and this test red first.
    """
    mount = tmp_path / "mnt"
    mount.mkdir()
    real = (
        probe(
            denylist=denylist,
            interpreters=(sys.executable,),
            extra_paths=(str(mount),),
            strict_import_hooks=False,
        ),
        assert_mounts_match(
            [MountObservation("/repo", read_only=False)],
            [MountObservation("/repo", read_only=False)],
        ),
        assert_writable_set(
            [MountObservation("/repo", read_only=False)],
            writable_roots=["/repo"],
            interpreter_paths=[],
        ),
        assert_no_archives_or_caches([tmp_path]),
        evaluate(_shell("C16"), CLEAN),
        evaluate(_shell("C17"), CLEAN_LAUNCH),
    )
    assert tuple(a.assertion_id for a in real) == REASSERTED
    for assertion in real:
        assert assertion.observed, assertion.assertion_id

    report = AssertionReport(real)
    assert value_blind(report, report) == ()
    assert compare(report, report) == ()


def test_drifted_ids_deduplicates_and_keeps_the_closed_sets_order() -> None:
    boot = Assertion("C13", AssertionOutcome.PASSED, "ok", observed={"a": "1", "b": "1"})
    end = Assertion("C13", AssertionOutcome.FAILED, "no", observed={"a": "2", "b": "2"})
    drifts = compare(AssertionReport((boot, _passed("C9"))), AssertionReport((end, _passed("C9"))))
    assert len(drifts) > 1
    assert drifted_ids(drifts) == ("C13",)


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
    assert drifted_ids(compare(boot, end)) == ("C13",)
    assert [d.kind for d in compare(boot, end)] == [DriftKind.OUTCOME]


def test_c14_compare_is_silent_when_nothing_moved() -> None:
    boot = AssertionReport(tuple(_passed(i) for i in REASSERTED))
    assert compare(boot, boot) == ()


# ================================================================================= C15

_DIFF_HEADER = "--- a/{p}\n+++ b/{p}\n@@ -0,0 +1 @@\n"


def _diff(path: str, *added: str) -> str:
    return _DIFF_HEADER.format(p=path) + "".join(f"+{line}\n" for line in added)



@pytest.mark.parametrize(
    "line",
    [
        "import os, commonroad_crime",
        "import commonroad_crime, os",
        "import commonroad_crime as crime",
        "import commonroad_crime.measure.time",
        "from . import commonroad_crime",
        "from .vendor import commonroad_crime",
        "from commonroad_crime.measure import ttc",
        'x = __import__("commonroad_crime")',
        'm = importlib.import_module("commonroad_crime.measure")',
    ],
)
def test_c15_catches_every_import_form_not_only_the_first_name_on_the_line(
    line: str, denylist: Denylist
) -> None:
    """`import os, commonroad_crime` passed. It is the same line as the caught one, reordered.

    The pattern read one name per line and stopped, so the miss was positional. Relative and
    dynamic forms were missed outright — neither is exotic in a patch someone wrote to get a
    number past a gate.
    """
    result = assert_patch_carries_no_oracle(
        f"--- a/m.py\n+++ b/m.py\n@@ -1,0 +1,1 @@\n+{line}\n", denylist
    )
    assert result.outcome is AssertionOutcome.FAILED, result.detail
    assert "commonroad_crime" in result.detail


@pytest.mark.parametrize(
    "line",
    [
        "import os, sys",
        "from pathlib import Path",
        "import numpy as np",
        "from . import helpers",
        'x = __import__("json")',
        "# import commonroad_crime",
        "commonroad_crime_notes = 1",
    ],
)
def test_c15_does_not_fire_on_innocent_imports(line: str, denylist: Denylist) -> None:
    """The control. A widened matcher that fires on everything is not a widened matcher."""
    result = assert_patch_carries_no_oracle(
        f"--- a/m.py\n+++ b/m.py\n@@ -1,0 +1,1 @@\n+{line}\n", denylist
    )
    assert result.outcome is AssertionOutcome.PASSED, result.detail


def test_imported_top_level_names_reads_the_top_level_only() -> None:
    """The denylist names top-level modules; `import a.b.c` denies on `a`."""
    assert imported_top_level_names("import a.b.c, d as e") == frozenset({"a", "d"})
    assert imported_top_level_names("from x.y import z") == frozenset({"x"})
    assert imported_top_level_names("from . import p, q") == frozenset({"p", "q"})
    assert imported_top_level_names("total = 1") == frozenset()


def test_c15_reports_a_line_number_a_reviewer_can_open(denylist: Denylist) -> None:
    """A finding in a hunk at line 501 was reported as `m.py:1`, and acted on as one.

    The hunk header was in the `@@`-skipping branch. A position that is confidently wrong is
    worse than no position, because a reviewer opens it and finds nothing.
    """
    diff = (
        "--- a/src/m.py\n+++ b/src/m.py\n@@ -500,2 +500,3 @@\n"
        " context line\n"
        "-removed line\n"
        "+import commonroad_crime\n"
    )
    result = assert_patch_carries_no_oracle(diff, denylist)
    assert result.outcome is AssertionOutcome.FAILED
    # 500 is the context line; the removed line does not advance the post-image; 501 is the
    # added one.
    assert "src/m.py:501" in result.detail


def test_c15_numbers_from_one_when_the_fragment_states_no_hunk(denylist: Denylist) -> None:
    """A fragment handed in without a header is still scanned — trimming a line must not
    disable the check — and numbered from 1, the honest answer for a stated-by-nobody position.
    """
    result = assert_patch_carries_no_oracle(
        "+++ b/m.py\n+import commonroad_crime\n", denylist
    )
    assert result.outcome is AssertionOutcome.FAILED
    assert "m.py:1" in result.detail



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
    result = assert_patch_carries_no_oracle(
        _diff("src/x.py", "import numpy"), denylist, denied_source_hashes={}
    )
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


def test_the_crossing_treats_an_explicit_empty_observed_as_a_statement() -> None:
    """`{} or x` silently substituted the probe's values for an adaptor saying "I saw none"."""
    assertion = Assertion("C9", AssertionOutcome.PASSED, "prose", observed={"mounts": "/repo:rw"})
    stated = to_result(assertion, executed_inside_container=True, observed={})
    assert stated.observed == {}
    inherited = to_result(assertion, executed_inside_container=True)
    assert inherited.observed == {"mounts": "/repo:rw"}


def test_the_crossing_falls_back_to_prose_only_when_the_probe_observed_nothing() -> None:
    """The fallback still exists; it is now the last resort rather than the second."""
    bare = Assertion("C9", AssertionOutcome.PASSED, "prose")
    assert to_result(bare, executed_inside_container=True).observed == {"detail": "prose"}


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


# ================================================================ C17 — ingress and launch


def _c17(**overrides: object) -> Assertion:
    """C17 over an otherwise-clean observation. Overrides are what each test is about."""
    base = {
        "config": {"session_api_keys": ["k"]},
        "container_launch_args": _HARDENED_ARGV,
        "published_port_bindings": _LOOPBACK_BINDING,
    }
    return evaluate(C17, ExecutorObservation(**{**base, **overrides}))  # pyright: ignore[reportArgumentType]


def test_c17_passes_on_an_authenticated_loopback_hardened_launch() -> None:
    """The positive control. Without it every test below passes on a check that never passes."""
    result = _c17()
    assert result.outcome is AssertionOutcome.PASSED
    assert result.observed["container_launch_args"] == " ".join(_HARDENED_ARGV)


@pytest.mark.parametrize(
    ("label", "override"),
    [
        # ADR-0019 point 1: the default is an empty list, and empty means unsecured.
        ("empty key list", {"config": {"session_api_keys": []}}),
        # DockerWorkspace sets it to None outright, which is a second way to the same place.
        ("key set to None", {"config": {"session_api_keys": None}}),
        ("key absent entirely", {"config": {}}),
        ("blank string key", {"config": {"session_api_keys": "  "}}),
    ],
)
def test_c17_fails_every_way_the_server_ends_up_unauthenticated(
    label: str, override: dict[str, object]
) -> None:
    assert _c17(**override).outcome is AssertionOutcome.FAILED, label


@pytest.mark.parametrize(
    "binding",
    [
        # What Docker actually does with `-p {host_port}:8000`.
        "0.0.0.0:8010->8000/tcp",
        "[::]:8010->8000/tcp",
        "192.168.1.10:8010->8000/tcp",
        # Unparseable is a finding, not loopback: a binding nobody can read is not one
        # anybody checked.
        "nonsense",
    ],
)
def test_c17_fails_on_a_binding_that_is_not_loopback(binding: str) -> None:
    assert _c17(published_port_bindings=(binding,)).outcome is AssertionOutcome.FAILED


def test_c17_accepts_ipv6_loopback_without_mistaking_the_hextet_for_a_host() -> None:
    """`[::1]:8010` must parse to `::1`, not to `[`. The bracket-stripping path, asserted."""
    assert _c17(published_port_bindings=("[::1]:8010->8000/tcp",)).outcome is AssertionOutcome.PASSED


@pytest.mark.parametrize(
    ("label", "argv"),
    [
        ("no --cap-drop", ("docker", "run", "--network", "none", "img")),
        ("no --network", ("docker", "run", "--cap-drop", "ALL", "img")),
        # Naming the flag is not the same as leaving the default network -- the failure this
        # clause exists for, because the argv looks hardened at a glance.
        ("--network bridge", ("docker", "run", "--cap-drop", "ALL", "--network", "bridge", "img")),
        ("--network with no value", ("docker", "run", "--cap-drop", "ALL", "--network")),
    ],
)
def test_c17_fails_on_an_unhardened_launch(label: str, argv: tuple[str, ...]) -> None:
    assert _c17(container_launch_args=argv).outcome is AssertionOutcome.FAILED, label


@pytest.mark.parametrize("unread", ["container_launch_args", "published_port_bindings"])
def test_c17_reports_not_executed_when_it_read_nothing(unread: str) -> None:
    """The vacuity control (D57/F25).

    An argv nobody collected reports the same thing on a hardened launch and an unhardened
    one. `not_executed` is the only honest outcome, and `require_all_passed` treats it as a
    failure -- which is the point: an unread launch posture must not let a run start.
    """
    result = _c17(**{unread: ()})
    assert result.outcome is AssertionOutcome.NOT_EXECUTED
    assert unread in result.detail


def test_c17_reports_all_of_its_problems_at_once() -> None:
    """Three findings, one report. Fixing them one run at a time is three runs."""
    result = _c17(
        config={"session_api_keys": []},
        published_port_bindings=("0.0.0.0:8010->8000/tcp",),
        container_launch_args=("docker", "run", "img"),
    )
    assert result.outcome is AssertionOutcome.FAILED
    for fragment in ("session_api_keys", "not loopback", "--cap-drop", "--network"):
        assert fragment in result.detail


def test_c17_records_what_it_read_on_failure_too() -> None:
    """`reassert.compare` reads values across boot and end regardless of outcome.

    A container relaunched with different flags is indistinguishable from one launched twice
    the same way if the argv is only attached to passes.
    """
    result = _c17(container_launch_args=("docker", "run", "img"))
    assert result.outcome is AssertionOutcome.FAILED
    assert result.observed["container_launch_args"] == "docker run img"


# ============================================== C15 clause 3, against the real register


def _source_hash_register() -> dict[str, str]:
    from harness.containment.source_hashes import load as _load

    return _load().as_mapping()


def test_the_source_hash_register_is_not_empty_and_names_its_pin() -> None:
    """D57. A register of nothing disables clause 3 while looking built.

    This is the test that would have failed on 2026-08-18, when the register did not exist and
    clause 3 reported `2 of 3 clauses` on every real invocation with nothing recording it.
    """
    from harness.containment.source_hashes import load as _load

    register = _load()
    assert register.hashes, "the register carries no hashes"
    assert len(register.hashes) >= 40, len(register.hashes)
    assert register.oracle_commit_sha == "60bebed8005610f1b856e601852676a21e85cfc6"


def test_clause_three_misses_a_fragment_pasted_into_an_existing_file(denylist: Denylist) -> None:
    """Finding 8, pinned as a test rather than only as a docstring.

    The register holds whole-file digests and the clause hashes a path's added lines, so a
    vendored fragment appended to an existing file cannot match. Asserting the limit means a
    future change that closes it fails here and has to say so, instead of quietly widening
    what a green C15 means.
    """
    whole = "def ttc(a, b):\n    return a - b"
    register = {normalized_source_hash(whole): "commonroad_crime/measure/time/ttc.py"}

    # The control: the same register, the same content, added as a whole file. It must fail,
    # or the test below would pass against a clause that never matches anything.
    caught = assert_patch_carries_no_oracle(
        _diff("src/metrics/copied.py", *whole.splitlines()),
        denylist,
        denied_source_hashes=register,
    )
    assert caught.outcome is AssertionOutcome.FAILED

    # The limit: the second line alone, pasted into a file that already existed.
    missed = assert_patch_carries_no_oracle(
        _diff("src/metrics/existing.py", "    return a - b"),
        denylist,
        denied_source_hashes=register,
    )
    assert missed.outcome is AssertionOutcome.PASSED


def test_c15_is_not_executed_when_the_register_cannot_be_read(
    denylist: Denylist, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An unreadable policy is not an absent one. Fail closed, never fall back to two clauses."""
    import harness.containment.patch_side as patch_side
    import harness.containment.source_hashes as source_hashes

    monkeypatch.setattr(source_hashes, "DEFAULT_PATH", tmp_path / "absent.json")
    monkeypatch.setattr(
        patch_side, "load_source_hashes", lambda: source_hashes.load(source_hashes.DEFAULT_PATH)
    )
    result = assert_patch_carries_no_oracle(_diff("src/x.py", "import numpy"), denylist)
    assert result.outcome is AssertionOutcome.NOT_EXECUTED
    assert "register could not be read" in result.detail


def test_the_normalization_vectors_agree_with_patch_sides_implementation() -> None:
    """The committed side of the cross-check that keeps one canonical form out of two copies.

    The in-image side is asserted by `harness/oracle/run.py::run_fingerprints`, which refuses
    a run on disagreement. This is the half that can run without Docker, and without it a
    drift would only be caught on a machine that happens to have the oracle image built.
    """
    vectors = json.loads(
        (Path(__file__).resolve().parents[1] / "oracle" / "normalization_vectors.json").read_text()
    )["vectors"]
    assert len(vectors) >= 8
    for vector in vectors:
        assert normalized_source_hash(vector["input"]) == vector["normalized_sha256"], vector["name"]


# ==================================================== the adaptor configuration contract


def test_a_legal_configuration_survives_validation_unchanged() -> None:
    """The positive control. Without it every refusal below could come from a broken reader."""
    legal = {"a": 1, "b": "x", "c": True, "d": None, "e": 1.5, "f": [1, "y"], "g": {"h": False}}
    assert validated_config(legal) == legal
    assert ExecutorObservation(config=legal).config == legal


@pytest.mark.parametrize(
    ("label", "config"),
    [
        ("an arbitrary object", {"k": object()}),
        ("a nested arbitrary object", {"k": {"n": object()}}),
        ("an arbitrary object inside a list", {"k": [1, object()]}),
        # No JSON spelling. Admitting them puts a value in the configuration that cannot
        # survive being written down, and every check downstream would read it anyway.
        ("NaN", {"k": float("nan")}),
        ("positive infinity", {"k": float("inf")}),
        ("negative infinity", {"k": float("-inf")}),
        ("bytes", {"k": b"x"}),
    ],
)
def test_the_configuration_contract_refuses_what_has_no_serialization(
    label: str, config: dict[str, object]
) -> None:
    with pytest.raises(ConfigContractViolation):
        validated_config(config)


def test_the_refusal_happens_at_construction_not_inside_a_check() -> None:
    """A check reading an arbitrary object renders it with `str()` and compares a repr.

    That comparison can only fail, and it fails for a reason the report cannot explain. The
    boundary is where this belongs.
    """
    with pytest.raises(ConfigContractViolation):
        ExecutorObservation(config={"k": object()})


def test_the_refusal_names_the_path_that_is_wrong() -> None:
    """A nested violation reported as "the configuration is invalid" is a bug report nobody
    can act on. The path is what makes it actionable."""
    with pytest.raises(ConfigContractViolation, match=r"outer\.inner\[1\]"):
        validated_config({"outer": {"inner": [1, object()]}})


def test_a_boolean_is_not_narrowed_to_an_integer() -> None:
    """`bool` subclasses `int`, so an isinstance check ordered the other way accepts True as
    a number — which is how a flag becomes the integer 1 somewhere downstream."""
    validated = validated_config({"flag": True})
    assert validated["flag"] is True


def test_typing_the_contract_does_not_make_a_wrong_value_right() -> None:
    """The limit, asserted so a green C-assertion is not over-quoted.

    A string where a boolean belongs is legal JSON and still reaches `_as_flag`, which still
    reports it as uninterpretable. This change closes the serialization half of the finding
    and not the semantic half.
    """
    observation = ExecutorObservation(config={"delete_on_close": "perhaps"})
    result = evaluate(C1.with_holes(persistence_dir_key="p", delete_on_close_key="delete_on_close"),
                      observation)
    assert result.outcome is AssertionOutcome.FAILED
    assert "does not spell a boolean" in result.detail


# ================================================= the key set half of the same contract


def test_the_named_key_set_is_derived_from_the_register_and_is_not_empty() -> None:
    """D57 for this check. An empty reference set finds nothing and reports clean.

    Derived rather than typed out, so a hole added later is covered without anybody
    remembering a list — and asserted to contain the keys the checks actually read, so a
    derivation that silently returned nothing goes red here rather than in a green run.
    """
    named = named_config_keys()
    assert named
    for key in ("persistence_dir", "delete_on_close", "session_api_keys", "enable_vscode"):
        assert key in named, key


def test_a_respelt_key_is_refused_at_the_boundary() -> None:
    """The finding ADR-0026 left open, closed. The message names both spellings.

    `sessionApiKeys` and `session_api_keys` cannot both be real keys of one executor, so the
    collision is a fact rather than a guess at what the adaptor meant.
    """
    with pytest.raises(ConfigKeyConfusion, match="session_api_keys"):
        ExecutorObservation(config={"sessionApiKeys": ["k"]})


@pytest.mark.parametrize(
    "sent",
    [
        "sessionApiKeys",
        "session-api-keys",
        "SESSION_API_KEYS",
        "sessionapikeys",
        "Session_Api_Keys",
    ],
)
def test_every_spelling_convention_an_adaptor_might_use_is_caught(sent: str) -> None:
    """Case, separators and both together — the class an adaptor written against JSON
    documentation actually produces."""
    assert confusable_config_keys({sent: ["k"]}) == ((sent, "session_api_keys"),)


def test_a_key_alfred_does_not_read_is_legal_and_is_not_reported() -> None:
    """The control that stops this being "reject unknown keys", which is a different and
    false claim: the executor's configuration surface is larger than the set Alfred reads,
    and every real observation carries keys no hole names.

    Without this test the check could refuse everything and every other test here would
    still pass.
    """
    assert confusable_config_keys({"some_key_alfred_does_not_read": 1}) == ()
    assert ExecutorObservation(config={"some_key_alfred_does_not_read": 1}).config


def test_the_key_a_hole_names_is_not_confusable_with_itself() -> None:
    """The other half of the positive control: the real spelling passes through untouched."""
    assert confusable_config_keys({"session_api_keys": ["k"]}) == ()


def test_without_the_guard_a_respelt_key_reads_as_absent_and_fails_for_the_wrong_reason() -> None:
    """Why this is refused at the boundary rather than reported inside a check.

    By the time the check runs, the only thing it can say is that `session_api_keys` is
    absent — which is exactly what it says about an executor that genuinely does not set it.
    Two different findings, one sentence in the record. The observation here is built past
    the guard on purpose, to show the state the guard now makes unreachable.
    """
    respelt: dict[str, object] = {"sessionApiKeys": ["k"]}
    assert confusable_config_keys(respelt) == (("sessionApiKeys", "session_api_keys"),)

    past_the_guard = ExecutorObservation(
        container_launch_args=_HARDENED_ARGV, published_port_bindings=_LOOPBACK_BINDING
    )
    object.__setattr__(past_the_guard, "config", respelt)
    result = evaluate(C17, past_the_guard)
    assert result.outcome is AssertionOutcome.FAILED
    assert "absent from the loaded configuration" in result.detail


def test_a_misspelling_that_is_not_a_respelling_is_the_stated_limit() -> None:
    """The limit, pinned rather than left to be discovered.

    `sesion_api_keys` normalizes to itself and is not caught. What is caught is
    spelling-convention drift. Edit-distance matching would catch this one and would produce
    false positives in a check whose finding refuses a configuration outright — and a future
    change that widens the rule fails here and has to say so.
    """
    assert confusable_config_keys({"sesion_api_keys": ["k"]}) == ()


def test_a_nested_key_collides_with_nothing_because_no_hole_names_one() -> None:
    """Every check reads `config[key]` at the top level, so a nested key is not a key any
    hole names at all."""
    assert confusable_config_keys({"outer": {"sessionApiKeys": ["k"]}}) == ()
