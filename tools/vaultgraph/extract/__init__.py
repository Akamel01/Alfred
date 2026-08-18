"""The one ordered registry. Adding an extractor means adding it here, with its floors.

`validate_registry` runs at import time, so a malformed registry is an import error rather
than a run that quietly produces a smaller graph.

Order is extraction order, and extraction order is claim order: `decisions` runs before
`amendments` so a decision id exists by the time an amendment points at it, and `references`
runs last because it mints nothing and only relates nodes the others already made.
"""

from __future__ import annotations

from typing import Final

from ..protocol import ExtractorSpec, validate_registry
from . import adrs, amendments, code, decisions, documents, references, workflows

EXTRACTORS: Final[tuple[ExtractorSpec, ...]] = (
    documents.SPEC,
    adrs.SPEC,
    decisions.SPEC,
    amendments.SPEC,
    code.SPEC,
    workflows.SPEC,
    # Last: it mints nothing and only relates what the others minted, so every endpoint it
    # names already exists by the time it runs.
    references.SPEC,
)

#: The registry has its own floor, for the same reason each extractor does: a registry that
#: lost every entry would otherwise report a clean run over an empty graph.
REGISTRY_FLOOR: Final = 7

validate_registry(EXTRACTORS, floor=REGISTRY_FLOOR)
