"""Base model and the invariants every persisted record carries.

Cross-stage invariants I1 (tenancy on every table), I4 (typed sortable IDs),
I6 (schema version on state, criteria and artifacts) and I10 (causality) are
enforced here rather than per model, so a new record type inherits them instead
of remembering them.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any, ClassVar, cast
from uuid import UUID

import numpy as np
import numpy.typing as npt
from pydantic import BaseModel, ConfigDict, Field, field_validator

__all__ = ["AlfredModel", "Tenanted", "utc_now"]


def utc_now() -> datetime:
    """Timezone-aware UTC. A naive datetime in a hashed record is ambiguous bytes."""
    return datetime.now(tz=UTC)


class AlfredModel(BaseModel):
    """Frozen, extra-forbidding, ndarray-tolerant base.

    `extra="forbid"` matters more than it looks: a boundary model that silently
    absorbs an unrecognized field is how a renamed key becomes a missing value
    with a plausible default rather than an error.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        arbitrary_types_allowed=True,
        validate_assignment=True,
        validate_default=True,
    )

    def __eq__(self, other: object) -> bool:
        """Field-wise equality that understands arrays.

        Pydantic's generated `__eq__` compares `__dict__`s, and comparing two
        dicts holding ndarrays raises `ValueError: truth value ... is ambiguous`.
        An equality operator that raises is worse than one that is merely slow.
        """
        if other.__class__ is not self.__class__:
            return NotImplemented
        mine: Mapping[str, Any] = self.__dict__
        theirs: Mapping[str, Any] = other.__dict__
        if mine.keys() != theirs.keys():
            return False
        for key, value in mine.items():
            found = theirs[key]
            if isinstance(value, np.ndarray) or isinstance(found, np.ndarray):
                if not np.array_equal(
                    np.asarray(cast("npt.ArrayLike", value)),
                    np.asarray(cast("npt.ArrayLike", found)),
                ):
                    return False
            elif value != found:
                return False
        return True


class Tenanted(AlfredModel):
    """Tenancy scope and schema version, carried even with a single tenant.

    Retrofitting multi-tenancy is a full migration plus a rewrite of every query
    and every access check — the single most expensive omission available (I1).
    """

    SCHEMA_VERSION: ClassVar[int] = 1

    org_id: UUID
    project_id: UUID
    schema_version: int = Field(default=1, ge=1)
    created_at: datetime = Field(default_factory=utc_now)
    caused_by: UUID | None = Field(
        default=None,
        description="The record that caused this one (I10). None only for a root cause.",
    )

    @field_validator("created_at")
    @classmethod
    def _require_tz(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        return value.astimezone(UTC)
