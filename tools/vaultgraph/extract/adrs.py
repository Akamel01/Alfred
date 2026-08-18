"""ADR-0001 to ADR-0014, and the relations stated on each entry's metadata line.

The log is append-only in one file, and each entry opens with a heading followed by a single
line of `**Key:** value` fields joined by ` · `. `scripts/gen_reading_map.py:163-176` already
reads the heading and the status; nothing has ever read the rest, which is where
`Supersedes`, `Amends`, `Amended by`, `See also` and `Forward pointers` live. Those five are
the closest thing this corpus has to typed edges written by hand.

The field vocabulary is not uniform and the parser does not pretend otherwise: one entry
spells its status lowercase, one carries `Date: TBD`, and one uses `Forward pointers` where
the others use `See also`. Each is handled by name, and a key outside the observed vocabulary
is reported rather than ignored -- an append-only log gains new entries by design, and a new
field spelling should surface the first time it appears rather than the first time somebody
notices an edge is missing.
"""

from __future__ import annotations

import re

from ..model import Confidence, Edge, EdgeKind, Node, NodeKind, SourceRef
from ..protocol import Anomaly, Context, ExtractorSpec, Harvest, Unparsed
from ..textio import read_lines

NAME = "adrs"
LOG = "docs/tier1/adr-log.md"
EXPECTED = 14

_HEADING = re.compile(r"^## (ADR-\d{4}) — (.+)$")
_FIELD = re.compile(r"\*\*([A-Za-z ]+):\*\*\s*([^·]*)")
_ADR_REF = re.compile(r"ADR-\d{4}")

#: Field name -> the edge it states. `Date` and `Status` are attributes, not edges.
RELATIONS = {
    "Supersedes": EdgeKind.SUPERSEDES,
    "Amends": EdgeKind.AMENDS,
    "Amended by": EdgeKind.AMENDED_BY,
    "See also": EdgeKind.SEE_ALSO,
    "Forward pointers": EdgeKind.SEE_ALSO,
}
ATTRIBUTES = ("Date", "Status")


def extract(ctx: Context) -> Harvest:
    harvest = Harvest()
    path = ctx.root / LOG
    if not path.is_file():
        return harvest
    lines = read_lines(path)
    harvest.scanned = 1

    entries: list[tuple[str, str, int, str]] = []
    for index, line in enumerate(lines):
        heading = _HEADING.match(line)
        if not heading:
            continue
        # The metadata line is the first non-blank line after the heading.
        meta = ""
        for candidate in lines[index + 1: index + 5]:
            if candidate.strip():
                meta = candidate.strip()
                break
        entries.append((heading.group(1), heading.group(2).strip(), index + 1, meta))

    minted: dict[str, str] = {}
    for adr_id, title, line_no, meta in entries:
        src = SourceRef(LOG, line_no)
        node_id = ctx.minter.mint(NodeKind.ADR, adr_id, src)
        minted[adr_id] = node_id
        fields = {key.strip(): value.strip() for key, value in _FIELD.findall(meta)}
        attrs = {
            "date": fields.get("Date", ""),
            # One entry spells it `accepted`; normalized here, raw kept beside it.
            "status": fields.get("Status", "").lower(),
            "status_raw": fields.get("Status", ""),
        }
        harvest.nodes.append(Node(
            id=node_id, kind=NodeKind.ADR, title=title, source=src, shape="heading",
            status=attrs["status"], body=meta, attrs=attrs, extractor=NAME,
        ))
        for key in fields:
            if key not in RELATIONS and key not in ATTRIBUTES:
                harvest.unparsed.append(Unparsed(
                    NAME, src, key, "metadata field outside the observed vocabulary"
                ))

    for adr_id, _title, line_no, meta in entries:
        fields = {key.strip(): value.strip() for key, value in _FIELD.findall(meta)}
        for key, edge_kind in RELATIONS.items():
            value = fields.get(key, "")
            if not value or value.lower().startswith("none"):
                continue
            for target in _ADR_REF.findall(value):
                if target not in minted or target == adr_id:
                    continue
                harvest.edges.append(Edge(
                    src=minted[adr_id], dst=minted[target], kind=edge_kind,
                    confidence=Confidence.STRUCTURAL, source=SourceRef(LOG, line_no),
                    evidence=f"**{key}:** {value}"[:200], extractor=NAME,
                ))

    numbers = sorted(int(a[0][4:]) for a in entries)
    gaps = [n for n in range(1, (numbers[-1] if numbers else 0) + 1) if n not in numbers]
    if gaps:
        harvest.anomalies.append(Anomaly(
            kind="adr-numbering-gap",
            detail="the log is append-only and numbers are never reused; missing: "
                   + ", ".join(f"ADR-{n:04d}" for n in gaps),
        ))
    return harvest


SPEC = ExtractorSpec(
    name=NAME,
    kinds=(NodeKind.ADR,),
    # A minimum, not exact: the log is append-only and a fifteenth ADR must not red the build.
    min_nodes=EXPECTED,
    max_nodes=None,
    min_edges=4,
    max_unparsed=0,
    expect_rejected=None,
    run=extract,
)
