"""Where decisions are enforced in code, read out of comments and docstrings.

**`tokenize`, not `ast`.** The obvious approach -- walk the AST and read docstrings -- misses
most of the evidence, because `ast` discards comments entirely and the majority of decision
references in this repo sit in `#` comments directly above the construct they justify.
`tokenize` yields COMMENT and STRING tokens with exact positions, which is both the complete
set and the constrained span the identifier patterns need.

**The span constraint is the whole point.** `\\bA\\d{1,2}\\b` and `\\bC\\d{1,2}\\b` match hex
digits and ordinary identifiers, so scanning raw lines would produce confident nonsense.
Restricting to comment and string tokens is what makes these edges worth recording, and it is
why `.mjs`, `.sql`, `.yaml` and `.json` files get their own narrow comment scanners rather
than being run through the same line regex.

Confidence is DERIVED, never STRUCTURAL: a decision id written beside a function is a claim by
whoever wrote the comment, not a checked relation. It is far better than nothing -- and
`docs/tier7/decision-index.md` is a register stub whose falsification condition is *"a
decision is enforced in code with no index entry"* -- but it is not the same kind of fact as a
table column, and the graph says so.
"""

from __future__ import annotations

import io
import re
import tokenize

from ..model import Confidence, Edge, EdgeKind, NodeKind, SourceRef
from ..protocol import Context, ExtractorSpec, Harvest
from ..textio import read_lines, rel

NAME = "references"

#: Trees worth scanning. `docs/` is prose and belongs to other extractors; `plan/` is the
#: mirror and is parsed by the plan extractors, not grepped.
TREES = ("harness", "src", "scripts", "migrations", "policy", "bench", "tests")
EXTRA_FILES = (".github/workflows/gates.yml",)

PY_SUFFIX = ".py"
COMMENT_SUFFIXES = {".mjs", ".js", ".sql", ".yaml", ".yml", ".json"}

#: `D` and `ADR` only. `A\d` and `F\d` were measured and rejected for this pass: even inside
#: comment spans they collide with prose ("A1" as a table cell label, "F1" as a figure), and
#: an edge set that is 90% right is worse here than one that is smaller and trustworthy.
_IDS = re.compile(r"\b(D\d{1,2})\b|\b(ADR-\d{4})\b")

_JS_COMMENT = re.compile(r"//(.*)|/\*(.*?)\*/", re.DOTALL)
_HASH_COMMENT = re.compile(r"#(.*)")
_SQL_COMMENT = re.compile(r"--(.*)")
_JSON_COMMENT_KEY = re.compile(r'"_comment"')


def _python_spans(path) -> list[tuple[int, str]]:
    """(line, text) for every comment and string token. A file that will not tokenize is a
    finding for the caller, not a silent skip."""
    spans: list[tuple[int, str]] = []
    with open(path, "rb") as handle:
        for token in tokenize.tokenize(handle.readline):
            if token.type in (tokenize.COMMENT, tokenize.STRING):
                spans.append((token.start[0], token.string))
    return spans


def _text_spans(path, suffix: str) -> list[tuple[int, str]]:
    """Comment spans for the non-Python formats. `policy/*.json` carries its prose in
    `"_comment"` arrays, which is why JSON is scanned at all."""
    spans: list[tuple[int, str]] = []
    lines = read_lines(path)
    if suffix == ".json":
        collecting = False
        for index, line in enumerate(lines):
            if _JSON_COMMENT_KEY.search(line):
                collecting = True
            if collecting:
                spans.append((index + 1, line))
                if line.rstrip().endswith("],"):
                    collecting = False
        return spans
    pattern = (
        _JS_COMMENT if suffix in {".mjs", ".js"}
        else _SQL_COMMENT if suffix == ".sql"
        else _HASH_COMMENT
    )
    for index, line in enumerate(lines):
        for match in pattern.finditer(line):
            spans.append((index + 1, next((g for g in match.groups() if g), "")))
    return spans


def _module_id(rel_path: str) -> str:
    local = rel_path.replace("/", ".")
    if rel_path.endswith(PY_SUFFIX):
        local = local.removesuffix(PY_SUFFIX)
    return f"{NodeKind.MODULE.value}:{local}"


def extract(ctx: Context) -> Harvest:
    harvest = Harvest()
    root = ctx.root

    paths = []
    for tree in TREES:
        base = root / tree
        if base.is_dir():
            paths.extend(sorted(
                p for p in base.rglob("*")
                if p.is_file() and "__pycache__" not in p.parts
                and (p.suffix == PY_SUFFIX or p.suffix in COMMENT_SUFFIXES)
            ))
    paths.extend(root / name for name in EXTRA_FILES if (root / name).is_file())

    seen: set[tuple[str, str, int]] = set()
    for path in paths:
        rel_path = rel(path, root)
        harvest.scanned += 1
        try:
            spans = (_python_spans(path) if path.suffix == PY_SUFFIX
                     else _text_spans(path, path.suffix))
        except (tokenize.TokenError, SyntaxError, UnicodeDecodeError) as error:
            harvest.unparsed.append(
                __import__("tools.vaultgraph.protocol", fromlist=["Unparsed"]).Unparsed(
                    NAME, SourceRef(rel_path, 1), rel_path, f"could not tokenize: {error}"
                )
            )
            continue

        for line_no, text in spans:
            for match in _IDS.finditer(text):
                identifier = match.group(1) or match.group(2)
                target = (f"{NodeKind.DECISION.value}:{identifier}"
                          if identifier.startswith("D")
                          else f"{NodeKind.ADR.value}:{identifier}")
                key = (target, rel_path, line_no)
                if key in seen:
                    continue
                seen.add(key)
                harvest.edges.append(Edge(
                    src=target, dst=_module_id(rel_path), kind=EdgeKind.ENFORCED_BY,
                    confidence=Confidence.DERIVED, source=SourceRef(rel_path, line_no),
                    evidence=text.strip()[:180], extractor=NAME,
                ))
    return harvest


SPEC = ExtractorSpec(
    name=NAME,
    # This extractor mints no nodes; it only relates ones other extractors minted. `min_nodes`
    # cannot express that, so the floor it carries is on edges, and `kinds` records what it
    # relates rather than what it creates.
    kinds=(NodeKind.DECISION, NodeKind.ADR, NodeKind.MODULE),
    min_nodes=0,
    max_nodes=0,
    min_edges=80,
    max_unparsed=0,
    expect_rejected=None,
    run=extract,
)
