"""The gates: five jobs and every step they run, read out of `.github/workflows/gates.yml`.

Parsed by hand rather than with a YAML library, for the reason `scripts/lint_docs.py:42-44`
gives about its own frontmatter parser: a dependency here would make the tool that reads the
gates depend on the supply chain the gates are supposed to govern. `harness/db/grants_declared.py`
takes the same position on `grants.yaml` and is the precedent.

The parser is deliberately narrow and **fails closed**: it recognizes exactly the indentation
shapes this file uses, and anything under `jobs:` it cannot classify is reported as unparsed
rather than skipped. `gates.yml` is D20-protected, so it does not drift casually -- but a
parser that silently ignored a step it did not understand would report a complete gate set
while missing the gate that mattered.

The file's own header says it best: if a check a document names is not in this file, that
document's enforcement value is a wish. Making the step set queryable is what lets the vault
answer whether a given `enforcement: ci-gate` is real.
"""

from __future__ import annotations

import re

from ..model import Confidence, Edge, EdgeKind, Node, NodeKind, SourceRef, module_id
from ..protocol import Context, ExtractorSpec, Harvest, Unparsed
from ..textio import read_lines

NAME = "workflows"
WORKFLOW = ".github/workflows/gates.yml"

#: Path-shaped tokens inside a step's command, restricted to the trees `code` mints nodes for.
#: Anchored on a tree name rather than on "anything with a slash": a step's command also
#: carries flags, shell fragments and URLs, and a looser pattern would mint edges out of
#: `--frozen` and `actions/checkout@v4`.
_COMMAND_PATH = re.compile(
    r"\b((?:harness|src|tools|scripts|bench|tests|migrations|policy)/[A-Za-z0-9_./-]*)"
)

_JOBS_HEADER = re.compile(r"^jobs:\s*$")
_JOB = re.compile(r"^  ([A-Za-z][\w-]*):\s*$")
_JOB_NAME = re.compile(r'^    name:\s*(.+?)\s*$')
_NEEDS = re.compile(r"^    needs:\s*(.+?)\s*$")
_STEP_NAME = re.compile(r"^      - name:\s*(.+?)\s*$")
_RUN_INLINE = re.compile(r"^        run:\s*(?!\|)(.+?)\s*$")
_RUN_BLOCK = re.compile(r"^        run:\s*\|\s*$")
_USES = re.compile(r"^        uses:\s*(.+?)\s*$")


def _unquote(text: str) -> str:
    return text.strip().strip('"').strip("'")


def _run_targets(ctx: Context, command: str) -> list[str]:
    """Module ids a step's command names, in a stable order and each named once.

    Resolution is by asking the minter, not by re-deriving which paths `code` mints. A token
    that names nothing -- `migrations/roles/` is a directory in a flat tree, `harness/acs/vectors.json`
    is data -- is dropped rather than reported: `gates.yml` legitimately names paths that are
    not modules, and reporting those as unparsed would spend a zero budget on the file working
    as intended. What the graph must not do is invent an endpoint, and it does not.
    """
    found: list[str] = []
    for token in _COMMAND_PATH.findall(command):
        candidate = module_id(token.rstrip("/"))
        if ctx.minter.knows(candidate) and candidate not in found:
            found.append(candidate)
    return sorted(found)


def extract(ctx: Context) -> Harvest:
    harvest = Harvest()
    path = ctx.root / WORKFLOW
    if not path.is_file():
        return harvest

    lines = read_lines(path)
    harvest.scanned = 1

    in_jobs = False
    job_id: str | None = None
    job_index = 0
    step_index = 0
    pending: dict[str, str] | None = None
    block_run: list[str] = []
    #: Whether the scan is still inside a `run: |` block. Kept separate from `block_run`:
    #: leaving the block must stop the appending without discarding what was collected. The
    #: comment line separating two jobs used to null the list before the step closed, which
    #: silently emptied the ACS-1 byte-identity step's command.
    in_block = False

    def close_step() -> None:
        nonlocal pending, block_run, step_index, in_block
        if pending is None or job_id is None:
            pending, block_run, in_block = None, [], False
            return
        command = pending.get("run") or "\n".join(block_run).strip() or pending.get("uses", "")
        step_index += 1
        src = SourceRef(WORKFLOW, int(pending["line"]))
        step_id = ctx.minter.mint(NodeKind.GATE_STEP, f"{job_id}.{step_index:02d}", src)
        harvest.nodes.append(Node(
            id=step_id, kind=NodeKind.GATE_STEP, title=pending["name"], source=src, shape="step",
            body=command,
            attrs={"job": job_id, "command": command, "ordinal": str(step_index),
                   "kind": "action" if pending.get("uses") else "run"},
            tags=("protected",), extractor=NAME,
        ))
        harvest.edges.append(Edge(
            src=f"{NodeKind.GATE.value}:{job_id}", dst=step_id, kind=EdgeKind.CONTAINS,
            confidence=Confidence.STRUCTURAL, source=src, evidence=pending["name"],
            extractor=NAME,
        ))
        # What this step actually executes. Before this, all 36 gate steps were dead ends whose
        # only relation was the job containing them, and the register could say a decision was
        # enforced in a module without being able to say anything ran that module.
        for target in _run_targets(ctx, command):
            harvest.edges.append(Edge(
                src=step_id, dst=target, kind=EdgeKind.RUNS,
                confidence=Confidence.STRUCTURAL, source=src,
                evidence=command.strip()[:180], extractor=NAME,
            ))
        pending, block_run, in_block = None, [], False

    needs_edges: list[tuple[str, str, int]] = []

    for index, line in enumerate(lines):
        line_no = index + 1
        if not in_jobs:
            in_jobs = bool(_JOBS_HEADER.match(line))
            continue

        job_match = _JOB.match(line)
        if job_match:
            close_step()
            job_id = job_match.group(1)
            job_index += 1
            step_index = 0
            src = SourceRef(WORKFLOW, line_no)
            ctx.minter.mint(NodeKind.GATE, job_id, src)
            harvest.nodes.append(Node(
                id=f"{NodeKind.GATE.value}:{job_id}", kind=NodeKind.GATE, title=job_id,
                source=src, shape="job", attrs={"job": job_id, "ordinal": str(job_index)},
                tags=("protected",), extractor=NAME,
            ))
            continue

        if job_id is None:
            continue

        name_match = _JOB_NAME.match(line)
        if name_match and pending is None:
            for node in harvest.nodes:
                if node.kind is NodeKind.GATE and node.attrs["job"] == job_id:
                    harvest.nodes[harvest.nodes.index(node)] = Node(
                        id=node.id, kind=node.kind, title=_unquote(name_match.group(1)),
                        source=node.source, shape=node.shape, attrs=node.attrs,
                        tags=node.tags, extractor=NAME,
                    )
            continue

        needs_match = _NEEDS.match(line)
        if needs_match:
            for target in re.findall(r"[\w-]+", needs_match.group(1)):
                needs_edges.append((job_id, target, line_no))
            continue

        step_match = _STEP_NAME.match(line)
        if step_match:
            close_step()
            pending = {"name": _unquote(step_match.group(1)), "line": str(line_no)}
            continue

        if pending is None:
            continue

        if _RUN_BLOCK.match(line):
            block_run, in_block = [], True
            continue
        run_match = _RUN_INLINE.match(line)
        if run_match:
            pending["run"] = run_match.group(1)
            continue
        uses_match = _USES.match(line)
        if uses_match:
            pending["uses"] = uses_match.group(1)
            continue
        if in_block:
            if line.startswith("          ") or not line.strip():
                block_run.append(line.strip())
            else:
                in_block = False

    close_step()

    known = {n.id for n in harvest.nodes}
    for source_job, target_job, line_no in needs_edges:
        target_id = f"{NodeKind.GATE.value}:{target_job}"
        if target_id not in known:
            harvest.unparsed.append(Unparsed(
                NAME, SourceRef(WORKFLOW, line_no), target_job, "needs: names an unknown job"
            ))
            continue
        harvest.edges.append(Edge(
            src=f"{NodeKind.GATE.value}:{source_job}", dst=target_id, kind=EdgeKind.NEEDS,
            confidence=Confidence.STRUCTURAL, source=SourceRef(WORKFLOW, line_no),
            evidence=f"needs: {target_job}", extractor=NAME,
        ))
    return harvest


SPEC = ExtractorSpec(
    name=NAME,
    kinds=(NodeKind.GATE, NodeKind.GATE_STEP),
    # 5 jobs and the steps under them. A minimum: the operator adds gates, and a new one must
    # not red the build. The ceiling that matters here is the unparsed budget, which is zero.
    min_nodes=30,
    max_nodes=None,
    # 36 `contains` + 4 `needs` + the `runs` edges. Raised from 28 when `runs` landed, so that
    # a command parser which stopped matching reds the build instead of quietly returning a
    # graph where nothing executes anything -- the aggregate floor is the only floor this
    # contract has, so it has to be tight enough for the newest edge kind to be missed.
    min_edges=50,
    max_unparsed=0,
    expect_rejected=None,
    run=extract,
)
