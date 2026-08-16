"""Fail-closed fingerprint assertion for the inference lane (D19/D40).

The serving stack auto-unloads an idle model and JIT-reloads it on the next request at
its *default* context length rather than the length it was loaded with. Observed
directly: a model loaded at 262,144 was found serving at 28,672 after an idle gap, and
the probes that ran against it returned 0/10 on a tool-calling suite the same model had
just scored 10/10 on. Nothing errored; it read as a capability regression.

`loaded_context_length` is a fingerprint field. **A fingerprint field the server can
change without notice is not a fingerprint unless something checks it**, so this module
asserts the fingerprint at run start rather than recording it from the server and
trusting it.

Every failure path here is fail-closed, per the fail-closed table in
`docs/tier1/failure-semantics.md`: the run does not start. In particular a fingerprint
that could not be *read* is treated exactly like one that does not match — an unproven
control is a failed control, and "the check did not run" is never collapsed into "the
check passed".

No third-party imports: the inspector must not depend on the supply chain it inspects.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Mapping

DEFAULT_BASE = "http://127.0.0.1:1234"
DEFAULT_TIMEOUT_S = 30

#: Every field that participates in the lane fingerprint. Order is presentation order.
FINGERPRINT_FIELDS: tuple[str, ...] = (
    "model_id",
    "engine",
    "quantization",
    "arch",
    "loaded_context_length",
    "max_context_length",
)

#: Fields an expectation must declare. An expectation that omits `loaded_context_length`
#: cannot catch the defect this control exists for, so omitting it is an error rather
#: than a narrower assertion.
REQUIRED_FIELDS: tuple[str, ...] = ("model_id", "loaded_context_length")


# ------------------------------------------------------------------------ errors


class LaneControlError(RuntimeError):
    """Base for every lane-control failure. Carries its error-taxonomy class."""

    taxonomy_class = "contract-violation"


class FingerprintUnavailable(LaneControlError):
    """The fingerprint could not be read, or the model is not loaded.

    Infrastructure class: `indeterminate`, bounded requeue. Never a pass.
    """

    taxonomy_class = "infrastructure"


class FingerprintIncomplete(LaneControlError):
    """The expectation or the observation is missing a field the control needs.

    Contract violation: an assertion that cannot compare a field is not an assertion.
    """


@dataclass(frozen=True)
class FieldDiff:
    field: str
    expected: Any
    observed: Any

    def __str__(self) -> str:
        return f"{self.field}: expected {self.expected!r}, serving {self.observed!r}"


class FingerprintDrift(LaneControlError):
    """The lane is not the lane the run was dispatched against."""

    def __init__(self, model: str, differences: tuple[FieldDiff, ...]) -> None:
        self.model = model
        self.differences = differences
        detail = "; ".join(str(d) for d in differences)
        super().__init__(
            f"lane fingerprint drift for '{model}' — {detail}. The lane reconfigured "
            f"itself; reload it at the dispatched configuration. Run does not start."
        )


# ------------------------------------------------------------------------ reading


def read_fingerprint(
    model: str,
    *,
    base_url: str = DEFAULT_BASE,
    timeout: int = DEFAULT_TIMEOUT_S,
) -> dict[str, Any]:
    """Read the live fingerprint of `model` from the serving layer.

    Raises `FingerprintUnavailable` for every way this can fail to produce a fingerprint
    — transport error, malformed payload, model absent, model present but not loaded.
    The caller must not be able to tell "unreadable" apart from "mismatched" by whether
    it got a value back.
    """
    url = f"{base_url.rstrip('/')}/api/v0/models"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            payload = json.loads(resp.read())
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as exc:
        raise FingerprintUnavailable(f"cannot reach the lane at {url}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise FingerprintUnavailable(f"lane returned unparseable JSON from {url}: {exc}") from exc

    entries = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(entries, list):
        raise FingerprintUnavailable(f"lane returned no model list from {url}")

    for entry in entries:
        if not isinstance(entry, dict) or entry.get("id") != model:
            continue
        if entry.get("state") != "loaded":
            raise FingerprintUnavailable(
                f"model '{model}' is present but not loaded (state="
                f"{entry.get('state')!r}) — load it before dispatching"
            )
        return {
            "model_id": entry.get("id"),
            "engine": entry.get("compatibility_type"),
            "quantization": entry.get("quantization"),
            "arch": entry.get("arch"),
            "loaded_context_length": entry.get("loaded_context_length"),
            "max_context_length": entry.get("max_context_length"),
        }
    raise FingerprintUnavailable(f"model '{model}' is not served by {base_url}")


# ----------------------------------------------------------------------- asserting


def _equal(expected: Any, observed: Any) -> bool:
    """Equality that does not let Python's bool/int identity paper over a difference."""
    if isinstance(expected, bool) != isinstance(observed, bool):
        return False
    return expected == observed


def assert_fingerprint(
    model: str,
    expected: Mapping[str, Any],
    *,
    fetch: Callable[[str], Mapping[str, Any]] | None = None,
    base_url: str = DEFAULT_BASE,
    timeout: int = DEFAULT_TIMEOUT_S,
) -> dict[str, Any]:
    """Assert the live lane matches the fingerprint the run was dispatched against.

    Returns the observed fingerprint on success, so the caller records what it verified
    rather than what it hoped for. Raises — never warns — on every other outcome:

    * `FingerprintIncomplete` — the expectation omits a required field, or declares a
      field the observation does not carry. Nothing was compared, so nothing passed.
    * `FingerprintUnavailable` — the fingerprint could not be read.
    * `FingerprintDrift` — any declared field differs, `loaded_context_length` included.

    `fetch` exists so callers can supply a fingerprint they already read this run (and
    so tests can drive every branch without a live server). It takes the model id and
    returns a fingerprint mapping.
    """
    if not isinstance(expected, Mapping) or not expected:
        raise FingerprintIncomplete(
            "no expected fingerprint was supplied — a run with nothing to assert is a "
            "run with no fingerprint control"
        )

    missing = [f for f in REQUIRED_FIELDS if expected.get(f) is None]
    if missing:
        raise FingerprintIncomplete(
            f"expected fingerprint omits {', '.join(missing)} — a fingerprint that does "
            f"not pin these cannot detect a lane that reconfigured itself"
        )

    if not _equal(expected["model_id"], model):
        raise FingerprintIncomplete(
            f"expected fingerprint is for model {expected['model_id']!r} but the run "
            f"dispatches {model!r}"
        )

    reader = fetch if fetch is not None else (
        lambda m: read_fingerprint(m, base_url=base_url, timeout=timeout)
    )
    try:
        observed = reader(model)
    except LaneControlError:
        raise
    except Exception as exc:  # any reader fault is an unread fingerprint, never a pass
        raise FingerprintUnavailable(
            f"fingerprint read for '{model}' failed: {exc!r}"
        ) from exc

    if not isinstance(observed, Mapping):
        raise FingerprintUnavailable(
            f"fingerprint read for '{model}' returned {type(observed).__name__}, "
            f"not a mapping"
        )

    absent = [f for f in expected if f not in observed]
    if absent:
        raise FingerprintIncomplete(
            f"observed fingerprint carries no {', '.join(sorted(absent))} — the field "
            f"cannot be compared, so the control cannot be shown to have executed"
        )

    diffs = tuple(
        FieldDiff(field, expected[field], observed[field])
        for field in FINGERPRINT_FIELDS + tuple(f for f in expected if f not in FINGERPRINT_FIELDS)
        if field in expected and not _equal(expected[field], observed[field])
    )
    if diffs:
        raise FingerprintDrift(model, diffs)

    return dict(observed)
