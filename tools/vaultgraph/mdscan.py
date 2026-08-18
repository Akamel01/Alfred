"""Line-oriented markdown primitives. The risky parsing, isolated from anything that uses it.

**No markdown AST, deliberately.** The plan encodes D38 and D48-D57 as single `| N | ... |`
rows separated by blank lines. In CommonMark each is its own headerless fragment, so a table
parser does not see them as rows at all -- it is not that a parser is a heavier tool than
needed, it is that a parser is *wrong* here and a line regex is right.

Everything in this module is a pure function over strings, so the adversarial cases -- escaped
pipes, strikethrough, unterminated bold spans, U+2212 minus signs, en-dash ranges -- are
testable without a fixture tree.
"""

from __future__ import annotations

import re

#: U+2212 MINUS SIGN. The plan spells `Phase −1` and `Phase −2` with it; ASCII `Phase -1`
#: never appears. An id built from the raw glyph is not a portable filename.
MINUS = "−"
EN_DASH = "–"
EM_DASH = "—"

#: A `|` that is not escaped. D55's row carries `Simulated \| Corpus \| Unknown` inside a code
#: span, so a naive `line.split("|")` yields seven fields where every other row yields five.
_UNESCAPED_PIPE = re.compile(r"(?<!\\)\|")

_STRIKE = re.compile(r"~~(.+?)~~", re.DOTALL)
_BOLD_SPAN = re.compile(r"\*\*(.+?)\*\*")
_RANGE = re.compile(rf"\b([A-Z])(\d+)\s*[{EN_DASH}{EM_DASH}{MINUS}-]\s*([A-Z]?)(\d+)\b")


def is_table_row(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|") and len(stripped) > 2


def is_separator_row(line: str) -> bool:
    return bool(re.fullmatch(r"\s*\|[\s:|-]+\|\s*", line)) and "-" in line


def split_row(line: str) -> list[str]:
    """Cells of a table row, escaped pipes preserved as literal `|` inside a cell."""
    stripped = line.strip()
    if not is_table_row(stripped):
        return []
    parts = _UNESCAPED_PIPE.split(stripped)
    # The leading and trailing pipes produce empty edge fields; drop exactly those two.
    return [cell.strip().replace(r"\|", "|") for cell in parts[1:-1]]


def strip_strikethrough(text: str) -> tuple[str, str]:
    """Split a cell into (text with withdrawn spans removed, the withdrawn text).

    D30 is the only cell in the plan that uses `~~...~~`, and it pairs the withdrawal with a
    bracketed bold replacement in the same cell. Dropping either half loses the fact that a
    clause was retracted and what replaced it, which is precisely what a decision graph is for.
    """
    withdrawn = " ".join(m.group(1).strip() for m in _STRIKE.finditer(text))
    return _STRIKE.sub("", text).strip(), withdrawn


def bold_span(text: str, label: str) -> str:
    """The body of a `**label:**` clause, running to the next bold span or the end of the cell.

    There is no closing delimiter -- `**Falsifies if:**` simply runs until something else
    starts. Both terminators occur in the plan, so both are handled here rather than at the
    five call sites.
    """
    marker = f"**{label}:**"
    start = text.find(marker)
    if start == -1:
        return ""
    rest = text[start + len(marker):]
    nxt = _BOLD_SPAN.search(rest)
    return (rest[: nxt.start()] if nxt else rest).strip()


def normalize_minus(text: str) -> str:
    """U+2212 to ASCII hyphen, for ids only. Callers keep the raw glyph in `attrs`."""
    return text.replace(MINUS, "-")


def expand_range(token: str) -> list[str]:
    """`S1-S8` to the eight ids it names. Stage dependency clauses state ranges, and an edge
    to a literal `S1–S8` is an edge to nothing."""
    match = _RANGE.fullmatch(token.strip())
    if not match:
        return [token.strip()]
    prefix, lo, tail_prefix, hi = match.groups()
    if tail_prefix and tail_prefix != prefix:
        return [token.strip()]
    low, high = int(lo), int(hi)
    if high < low or high - low > 64:
        return [token.strip()]
    return [f"{prefix}{n}" for n in range(low, high + 1)]


def bold_lead(line: str) -> str:
    """The bold run a paragraph opens with, or empty. `**Decision 42 - title.** body` -> the
    text inside the first `**...**`, only when the line actually starts with it."""
    if not line.startswith("**"):
        return ""
    match = _BOLD_SPAN.match(line)
    return match.group(1).strip() if match else ""
