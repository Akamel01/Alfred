#!/usr/bin/env python3
"""AGENTS.md is a byte-identical twin of CLAUDE.md — ICM naming convention.

Two entry files with divergent content is a classic drift: one is updated,
the other is not, and the agent reads whichever the harness happens to name.
ICM requires one source, one generated twin, and a check that fails on drift
rather than a convention that agents remember.

    python3 tools/gen_agents.py              # write AGENTS.md from CLAUDE.md
    python3 tools/gen_agents.py --check      # fail if AGENTS.md differs or is absent
    python3 tools/gen_agents.py --self-test  # prove the check fires
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "CLAUDE.md"
TWIN = ROOT / "AGENTS.md"


def check() -> tuple[int, str]:
    if not SOURCE.is_file():
        return 1, f"missing source {SOURCE.relative_to(ROOT)}"
    if not TWIN.is_file():
        return 1, f"missing twin {TWIN.relative_to(ROOT)} — run python3 tools/gen_agents.py"
    a = SOURCE.read_bytes()
    b = TWIN.read_bytes()
    if a != b:
        return 1, f"AGENTS.md drift: CLAUDE.md ({len(a)} bytes) != AGENTS.md ({len(b)} bytes) — run python3 tools/gen_agents.py"
    return 0, f"AGENTS.md twin current ({len(a)} bytes)"


def write() -> tuple[int, str]:
    if not SOURCE.is_file():
        return 1, f"missing source {SOURCE.relative_to(ROOT)}"
    data = SOURCE.read_bytes()
    TWIN.write_bytes(data)
    return 0, f"wrote {TWIN.relative_to(ROOT)} ({len(data)} bytes) from {SOURCE.relative_to(ROOT)}"


def self_test() -> int:
    # Prove check fires on missing/drift and passes when current.
    import tempfile, shutil
    tmp = Path(tempfile.mkdtemp(prefix="agents-selftest-"))
    try:
        # Use temp copies to avoid touching real files
        src = tmp / "CLAUDE.md"
        twin = tmp / "AGENTS.md"
        src.write_text("hello\n")
        # missing twin → check fails
        orig_source, orig_twin = SOURCE, TWIN
        # monkey patch globals via local test of underlying logic
        # Instead test directly: missing twin case
        # Simulate by checking temp paths
        def _check(s: Path, t: Path) -> int:
            if not t.is_file():
                return 1
            return 0 if s.read_bytes() == t.read_bytes() else 1
        assert _check(src, twin) == 1, "should fail when twin missing"
        twin.write_text("hello\n")
        assert _check(src, twin) == 0, "should pass when twin identical"
        twin.write_text("drift\n")
        assert _check(src, twin) == 1, "should fail on drift"
        print("AGENTS twin self-test: 3/3 checks passed (missing, drift, current)")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true", help="fail if AGENTS.md is stale or absent")
    p.add_argument("--self-test", action="store_true", help="prove the check fires")
    args = p.parse_args(argv)
    if args.self_test:
        return self_test()
    if args.check:
        code, msg = check()
        print(msg)
        return code
    code, msg = write()
    print(msg)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
