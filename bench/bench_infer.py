"""Phase -1 local-model benchmark.

Measures the three things that decide Alfred's inference lane:

  1. prefill throughput at 8k / 32k / 64k prompt tokens  (the binding constraint)
  2. prefix-cache reuse across separate requests          (D45 tier 2)
  3. tool-calling reliability through the real serving stack (D40)

Every result carries the full serving fingerprint, because a measurement that
does not name its runtime describes nothing (D19/D40).

Usage:
    python3 bench/bench_infer.py --model openai/gpt-oss-120b
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
import uuid
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

BASE_URL = "http://127.0.0.1:1234/v1"
RESULTS_DIR = Path(__file__).parent / "results"

# Prompt filler. Deliberately code-shaped: Alfred's real context is source and
# specifications, not prose, and tokenizer behaviour differs sharply between them.
FILLER_UNIT = """
def compute_ttc(ego_state: State, obstacle_state: State, dt: float) -> float:
    \"\"\"Time to collision along the longitudinal axis.\"\"\"
    delta_s = obstacle_state.s - ego_state.s - obstacle_state.length
    delta_v = ego_state.velocity - obstacle_state.velocity
    if delta_v <= 0.0:
        return math.inf
    return delta_s / delta_v

"""


@dataclass
class Fingerprint:
    """D19/D40 fields obtainable without loading the weights ourselves."""

    model_id: str
    server: str
    server_version: str
    engine: str = "unknown"
    quantization: str = "unknown"
    arch: str = "unknown"
    context_length: int | None = None
    max_context_length: int | None = None
    selected_runtimes: list[str] = field(default_factory=list)
    captured_at: str = field(
        default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%S%z")
    )


def _post(path: str, payload: dict[str, Any], timeout: float = 1800.0) -> dict[str, Any]:
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def capture_fingerprint(model_id: str) -> Fingerprint:
    version = "unavailable"
    try:
        raw = subprocess.run(
            ["lms", "version"], capture_output=True, text=True, timeout=30
        ).stdout
        for line in raw.splitlines():
            if "commit" in line.lower():
                version = line.strip()
                break
    except (OSError, subprocess.SubprocessError):
        pass

    runtimes: list[str] = []
    try:
        raw = subprocess.run(
            ["lms", "runtime", "ls"], capture_output=True, text=True, timeout=30
        ).stdout
        # Selected engines are marked with a check; those are the ones that
        # actually served the request, so they belong in the fingerprint.
        runtimes = [ln.split()[0] for ln in raw.splitlines() if "✓" in ln]
    except (OSError, subprocess.SubprocessError, IndexError):
        pass

    fp = Fingerprint(
        model_id=model_id,
        server="lmstudio",
        server_version=version,
        selected_runtimes=runtimes,
    )

    # LM Studio's native endpoint reports the engine family and quantization
    # directly. The CLI does not, and guessing either would put a wrong value
    # into a fingerprint that autonomy grants are keyed on (D19/D40).
    try:
        req = urllib.request.Request(f"{BASE_URL.rsplit('/v1', 1)[0]}/api/v0/models")
        with urllib.request.urlopen(req, timeout=30) as resp:
            for entry in json.loads(resp.read()).get("data", []):
                if entry.get("id") == model_id:
                    fp.engine = entry.get("compatibility_type") or "unknown"
                    fp.quantization = entry.get("quantization") or "unknown"
                    fp.arch = entry.get("arch") or "unknown"
                    fp.context_length = entry.get("loaded_context_length")
                    fp.max_context_length = entry.get("max_context_length")
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, TypeError):
        pass

    return fp


def build_prompt(target_tokens: int, salt: str) -> str:
    """Roughly target_tokens of code-shaped filler, prefixed with a unique salt.

    The salt is load-bearing, not decoration. Prefix caches are hash-chained from
    the first token, so a measurement that reuses filler another measurement
    already sent is not measuring prefill at all — it is measuring a cache hit.
    The first version of this harness omitted the salt and reported a 15.6k-token
    "cold" prefill at 0.219 s against 12.621 s for the identical prompt minutes
    earlier. Every cold measurement gets its own salt.
    """
    # ~4 chars/token is the usual ballpark for code; overshoot and let the
    # server report the truth.
    repeats = max(1, (target_tokens * 4) // len(FILLER_UNIT))
    return f"# run-id {salt}\n" + FILLER_UNIT * repeats


def _salt() -> str:
    return uuid.uuid4().hex


def warmup(model_id: str) -> float:
    """First request after a load pays engine warmup. Charging that to the 8k
    measurement is how a fixed cost gets reported as a prefill rate."""
    started = time.perf_counter()
    try:
        _post(
            "/chat/completions",
            {
                "model": model_id,
                "messages": [{"role": "user", "content": "Reply with the digit 1."}],
                "max_tokens": 1,
                "temperature": 0.0,
            },
            timeout=600.0,
        )
    except (urllib.error.URLError, TimeoutError):
        return -1.0
    return round(time.perf_counter() - started, 3)


def measure_prefill(model_id: str, target_tokens: int) -> dict[str, Any]:
    """One request, one generated token. Wall-clock is therefore prefill-dominated."""
    prompt = build_prompt(target_tokens, _salt())
    started = time.perf_counter()
    try:
        resp = _post(
            "/chat/completions",
            {
                "model": model_id,
                "messages": [
                    {"role": "user", "content": prompt + "\n\nReply with the digit 1."}
                ],
                "max_tokens": 1,
                "temperature": 0.0,
                "stream": False,
            },
        )
    except (urllib.error.URLError, TimeoutError) as exc:
        return {"target_tokens": target_tokens, "error": repr(exc)}
    elapsed = time.perf_counter() - started

    usage = resp.get("usage", {})
    prompt_tokens = usage.get("prompt_tokens")
    return {
        "target_tokens": target_tokens,
        "prompt_tokens": prompt_tokens,
        "wall_clock_s": round(elapsed, 3),
        "prefill_tok_per_s": (
            round(prompt_tokens / elapsed, 1) if prompt_tokens and elapsed else None
        ),
    }


def measure_prefix_reuse(model_id: str, target_tokens: int = 16000) -> dict[str, Any]:
    """Same prefix twice. If the serving stack reuses KV across separate
    requests, the second call is dramatically cheaper. If it does not, D45's
    tier-2 win is unavailable on this lane and that decides the stack."""
    prompt = build_prompt(target_tokens, _salt())
    timings: list[float] = []
    prompt_tokens = None

    for suffix in ("Reply with the digit 1.", "Reply with the digit 2."):
        started = time.perf_counter()
        try:
            resp = _post(
                "/chat/completions",
                {
                    "model": model_id,
                    "messages": [{"role": "user", "content": f"{prompt}\n\n{suffix}"}],
                    "max_tokens": 1,
                    "temperature": 0.0,
                    "stream": False,
                },
            )
        except (urllib.error.URLError, TimeoutError) as exc:
            return {"error": repr(exc)}
        timings.append(time.perf_counter() - started)
        prompt_tokens = resp.get("usage", {}).get("prompt_tokens", prompt_tokens)

    cold, warm = timings
    return {
        "prompt_tokens": prompt_tokens,
        "cold_s": round(cold, 3),
        "warm_s": round(warm, 3),
        "speedup": round(cold / warm, 2) if warm else None,
        # A speedup near 1.0 means no cross-request reuse. Anything above ~1.5
        # is real reuse, not noise.
        "reuse_detected": bool(warm and cold / warm > 1.5),
    }


TOOL_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "record_metric_value",
            "description": "Record a computed surrogate safety metric value.",
            "parameters": {
                "type": "object",
                "properties": {
                    "metric": {
                        "type": "string",
                        "enum": ["TTC", "THW", "PET", "DRAC"],
                    },
                    "scenario_id": {"type": "string"},
                    "value": {"type": "number"},
                    "units": {"type": "string", "enum": ["s", "m", "m/s^2"]},
                },
                "required": ["metric", "scenario_id", "value", "units"],
            },
        },
    }
]

TOOL_PROMPTS = [
    "Record a TTC of 2.4 seconds for scenario ZAM_Urban-3_3_Repair.",
    "Record a PET of 3.2 seconds for scenario ZAM_Tjunction-1_97_T-1.",
    "Record a THW of 2.4 seconds for scenario BEL_Putte-8_2_T-1.",
    "Record a TTC of 1.25 seconds for scenario DEU_Test-1_1_T-1.",
    "For scenario ZAM_Zip-2_1_T-1 the time headway measured 2.4 s. Record it.",
]


def measure_tool_calling(model_id: str, trials: int = 4) -> dict[str, Any]:
    """Reliability, not capability. A schema-capable model still emits invalid
    JSON through a bad serving layer (D40) — that is what this catches."""
    attempts = 0
    well_formed = 0
    schema_valid = 0
    failures: list[str] = []

    for trial in range(trials):
        for prompt in TOOL_PROMPTS:
            attempts += 1
            try:
                resp = _post(
                    "/chat/completions",
                    {
                        "model": model_id,
                        "messages": [{"role": "user", "content": prompt}],
                        "tools": TOOL_SCHEMA,
                        "tool_choice": "auto",
                        "temperature": 0.0 if trial == 0 else 0.7,
                        "max_tokens": 256,
                    },
                    timeout=300.0,
                )
            except (urllib.error.URLError, TimeoutError) as exc:
                failures.append(f"transport: {exc!r}")
                continue

            calls = (resp.get("choices") or [{}])[0].get("message", {}).get(
                "tool_calls"
            )
            if not calls:
                failures.append(f"no tool_call: {prompt[:40]}")
                continue

            raw = calls[0].get("function", {}).get("arguments", "")
            try:
                args = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                failures.append(f"invalid JSON: {raw[:120]}")
                continue
            well_formed += 1

            required = {"metric", "scenario_id", "value", "units"}
            if required.issubset(args) and isinstance(args.get("value"), (int, float)):
                schema_valid += 1
            else:
                failures.append(f"schema miss: {args}")

    return {
        "attempts": attempts,
        "well_formed_json": well_formed,
        "schema_valid": schema_valid,
        "well_formed_rate": round(well_formed / attempts, 4) if attempts else None,
        "schema_valid_rate": round(schema_valid / attempts, 4) if attempts else None,
        "failures": failures[:20],
    }


# Sections a full run produces. A run that skips one must not be allowed to
# erase it from a previous run's file — that already happened once: a
# --skip-prefill run replaced a complete result set, taking the whole prefill
# curve with it.
ALL_SECTIONS = ("prefill", "prefix_reuse", "tool_calling")

# Fingerprint fields that must agree before two runs may be merged into one
# file. Merging sections measured under different serving configurations would
# manufacture a result that no single configuration ever produced.
FINGERPRINT_KEYS = ("model_id", "engine", "quantization", "arch", "context_length")


class ResultsConflict(RuntimeError):
    pass


def _sections_present(report: dict[str, Any]) -> set[str]:
    return {s for s in ALL_SECTIONS if report.get(s) is not None}


def _fingerprints_compatible(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return all(a.get(k) == b.get(k) for k in FINGERPRINT_KEYS)


def persist(report: dict[str, Any], slug: str, results_dir: Path,
            force: bool = False) -> tuple[Path, Path, dict[str, Any]]:
    """Write this run immutably, then update the canonical file non-destructively.

    Two files come out of every run:

      * ``<slug>-<captured_at>.json`` — this run exactly as measured. Never
        overwritten, because the timestamp is part of the name. Whatever else
        goes wrong, the raw run survives.
      * ``<slug>.json`` — the canonical current picture. A run that measured
        fewer sections than the file already holds does not replace it; the
        missing sections are carried forward from the previous file and tagged
        with where they came from, so no reader can mistake a carried section
        for a fresh measurement.

    Carrying forward is only sound when the two runs describe the same serving
    configuration. If they do not, this refuses to touch the canonical file
    rather than silently splicing a 28k-context tool score onto a 262k-context
    prefill curve. ``force`` overrides, and records that it did.
    """
    results_dir.mkdir(parents=True, exist_ok=True)
    new_sections = _sections_present(report)
    report["sections_measured"] = sorted(new_sections)

    stamp = str(report["fingerprint"].get("captured_at", "")).replace(":", "")
    versioned = results_dir / f"{slug}-{stamp or 'run'}.json"
    n = 1
    while versioned.exists():
        n += 1
        versioned = results_dir / f"{slug}-{stamp or 'run'}-{n}.json"
    versioned.write_text(json.dumps(report, indent=2))

    canonical = results_dir / f"{slug}.json"
    merged = dict(report)
    notes: dict[str, Any] = {"versioned_run": versioned.name}

    if canonical.exists():
        try:
            prev = json.loads(canonical.read_text())
        except json.JSONDecodeError:
            prev = {}
        lost = _sections_present(prev) - new_sections
        if lost:
            compatible = _fingerprints_compatible(
                prev.get("fingerprint", {}), report.get("fingerprint", {})
            )
            if not compatible and not force:
                raise ResultsConflict(
                    f"{canonical.name} holds sections {sorted(lost)} this run did not "
                    f"measure, under a different serving configuration "
                    f"({ {k: prev.get('fingerprint', {}).get(k) for k in FINGERPRINT_KEYS} } "
                    f"vs { {k: report['fingerprint'].get(k) for k in FINGERPRINT_KEYS} }). "
                    f"Refusing to overwrite. This run is safe in {versioned.name}. "
                    f"Re-run without --skip-* to produce a complete set, or pass "
                    f"--force-overwrite to discard the older sections."
                )
            for section in lost:
                merged[section] = prev[section]
            notes["carried_forward"] = {
                "sections": sorted(lost),
                "from_run": prev.get("fingerprint", {}).get("captured_at"),
                "from_versioned": prev.get("results_provenance", {}).get("versioned_run"),
                "fingerprint_compatible": compatible,
                "forced_across_incompatible_fingerprint": bool(force and not compatible),
            }
            merged["sections_measured"] = sorted(new_sections)

    merged["results_provenance"] = notes
    canonical.write_text(json.dumps(merged, indent=2))
    return versioned, canonical, notes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument(
        "--prefill-sizes",
        default="8000,32000,64000",
        help="comma-separated target prompt token counts",
    )
    parser.add_argument("--tool-trials", type=int, default=4)
    parser.add_argument("--skip-prefill", action="store_true")
    parser.add_argument(
        "--expect-context",
        type=int,
        default=None,
        help="fail if the loaded context differs; the stack silently JIT-reloads "
             "idle models at defaultContextLength, which has already produced a "
             "bogus 0/10 tool score",
    )
    parser.add_argument(
        "--force-overwrite",
        action="store_true",
        help="allow this run to discard sections held by an existing results file",
    )
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    fingerprint = capture_fingerprint(args.model)
    print(f"fingerprint: {json.dumps(asdict(fingerprint))}\n")

    if args.expect_context and fingerprint.context_length != args.expect_context:
        raise SystemExit(
            f"loaded context is {fingerprint.context_length}, expected "
            f"{args.expect_context} — the lane reconfigured itself; reload before "
            f"benchmarking"
        )

    report: dict[str, Any] = {"fingerprint": asdict(fingerprint)}

    print("warmup ...", flush=True)
    report["warmup_s"] = warmup(args.model)
    print(f"  {report['warmup_s']} s", flush=True)

    if not args.skip_prefill:
        report["prefill"] = []
        for size in [int(s) for s in args.prefill_sizes.split(",")]:
            print(f"prefill @ ~{size} tokens ...", flush=True)
            result = measure_prefill(args.model, size)
            print(f"  {json.dumps(result)}", flush=True)
            report["prefill"].append(result)

    print("\nprefix reuse @ ~16k tokens ...", flush=True)
    report["prefix_reuse"] = measure_prefix_reuse(args.model)
    print(f"  {json.dumps(report['prefix_reuse'])}", flush=True)

    print(f"\ntool calling ({args.tool_trials} trials x {len(TOOL_PROMPTS)}) ...", flush=True)
    report["tool_calling"] = measure_tool_calling(args.model, args.tool_trials)
    tc = report["tool_calling"]
    print(
        f"  well-formed {tc['well_formed_json']}/{tc['attempts']}  "
        f"schema-valid {tc['schema_valid']}/{tc['attempts']}",
        flush=True,
    )

    slug = args.model.replace("/", "_")
    try:
        versioned, canonical, notes = persist(
            report, slug, RESULTS_DIR, force=args.force_overwrite
        )
    except ResultsConflict as exc:
        raise SystemExit(f"\nRESULTS CONFLICT — canonical file untouched.\n{exc}")
    print(f"\nwrote {versioned}")
    print(f"wrote {canonical}")
    if "carried_forward" in notes:
        print(f"  carried forward from the previous run: "
              f"{notes['carried_forward']['sections']}")


if __name__ == "__main__":
    main()
