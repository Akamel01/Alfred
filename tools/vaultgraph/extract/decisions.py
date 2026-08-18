"""D1-D57, which the plan encodes four different ways, two of them traps.

* **D1-D37** contiguous three-column table rows.
* **D38 and D48-D57** the same row syntax, each separated by blank lines. In CommonMark these
  are headerless fragments, not table rows -- which is why nothing here uses a table parser.
* **D39-D41** `### Decision NN -- ...` headings, three different spellings, D41 sitting 477
  lines from its siblings with a status word and a date inside the heading.
* **D42-D47** `**Decision NN -- title.**` bold-lead paragraphs, several restated later as
  `amended` or `finalized`.

**The classification rule is one property, applied everywhere.** A bold run or heading naming
a decision is a *definition or restatement* when the em dash separating the number from a title
falls inside the span, and *commentary* when it does not. That single test sorts
`**Decision 42 — Demand gate...**` from `**Decision 12 becomes a machine-checkable criterion**`
and `**Decision 7's LLM exclusion**` without an enumerated blacklist that would rot the moment
the plan is edited.

Commentary is **rejected, and counted**. `expect_rejected` is checked for equality by the
runner: a rule that stopped firing would admit eight junk decisions, and a rule that
over-tightened would report zero rejections while silently dropping real ones. A floor catches
neither; equality catches both.
"""

from __future__ import annotations

import re

from ..model import Confidence, Edge, EdgeKind, Node, NodeKind, SourceRef
from ..mdscan import bold_lead, bold_span, split_row, strip_strikethrough
from ..mirror import MIRROR_NAME
from ..protocol import Anomaly, Context, ExtractorSpec, Harvest, Rejected, Unparsed
from ..textio import read_lines

NAME = "decisions"

EXPECTED = 57
EXPECTED_REJECTED = 8

_ROW = re.compile(r"^\|\s*(\d{1,2})\s*\|")
_HEADING = re.compile(r"^###\s+Decision\s+(\d{1,2})\b(.*)$")
_BOLD_DECISION = re.compile(r"\*\*(Decision\s+(\d{1,2})\b[^*]*)\*\*")
#: A title separator inside the span: a dash with space on both sides. Em dash is the plan's
#: spelling and en dash is accepted so a future edit reaching for the other one does not
#: silently become commentary. **A bare ASCII hyphen is not accepted** -- it appears inside
#: compound words on nearly every line, and admitting it read
#: `**Decision 12 becomes a machine-checkable criterion**` as a titled definition by matching
#: the hyphen in "machine-checkable".
_TITLED = re.compile(r"^Decision\s+\d{1,2}\b[^—–]*\s[—–]\s+\S")
_SUPERSEDES = re.compile(r"[Ss]upersedes\s+decision\s+(\d{1,2})")


def _title_from(text: str) -> str:
    """The clause after the title separator, or the whole thing when there is none."""
    for dash in (" — ", " – "):
        if dash in text:
            return text.split(dash, 1)[1].strip().rstrip(".")
    return text.strip().rstrip(".")


def _scan_bold(line, src, own_number, claim, harvest) -> None:
    """Classify every `**Decision N ...**` span on a line. Runs on table rows too: D38's own
    row opens with `**Decision 9's named harness ... demoted to provisional.**`, a commentary
    span that a scan skipping rows would never see and never count."""
    for match in _BOLD_DECISION.finditer(line):
        span, number = match.group(1).strip(), int(match.group(2))
        if number == own_number:
            continue
        if not _TITLED.match(span):
            harvest.rejected.append(
                Rejected(NAME, src, span[:200], "names a decision without titling it")
            )
            continue
        claim(number, Node(
            id="", kind=NodeKind.DECISION, title=_title_from(span), source=src,
            shape="bold-paragraph", body=line.strip()[:600],
            attrs={"number": str(number)}, extractor=NAME,
        ))


def extract(ctx: Context) -> Harvest:
    harvest = Harvest()
    path = ctx.root / "plan" / MIRROR_NAME
    if not path.is_file():
        return harvest

    lines = read_lines(path)
    rel_path = f"plan/{MIRROR_NAME}"
    harvest.scanned = 1

    #: number -> (line, title, body, rationale, shape). Populated in source order so a table
    #: row always claims the number before a later heading or paragraph can restate it.
    found: dict[int, Node] = {}
    restatements: dict[int, list[SourceRef]] = {}
    supersedes: list[tuple[int, int, int, str]] = []

    def claim(number: int, node: Node) -> None:
        if number in found:
            restatements.setdefault(number, []).append(node.source)
        else:
            found[number] = node

    for index, line in enumerate(lines):
        line_no = index + 1
        src = SourceRef(rel_path, line_no)

        # ---- Variants A and B. Identical syntax; the blank lines between the B rows are why
        #      this is a line scan and not a table parse.
        row_match = _ROW.match(line)
        if row_match:
            cells = split_row(line)
            if len(cells) != 3:
                harvest.unparsed.append(
                    Unparsed(NAME, src, line[:200], f"numbered row split into {len(cells)} cells")
                )
                continue
            number = int(row_match.group(1))
            decision, withdrawn = strip_strikethrough(cells[1])
            attrs = {
                "rationale": cells[2],
                "falsifies_if": bold_span(cells[1], "Falsifies if"),
                "number": str(number),
            }
            if withdrawn:
                attrs["withdrawn"] = withdrawn
            claim(number, Node(
                id="", kind=NodeKind.DECISION, title=_title_from(bold_lead(decision) or decision),
                source=src, shape="table-row", body=decision, attrs=attrs, extractor=NAME,
            ))
            for target in _SUPERSEDES.finditer(cells[1] + " " + cells[2]):
                supersedes.append((number, int(target.group(1)), line_no, target.group(0)))
            _scan_bold(line, src, number, claim, harvest)
            continue

        # ---- Variant C. Headings.
        heading = _HEADING.match(line)
        if heading:
            number = int(heading.group(1))
            span = f"Decision {number}{heading.group(2)}"
            if not _TITLED.match(span):
                harvest.rejected.append(
                    Rejected(NAME, src, line[:200], "heading names a decision without titling it")
                )
                continue
            claim(number, Node(
                id="", kind=NodeKind.DECISION, title=_title_from(span), source=src,
                shape="heading", body=line.strip(), attrs={"number": str(number)}, extractor=NAME,
            ))
            continue

        # ---- Variant D, and every commentary lookalike.
        _scan_bold(line, src, None, claim, harvest)
        for target in _SUPERSEDES.finditer(line):
            if not _ROW.match(line):
                supersedes.append((0, int(target.group(1)), line_no, target.group(0)))

    # ---- Mint in numeric order so the graph reads the way the plan is numbered.
    minted: dict[int, str] = {}
    for number in sorted(found):
        node = found[number]
        node_id = ctx.minter.mint(NodeKind.DECISION, f"D{number}", node.source)
        minted[number] = node_id
        harvest.nodes.append(Node(
            id=node_id, kind=node.kind, title=node.title, source=node.source, shape=node.shape,
            body=node.body, attrs=node.attrs,
            occurrences=tuple(sorted(restatements.get(number, []))),
            extractor=NAME,
        ))

    for src_number, dst_number, line_no, evidence in supersedes:
        if src_number not in minted or dst_number not in minted:
            continue
        harvest.edges.append(Edge(
            src=minted[src_number], dst=minted[dst_number], kind=EdgeKind.SUPERSEDES,
            confidence=Confidence.PROSE, source=SourceRef(rel_path, line_no),
            evidence=evidence, extractor=NAME,
        ))

    missing = [n for n in range(1, EXPECTED + 1) if n not in found]
    if missing:
        harvest.anomalies.append(Anomaly(
            kind="missing-decision",
            detail=f"D1-D{EXPECTED} declared, {len(missing)} not found: "
                   + ", ".join(f"D{n}" for n in missing),
        ))
    return harvest


SPEC = ExtractorSpec(
    name=NAME,
    kinds=(NodeKind.DECISION,),
    # Exact, not a floor. The input is a byte-frozen mirror with a recorded sha256, so the
    # count is knowable; a re-sync that breaks a shape must red the build rather than quietly
    # produce 55. Updating these two numbers after a sync is the review trigger.
    min_nodes=EXPECTED,
    max_nodes=EXPECTED,
    min_edges=1,
    max_unparsed=0,
    expect_rejected=EXPECTED_REJECTED,
    run=extract,
)
