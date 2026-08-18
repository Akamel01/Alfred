"""K1-K6 and R1-R12, which live in Tier 0 and not, as the handoff assumed, in the plan.

The plan references kill criteria and risks constantly and defines neither. K1-K6 are table
rows in the charter; R1-R12 are `## Rn — title` headings in the risk register. Reading them
from the plan would have produced six and twelve empty shells.

The risk register is **not in numeric order** -- R12 sits between R10 and R11, because R12 was
added when the licensing question closed and appended where the argument put it rather than
where the numbering would. A parser that assumed ordering would have been right until it
wasn't; this one reads headings wherever they fall and reports gaps separately.
"""

from __future__ import annotations

import re

from ..mdscan import split_row
from ..model import Node, NodeKind, SourceRef
from ..protocol import Anomaly, Context, ExtractorSpec, Harvest, Unparsed
from ..textio import read_lines

NAME = "charter"
CHARTER = "docs/tier0/charter-and-non-goals.md"
RISKS = "docs/tier0/risk-register.md"
EXPECTED_KILLS = 6
EXPECTED_RISKS = 12

_KILL_ROW = re.compile(r"^\|\s*(K\d)\s*\|")
_RISK_HEADING = re.compile(r"^## (R\d{1,2})\s+—\s+(.+)$")
_FIRED = re.compile(r"\*\*(FIRED|DISCHARGED)[^*]*\*\*")


def _kill_criteria(ctx: Context, harvest: Harvest) -> int:
    path = ctx.root / CHARTER
    if not path.is_file():
        return 0
    harvest.scanned += 1
    count = 0
    for index, line in enumerate(read_lines(path)):
        match = _KILL_ROW.match(line)
        if not match:
            continue
        cells = split_row(line)
        src = SourceRef(CHARTER, index + 1)
        if len(cells) != 3:
            harvest.unparsed.append(Unparsed(
                NAME, src, line[:200], f"kill-criterion row split into {len(cells)} cells"
            ))
            continue
        fired = _FIRED.search(cells[1] + cells[2])
        harvest.nodes.append(Node(
            id=ctx.minter.mint(NodeKind.KILL_CRITERION, match.group(1), src),
            kind=NodeKind.KILL_CRITERION, title=cells[1][:200], source=src, shape="table-row",
            # A criterion that has fired and whose consequence has been executed is a
            # different state from one still waiting, and the board should show which.
            status="fired" if fired else "armed",
            body=cells[1],
            attrs={"consequence": cells[2], "number": match.group(1),
                   "event": fired.group(0).strip("*") if fired else ""},
            extractor=NAME,
        ))
        count += 1
    return count


def _risks(ctx: Context, harvest: Harvest) -> list[int]:
    path = ctx.root / RISKS
    if not path.is_file():
        return []
    harvest.scanned += 1
    numbers: list[int] = []
    for index, line in enumerate(read_lines(path)):
        match = _RISK_HEADING.match(line)
        if not match:
            continue
        risk_id, title = match.group(1), match.group(2).strip()
        src = SourceRef(RISKS, index + 1)
        accepted = "(accepted)" in title
        harvest.nodes.append(Node(
            id=ctx.minter.mint(NodeKind.RISK, risk_id, src),
            kind=NodeKind.RISK, title=title, source=src, shape="heading",
            status="accepted" if accepted else "open",
            attrs={"number": risk_id, "heading": title},
            extractor=NAME,
        ))
        numbers.append(int(risk_id[1:]))
    return numbers


def extract(ctx: Context) -> Harvest:
    harvest = Harvest()
    kills = _kill_criteria(ctx, harvest)
    numbers = _risks(ctx, harvest)

    if kills != EXPECTED_KILLS:
        harvest.anomalies.append(Anomaly(
            kind="kill-criterion-count",
            detail=f"{kills} kill criteria found in the charter, {EXPECTED_KILLS} expected",
        ))
    if numbers and numbers != sorted(numbers):
        harvest.anomalies.append(Anomaly(
            kind="risk-register-order",
            detail="the risk register is not in numeric order: "
                   + ", ".join(f"R{n}" for n in numbers),
        ))
    gaps = [n for n in range(1, (max(numbers) if numbers else 0) + 1) if n not in numbers]
    if gaps:
        harvest.anomalies.append(Anomaly(
            kind="risk-numbering-gap",
            detail="missing: " + ", ".join(f"R{n}" for n in gaps),
        ))
    return harvest


SPEC = ExtractorSpec(
    name=NAME,
    kinds=(NodeKind.KILL_CRITERION, NodeKind.RISK),
    min_nodes=EXPECTED_KILLS + EXPECTED_RISKS,
    max_nodes=None,
    min_edges=0,
    max_unparsed=0,
    expect_rejected=None,
    run=extract,
)
