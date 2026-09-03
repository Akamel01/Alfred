#!/usr/bin/env python3
"""MR001-MR005: model routing policy conformance, checked before any spawn.

**Why a static lint can enforce this at all.** Model selection happens at spawn time, in a
harness Alfred does not control, so the obvious reading is that nothing here is checkable.
`scripts/lint_verdict_boundary.py` answers that shape already: *the boundary is physical …
and the security property comes from port separation, never from inspecting field names at
runtime.* The same split applies. This file is check **P** — policy conformance, read off two
protected files in the diff, before a spawn exists to observe.

Check **A** is the runtime half and does not live here: the model a harness reports is
asserted against the one the task's fingerprint declares, and a mismatch is fail-closed. That
is the identical rule `loaded_context_length` already gets in
`docs/tier3/run-instrumentation-specification.md`, for the identical reason — a fingerprint
field the server can change unobserved is not a fingerprint unless something checks it. P is
what does the work today; A is what keeps P non-vacuous once runs exist.

  MR001 every capability_id bound in role-bindings.json has exactly one route, and every
        route names a bound capability. Both directions: a route for a capability that no
        longer exists is as wrong as a capability with no route, and only the second fails
        loudly on its own.
  MR002 no route resolves to a forbidden identity. `inherit`, or anything unpinned, is the
        named case: it defers model_version — a D19 fingerprint field — to session state, so
        the fingerprint would move when someone changed a dropdown, silently suspending every
        autonomy grant measured on it.
  MR003 the cheap model appears on no route that is not declared trivial, and the trivial
        class contains only capabilities that are actually bound.
  MR004 the loud default is present and is not the cheap model. If a spawn ever omits its
        explicit override the vendored ECC default takes effect, and that default is
        gpt-5-nano — a failure landing silently on the permissive side, which is the
        direction `lint_ci_coverage.py`'s docstring says this project has already paid for
        three times.
  MR005 no route declares `trivial: true` unless its capability is listed in the trivial
        class, and vice versa. The class is empty at Phase 0 and this is what keeps it empty
        by accident rather than by discipline.

**Vacuity guard.** The check reports how many routes and kinds it scanned, and a scan of zero
fails. Taken from `lint_verdict_boundary.py`, whose docstring explains the hazard: a check
with nothing to look at reports exactly what a passing check reports.

`--self-test` plants each violation in a temporary tree and requires the check to fire, and
requires it to stay quiet on the paired control. A lint with no negative control reports the
same thing whether it works or not.

Exit 0 clean, 1 on any violation. Protected set: agents may not write this file.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lintkit import REPO_ROOT, Findings, self_test_exit, vacuity_guard

BINDINGS_PATH: Path = Path("policy/role-bindings.json")
ROUTING_PATH: Path = Path("policy/model-routing.json")

#: The identity that must never reach a route. Not a list of "bad models" — a list of
#: non-identities. `inherit` names whatever a UI control currently says, which is not a value
#: a fingerprint can record.
UNPINNED = {"inherit", "", None}


def _load_json(path: Path, base: Path = REPO_ROOT) -> tuple[dict[str, Any] | None, str | None]:
    target = base / path
    if not target.exists():
        return None, f"MR000 missing {path}"
    try:
        return json.loads(target.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as exc:
        return None, f"MR000 {path} is not valid JSON: {exc}"


def check_routing(base: Path = REPO_ROOT) -> Findings:
    findings = Findings()
    bindings_data, b_err = _load_json(BINDINGS_PATH, base)
    routing_data, r_err = _load_json(ROUTING_PATH, base)

    if b_err is not None:
        findings.violations.append(b_err)
        return findings
    if r_err is not None:
        findings.violations.append(r_err)
        return findings

    assert bindings_data is not None and routing_data is not None

    bound = {
        b["capability_id"]
        for b in bindings_data.get("bindings", [])
        if isinstance(b.get("capability_id"), str)
    }
    routes: list[dict[str, Any]] = routing_data.get("routes", [])  # type: ignore[assignment]
    forbidden: dict[str, Any] = routing_data.get("forbidden", {})
    trivial: dict[str, Any] = routing_data.get("trivial_class", {})
    trivial_members = set(trivial.get("members", []))
    findings.scanned = len(bound) + len(routes)

    cheap = {m for m in forbidden if m != "inherit"}

    # MR001 -- both directions.
    routed: dict[str, int] = {}
    for route in routes:
        cap = route.get("capability_id")
        if not isinstance(cap, str):
            findings.violations.append("MR001 a route has no capability_id")
            continue
        routed[cap] = routed.get(cap, 0) + 1
        if cap not in bound:
            findings.violations.append(f"MR001 route for {cap!r}, which no binding declares")
    for cap in sorted(bound):
        if cap not in routed:
            findings.violations.append(f"MR001 bound capability {cap!r} has no route")
    for cap, count in sorted(routed.items()):
        if count > 1:
            findings.violations.append(f"MR001 capability {cap!r} has {count} routes, expected 1")

    # MR002 -- no unpinned identity.
    for route in routes:
        cap = route.get("capability_id", "<unnamed>")
        model = route.get("model")
        if model in UNPINNED:
            findings.violations.append(
                f"MR002 route {cap!r} resolves to {model!r}, which is not a pinned identity"
            )

    # MR003 -- the cheap model only where the class allows it.
    for route in routes:
        cap = route.get("capability_id", "<unnamed>")
        if route.get("model") in cheap and cap not in trivial_members:
            findings.violations.append(
                f"MR003 route {cap!r} uses {route.get('model')!r} but is not in the trivial class"
            )
    for cap in sorted(trivial_members):
        if cap not in bound:
            findings.violations.append(
                f"MR003 trivial class names {cap!r}, which no binding declares"
            )

    # MR004 -- the default fails expensively.
    default = routing_data.get("loud_default", {}).get("model")
    if default in UNPINNED:
        findings.violations.append(f"MR004 loud_default is {default!r}, not a pinned identity")
    elif default in cheap:
        findings.violations.append(
            f"MR004 loud_default is {default!r}, the cheap model — an omitted override would "
            "then fail silently on the permissive side"
        )

    # MR005 -- the trivial flag and the class agree.
    for route in routes:
        cap = route.get("capability_id", "<unnamed>")
        flagged = bool(route.get("trivial"))
        listed = cap in trivial_members
        if flagged and not listed:
            findings.violations.append(f"MR005 route {cap!r} claims trivial but is not in the class")
        if listed and not flagged:
            findings.violations.append(f"MR005 {cap!r} is in the trivial class but its route does not say so")

    return findings


# ------------------------------------------------------------------------------- self-test


def _valid_bindings() -> dict[str, Any]:
    return {
        "version": 1,
        "bindings": [
            {"kind": "planner", "capability_id": "capability:planner@1", "agents": []},
            {"kind": "reviewer", "capability_id": "capability:reviewer@1", "agents": []},
        ],
    }


def _valid_routing() -> dict[str, Any]:
    return {
        "version": 1,
        "forbidden": {"inherit": "unpinned", "gpt-5-nano": ["review"]},
        "loud_default": {"model": "claude-opus-5"},
        "trivial_class": {"members": []},
        "routes": [
            {"capability_id": "capability:planner@1", "model": "claude-opus-5", "trivial": False},
            {"capability_id": "capability:reviewer@1", "model": "claude-opus-5", "trivial": False},
        ],
    }


def _write(root: Path, bindings: dict[str, Any], routing: dict[str, Any]) -> None:
    for path, data in ((BINDINGS_PATH, bindings), (ROUTING_PATH, routing)):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(data), encoding="utf-8")


def self_test() -> int:
    failures: list[str] = []

    with tempfile.TemporaryDirectory() as raw:
        scratch = Path(raw)

        clean = scratch / "clean"
        _write(clean, _valid_bindings(), _valid_routing())
        ctrl = check_routing(base=clean)
        if ctrl.violations:
            failures.append(f"control fired on clean: {ctrl.violations}")

        # MR001 a bound capability with no route
        case = scratch / "mr001a"
        r = _valid_routing()
        r["routes"] = r["routes"][:1]
        _write(case, _valid_bindings(), r)
        if not any("MR001" in v for v in check_routing(base=case).violations):
            failures.append("MR001 did not fire on a bound capability with no route")

        # MR001 the reverse: a route for no binding
        case = scratch / "mr001b"
        r = _valid_routing()
        r["routes"].append({"capability_id": "capability:ghost@1", "model": "claude-opus-5"})
        _write(case, _valid_bindings(), r)
        if not any("MR001" in v for v in check_routing(base=case).violations):
            failures.append("MR001 did not fire on a route for no binding")

        # MR002 an unpinned identity
        case = scratch / "mr002"
        r = _valid_routing()
        r["routes"][0]["model"] = "inherit"
        _write(case, _valid_bindings(), r)
        if not any("MR002" in v for v in check_routing(base=case).violations):
            failures.append("MR002 did not fire on inherit")

        # MR003 the cheap model outside the trivial class
        case = scratch / "mr003a"
        r = _valid_routing()
        r["routes"][1]["model"] = "gpt-5-nano"
        _write(case, _valid_bindings(), r)
        if not any("MR003" in v for v in check_routing(base=case).violations):
            failures.append("MR003 did not fire on the cheap model outside the class")

        # MR003 the trivial class naming an unbound capability
        case = scratch / "mr003b"
        r = _valid_routing()
        r["trivial_class"]["members"] = ["capability:ghost@1"]
        _write(case, _valid_bindings(), r)
        if not any("MR003" in v for v in check_routing(base=case).violations):
            failures.append("MR003 did not fire on a trivial member with no binding")

        # MR004 the default set to the cheap model
        case = scratch / "mr004"
        r = _valid_routing()
        r["loud_default"]["model"] = "gpt-5-nano"
        _write(case, _valid_bindings(), r)
        if not any("MR004" in v for v in check_routing(base=case).violations):
            failures.append("MR004 did not fire on a cheap loud_default")

        # MR005 a route claiming trivial without being in the class
        case = scratch / "mr005"
        r = _valid_routing()
        r["routes"][0]["trivial"] = True
        _write(case, _valid_bindings(), r)
        if not any("MR005" in v for v in check_routing(base=case).violations):
            failures.append("MR005 did not fire on an unlisted trivial claim")

        # MR005 paired control: listed AND flagged is legal
        case = scratch / "mr005-ok"
        r = _valid_routing()
        r["routes"][0]["trivial"] = True
        r["routes"][0]["model"] = "gpt-5-nano"
        r["trivial_class"]["members"] = ["capability:planner@1"]
        _write(case, _valid_bindings(), r)
        if any("MR005" in v or "MR003" in v for v in check_routing(base=case).violations):
            failures.append("MR005/MR003 fired on a capability correctly listed and flagged")

    return self_test_exit(
        failures,
        "OK self-test — MR001 route/binding mismatch both directions, MR002 unpinned "
        "identity, MR003 cheap model outside the class and unbound trivial member, "
        "MR004 cheap loud_default, MR005 trivial flag against the class with its paired "
        "control; control clean\n",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint model routing policy MR001-MR005")
    parser.add_argument("--check", action="store_true", help="check files (default)")
    parser.add_argument("--self-test", action="store_true", help="plant violations and verify each check fires")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    findings = check_routing()
    for violation in findings.violations:
        sys.stdout.write(f"{violation}\n")
    if vacuity_guard(findings.scanned, "VACUOUS routing: scanned 0 capabilities+routes\n"):
        return 1
    if findings.violations:
        return 1
    sys.stdout.write(
        f"OK model routing — {findings.scanned} capabilities+routes, all MR001-MR005 satisfied\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
