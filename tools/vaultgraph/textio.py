"""Reading the repo the same way the repo already reads itself, and one path spelling.

Two properties this module exists to hold:

**Every path that reaches output is repo-relative POSIX.** `rel()` is the single choke point.
An absolute path in `graph.json` makes the output machine-specific, which is the same defect
as a timestamp and harder to spot.

**Line endings are normalized before parsing, never before hashing.** `read_lines()` folds
CRLF so a checkout under a different `core.autocrlf` parses identically; the mirror is hashed
from raw bytes, because a hash of normalized text would not detect the rewrite it exists to
detect.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def rel(path: Path, root: Path = ROOT) -> str:
    """Root-relative POSIX spelling. The only path form allowed to reach output.

    `root` is a parameter rather than the module constant because the self-test builds planted
    fixtures under a temporary directory, and a hardcoded repo root would put an absolute
    `/var/folders/...` path into that run's output — the exact defect this function exists to
    prevent, arriving through the door meant to close it.
    """
    return path.resolve().relative_to(root.resolve()).as_posix()


def read_lines(path: Path) -> list[str]:
    """File as a list of lines, no terminators, CRLF folded. 1-based indexing is the
    caller's job: `lines[i]` is line `i + 1`."""
    return path.read_text(encoding="utf-8").replace("\r\n", "\n").split("\n")


def parse_frontmatter(path: Path) -> tuple[dict[str, str], list[str]]:
    """Ported verbatim from `scripts/lint_docs.py:41-63`, for the reason stated there:
    a YAML dependency would make the tool that reads the register depend on the supply
    chain the register governs. Values are flat strings — there are no lists, which is
    why every document keeps `evidence:` and `falsifies_if:` on one long line.

    Kept a copy rather than an import: `scripts/` is D20-protected inspector machinery,
    and a generator in `tools/` importing from it would put a factory module inside the
    inspector's import closure.
    """
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    errors: list[str] = []
    if not text.startswith("---\n"):
        return {}, [f"{path.name}: missing frontmatter"]

    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, [f"{path.name}: unterminated frontmatter"]

    fields: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            errors.append(f"{path.name}: unparseable frontmatter line: {line.strip()[:60]}")
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields, errors


def frontmatter_end_line(path: Path) -> int:
    """1-based line number of the closing `---`, so a body source pointer can start after it."""
    for i, line in enumerate(read_lines(path)[1:], start=2):
        if line == "---":
            return i
    return 1


def title_of(lines: list[str], fallback: str) -> str:
    """First `# ` heading, as `lint_docs.build_index` does, falling back to the stem."""
    for line in lines:
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


_SLUG_STRIP = re.compile(r"[^A-Za-z0-9 ._-]+")
_SLUG_SPACE = re.compile(r"\s+")


def slug(text: str) -> str:
    """A filename-safe rendering of a title, for note filenames and aliases."""
    cleaned = _SLUG_STRIP.sub("", text.replace("—", "-").replace("–", "-").replace("−", "-"))
    return _SLUG_SPACE.sub(" ", cleaned).strip(" .-") or "untitled"
