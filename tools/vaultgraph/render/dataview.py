"""Dataview boards. Queries, not materialized tables.

A materialized table would be a second copy of the graph inside the vault, stale the moment
the graph changed and diffing on every rebuild. A query is computed by Obsidian from the
frontmatter the notes already carry, so there is exactly one representation of each fact.

`confidence` is queryable, which is the point of carrying it as data: "show me every stage
dependency nobody has verified" is one filter rather than a reading exercise.
"""

from __future__ import annotations

from ..model import Edge, Node, NodeKind
from .html import LOCAL_SURFACE
from .note import BANNER

VAULT = "vault"

REFRESH = f"""## Refresh

This vault is derived. Nothing here is authored, and a hand edit fails
`python3 tools/gen_vault.py --check`, so the way to change a note is to change what it was
read from and rebuild.

```
python3 tools/serve_vault.py
```

Then open <{LOCAL_SURFACE}> and press **Regenerate from repository**. One press re-syncs the
plan mirror, re-reads the repository, and rewrites `vault/`, `graph.json` and
`docs-graph.html` together, so the three never disagree about what the repository says.

The button is a link rather than a button because a note is markdown and markdown does not
run. It is on the served page, where code can run and where the working tree is reachable."""


def _page(title: str, intro: str, blocks: list[tuple[str, str]], *, refresh: bool = False) -> str:
    lines = [
        "---", "kind: index", f'title: "{title}"', "generated: true", "---", "",
        f"# {title}", "", BANNER, "", intro, "",
    ]
    for heading, query in blocks:
        lines.append(f"## {heading}")
        lines.append("")
        lines.append("```dataview")
        lines.append(query.strip())
        lines.append("```")
        lines.append("")
    if refresh:
        lines.append(REFRESH)
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def boards(nodes: list[Node], edges: list[Edge]) -> dict[str, str]:
    counts: dict[str, int] = {}
    for node in nodes:
        counts[node.kind.value] = counts.get(node.kind.value, 0) + 1

    overview = _page(
        "Alfred knowledge graph",
        f"{len(nodes)} nodes, {len(edges)} edges, generated from the repository. "
        "Every note is derived; nothing is authored here.",
        [
            ("Everything, by kind", """
TABLE length(rows) AS Notes
FROM "vault"
WHERE generated AND kind
GROUP BY kind
SORT length(rows) DESC
"""),
        ],
        refresh=True,
    )

    documents = _page(
        "Documents by status and enforcement",
        "The register's 63 documents. `enforcement` names a gate; whether that gate exists is "
        "answerable from the gate notes, which is the point of holding both in one graph.",
        [
            ("Status × enforcement", """
TABLE status, owner, enforcement, written, review_after
FROM "vault/documents"
WHERE kind = "document"
SORT enforcement ASC, status ASC, title ASC
"""),
            ("Stubs still waiting on evidence", """
TABLE tier, review_after
FROM "vault/documents"
WHERE kind = "document" AND written = "stub"
SORT tier ASC
"""),
            ("Claiming a CI gate", """
TABLE tier, owner
FROM "vault/documents"
WHERE kind = "document" AND enforcement = "ci-gate"
SORT tier ASC
"""),
        ],
    )

    open_items = _page(
        "Open items board",
        "What is not done, and who owns it. Operator items are non-delegable by definition; "
        "four of them block stages.",
        [
            ("Stages not finished", """
TABLE status, completion, clause
FROM "vault/execution"
WHERE kind = "stage" AND status != "done"
SORT number ASC
"""),
            ("Operator-owned, non-delegable", """
TABLE due, blocks
FROM "vault/execution"
WHERE kind = "operator-item"
SORT due ASC
"""),
            ("Kill criteria", """
TABLE status, consequence
FROM "vault/charter"
WHERE kind = "kill-criterion"
SORT number ASC
"""),
            ("Risks not accepted", """
TABLE status
FROM "vault/charter"
WHERE kind = "risk" AND status != "accepted"
SORT number ASC
"""),
            ("Targets nothing has defined yet", """
TABLE source
FROM "vault/execution"
WHERE kind = "unresolved"
"""),
        ],
    )

    code = _page(
        "Code and gates",
        "What the product tree's lint and type gates actually reach is narrower than the tree. "
        "`lint_gated` records it rather than letting the graph imply otherwise.",
        [
            ("Modules outside ruff and pyright", """
TABLE tree, protected
FROM "vault/code"
WHERE kind = "module" AND lint_gated = "false" AND present = "true"
SORT tree ASC, title ASC
"""),
            ("D20-protected — inspector machinery", """
TABLE tree
FROM "vault/code"
WHERE contains(tags, "protected")
SORT title ASC
"""),
            ("Declared and absent", """
TABLE source
FROM "vault/code"
WHERE present = "false"
"""),
            ("Gate steps, in order", """
TABLE job, ordinal, kind
FROM "vault/gates"
WHERE kind = "gate-step"
SORT job ASC, ordinal ASC
"""),
        ],
    )

    return {
        f"{VAULT}/Overview.md": overview,
        f"{VAULT}/Documents by status.md": documents,
        f"{VAULT}/Open items.md": open_items,
        f"{VAULT}/Code and gates.md": code,
    }
