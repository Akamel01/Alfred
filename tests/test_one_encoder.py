"""ADR-0003: "A CI check asserts no code path hashes a structure through any encoder
but this one."

Structural rather than behavioural, deliberately. The failure this guards against
is a second canonical form appearing somewhere quiet — a `json.dumps(...,
sort_keys=True)` in a caching layer, a `hashlib.sha256(repr(x))` in a debug
helper — and no unit test of the *right* encoder can notice that.
"""

from __future__ import annotations

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"

# The one door to ACS-1. Everything else in src/ goes through it.
ENCODER_DOOR = SRC / "provenance" / "encoding.py"

FORBIDDEN_MODULES = {"hashlib", "pickle", "marshal"}
FORBIDDEN_CALLS = {"json.dumps", "json.dump"}


def _product_modules() -> list[Path]:
    return sorted(p for p in SRC.rglob("*.py") if p != ENCODER_DOOR)


def test_no_product_module_imports_a_hashing_or_serialization_backdoor() -> None:
    offenders: list[str] = []
    for path in _product_modules():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] in FORBIDDEN_MODULES:
                        offenders.append(f"{path}:{node.lineno} import {alias.name}")
            elif (
                isinstance(node, ast.ImportFrom)
                and node.module is not None
                and node.module.split(".")[0] in FORBIDDEN_MODULES
            ):
                offenders.append(f"{path}:{node.lineno} from {node.module}")
    assert not offenders, "a second hashing path exists:\n" + "\n".join(offenders)


def test_no_product_module_serializes_through_stdlib_json() -> None:
    offenders: list[str] = []
    for path in _product_modules():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                dotted = f"{func.value.id}.{func.attr}"
                if dotted in FORBIDDEN_CALLS:
                    offenders.append(f"{path}:{node.lineno} {dotted}")
    assert not offenders, "a second canonical form exists:\n" + "\n".join(offenders)


def test_acs1_is_imported_from_the_harness_and_not_vendored() -> None:
    source = ENCODER_DOOR.read_text(encoding="utf-8")
    assert "from harness.acs.acs1 import" in source
    # If ACS-1 were reimplemented here, these would be its unmistakable fingerprints.
    for fingerprint in ("def encode_float", "def canonicalize(", "unicodedata.normalize"):
        assert fingerprint not in source, f"ACS-1 looks reimplemented: {fingerprint}"


def test_the_encoder_lives_outside_the_agent_tree() -> None:
    harness_encoder = SRC.parent / "harness" / "acs" / "acs1.py"
    assert harness_encoder.is_file()
    assert not (SRC / "acs1.py").exists()
