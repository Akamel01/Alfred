"""S8. Deploy and rollback, verified by observation rather than by exit code.

The ledger half runs anywhere. The docker half is skipped without a daemon, which is why
every refusal that can be tested without one is tested without one — a suite whose only
real assertions sit behind a skip is a suite that does not run.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from harness.deploy import driver
from harness.deploy.ledger import Entry, Ledger, LedgerError


@pytest.fixture
def ledger(tmp_path: Path) -> Ledger:
    return Ledger(tmp_path / "releases.jsonl")


def _entry(release_id: str, at: float, action: str = "deploy") -> Entry:
    return Entry(
        release_id=release_id,
        image_ref=f"alfred-api:{release_id}",
        source_digest=f"digest-{release_id}",
        action=action,  # type: ignore[arg-type]
        at=at,
    )


# ------------------------------------------------------------------- the ledger


def test_rollback_against_an_empty_history_fails(ledger: Ledger) -> None:
    """The dangerous no-op. A rollback that succeeds having deployed nothing is the
    check passing with nothing to check."""
    with pytest.raises(LedgerError, match="nothing to roll back to"):
        ledger.rollback_target()


def test_rollback_against_a_single_release_fails(ledger: Ledger) -> None:
    ledger.append(_entry("r1", 1.0))
    with pytest.raises(LedgerError, match="already serving"):
        ledger.rollback_target()


def test_rollback_target_is_chosen_by_release_not_by_position(ledger: Ledger) -> None:
    """Taking the second-to-last row oscillates between two releases forever.

    After deploy r1, deploy r2, rollback to r1, the second-to-last row IS r2 — so a
    positional rule would roll "back" to r2, then to r1, reporting success every time
    while never converging.
    """
    ledger.append(_entry("r1", 1.0))
    ledger.append(_entry("r2", 2.0))
    assert ledger.rollback_target().release_id == "r1"
    ledger.append(_entry("r1", 3.0, action="rollback"))
    assert ledger.rollback_target().release_id == "r2"


def test_the_ledger_is_append_only_in_practice(ledger: Ledger) -> None:
    ledger.append(_entry("r1", 1.0))
    ledger.append(_entry("r2", 2.0))
    assert [e.release_id for e in ledger.entries()] == ["r1", "r2"]
    assert ledger.current() is not None
    assert ledger.current().release_id == "r2"  # type: ignore[union-attr]


# ------------------------------------------------------------- identity in the artifact


def test_the_service_refuses_to_start_without_a_baked_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    """An artifact that cannot say which release it is makes rollback unverifiable."""
    from src.api.app import DIGEST_ENV_VAR, RELEASE_ENV_VAR, build_identity

    monkeypatch.delenv(RELEASE_ENV_VAR, raising=False)
    monkeypatch.delenv(DIGEST_ENV_VAR, raising=False)
    with pytest.raises(RuntimeError, match="baked into the image"):
        build_identity()


def test_identity_comes_from_the_environment_not_from_the_repository(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Read it from outside the artifact and a failed rollback verifies as a success."""
    from src.api.app import DIGEST_ENV_VAR, RELEASE_ENV_VAR, build_identity

    monkeypatch.setenv(RELEASE_ENV_VAR, "r-test")
    monkeypatch.setenv(DIGEST_ENV_VAR, "digest-test")
    identity = build_identity()
    assert identity.release_id == "r-test"
    assert identity.source_digest == "digest-test"


# ---------------------------------------------------------------------- the real path


def _images_present() -> bool:
    if shutil.which("docker") is None:
        return False
    return all(
        subprocess.run(
            ["docker", "image", "inspect", f"alfred-api:{tag}"],
            capture_output=True, check=False,
        ).returncode
        == 0
        for tag in ("r1", "r2")
    )


requires_images = pytest.mark.skipif(
    not _images_present(), reason="alfred-api:r1 and :r2 not built on this host"
)


@requires_images
def test_deploy_is_verified_by_what_is_serving(ledger: Ledger) -> None:
    release = driver.Release("r1", "alfred-api:r1", "aaa111")
    observed = driver.deploy(release, ledger, now=1.0)
    assert observed["release_id"] == "r1"
    assert driver.served_identity()["release_id"] == "r1"
    driver.take_down()


@requires_images
def test_rollback_returns_the_previous_release_to_service(ledger: Ledger) -> None:
    r1 = driver.Release("r1", "alfred-api:r1", "aaa111")
    r2 = driver.Release("r2", "alfred-api:r2", "bbb222")
    driver.deploy(r1, ledger, now=1.0)
    driver.deploy(r2, ledger, now=2.0)
    assert driver.served_identity()["release_id"] == "r2"

    driver.rollback(ledger, now=3.0)
    assert driver.served_identity()["release_id"] == "r1"
    assert [e.action for e in ledger.entries()] == ["deploy", "deploy", "rollback"]
    driver.take_down()


@requires_images
def test_a_deploy_that_does_not_take_is_a_failure_and_records_nothing(ledger: Ledger) -> None:
    """The control the whole mechanism rests on.

    A release claiming to be r2 whose image actually serves r1 is exactly what a deploy
    looks like when it silently did not take. Verified by observation it fails; verified
    by exit code it would pass, because `docker compose up` succeeded.
    """
    mislabelled = driver.Release("r2", "alfred-api:r1", "bbb222")
    with pytest.raises(driver.DeployError, match="is serving"):
        driver.deploy(mislabelled, ledger, now=1.0)
    assert ledger.entries() == ()
    driver.take_down()
