"""A1-A12, and the edges from an amendment to the decision it amends.

The cleanest construct in the plan: one contiguous three-column table, twelve rows, one
physical line each, no blank-line breaks and no escaped pipes. It is here as its own extractor
rather than folded into `decisions` because its floor is a different claim -- twelve is exact
and knowable, and an amendment table that stopped parsing must not be masked by fifty-seven
decisions still arriving.

`\\bA\\d{1,2}\\b` false-positives on `A2A` (the agent protocol) and `A2D2` (the dataset). Both
are excluded by requiring the row's first cell to be the whole id, which is why the ids are
read from the table column and never from prose.
"""

from __future__ import annotations

import re

from ..mdscan import split_row
from ..mirror import MIRROR_NAME
from ..model import Confidence, Edge, EdgeKind, Node, NodeKind, SourceRef
from ..protocol import Anomaly, Context, ExtractorSpec, Harvest, Unparsed
from ..textio import read_lines

NAME = "amendments"
EXPECTED = 12

_ROW = re.compile(r"^\|\s*(A\d{1,2})\s*\|")
#: The amendment table cites decisions three ways and only three times in twelve rows --
#: "Supersedes decision 11's", "decision 19", "decision 7's". The short `D19` form the rest of
#: the plan uses does not appear here at all, which is why the floor below is 3 and not the
#: dozen a reader would guess.
_TARGET = re.compile(r"\bdecisions?\s+(\d{1,2})\b|\bD(\d{1,2})\b")


def _title_from(cell: str) -> str:
    lead = re.match(r"\*\*(.+?)\*\*", cell)
    text = lead.group(1) if lead else cell
    return text.strip().rstrip(".:")[:200]


def extract(ctx: Context) -> Harvest:
    harvest = Harvest()
    path = ctx.root / "plan" / MIRROR_NAME
    if not path.is_file():
        return harvest
    lines = read_lines(path)
    rel_path = f"plan/{MIRROR_NAME}"
    harvest.scanned = 1

    seen: list[tuple[str, SourceRef, list[str]]] = []
    for index, line in enumerate(lines):
        match = _ROW.match(line)
        if not match:
            continue
        cells = split_row(line)
        src = SourceRef(rel_path, index + 1)
        if len(cells) != 3:
            harvest.unparsed.append(
                Unparsed(NAME, src, line[:200], f"amendment row split into {len(cells)} cells")
            )
            continue
        seen.append((match.group(1), src, cells))

    for amendment_id, src, cells in seen:
        node_id = ctx.minter.mint(NodeKind.AMENDMENT, amendment_id, src)
        harvest.nodes.append(Node(
            id=node_id, kind=NodeKind.AMENDMENT, title=_title_from(cells[1]), source=src,
            shape="table-row", body=cells[1],
            attrs={"evidence": cells[2], "number": amendment_id}, extractor=NAME,
        ))
        # Targets are read from both cells: the amendment states what it changes, and the
        # evidence column is where "Supersedes decision 11's enumerate-the-bad primitive" lives.
        targets: set[str] = set()
        for target in _TARGET.finditer(f"{cells[1]} {cells[2]}"):
            number = next(g for g in target.groups() if g)
            targets.add(number)
        for number in sorted(targets, key=int):
            harvest.edges.append(Edge(
                src=node_id, dst=f"decision:D{number}", kind=EdgeKind.AMENDS,
                confidence=Confidence.PROSE, source=src,
                evidence=f"D{number} named in A{amendment_id[1:]}", extractor=NAME,
            ))

    missing = [f"A{n}" for n in range(1, EXPECTED + 1)
               if f"A{n}" not in {a for a, _, _ in seen}]
    if missing:
        harvest.anomalies.append(Anomaly(
            kind="missing-amendment",
            detail=f"A1-A{EXPECTED} declared, not found: {', '.join(missing)}",
        ))
    return harvest


SPEC = ExtractorSpec(
    name=NAME,
    kinds=(NodeKind.AMENDMENT,),
    min_nodes=EXPECTED,
    max_nodes=EXPECTED,
    min_edges=3,
    max_unparsed=0,
    expect_rejected=None,
    run=extract,
)
