"""Planted fixture trees, kept apart from the assertions that use them.

The fixtures are real text lightly trimmed, not invented prose. A rule proved against prose
nobody will ever parse is proved against nothing -- so the decision fixture carries the actual
escaped-pipe row, the actual U+2212 heading, and the eight commentary spans in the shapes the
plan writes them.
"""

from __future__ import annotations

from pathlib import Path

from .mirror import MIRROR_NAME

DOC = """---
status:        frozen
owner:         human
enforcement:   none
evidence:      none — planted fixture
falsifies_if:  This fixture is read as anything other than a fixture.
review_after:  Phase 4
---

# {title}

Body.
"""


#: Every decision shape the plan uses, one instance each, plus the eight commentary spans that
#: wear the same clothes. Real text, lightly trimmed -- a fixture written in invented prose
#: proves the rule against prose nobody will ever parse.
PLAN_FIXTURE = """# Fixture

| # | Decision | Rationale |
|---|---|---|
| 1 | **Real product with real users** is the first deliverable. | Real usage supplies ground truth. |
| 55 | **Stamp carries `upstream: Simulated \\| Corpus \\| Unknown`.** | ADR-0003 treats these as two problems. |

| 48 | **Alfred's buyer is the AV developer's own V&V function.** Supersedes decision 1. | K5 established this. **Falsifies if:** no design-partner engagement by Phase 1 exit. |

### Decision 39 — structural enforcement of D16/D20

### Decision 41 RESOLVED — the lane is Qwen3 on MLX (2026-08-11)

**Decision 42 — Demand gate and company-level kill criteria.** The largest risk.

**Decision 42 amended — the gate moves to Phase 0.75.** Restated later.

| A7 | **Decision 12 becomes a machine-checkable criterion**, not a policy. | Egress canary. |
| A9 | **Decision 23 extends to the read side**: readable paths fixed by the harness. | Enforced by mount. |
| 38 | **Decision 9's named harness demoted to provisional.** Buy-the-loop stands. | The SDK's loop is Anthropic-shaped. |

- **Decision 7's LLM exclusion** — EvilGenie found LLM judges outperformed held-out tests.
- **Decision 6's graduation metric** — calibrating on visible-criterion pass rate.
- **Decision 2's ceiling** — metric computation is machine-checkable.
- **Decision 17** — no evidence exists either way.

**Decision 37 turns out to be a correctness safeguard, not just a constraint.** mlx-lm issue #965.
"""


def _plant_plan(root: Path) -> None:
    (root / "plan").mkdir(parents=True, exist_ok=True)
    (root / "plan" / MIRROR_NAME).write_text(PLAN_FIXTURE, encoding="utf-8")


#: A module where the same token appears twice: once as live code, once in a comment. Only
#: the comment is a claim about a decision. `0xD16` and `D16_CONSTANT` are the reason this
#: extractor uses `tokenize` spans rather than a line regex.
REFERENCE_FIXTURE = '''"""Fixture module (ADR-0001).

Docstrings are claims too, so this one must be found.
"""

MASK = 0xD16ABC
D40_CONSTANT = 7


def compute() -> int:
    # D19: this comment is the claim, and the only D19 on this line that counts.
    return MASK + D40_CONSTANT
'''


def _plant_code(root: Path) -> None:
    package = root / "harness" / "fixture"
    package.mkdir(parents=True, exist_ok=True)
    (package / "__init__.py").write_text('"""Fixture package."""\n', encoding="utf-8")
    (package / "probe.py").write_text(REFERENCE_FIXTURE, encoding="utf-8")


def _plant(root: Path) -> None:
    docs = root / "docs"
    (docs / "tier0").mkdir(parents=True)
    (docs / "tier1").mkdir(parents=True)
    (docs / "tier0" / "charter.md").write_text(DOC.format(title="Charter"), encoding="utf-8")
    (docs / "tier1" / "architecture.md").write_text(DOC.format(title="Architecture"), encoding="utf-8")
    # The adjacent pair: same directory, same extension, same frontmatter shape. Generated,
    # therefore excluded — exactly as `lint_docs.main` excludes them.
    (docs / "README.md").write_text(DOC.format(title="Register"), encoding="utf-8")
    (docs / "READING-MAP.md").write_text(DOC.format(title="Reading map"), encoding="utf-8")
