"""Regression + negative control for the results-file overwrite defect.

The defect: `bench_infer.py` wrote its results file unconditionally, so a
`--skip-prefill` run replaced a complete result set with a partial one and the
whole prefill curve was gone with no warning.

Every test here carries its own negative control: before asserting that the
guard saves the data, it asserts that the *unguarded* write — the code as it
was — destroys it. A test that only exercises the fix cannot tell a working
guard from a test that never reproduced the bug.

    python3 bench/test_results_integrity.py     # or: python3 -m pytest bench/ -q
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bench_infer import ResultsConflict, persist  # noqa: E402

FP_262K = {
    "model_id": "m", "engine": "mlx", "quantization": "4bit", "arch": "a",
    "context_length": 262144, "captured_at": "2026-08-14T10:00:00-0700",
}
FP_262K_LATER = dict(FP_262K, captured_at="2026-08-14T11:00:00-0700")
FP_28K = dict(FP_262K, context_length=28672,
              captured_at="2026-08-14T12:00:00-0700")

COMPLETE = {
    "fingerprint": FP_262K,
    "prefill": [{"target_tokens": 64000, "prefill_tok_per_s": 820.5}],
    "prefix_reuse": {"speedup": 79.4},
    "tool_calling": {"schema_valid_rate": 1.0},
}


def _partial(fp: dict) -> dict:
    """What a --skip-prefill run produces: no prefill section at all."""
    return {
        "fingerprint": fp,
        "prefix_reuse": {"speedup": 1.0},
        "tool_calling": {"schema_valid_rate": 1.0},
    }


def _fresh_dir() -> Path:
    return Path(tempfile.mkdtemp(prefix="benchresults-"))


def test_negative_control_unguarded_write_destroys_prefill() -> None:
    """The bug reproduces under the original write path. If this ever fails,
    the other tests prove nothing — they would be guarding a bug that the
    fixture no longer creates."""
    d = _fresh_dir()
    canonical = d / "m.json"
    canonical.write_text(json.dumps(COMPLETE))
    # The original code, verbatim in behaviour: one unconditional write.
    canonical.write_text(json.dumps(_partial(FP_262K_LATER)))
    assert "prefill" not in json.loads(canonical.read_text()), (
        "negative control failed: the unguarded write did not destroy prefill, "
        "so this fixture does not reproduce the defect")


def test_partial_run_cannot_erase_prefill() -> None:
    d = _fresh_dir()
    persist(dict(COMPLETE), "m", d)
    persist(_partial(FP_262K_LATER), "m", d)

    got = json.loads((d / "m.json").read_text())
    assert got["prefill"] == COMPLETE["prefill"], "prefill was lost"
    # The partial run's own numbers still win where it measured them.
    assert got["prefix_reuse"]["speedup"] == 1.0
    # And the carried section is labelled, so nobody reads it as fresh.
    assert got["results_provenance"]["carried_forward"]["sections"] == ["prefill"]
    assert got["sections_measured"] == ["prefix_reuse", "tool_calling"]


def test_every_run_leaves_an_immutable_copy() -> None:
    d = _fresh_dir()
    v1, _, _ = persist(dict(COMPLETE), "m", d)
    v2, _, _ = persist(_partial(FP_262K_LATER), "m", d)
    assert v1 != v2
    assert "prefill" in json.loads(v1.read_text()), (
        "the versioned copy of the complete run was mutated")
    assert "prefill" not in json.loads(v2.read_text()), (
        "the versioned copy must record what that run actually measured")


def test_same_timestamp_does_not_collide() -> None:
    d = _fresh_dir()
    v1, _, _ = persist(dict(COMPLETE), "m", d)
    v2, _, _ = persist(dict(COMPLETE), "m", d)
    assert v1 != v2 and v1.exists() and v2.exists()


def test_refuses_to_splice_across_serving_configurations() -> None:
    """A 28k-context partial run must not inherit a 262k-context prefill curve;
    that would fabricate a configuration that was never measured."""
    d = _fresh_dir()
    persist(dict(COMPLETE), "m", d)
    try:
        persist(_partial(FP_28K), "m", d)
    except ResultsConflict:
        pass
    else:  # pragma: no cover
        raise AssertionError("expected ResultsConflict across context lengths")

    got = json.loads((d / "m.json").read_text())
    assert got["prefill"] == COMPLETE["prefill"]
    assert got["prefix_reuse"]["speedup"] == 79.4, "canonical file was modified"
    # The refused run is not lost — it is on disk under its own name.
    assert any(p.name.startswith("m-2026-08-14T12") for p in d.iterdir())


def test_force_overwrite_is_recorded_not_silent() -> None:
    d = _fresh_dir()
    persist(dict(COMPLETE), "m", d)
    _, canonical, notes = persist(_partial(FP_28K), "m", d, force=True)
    got = json.loads(canonical.read_text())
    cf = got["results_provenance"]["carried_forward"]
    assert cf["forced_across_incompatible_fingerprint"] is True
    assert cf["fingerprint_compatible"] is False
    assert notes["carried_forward"]["sections"] == ["prefill"]


def test_superset_run_replaces_cleanly() -> None:
    d = _fresh_dir()
    persist(_partial(FP_262K), "m", d)
    _, canonical, notes = persist(dict(COMPLETE), "m", d)
    got = json.loads(canonical.read_text())
    assert "carried_forward" not in notes, "a complete run should carry nothing"
    assert got["prefix_reuse"]["speedup"] == 79.4
    assert got["sections_measured"] == ["prefill", "prefix_reuse", "tool_calling"]


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except AssertionError as exc:
                failures += 1
                print(f"FAIL {name}: {exc}")
    print(f"\n{failures} failure(s)")
    sys.exit(1 if failures else 0)
