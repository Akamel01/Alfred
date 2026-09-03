"""S0-S9 and O1-O9, and the dependency clauses that make them a DAG.

The stage headings carry their dependencies as free prose in an italic clause:
`### S4 — The two suites, together · *blocks Phase 0 exit; blocked by S1, S2, S3*`. One clause
mixes both directions, ranges use an en dash (`S1-S8`), and targets cross kinds -- a stage
blocks `Phase 0 exit` and is blocked `by O1`.

**The clause is matched against a closed vocabulary, and everything else is reported.** Prose
is the one input here that cannot be trusted to keep its shape, so the parser refuses rather
than guesses: a fragment matching none of the known patterns becomes an `Unparsed` carrying
the whole clause. Guessing would produce edges nobody could audit, and the `blocks` relation
is the one the vault exists to draw.

Direction is normalized to `blocks` at extraction with the original phrasing kept as evidence,
so `blocked by S1` and `blocks S4` do not become two different relations that a query has to
remember to union.

Targets that name something no extractor has minted -- `Phase 0 exit`, `Phase 1 dispatch` --
become `unresolved` nodes rather than dropped edges. The vault renders them as visibly empty
stubs, and the count falling as later extractors land is a measurable improvement rather than
a silent one.
"""

from __future__ import annotations

import re

from ..mdscan import expand_range, split_row, strip_strikethrough
from ..model import Confidence, Edge, EdgeKind, Node, NodeKind, SourceRef
from ..protocol import Anomaly, Context, ExtractorSpec, Harvest, Unparsed
from ..textio import read_lines, slug

NAME = "stages"
ORDER = "docs/tier2/execution-order.md"
EXPECTED_STAGES = 10
EXPECTED_OPERATOR_ITEMS = 9

_STAGE = re.compile(r"^### (S\d)\s+—\s+(.+)$")
#: `~{0,2}` admits the struck-through form: a discharged item is still a declared one, and the
#: count must see it. O5 is the instance — `| ~~O5~~ |` — struck through when ADR-0018 closed
#: it, which is also why the ADR's `Discharges: O5` must resolve rather than dangle.
_OPERATOR_ROW = re.compile(r"^\|\s*~{0,2}(O\d)~{0,2}\s*\|")
_CLAUSE = re.compile(r"\*([^*]+)\*")
#: `**DONE 2026-08-17**`, `**PROBES DONE ...**`, `**D-SYNTHETIC DONE ...**`. The marker may
#: begin with the word DONE itself, which an anchored `[A-Z]` prefix could not match.
_DONE = re.compile(r"\*\*([^*]*\bDONE\b[^*]*)\*\*")
_ID_TOKEN = re.compile(r"\b([SOKRD]\d{1,2}(?:\s*[–—−-]\s*[SOKRD]?\d{1,2})?)\b")
_PHASE_TOKEN = re.compile(r"\b(Phase\s+[\d.]+(?:\s+(?:exit|dispatch))?)", re.IGNORECASE)

#: The two directions the clause states, and nothing else. `after` is included because the
#: vocabulary is closed by choice: a phrasing not listed here must surface, not be absorbed.
_BLOCKS = re.compile(r"\bblocks\b", re.IGNORECASE)
_BLOCKED_BY = re.compile(r"\bblocked by\b", re.IGNORECASE)
_NOTHING = re.compile(r"\bblocks nothing\b", re.IGNORECASE)


def _targets(fragment: str) -> list[str]:
    found: list[str] = []
    for match in _ID_TOKEN.finditer(fragment):
        found.extend(expand_range(match.group(1)))
    for match in _PHASE_TOKEN.finditer(fragment):
        found.append(match.group(1).strip())
    return found


def extract(ctx: Context) -> Harvest:
    harvest = Harvest()
    path = ctx.root / ORDER
    if not path.is_file():
        return harvest
    lines = read_lines(path)
    harvest.scanned = 1

    stage_ids: dict[str, str] = {}
    operator_ids: dict[str, str] = {}
    pending: list[tuple[str, str, str, int]] = []   # (source stage, direction, target, line)

    for index, line in enumerate(lines):
        line_no = index + 1
        src = SourceRef(ORDER, line_no)

        stage = _STAGE.match(line)
        if stage:
            stage_id, rest = stage.group(1), stage.group(2)
            title = rest.split(" · ", 1)[0].strip()
            clause_match = _CLAUSE.search(rest)
            clause = clause_match.group(1).strip() if clause_match else ""
            done = _DONE.search(rest)
            node_id = ctx.minter.mint(NodeKind.STAGE, stage_id, src)
            stage_ids[stage_id] = node_id
            harvest.nodes.append(Node(
                id=node_id, kind=NodeKind.STAGE, title=title, source=src, shape="heading",
                status="done" if done and done.group(1).startswith("DONE") else
                       "partial" if done else "not-started",
                body=rest.strip(),
                attrs={"clause": clause, "completion": done.group(1) if done else "",
                       "number": stage_id},
                extractor=NAME,
            ))
            if not clause:
                harvest.unparsed.append(
                    Unparsed(NAME, src, rest[:200], "stage heading carries no dependency clause")
                )
                continue
            if _NOTHING.search(clause):
                continue
            # Split on the separators the clauses actually use, then classify each fragment by
            # the direction word it carries. A fragment with neither word is reported.
            # A clause states its direction once and then continues: `blocks S3, S4, S6, and
            # all of Phase 1`. A continuation fragment inherits the direction in force rather
            # than being read as directionless, which is what the list comma means.
            direction = ""
            for fragment in re.split(r";|(?<!\bblocked)\band\b(?!\s+by)", clause):
                fragment = fragment.strip()
                if not fragment:
                    continue
                if _BLOCKED_BY.search(fragment):
                    direction = "blocked_by"
                elif _BLOCKS.search(fragment):
                    direction = "blocks"
                elif not direction:
                    harvest.unparsed.append(Unparsed(
                        NAME, src, fragment[:200],
                        "dependency fragment opens a clause with no direction word",
                    ))
                    continue
                targets = _targets(fragment)
                if not targets:
                    # A real dependency stated only in prose -- "every verdict ever recorded"
                    # names nothing this graph holds. Reported rather than dropped, with a
                    # frozen budget: the residue is known, and it must not grow.
                    harvest.unparsed.append(Unparsed(
                        NAME, src, fragment[:200],
                        "dependency names no target this graph can resolve",
                    ))
                    continue
                for target in targets:
                    pending.append((stage_id, direction, target, line_no))
            continue

        operator = _OPERATOR_ROW.match(line)
        if operator:
            cells = split_row(line)
            if len(cells) != 4:
                harvest.unparsed.append(Unparsed(
                    NAME, src, line[:200], f"operator row split into {len(cells)} cells"
                ))
                continue
            item_id = operator.group(1)
            node_id = ctx.minter.mint(NodeKind.OPERATOR_ITEM, item_id, src)
            operator_ids[item_id] = node_id
            # A struck-through id is a discharged item: still declared (the count sees it),
            # no longer open. The withdrawal is the status, not the absence of a row.
            _, withdrawn = strip_strikethrough(cells[0])
            harvest.nodes.append(Node(
                id=node_id, kind=NodeKind.OPERATOR_ITEM, title=cells[1][:200], source=src,
                shape="table-row", body=cells[1],
                status="discharged" if withdrawn else "open",
                attrs={"blocks": cells[2], "due": cells[3].replace("**", ""),
                       "number": item_id},
                extractor=NAME,
            ))
            for target in _targets(cells[2]):
                pending.append((item_id, "blocks", target, line_no))

    # ---- Resolve targets, minting `unresolved` stubs for what nothing owns yet.
    known = {**stage_ids, **operator_ids}
    unresolved: dict[str, str] = {}

    def resolve(token: str, src: SourceRef) -> str:
        if token in known:
            return known[token]
        if token.startswith("D") and token[1:].isdigit():
            return f"{NodeKind.DECISION.value}:{token}"
        if token.startswith("K") and token[1:].isdigit():
            return f"{NodeKind.KILL_CRITERION.value}:{token}"
        if token.startswith("R") and token[1:].isdigit():
            return f"{NodeKind.RISK.value}:{token}"
        key = slug(token).replace(" ", "-").lower()
        if key not in unresolved:
            node_id = ctx.minter.mint(NodeKind.UNRESOLVED, key, src)
            unresolved[key] = node_id
            harvest.nodes.append(Node(
                id=node_id, kind=NodeKind.UNRESOLVED, title=token, source=src,
                shape="stub", attrs={"raw": token},
                tags=("unresolved",), extractor=NAME,
            ))
        return unresolved[key]

    for source_id, direction, token, line_no in pending:
        src = SourceRef(ORDER, line_no)
        target_id = resolve(token, src)
        origin = known.get(source_id, source_id)
        # Normalized to `blocks`: `blocked by X` is `X blocks this`, and a query should not
        # have to union two relations to ask one question.
        edge = (target_id, origin) if direction == "blocked_by" else (origin, target_id)
        harvest.edges.append(Edge(
            src=edge[0], dst=edge[1], kind=EdgeKind.BLOCKS, confidence=Confidence.PROSE,
            source=src, evidence=f"{source_id} {direction.replace('_', ' ')} {token}",
            extractor=NAME,
        ))

    for label, seen, expected in (
        ("stage", stage_ids, EXPECTED_STAGES),
        ("operator item", operator_ids, EXPECTED_OPERATOR_ITEMS),
    ):
        if len(seen) != expected:
            harvest.anomalies.append(Anomaly(
                kind=f"{label.replace(' ', '-')}-count",
                detail=f"{len(seen)} {label}s found, {expected} declared in the execution order",
            ))

    # ---- Stage pipeline cross-check (ADR-0041/0042): DONE ↔ output/exit.md
    stages_root = ctx.root / "stages"
    if stages_root.is_dir():
        harvest.scanned += 1
        # Map S-id → exit record presence
        exit_present: set[str] = set()
        for child in stages_root.iterdir():
            if not child.is_dir():
                continue
            # child is NN_sN_slug — extract sN
            sid = None
            for part in child.name.split("_"):
                if part.startswith("s") and part[1:].isdigit():
                    sid = f"S{part[1:]}"
                    break
                if part.startswith("S") and part[1:].isdigit():
                    sid = part
                    break
            if not sid:
                continue
            if (child / "output" / "exit.md").is_file():
                exit_present.add(sid)
            elif (child / "output" / "README.md").is_file():
                # In-progress marker — not a DONE evidence, but not an orphan either
                pass
        for sid, node_id in stage_ids.items():
            stage_node = next((n for n in harvest.nodes if n.id == node_id), None)
            if stage_node is None:
                continue
            is_doneish = stage_node.status in ("done", "partial")
            if is_doneish and sid not in exit_present:
                harvest.anomalies.append(Anomaly(
                    kind="stage-evidence-miss",
                    detail=f"{sid} is {stage_node.status} in {ORDER} but stages/*/output/exit.md is absent",
                    refs=(stage_node.source,),
                ))
            if not is_doneish and sid in exit_present:
                pass
    return harvest


SPEC = ExtractorSpec(
    name=NAME,
    kinds=(NodeKind.STAGE, NodeKind.OPERATOR_ITEM, NodeKind.UNRESOLVED),
    min_nodes=EXPECTED_STAGES + EXPECTED_OPERATOR_ITEMS,
    max_nodes=None,
    min_edges=20,
    # One dependency in the execution order names nothing this graph holds -- S3 "blocks S4,
    # and every verdict ever recorded". The residue is frozen at one rather than waved away:
    # a second unresolvable dependency appearing is something to look at.
    max_unparsed=1,
    expect_rejected=None,
    run=extract,
)
