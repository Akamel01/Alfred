"""The deterministic replay harness. The port is here; the implementation is domain work.

`ReplayHarness` fixes what determinism means for a reproduced number: same inputs, same
bytes, checked by content hash rather than asserted in prose.
"""

from replay.port import ReplayHarness, ReplayResult

__all__ = ["ReplayHarness", "ReplayResult"]
