"""The one ordered registry. Adding an extractor means adding it here, with its floors.

`validate_registry` runs at import time, so a malformed registry is an import error rather
than a run that quietly produces a smaller graph.

Order is extraction order, and extraction order is claim order: `decisions` runs before
`amendments` so a decision id exists by the time an amendment points at it.
"""

from __future__ import annotations

from typing import Final

from ..protocol import ExtractorSpec, validate_registry
from . import amendments, decisions, documents

EXTRACTORS: Final[tuple[ExtractorSpec, ...]] = (
    documents.SPEC,
    decisions.SPEC,
    amendments.SPEC,
)

#: The registry has its own floor, for the same reason each extractor does: a registry that
#: lost every entry would otherwise report a clean run over an empty graph.
REGISTRY_FLOOR: Final = 3

validate_registry(EXTRACTORS, floor=REGISTRY_FLOOR)
