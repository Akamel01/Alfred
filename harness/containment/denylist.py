"""Load the oracle denylist and give it a digest the fingerprint can carry.

The denylist is versioned protected policy configuration (D54) and its version is a D19
fingerprint field, so a reclassification invalidates the grants measured under the old
one. The digest is over ACS-1 with its own domain separator, which means the recorded
reasons are part of it: silently changing why a package is denied changes the fingerprint,
which is the correct behaviour for a classification the document calls a recorded human
judgement.

**Both sets are loaded, and the permitted set is not decoration.** A package appearing in
neither set is not "allowed by default" — it is *unclassified*, and `classify` says so.
The image-build closure check fails on unclassified entries rather than passing them,
because "we have not looked at this one" and "we looked and it carries no measure" are
different facts and only one of them is a decision.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Final

from harness.acs.acs1 import acs_sha256

DENYLIST_RECORD_TYPE: Final = "alfred.policy.oracle_denylist.v1"
DEFAULT_PATH: Final = Path(__file__).resolve().parents[2] / "policy" / "oracle-denylist.json"


class DenylistError(RuntimeError):
    """The policy could not be loaded. Fail closed: no denylist, no run (F17)."""


class Classification(Enum):
    DENIED = "denied"
    PERMITTED_SUBSTRATE = "permitted_substrate"
    UNCLASSIFIED = "unclassified"


@dataclass(frozen=True)
class Entry:
    distribution: str
    modules: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class Denylist:
    version: int
    denied: tuple[Entry, ...]
    permitted_substrate: tuple[Entry, ...]
    sha256: str

    @property
    def denied_modules(self) -> frozenset[str]:
        return frozenset(module for entry in self.denied for module in entry.modules)

    @property
    def denied_distributions(self) -> frozenset[str]:
        # Normalized per PEP 503: `commonroad_crime` and `commonroad-crime` are the same
        # distribution to a resolver, and a check comparing raw strings would miss one.
        return frozenset(_normalize(entry.distribution) for entry in self.denied)

    def classify(self, *, distribution: str | None = None, module: str | None = None) -> Classification:
        if distribution is not None:
            normalized = _normalize(distribution)
            if normalized in self.denied_distributions:
                return Classification.DENIED
            if normalized in {_normalize(e.distribution) for e in self.permitted_substrate}:
                return Classification.PERMITTED_SUBSTRATE
        if module is not None:
            if module in self.denied_modules:
                return Classification.DENIED
            if module in {m for e in self.permitted_substrate for m in e.modules}:
                return Classification.PERMITTED_SUBSTRATE
        return Classification.UNCLASSIFIED


def _normalize(name: str) -> str:
    return name.lower().replace("_", "-").replace(".", "-")


def _entries(raw: object, section: str) -> tuple[Entry, ...]:
    if not isinstance(raw, list):
        raise DenylistError(f"{section} is not a list")
    built: list[Entry] = []
    for item in raw:
        if not isinstance(item, dict):
            raise DenylistError(f"{section} contains a non-object entry")
        try:
            distribution = str(item["distribution"])
            modules = tuple(str(m) for m in item["modules"])
            reason = str(item["reason"])
        except (KeyError, TypeError) as exc:
            raise DenylistError(f"{section} entry is missing a required key: {exc}") from exc
        if not modules:
            raise DenylistError(f"{section} entry {distribution!r} names no module")
        if not reason.strip():
            # An entry with no reason is an entry nobody decided. The document calls this
            # a recorded human judgement, and an empty reason is the absence of one.
            raise DenylistError(f"{section} entry {distribution!r} records no reason")
        built.append(Entry(distribution=distribution, modules=modules, reason=reason))
    return tuple(built)


def load(path: Path = DEFAULT_PATH) -> Denylist:
    """Read and digest the policy. Any problem raises; nothing is defaulted.

    A missing or malformed denylist does not fall back to an empty one. An empty denylist
    denies nothing and every probe below it reports `passed`, which is the exact shape of
    a control that has stopped working while still being green.
    """
    try:
        raw: Any = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise DenylistError(f"cannot read {path}: {exc}") from exc
    except ValueError as exc:
        raise DenylistError(f"{path} is not valid JSON: {exc}") from exc

    if not isinstance(raw, dict):
        raise DenylistError(f"{path} is not an object")
    try:
        version = int(raw["version"])
    except (KeyError, TypeError, ValueError) as exc:
        raise DenylistError(f"{path} has no integer version") from exc

    denied = _entries(raw.get("denied"), "denied")
    substrate = _entries(raw.get("permitted_substrate"), "permitted_substrate")
    if not denied:
        raise DenylistError(f"{path} denies nothing; an empty denylist passes every probe")

    overlap = {_normalize(e.distribution) for e in denied} & {
        _normalize(e.distribution) for e in substrate
    }
    if overlap:
        # Both-listed is not a conservative default. It is a policy that says two things,
        # and whichever the code reads first becomes the decision.
        raise DenylistError(f"{path} lists {sorted(overlap)} as both denied and permitted")

    digest_input = {
        "version": version,
        "denied": [
            {"distribution": e.distribution, "modules": list(e.modules), "reason": e.reason}
            for e in denied
        ],
        "permitted_substrate": [
            {"distribution": e.distribution, "modules": list(e.modules), "reason": e.reason}
            for e in substrate
        ],
    }
    return Denylist(
        version=version,
        denied=denied,
        permitted_substrate=substrate,
        sha256=acs_sha256(DENYLIST_RECORD_TYPE, digest_input),
    )
