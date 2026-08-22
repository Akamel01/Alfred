"""The vault's `protected` node flag answers to the policy file, not to a hand copy.

`extract/code.py` tags modules as protected using its own tuple of prefixes. The
authoritative machine-readable protected set lives in `policy/protected-paths.json`
(D20 / ADR-0031). Two lists that both claim to know what "protected" means will drift
silently — the graph would then draw an unprotected module as protected, or hide a
protected one behind no marker at all, and nothing downstream could tell.

The relationship is deliberately subset-with-nesting, not equality: the graph only
needs to flag *code* trees, while the policy also covers files (`pyproject.toml`) and
test data (`tests/heldout/`). What this binding pins is the direction that matters:
every prefix the extractor marks must be justified by the policy — either exactly a
policy prefix or inside one. A new protected area added to the policy without the
graph noticing is a coverage gap someone should see and decide on; it fails loudly
here rather than rendering quietly wrong.
"""

from __future__ import annotations

import json
from pathlib import Path

from tools.vaultgraph.extract.code import PROTECTED

ROOT = Path(__file__).resolve().parent.parent.parent


def _policy_prefixes() -> list[str]:
    raw = json.loads((ROOT / "policy" / "protected-paths.json").read_text())
    return [entry["path"] for entry in raw["prefixes"]]


def test_every_graph_protected_prefix_is_justified_by_the_policy() -> None:
    prefixes = _policy_prefixes()
    unclaimed = [
        p for p in PROTECTED if not any(p == q or p.startswith(q) for q in prefixes)
    ]
    assert unclaimed == [], (
        f"{unclaimed} are marked protected in the vault but claimed by no "
        f"policy prefix {prefixes}; fix code.py or the policy — never neither"
    )


def test_the_binding_covers_the_whole_code_side() -> None:
    """Vacuity control (D57): if PROTECTED ever becomes empty or loses entries, the
    subset check above would pass for free."""
    assert len(PROTECTED) >= 4
    assert all(p.endswith("/") for p in PROTECTED), "prefixes are directories"
