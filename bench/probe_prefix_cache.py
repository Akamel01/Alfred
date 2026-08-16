"""Prefix-cache discriminator — why 79.4x at 28672 and 1.0x at 262144?

`bench_infer.py` measures prefix reuse with exactly two requests, so every
explanation for a 1.0x result fits it equally well. This probe sends a
*sequence* of requests whose timing pattern differs between the explanations,
so a single run rules some of them out.

Candidate explanations and the signature each produces in `--repeats N` of one
identical prefix (t1..tN), followed by a different-salt prompt (tX) and then
the original prefix again (tR):

  H1 cache disabled/too small at this context
        t1..tN all cold.
  H2 slot round-robin: P parallel slots, each with its own cache, requests
     dispatched round-robin
        t1..tP cold, then t(P+1).. warm — a cold *run* of exactly P, not 1.
  H3 single-entry cache, works normally
        t1 cold, t2..tN warm, tX cold, tR cold (evicted by tX).
  H4 multi-entry cache
        t1 cold, t2..tN warm, tX cold, tR warm.

The different-salt prompt tX is also the negative control: it is the same size
and shape as the cached one and MUST come out cold. If tX is warm the timing
signal is not measuring prefix reuse at all and no other number here means
anything.

    python3 bench/probe_prefix_cache.py --model qwen3-next-80b-a3b-instruct \
        --expect-context 262144 --repeats 6
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

BASE = "http://127.0.0.1:1234"
RESULTS = Path(__file__).resolve().parent / "results"

FILLER_UNIT = """
def compute_ttc(ego_state: State, obstacle_state: State, dt: float) -> float:
    \"\"\"Time to collision along the longitudinal axis.\"\"\"
    delta_s = obstacle_state.s - ego_state.s - obstacle_state.length
    delta_v = ego_state.velocity - obstacle_state.velocity
    if delta_v <= 0.0:
        return math.inf
    return delta_s / delta_v

"""


def build_prompt(target_tokens: int, salt: str) -> str:
    repeats = max(1, (target_tokens * 4) // len(FILLER_UNIT))
    return f"# run-id {salt}\n" + FILLER_UNIT * repeats


def fingerprint(model: str) -> dict[str, Any]:
    with urllib.request.urlopen(f"{BASE}/api/v0/models", timeout=30) as r:
        data = json.loads(r.read())
    for m in data.get("data", []):
        if m["id"] == model and m.get("state") == "loaded":
            return {
                "model_id": m["id"],
                "engine": m.get("compatibility_type"),
                "quantization": m.get("quantization"),
                "arch": m.get("arch"),
                "loaded_context_length": m.get("loaded_context_length"),
                "max_context_length": m.get("max_context_length"),
            }
    raise SystemExit(f"model '{model}' is not loaded — load it before probing")


def ask(model: str, prompt: str, suffix: str, timeout: float) -> dict[str, Any]:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": f"{prompt}\n\n{suffix}"}],
        "max_tokens": 1,
        "temperature": 0.0,
        "stream": False,
    }
    req = urllib.request.Request(
        f"{BASE}/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read())
    except (urllib.error.URLError, TimeoutError) as exc:
        return {"error": repr(exc), "wall_s": round(time.perf_counter() - started, 3)}
    elapsed = time.perf_counter() - started
    return {
        "wall_s": round(elapsed, 3),
        "prompt_tokens": body.get("usage", {}).get("prompt_tokens"),
    }


def classify(rows: list[dict[str, Any]], parallel_hint: int | None) -> dict[str, Any]:
    """Turn the timing sequence into a verdict, or refuse to.

    'Warm' is defined relative to the slowest observed request rather than an
    absolute threshold, because prefill time scales with context and machine.
    A cache hit on this stack is ~2 orders of magnitude faster than a miss, so
    any cut in the middle of that gap separates them; 0.25x of the cold time is
    deliberately generous to the "no reuse" conclusion.
    """
    times = [r["wall_s"] for r in rows if "error" not in r]
    if not times:
        return {"verdict": "no data"}
    cold_ref = max(times)
    warm = [t < 0.25 * cold_ref for t in times]
    cold_run = 0
    for w in warm:
        if w:
            break
        cold_run += 1
    return {
        "cold_reference_s": round(cold_ref, 3),
        "warm_threshold_s": round(0.25 * cold_ref, 3),
        "warm_flags": warm,
        "leading_cold_run": cold_run,
        "any_reuse": any(warm),
        "parallel_hint": parallel_hint,
    }


def capacity_probe(model: str, tokens: int, k: int, timeout: float) -> dict[str, Any]:
    """How many *distinct* prefixes stay warm at once.

    Primes k distinct prefixes in order, then revisits them in the same order.
    A single-entry cache leaves only the last-primed prefix warm; an N-entry
    cache leaves the last N warm. This is the number that decides whether one
    serving lane can back several concurrently-running agents, each with its
    own system prefix, or only one.
    """
    prompts = [build_prompt(tokens, uuid.uuid4().hex) for _ in range(k)]
    prime = []
    for i, p in enumerate(prompts):
        row = ask(model, p, f"Reply with the digit {i % 9 + 1}.", timeout)
        row["step"] = f"P{i}"
        prime.append(row)
        print(f"  prime P{i}: {json.dumps(row)}", flush=True)
    revisit = []
    for i, p in enumerate(prompts):
        row = ask(model, p, f"Reply with the digit {(i + 3) % 9 + 1}.", timeout)
        row["step"] = f"R{i}"
        revisit.append(row)
        print(f"  revisit R{i}: {json.dumps(row)}", flush=True)

    cold_ref = max(r["wall_s"] for r in prime if "error" not in r)
    warm = [r["wall_s"] < 0.25 * cold_ref for r in revisit if "error" not in r]
    return {
        "distinct_prefixes": k,
        "cold_reference_s": round(cold_ref, 3),
        "revisit_warm_flags": warm,
        "warm_count": sum(warm),
        "prime": prime,
        "revisit": revisit,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--distinct", type=int, default=0,
                    help="if >0, run the cache-capacity probe with this many distinct prefixes")
    ap.add_argument("--expect-context", type=int, default=None,
                    help="fail if loaded context differs (the stack JIT-reloads silently)")
    ap.add_argument("--repeats", type=int, default=6,
                    help="identical-prefix requests; must exceed the parallel slot count")
    ap.add_argument("--tokens", type=int, default=16000)
    ap.add_argument("--parallel-hint", type=int, default=None,
                    help="slot count the model was loaded with; recorded, not enforced")
    ap.add_argument("--timeout", type=float, default=1800.0)
    ap.add_argument("--tag", default=None, help="results filename suffix")
    args = ap.parse_args()

    fp = fingerprint(args.model)
    if args.expect_context and fp["loaded_context_length"] != args.expect_context:
        raise SystemExit(
            f"loaded context is {fp['loaded_context_length']}, expected "
            f"{args.expect_context} — the lane reconfigured itself; reload before probing")

    print(f"model {args.model} | ctx {fp['loaded_context_length']} | "
          f"~{args.tokens} tok | repeats {args.repeats}\n", flush=True)

    if args.distinct:
        cap = capacity_probe(args.model, args.tokens, args.distinct, args.timeout)
        print("\n" + json.dumps({k: v for k, v in cap.items()
                                 if k not in ("prime", "revisit")}, indent=2))
        RESULTS.mkdir(exist_ok=True)
        tag = args.tag or f"ctx{fp['loaded_context_length']}-distinct{args.distinct}"
        out = RESULTS / f"prefixcapacity-{args.model.replace('/', '_')}-{tag}.json"
        out.write_text(json.dumps(
            {"fingerprint": fp, "tokens_requested": args.tokens,
             "parallel_hint": args.parallel_hint, "capacity": cap}, indent=2) + "\n")
        print(f"\nwrote {out}")
        return

    prompt_a = build_prompt(args.tokens, uuid.uuid4().hex)
    rows: list[dict[str, Any]] = []
    for i in range(args.repeats):
        row = ask(args.model, prompt_a, f"Reply with the digit {i + 1}.", args.timeout)
        row["step"] = f"A{i + 1}"
        rows.append(row)
        print(f"  A{i + 1}: {json.dumps(row)}", flush=True)

    # Negative control: same size, same shape, different salt. Must be cold.
    prompt_b = build_prompt(args.tokens, uuid.uuid4().hex)
    ctrl = ask(args.model, prompt_b, "Reply with the digit 1.", args.timeout)
    ctrl["step"] = "B-control"
    print(f"  B (negative control, fresh salt): {json.dumps(ctrl)}", flush=True)

    # Does A survive B? Distinguishes a one-entry cache from a multi-entry one.
    again = ask(args.model, prompt_a, "Reply with the digit 9.", args.timeout)
    again["step"] = "A-after-B"
    print(f"  A again (after B): {json.dumps(again)}", flush=True)

    verdict = classify(rows, args.parallel_hint)
    control_ok = (
        "error" not in ctrl
        and ctrl["wall_s"] > 0.5 * verdict.get("cold_reference_s", 0)
    )
    verdict["negative_control_cold"] = control_ok
    verdict["a_survives_b"] = (
        "error" not in again
        and again["wall_s"] < 0.25 * verdict.get("cold_reference_s", 0)
    )
    if not control_ok:
        verdict["WARNING"] = (
            "negative control was NOT cold — the timing signal does not distinguish "
            "a cache hit from a miss here; disregard every other field")

    print("\n" + json.dumps(verdict, indent=2))

    RESULTS.mkdir(exist_ok=True)
    tag = args.tag or f"ctx{fp['loaded_context_length']}"
    out = RESULTS / f"prefixcache-{args.model.replace('/', '_')}-{tag}.json"
    payload = {
        "fingerprint": fp,
        "tokens_requested": args.tokens,
        "repeats": args.repeats,
        "parallel_hint": args.parallel_hint,
        "sequence": rows + [ctrl, again],
        "verdict": verdict,
    }
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
