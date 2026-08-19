"""C4 — the runtime image is the one the fingerprint declares, and it came from local disk.

Runs **outside** the container, and it has to: an image assertion made from inside asks the
image to describe itself. The three conjuncts are the spec row
(`docs/tier4/sandbox-specification.md`, C4) and each catches a different failure:

1. **Digest equality.** The image the container was created from equals
   `runtime_image_digest` in the run fingerprint. Catches tag drift and a silent rebuild —
   both of which leave the tag identical and the bytes different, which is why the
   comparison is never against a tag.
2. **Mirrored locally.** The image is present in the local store. An image that has to be
   fetched is an image whose provenance is a registry's current answer rather than a
   recorded one.
3. **Pulled outside the sandbox network namespace.** A pull that happened inside is a
   registry host reachable from the sandbox, which is the failure C6's allowlist exists to
   prevent and which this row catches from the other side.

**The vacuity control is the count.** An inspection that enumerated zero images reports
`NOT_EXECUTED`, never `PASSED` — an empty local store and a clean one are indistinguishable
otherwise, and "the image was not found, so nothing contradicted the digest" is exactly the
shape of a control that stopped running. D57 and F25.

**This module reads nothing itself.** The caller supplies an `ImageObservation` taken by
whatever inspects the local image store, and the comparison is pure. That is what lets every
branch here be tested without a daemon, and it keeps the privileged read in the one place
that already has to be privileged.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from harness.containment.assertions import Assertion, AssertionOutcome
from harness.fingerprint.record import RunFingerprint

__all__ = ["ASSERTION_C4", "ImageObservation", "assert_runtime_image"]

ASSERTION_C4: Final = "C4"


@dataclass(frozen=True)
class ImageObservation:
    """The local image store's answer, as read outside the sandbox.

    `pulled_in_sandbox_netns` is a tri-state on purpose. `None` means the inspection could
    not determine where the pull happened, and that is not the same as "it happened
    outside" — an unread conjunct is an unexecuted assertion, not a satisfied one. Making
    it `bool` with a `False` default would turn every inspection that forgot to answer into
    a pass.
    """

    #: The digest of the image the container was created from, as the store reports it.
    digest: str
    #: Present in the local store, rather than resolvable from a registry.
    present_locally: bool
    #: True if the pull happened inside the sandbox network namespace; None if unread.
    pulled_in_sandbox_netns: bool | None
    #: How many images the inspection enumerated. Zero is the vacuity signal.
    images_enumerated: int


def assert_runtime_image(
    observed: ImageObservation | None,
    fingerprint: RunFingerprint,
) -> Assertion:
    """C4. Returns an `Assertion`; never raises for a comparison outcome.

    `observed is None` means the inspection did not run at all, which is `NOT_EXECUTED` for
    the same reason an inspection that enumerated zero images is: the caller must not be
    able to tell "no image store" from "an image store that agreed" by whether it got a
    value back. That rule is `lane_fingerprint`'s and it is the one this row inherits.
    """
    if observed is None:
        return Assertion(
            assertion_id=ASSERTION_C4,
            outcome=AssertionOutcome.NOT_EXECUTED,
            detail=(
                "no image inspection was supplied; the runtime image digest was never "
                "compared against the fingerprint"
            ),
        )
    if observed.images_enumerated < 1:
        return Assertion(
            assertion_id=ASSERTION_C4,
            outcome=AssertionOutcome.NOT_EXECUTED,
            detail=(
                "the image inspection enumerated zero images; an empty store and a "
                "matching one are indistinguishable from here"
            ),
            observed={"images_enumerated": "0"},
        )

    # Recorded whatever the outcome, so `reassert.compare` can tell "the same image" from
    # "an image of the same kind" — a container swapped for another built from a different
    # digest is a drift no outcome carries.
    values = {
        "runtime_image_digest": observed.digest,
        "present_locally": str(observed.present_locally).lower(),
        "pulled_in_sandbox_netns": (
            "unread" if observed.pulled_in_sandbox_netns is None
            else str(observed.pulled_in_sandbox_netns).lower()
        ),
        "images_enumerated": str(observed.images_enumerated),
    }

    if observed.pulled_in_sandbox_netns is None:
        return Assertion(
            assertion_id=ASSERTION_C4,
            outcome=AssertionOutcome.NOT_EXECUTED,
            detail=(
                "the inspection could not say whether the image was pulled inside the "
                "sandbox network namespace; the conjunct was not evaluated"
            ),
            observed=values,
        )

    problems: list[str] = []
    if observed.digest != fingerprint.runtime_image_digest:
        problems.append(
            f"digest is {observed.digest!r}, fingerprint declares "
            f"{fingerprint.runtime_image_digest!r}"
        )
    if not observed.present_locally:
        problems.append("image is not mirrored in the local store")
    if observed.pulled_in_sandbox_netns:
        problems.append(
            "image was pulled inside the sandbox network namespace, so a registry host "
            "was reachable from the sandbox"
        )

    if problems:
        return Assertion(
            assertion_id=ASSERTION_C4,
            outcome=AssertionOutcome.FAILED,
            detail="; ".join(problems) + ". Run does not start.",
            observed=values,
        )
    return Assertion(
        assertion_id=ASSERTION_C4,
        outcome=AssertionOutcome.PASSED,
        detail=(
            f"runtime image {observed.digest} matches the fingerprint, is mirrored "
            f"locally, and was pulled outside the sandbox network namespace"
        ),
        observed=values,
    )
