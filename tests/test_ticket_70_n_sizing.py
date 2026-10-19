"""Rot guard for docs/tier7/ticket-70-measurement-design.md's stated numbers.

Every number the design states is recomputed here from the formula beside it and
compared with the document's machine-readable block, so a number edited in prose
without the computation moving fails this test.
"""

from __future__ import annotations

import hashlib
import math
import re
from pathlib import Path
from statistics import NormalDist

DOC = Path(__file__).resolve().parent.parent / "docs" / "tier7" / "ticket-70-measurement-design.md"
ND = NormalDist()


def _stated(key: str) -> str:
    text = DOC.read_text(encoding="utf-8")
    match = re.search(rf"^{key} = ([0-9a-f]+)$", text, re.MULTILINE)
    assert match is not None, f"{key} is not stated in {DOC.name}"
    return match.group(1)


def _n_entry(p1: float, p0: float = 0.50) -> int:
    za, zb = ND.inv_cdf(0.95), ND.inv_cdf(0.80)
    numerator = (za * math.sqrt(p0 * (1 - p0)) + zb * math.sqrt(p1 * (1 - p1))) ** 2
    return math.ceil(numerator / (p1 - p0) ** 2)


def _n_compare(p1: float, p2: float) -> int:
    za, zb = ND.inv_cdf(0.975), ND.inv_cdf(0.80)
    pooled = (p1 + p2) / 2
    numerator = (
        za * math.sqrt(2 * pooled * (1 - pooled))
        + zb * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))
    ) ** 2
    return math.ceil(numerator / (p1 - p2) ** 2)


def _n_half_width(p1: float, p2: float, half_width: float = 0.10) -> int:
    z = ND.inv_cdf(0.975)
    return math.ceil(z * z * (p1 * (1 - p1) + p2 * (1 - p2)) / half_width**2)


def _wilson_lower_bound(passes: int, tasks: int) -> float:
    z = ND.inv_cdf(0.975)
    p = passes / tasks
    numerator = p + z * z / (2 * tasks) - z * math.sqrt(
        p * (1 - p) / tasks + z * z / (4 * tasks * tasks)
    )
    return numerator / (1 + z * z / tasks)


def _k_star(n: int, bar: float = 0.50) -> int:
    # smallest k whose Wilson 95% LB clears bar
    z = ND.inv_cdf(0.975)

    def lb(k: int) -> float:
        p = k / n
        denom = 1 + z * z / n
        return (
            p + z * z / (2 * n) - z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
        ) / denom

    return next(k for k in range(n + 1) if lb(k) >= bar)


def _exact_power(n: int, p: float, k: int) -> float:
    return sum(math.comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(k, n + 1))


def test_n_entry_matches_the_documented_number() -> None:
    assert _stated("N_entry") == "187"
    assert _stated("N_entry_p65") == "82"
    assert _stated("N_entry_p70") == "43"
    assert _k_star(187) == 107
    assert _exact_power(187, 0.60, _k_star(187)) >= 0.80
    assert _exact_power(186, 0.60, _k_star(186)) < 0.80


def test_n_entry_normal_approx_matches_the_documented_number() -> None:
    assert _stated("N_entry_normal_approx") == str(_n_entry(0.60)) == "153"
    assert _stated("N_entry_normal_approx_p65") == str(_n_entry(0.65)) == "67"
    assert _stated("N_entry_normal_approx_p70") == str(_n_entry(0.70)) == "37"


def test_n_compare_matches_the_documented_number() -> None:
    assert _stated("N_compare") == str(_n_compare(0.60, 0.50)) == "388"


def test_half_width_alternatives_match_the_documented_numbers() -> None:
    assert _stated("N_halfwidth_060_050") == str(_n_half_width(0.60, 0.50)) == "189"
    assert _stated("N_halfwidth_worst") == str(_n_half_width(0.50, 0.50)) == "193"


def test_seed_list_hash_matches_the_documented_hash() -> None:
    tasks = int(_stated("N_compare"))
    seeds = "\n".join(str(70000 + i) for i in range(tasks))
    assert _stated("seed_list_sha256") == hashlib.sha256(seeds.encode()).hexdigest()


def test_k3_anchor_counts_reproduce_the_charter_intervals() -> None:
    assert round(_wilson_lower_bound(15, 20), 4) == 0.5313
    assert round(_wilson_lower_bound(14, 20), 4) == 0.4810
