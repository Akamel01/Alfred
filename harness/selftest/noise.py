"""Measures ε. It is never chosen, and this is the module that makes that true.

The seeded-defect ladder has one rung that constrains τ's *calibration* — the rung just
outside tolerance. Placing it requires knowing how finely the criterion can resolve
anything at all, and that is an empirical property of the criterion, not a preference.

------------------------------------------------------------ what the noise floor IS here

The spread of values that **equally correct** implementations produce. Summation is
order-dependent in floating point, so two honest solutions that add the same numbers in
different orders disagree by a real amount. Below that spread the criterion cannot tell a
correct implementation from another correct implementation, so it certainly cannot tell
one from a defect.

A tolerance inside the noise floor therefore fails correct work at a rate set by luck, and
`tau_resolves_epsilon` returning False is a finding about τ — not an instruction to widen
it silently, which is why the caller is handed the fact rather than a corrected number.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Final

from harness.selftest.synthetic import SYNTHETIC_INPUT, naive_sum, reference_value

DEFAULT_SAMPLES: Final = 64


@dataclass(frozen=True)
class NoiseFloor:
    spread: float
    samples: int
    reference: float
    max_abs_error: float

    def epsilon_for(self, tolerance: float) -> float:
        """ε as a fraction of τ. Measured, then divided — never picked."""
        return self.spread / tolerance

    def tau_resolves_epsilon(self, tolerance: float) -> bool:
        return tolerance > self.spread


def measure_noise_floor(*, samples: int = DEFAULT_SAMPLES, seed: int = 20260818) -> NoiseFloor:
    """Permute the summation order and watch the answer move.

    Seeded, so the number is reproducible; a noise measurement that differs per run cannot
    be compared against the one that calibrated the tolerance in force.
    """
    if samples < 2:
        # One sample has no spread and would report a noise floor of zero, which reads as
        # "this criterion is perfectly precise" — the most flattering possible wrong answer.
        raise ValueError("a noise floor needs at least two samples")

    rng = random.Random(seed)
    exact = reference_value()
    values: list[float] = []
    for _ in range(samples):
        shuffled = list(SYNTHETIC_INPUT)
        rng.shuffle(shuffled)
        values.append(naive_sum(tuple(shuffled)))

    return NoiseFloor(
        spread=max(values) - min(values),
        samples=samples,
        reference=exact,
        max_abs_error=max(abs(v - exact) for v in values),
    )
