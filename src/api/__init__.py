"""The deployable unit. Deliberately almost empty.

S8 asks whether deploy and rollback execute and are *verified*. That is a question about
the mechanism, not about what the service does, so this surface carries the two endpoints
the mechanism needs and no domain at all. Metric endpoints are agent work and arrive
behind this, not inside it.
"""

from src.api.app import app, build_identity

__all__ = ["app", "build_identity"]
