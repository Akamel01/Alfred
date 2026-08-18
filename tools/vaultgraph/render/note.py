"""One node, one note. Frontmatter mirroring the repo's own contract, and a source pointer.

Two properties every note carries, and the vault's admissibility rests on both.

**A "generated -- do not edit" banner and a `source` pointer resolving to a real file:line.**
The vault is a read model under D44/D47/D51: legible to agents, authored by nobody. A hand
edit that survived a regeneration would make some fact exist only here, and a fact that exists
only in the vault is an unfingerprinted write path into agent context. `--check` is what makes
the banner true rather than merely stated.

**Prose-derived edges are rendered under their own heading, with the clause that produced
them.** A relation parsed from a table column and one guessed from a dependency clause are
not the same claim. Putting them in one list would let the second borrow the first's
authority, so they sit apart and the prose ones show their evidence inline for review.

`aliases` carry both the id and the title, so `[[D49]]` and `[[Provenance tiers]]` resolve to
the same note.
"""

from __future__ import annotations

from ..model import Confidence, Edge, Node, NodeKind

BANNER = (
    "> [!warning] Generated — do not edit\n"
    "> This note is emitted by `tools/gen_vault.py` from the repository. "
    "Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit."
)

#: Attributes rendered as frontmatter rather than in the body. Everything else becomes a
#: `## Fields` row, so a new attribute appears in the note instead of vanishing.
FRONTMATTER_ATTRS = (
    "status", "owner", "enforcement", "tier", "phase", "due", "number", "present",
    "protected", "lint_gated", "written", "review_after", "job", "date",
)

_ESCAPE = str.maketrans({"[": "(", "]": ")", "|": "\\|"})


def _scalar(value: str) -> str:
    """Frontmatter values are quoted flat strings. The repo's own parser has no list support
    and neither does this -- matching `scripts/lint_docs.py:41-63` rather than inventing a
    richer format the tooling around it could not read."""
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def filename(node: Node) -> str:
    return node.id.replace(":", "__").replace("/", "__").replace(".", "_") + ".md"


def link(node: Node) -> str:
    return f"[[{filename(node).removesuffix('.md')}|{node.title.translate(_ESCAPE)[:90]}]]"


def render(node: Node, outgoing: list[tuple[Edge, Node]], incoming: list[tuple[Edge, Node]]) -> str:
    lines: list[str] = ["---"]
    lines.append(f"kind: {node.kind.value}")
    lines.append(f"id: {_scalar(node.id)}")
    lines.append(f"title: {_scalar(node.title)}")
    if node.status:
        lines.append(f"status: {_scalar(node.status)}")
    if node.shape:
        lines.append(f"shape: {_scalar(node.shape)}")
    for key in FRONTMATTER_ATTRS:
        if key in node.attrs and node.attrs[key] and key != "status":
            lines.append(f"{key}: {_scalar(node.attrs[key])}")
    lines.append(f"source: {_scalar(str(node.source))}")
    lines.append(f"extractor: {_scalar(node.extractor)}")
    if node.tags:
        lines.append("tags: [" + ", ".join(sorted(t for t in node.tags if t)) + "]")
    lines.append("aliases:")
    for alias in sorted({node.id.split(":", 1)[1], node.title[:90]}):
        lines.append(f"  - {_scalar(alias)}")
    lines.append("generated: true")
    lines.append("---")
    lines.append("")
    lines.append(f"# {node.title}")
    lines.append("")
    lines.append(BANNER)
    lines.append("")
    lines.append(f"**Source** · `{node.source}`")
    lines.append("")

    if node.body:
        lines.append("## Statement")
        lines.append("")
        lines.append(node.body.strip())
        lines.append("")

    falsifies = node.attrs.get("falsifies_if", "")
    if falsifies:
        lines.append("## Falsifies if")
        lines.append("")
        lines.append(f"> {falsifies}")
        lines.append("")

    extra = sorted(
        (key, value) for key, value in node.attrs.items()
        if value and key not in FRONTMATTER_ATTRS and key not in ("falsifies_if",)
    )
    if extra:
        lines.append("## Fields")
        lines.append("")
        lines.append("| Field | Value |")
        lines.append("|---|---|")
        for key, value in extra:
            lines.append(f"| `{key}` | {value.translate(_ESCAPE)[:400]} |")
        lines.append("")

    if node.occurrences:
        lines.append("## Restated at")
        lines.append("")
        for ref in node.occurrences:
            lines.append(f"- `{ref}`")
        lines.append("")

    _relations(lines, "Binds", outgoing, incoming, Confidence.STRUCTURAL)
    _relations(lines, "Enforced by (code)", outgoing, incoming, Confidence.DERIVED)
    _relations(lines, "Stated in prose — unverified", outgoing, incoming, Confidence.PROSE)
    return "\n".join(lines).rstrip("\n") + "\n"


def _relations(
    lines: list[str],
    heading: str,
    outgoing: list[tuple[Edge, Node]],
    incoming: list[tuple[Edge, Node]],
    confidence: Confidence,
) -> None:
    out = [(e, n) for e, n in outgoing if e.confidence is confidence]
    inc = [(e, n) for e, n in incoming if e.confidence is confidence]
    if not out and not inc:
        return
    lines.append(f"## {heading}")
    lines.append("")
    for edge, other in out:
        suffix = f" — {edge.evidence[:120]}" if confidence is not Confidence.STRUCTURAL else ""
        lines.append(f"- **{edge.kind.value}** → {link(other)}{suffix}")
    for edge, other in inc:
        suffix = f" — {edge.evidence[:120]}" if confidence is not Confidence.STRUCTURAL else ""
        lines.append(f"- {link(other)} **{edge.kind.value}** → this{suffix}")
    lines.append("")


__all__ = ["BANNER", "filename", "link", "render"]
