"""The questions put to the oracle, and where each one came from.

Every point here was transcribed from CriMe's own test source at the pinned SHA —
`tests/test_time_domain.py` — and carries the line it came from. Nothing here is an
Alfred-authored value: the *value* is whatever the oracle returns, and the literal
recorded beside it is the oracle's own pinned assertion, used as a check on the
transcription rather than as the answer.

D49 settles why selecting the point is not authoring the answer: "Alfred selects the
input; CriMe produces the value. Selecting which question to ask an oracle is not
authoring the oracle's answer."

---------------------------------------------------------- what the literal is FOR

A transcription error here — wrong ego id, wrong scenario, wrong argument — produces a
number that does not match the pinned literal, and the extractor fails on it. That is the
entire reason each point carries `expected`: **the point set is a hypothesis and the
pinned literal is its control.** Without it a mistyped ego id yields a plausible number
for the wrong question, which is then loaded into `heldout` as ground truth and every
verdict computed against it is wrong in a way nothing downstream can see.

------------------------------------------------------- two labels the plan has wrong

Read from the source, not inferred. `tests/test_time_domain.py::test_ttc` computes 2.4
with **`TTCStar`**, not `TTC`; and the value 1.25 that the plan records as `ttc_4` is
returned by **`TTR`** on `ZAM_Urban-7_1_S-2`, in a test whose local variable is named
`ttc_4` after the pattern of the lines above it. The Phase 0 exit criterion quotes both as
TTC values. Reproducing "TTC = 1.25" would be reproducing a different measure and calling
it a success. `bench/tasks/phase1_tasks.json` has both right; the prose does not.

------------------------------------------------------------------- NaN is not a value

`tests/test_base.py::test_nan_evaluation` pins TTC to `NaN` at one time step. NaN is
banned as an output everywhere in Alfred (edge-case specification, totality rule), so the
extractor maps it to the `undefined` arm with a reason and never to a number. It is
recorded as a point precisely because it is the case most likely to be silently coerced.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final, Literal

ValueKind = Literal["defined", "infinite", "undefined"]


@dataclass(frozen=True)
class Expected:
    """The oracle's own pinned assertion for a point. A check, never the answer."""

    kind: ValueKind
    value: float | None = None
    infinite_sign: int | None = None
    reason: str | None = None


@dataclass(frozen=True)
class Point:
    """One question, fully self-describing.

    Self-describing rather than replaying the test's mutation order: each point rebuilds
    its configuration from the scenario named here. Where a test genuinely mutates state
    before computing — removing the static obstacles, widening the steering search — the
    mutation is named in `mutations` rather than inherited from a preceding assertion, so
    that running one point in isolation gives the same number as running all of them.
    """

    point_id: str
    measure: str
    scenario_id: str
    ego_id: int
    expected: Expected
    tolerance: float
    source_line: int
    # Positional and keyword arguments to `compute`.
    args: tuple[int, ...] = ()
    kwargs: dict[str, int] = field(default_factory=dict)
    # Dotted configuration overrides applied before `update()`, e.g. `time.steer_width`.
    config_overrides: dict[str, int | float | bool] = field(default_factory=dict)
    # Named, implemented in extract.py. Only what the source actually does.
    mutations: tuple[str, ...] = ()


def _finite(v: float) -> Expected:
    return Expected(kind="defined", value=v)


_POS_INF: Final = Expected(kind="infinite", infinite_sign=1)
_NEG_INF: Final = Expected(kind="infinite", infinite_sign=-1)

# The base scenario of `TestTimeDomain.setUp` — ZAM_Urban-3_3_Repair, ego 8.
_BASE: Final = "ZAM_Urban-3_3_Repair"
_BASE_EGO: Final = 8

# abs_tol used by the source's own assertion. Where the source uses assertEqual rather
# than isclose the oracle is claiming exactness; 1e-9 records that as a number without
# pretending the comparison is bit-exact across a rebuild.
_ISCLOSE: Final = 1e-2
_EXACT: Final = 1e-9

POINTS: Final[tuple[Point, ...]] = (
    # ---- TET / TIT, exposure and integral of time-to-collision -------------------
    Point("tet-obs6", "TET", _BASE, _BASE_EGO, _finite(2.0), _ISCLOSE, 50, args=(6,)),
    Point("tet-obs7", "TET", _BASE, _BASE_EGO, _finite(0.9), _ISCLOSE, 54, args=(7,)),
    Point("tit-obs6", "TIT", _BASE, _BASE_EGO, _finite(2.012), _ISCLOSE, 62, args=(6,)),
    Point("tit-obs7", "TIT", _BASE, _BASE_EGO, _finite(1.40), _ISCLOSE, 66, args=(7,)),
    # ---- TTC*, and note the class is TTCStar --------------------------------------
    Point("ttcstar-base", "TTCStar", _BASE, _BASE_EGO, _finite(2.4), _ISCLOSE, 74),
    Point(
        "ttcstar-no-static",
        "TTCStar",
        _BASE,
        _BASE_EGO,
        _POS_INF,
        _ISCLOSE,
        81,
        mutations=("remove_static_obstacles",),
    ),
    # 9 * dt on a set-based-prediction scenario. dt is 0.25 there, so 2.25 — but the
    # source states it relationally, and a relational point whose base is the same
    # computation is D49's "too loose" case. Recorded, and tiered P2 rather than P1.
    Point("ttcstar-setbased", "TTCStar", "ZAM_Urban-7_1_S-2", 100, _finite(2.25), _ISCLOSE, 90),
    # ---- TTB / TTK / TTS, the time-to-manoeuvre family ----------------------------
    Point("ttb-base", "TTB", _BASE, _BASE_EGO, _finite(2.0), _EXACT, 97),
    # TTK and TTS assert -inf only. A stub returning -inf passes; they are in the
    # enumeration's `weak` tier and are extracted anyway, because a degenerate value
    # that the oracle stops producing is a change worth detecting.
    Point("ttk-base", "TTK", _BASE, _BASE_EGO, _NEG_INF, _EXACT, 104),
    Point("tts-base", "TTS", _BASE, _BASE_EGO, _NEG_INF, _EXACT, 109),
    # ---- TTR, under two steering widths, plus the set-based scenario --------------
    Point(
        "ttr-steer2",
        "TTR",
        _BASE,
        _BASE_EGO,
        _finite(2.0),
        _EXACT,
        120,
        config_overrides={"time.steer_width": 2},
    ),
    Point(
        "ttr-steer1",
        "TTR",
        _BASE,
        _BASE_EGO,
        _finite(2.0),
        _EXACT,
        131,
        config_overrides={"time.steer_width": 1},
    ),
    # The plan records this as `ttc_4`. It is TTR.
    Point("ttr-setbased", "TTR", "ZAM_Urban-7_1_S-2", 100, _finite(1.25), _ISCLOSE, 142),
    # ---- THW, WTTC, WTTR -----------------------------------------------------------
    Point("thw-obs6-t0", "THW", _BASE, _BASE_EGO, _finite(2.4), _EXACT, 147, args=(6, 0)),
    Point("thw-obs7-t0", "THW", _BASE, _BASE_EGO, _POS_INF, _EXACT, 157, args=(7, 0)),
    Point("wttc-obs6-t0", "WTTC", _BASE, _BASE_EGO, _finite(1.3), _EXACT, 164, args=(6, 0)),
    Point(
        "wttr-t10",
        "WTTR",
        _BASE,
        _BASE_EGO,
        _finite(1.3),
        _EXACT,
        174,
        args=(10,),
        kwargs={"verbose": False},
    ),
    # ---- TTZ, on the crosswalk scenario ------------------------------------------
    Point("ttz-ego1", "TTZ", "ZAM_Zip-2_1_T-1", 1, _finite(1.05), _EXACT, 183, args=(0,)),
    # ---- TTCE ----------------------------------------------------------------------
    Point("ttce-obs6", "TTCE", _BASE, _BASE_EGO, _finite(2.4), _ISCLOSE, 190, args=(6,)),
    Point("ttce-obs7", "TTCE", _BASE, _BASE_EGO, _finite(2.4), _ISCLOSE, 195, args=(7,)),
    # ---- ET, encroachment time, across three scenarios ----------------------------
    Point("et-tjunction-obs5", "ET", "ZAM_Tjunction-1_97_T-1", 1, _finite(1.1), _ISCLOSE, 205, args=(5,)),
    Point("et-putte-obs328", "ET", "BEL_Putte-8_2_T-1", 349, _finite(1.5), _ISCLOSE, 215, args=(328,)),
    Point("et-putte-obs356", "ET", "BEL_Putte-8_2_T-1", 349, _POS_INF, _EXACT, 225, args=(356,)),
    Point("et-test-obs7", "ET", "DEU_Test-1_1_T-1", 6, _POS_INF, _EXACT, 235, args=(7,)),
    # ---- PET, post-encroachment time ----------------------------------------------
    Point("pet-tjunction-obs1", "PET", "ZAM_Tjunction-1_97_T-1", 5, _finite(3.2), _ISCLOSE, 245, args=(1,)),
    Point("pet-putte-obs328", "PET", "BEL_Putte-8_2_T-1", 349, _POS_INF, _EXACT, 255, args=(328,)),
    Point("pet-putte-obs356", "PET", "BEL_Putte-8_2_T-1", 349, _POS_INF, _EXACT, 265, args=(356,)),
    Point("pet-test-obs7", "PET", "DEU_Test-1_1_T-1", 6, _POS_INF, _EXACT, 275, args=(7,)),
)

# Vacuity floor. The extractor refuses to report success below this, because a point set
# that silently shrank to nothing is indistinguishable from one that all passed.
MINIMUM_POINTS: Final = 25

# The six scenarios Phase 0's exit criterion names. Asserted as a subset of what the point
# set actually reaches, so that "Phase 0's scenarios are covered" is a check rather than a
# claim someone made once.
PHASE0_SCENARIOS: Final = frozenset(
    {
        "ZAM_Urban-3_3_Repair",
        "ZAM_Urban-7_1_S-2",
        "ZAM_Zip-2_1_T-1",
        "ZAM_Tjunction-1_97_T-1",
        "BEL_Putte-8_2_T-1",
        "DEU_Test-1_1_T-1",
    }
)


def scenarios_covered() -> frozenset[str]:
    return frozenset(p.scenario_id for p in POINTS)
