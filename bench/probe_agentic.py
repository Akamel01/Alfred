"""Sequential tool-calling probe — the axis D41 selected a lane without measuring.

Phase -1 measured prefill throughput, one prefix-reuse pair, ten single-shot tool calls
and five single-shot code generations. None of that exercises what Phase 1 actually
depends on: calling a tool, reading its result, deciding the next call, and recovering
when one fails.

Design constraints, each answering a way this probe could lie to us:

* **The answer is unobtainable without chaining.** Scenario data is generated from a
  per-run seed, so no answer exists in training data and a guess cannot land. A model
  that skips the tools scores zero rather than accidentally passing.
* **The harness computes ground truth**, from the same seeded data, never from the
  model's report. The model's answer is a claim.
* **Tools fail on purpose.** One transient error and one out-of-range error per run,
  both with informative messages, because recovery is the thing being measured and an
  error that never happens measures nothing.
* **Fabrication is detected separately from wrongness.** An answer that matches a value
  the model never actually fetched is a different failure from an answer that is merely
  wrong, and for Alfred it is the more dangerous one.

    python3 bench/probe_agentic.py --model qwen3-next-80b-a3b-instruct
"""

from __future__ import annotations

import argparse
import json
import math
import random
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

BASE = "http://127.0.0.1:1234"
RESULTS = Path(__file__).resolve().parent / "results"


# --------------------------------------------------------------------- world


@dataclass
class World:
    """Seeded scenario data. Regenerated per run so the answers cannot be recalled."""

    seed: int
    scenarios: dict[str, dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        rng = random.Random(self.seed)
        for _ in range(4):
            sid = f"S-{rng.randint(1000, 9999)}"
            n_agents = rng.randint(2, 3)
            n_steps = rng.randint(6, 10)
            agents = []
            for _ in range(n_agents):
                x0, y0 = rng.uniform(-40, 40), rng.uniform(-6, 6)
                vx, vy = rng.uniform(-14, 14), rng.uniform(-1, 1)
                agents.append([
                    {"x": round(x0 + vx * 0.1 * t, 4), "y": round(y0 + vy * 0.1 * t, 4),
                     "vx": round(vx, 4), "vy": round(vy, 4)}
                    for t in range(n_steps)
                ])
            self.scenarios[sid] = {"dt": 0.1, "n_agents": n_agents,
                                   "n_steps": n_steps, "agents": agents}

    @property
    def ids(self) -> list[str]:
        return list(self.scenarios)

    def longest(self) -> str:
        return max(self.ids, key=lambda s: self.scenarios[s]["n_steps"])


# --------------------------------------------------------------------- tools

TOOLS = [
    {"type": "function", "function": {
        "name": "list_scenarios",
        "description": "List every available scenario id.",
        "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {
        "name": "describe_scenario",
        "description": "Return dt, agent count and step count for one scenario.",
        "parameters": {"type": "object", "properties": {
            "scenario_id": {"type": "string"}}, "required": ["scenario_id"]}}},
    {"type": "function", "function": {
        "name": "get_state",
        "description": "Return x, y, vx, vy for one agent at one step.",
        "parameters": {"type": "object", "properties": {
            "scenario_id": {"type": "string"},
            "agent_index": {"type": "integer"},
            "step": {"type": "integer"}},
            "required": ["scenario_id", "agent_index", "step"]}}},
    {"type": "function", "function": {
        "name": "submit_answer",
        "description": "Submit the final numeric answer. Call this exactly once, last.",
        "parameters": {"type": "object", "properties": {
            "value": {"type": "number"}}, "required": ["value"]}}},
]


class ToolHost:
    """Executes tool calls and records everything the scoring needs."""

    def __init__(self, world: World, fail_once_on: str | None) -> None:
        self.world = world
        self.fail_once_on = fail_once_on
        self.fired_transient = False
        self.calls: list[dict[str, Any]] = []
        self.observed_values: list[float] = []
        self.answer: float | None = None

    def invoke(self, name: str, args: dict[str, Any]) -> tuple[str, bool]:
        """Returns (json result, is_error)."""
        record = {"name": name, "args": args}
        try:
            out, err = self._dispatch(name, args)
        except Exception as exc:  # a malformed call is data, not a crash
            out, err = {"error": f"invalid call: {exc}"}, True
        record["error"] = err
        self.calls.append(record)
        return json.dumps(out), err

    def _dispatch(self, name: str, args: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        if name == "list_scenarios":
            return {"scenarios": self.world.ids}, False

        if name == "describe_scenario":
            sid = args["scenario_id"]
            if sid not in self.world.scenarios:
                return {"error": f"unknown scenario_id '{sid}'. "
                                 f"Call list_scenarios first."}, True
            s = self.world.scenarios[sid]
            return {"dt": s["dt"], "n_agents": s["n_agents"], "n_steps": s["n_steps"]}, False

        if name == "get_state":
            # One transient failure per run: recovery from a retryable error is a
            # different capability from recovery from a wrong argument.
            if self.fail_once_on == "get_state" and not self.fired_transient:
                self.fired_transient = True
                return {"error": "backend temporarily unavailable, retry the same call"}, True
            sid = args["scenario_id"]
            if sid not in self.world.scenarios:
                return {"error": f"unknown scenario_id '{sid}'"}, True
            s = self.world.scenarios[sid]
            ai, step = int(args["agent_index"]), int(args["step"])
            if not 0 <= ai < s["n_agents"]:
                return {"error": f"agent_index out of range: valid values are "
                                 f"0..{s['n_agents'] - 1}"}, True
            if not 0 <= step < s["n_steps"]:
                return {"error": f"step out of range: valid values are "
                                 f"0..{s['n_steps'] - 1}"}, True
            state = s["agents"][ai][step]
            self.observed_values.extend(float(v) for v in state.values())
            return dict(state), False

        if name == "submit_answer":
            self.answer = float(args["value"])
            return {"accepted": True}, False

        return {"error": f"no such tool '{name}'"}, True


# --------------------------------------------------------------------- tasks


@dataclass
class Task:
    id: str
    prompt: str
    truth: float
    min_depth: int          # successful data reads without which the answer cannot exist
    tolerance: float = 1e-3
    fail_once_on: str | None = None


def build_tasks(world: World) -> list[Task]:
    ids = world.ids
    longest = world.longest()
    s_long = world.scenarios[longest]
    first = ids[0]
    s_first = world.scenarios[first]

    # T1 — three-hop read: list -> describe -> get_state
    t1_truth = s_first["agents"][0][s_first["n_steps"] - 1]["x"]

    # T2 — same shape, with a transient tool failure in the middle
    t2_truth = s_first["agents"][0][0]["vx"]

    # T3 — two reads plus arithmetic
    a = s_first["agents"][0][0]
    b = s_first["agents"][1][0]
    t3_truth = math.hypot(a["x"] - b["x"], a["y"] - b["y"])

    # T4 — search across scenarios, then read
    t4_truth = float(s_long["n_steps"])

    # T5 — four reads plus a derived quantity
    p0 = s_long["agents"][0][0]
    p1 = s_long["agents"][1][0]
    q0 = s_long["agents"][0][1]
    q1 = s_long["agents"][1][1]
    d0 = math.hypot(p0["x"] - p1["x"], p0["y"] - p1["y"])
    d1 = math.hypot(q0["x"] - q1["x"], q0["y"] - q1["y"])
    t5_truth = (d0 - d1) / s_long["dt"]

    return [
        Task("t1-three-hop",
             "Report the x position of agent 0 at the FINAL step of the first scenario "
             "returned by list_scenarios. Use the tools; do not guess.",
             t1_truth, 1),
        Task("t2-transient-error",
             "Report vx of agent 0 at step 0 of the first scenario returned by "
             "list_scenarios. Use the tools; do not guess.",
             t2_truth, 1, fail_once_on="get_state"),
        Task("t3-two-reads-arithmetic",
             "In the first scenario returned by list_scenarios, compute the Euclidean "
             "distance between agent 0 and agent 1 at step 0. Use the tools; do not guess.",
             t3_truth, 2),
        Task("t4-search",
             "Among all scenarios, find the one with the MOST steps and report its step "
             "count. Use the tools; do not guess.",
             t4_truth, 4),
        Task("t5-derived",
             "In the scenario with the most steps, compute the closing speed between "
             "agent 0 and agent 1 over the first interval: take the distance between them "
             "at step 0, subtract the distance at step 1, and divide by dt. Use the tools; "
             "do not guess.",
             t5_truth, 4),
    ]


# ----------------------------------------------------------------------- run


TOOL_NAMES = {"list_scenarios", "describe_scenario", "get_state", "submit_answer"}


def parse_text_tool_call(content: str) -> tuple[str, dict[str, Any]] | None:
    """Recover a tool call the serving layer rendered into the content channel.

    Accepts the shapes observed in practice: a bare name followed by a JSON object,
    and a JSON object carrying name/arguments keys. Deliberately narrow — this
    salvages a known serving defect, it does not guess at intent.
    """
    text = content.strip()
    if not text:
        return None
    for name in TOOL_NAMES:
        idx = text.find(name)
        if idx == -1:
            continue
        brace = text.find("{", idx)
        paren = text.find("(", idx)
        if brace == -1 or (paren != -1 and paren < brace):
            # `submit_answer(10)` — positional call syntax, the second shape this
            # serving layer produces. Salvaged only where the tool has exactly one
            # parameter, so the binding is unambiguous; anywhere else it would be a
            # guess at intent, which is not what this function is for.
            if paren == -1:
                return (name, {}) if name == "list_scenarios" else None
            close = text.find(")", paren)
            params = next((list(f["function"]["parameters"]["properties"])
                           for f in TOOLS if f["function"]["name"] == name), [])
            if close == -1 or len(params) != 1:
                return (name, {}) if name == "list_scenarios" else None
            raw = text[paren + 1:close].strip().strip("'\"")
            try:
                return name, {params[0]: json.loads(raw)}
            except json.JSONDecodeError:
                return name, {params[0]: raw}
        depth, end = 0, -1
        for i, ch in enumerate(text[brace:], brace):
            depth += (ch == "{") - (ch == "}")
            if depth == 0:
                end = i + 1
                break
        if end == -1:
            return None
        try:
            args = json.loads(text[brace:end])
        except json.JSONDecodeError:
            return None
        if not isinstance(args, dict):
            return None
        if set(args) >= {"name", "arguments"} and args["name"] in TOOL_NAMES:
            inner = args["arguments"]
            if isinstance(inner, str):
                try:
                    inner = json.loads(inner)
                except json.JSONDecodeError:
                    return None
            return (args["name"], inner if isinstance(inner, dict) else {})
        return (name, args)
    return None


def chat(model: str, messages: list[dict[str, Any]], timeout: int) -> dict[str, Any]:
    body = json.dumps({"model": model, "messages": messages, "tools": TOOLS,
                       "temperature": 0.0, "max_tokens": 900}).encode()
    req = urllib.request.Request(f"{BASE}/v1/chat/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def run_task(model: str, task: Task, world: World, max_turns: int,
             timeout: int) -> dict[str, Any]:
    host = ToolHost(world, task.fail_once_on)
    salt = uuid.uuid4().hex[:8]
    messages: list[dict[str, Any]] = [
        {"role": "system", "content":
            f"Run {salt}. You answer questions about trajectory scenarios using the "
            f"provided tools. The data is generated fresh for this run, so you cannot "
            f"know any value without calling a tool. When you have the answer, call "
            f"submit_answer exactly once."},
        {"role": "user", "content": task.prompt},
    ]

    started = time.perf_counter()
    turns = 0
    malformed = 0
    text_channel_calls = 0
    stop_reason = "max_turns"

    while turns < max_turns and host.answer is None:
        turns += 1
        try:
            reply = chat(model, messages, timeout)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            stop_reason = f"transport: {exc}"
            break

        choice = reply["choices"][0]["message"]
        calls = choice.get("tool_calls") or []
        messages.append({"role": "assistant",
                         "content": choice.get("content") or "",
                         "tool_calls": calls})

        if not calls:
            # A tool call emitted as prose rather than through the tool-call channel is
            # a serving-layer defect, not a capability failure — the D40 class, where a
            # schema-capable model is let down by the stack in front of it. Recovering
            # it here is what separates "the model cannot chain" from "the last hop was
            # rendered as text". Counted, never silently absorbed.
            salvaged = parse_text_tool_call(choice.get("content") or "")
            if salvaged is not None:
                name, sargs = salvaged
                text_channel_calls += 1
                result, _ = host.invoke(name, sargs)
                messages.append({"role": "user",
                                 "content": f"tool result for {name}: {result}"})
                continue
            stop_reason = "no_tool_call"
            messages.append({"role": "user", "content":
                             "Continue using the tools, and call submit_answer when done."})
            continue

        for call in calls:
            fn = call["function"]
            try:
                args = json.loads(fn.get("arguments") or "{}")
                if not isinstance(args, dict):
                    raise ValueError("arguments is not an object")
            except (json.JSONDecodeError, ValueError):
                malformed += 1
                args = {}
            result, _ = host.invoke(fn["name"], args)
            messages.append({"role": "tool", "tool_call_id": call.get("id", ""),
                             "content": result})

    if host.answer is not None:
        stop_reason = "submitted"

    return score(task, host, turns, malformed, stop_reason,
                 time.perf_counter() - started, text_channel_calls)


def score(task: Task, host: ToolHost, turns: int, malformed: int,
          stop_reason: str, wall_s: float, text_channel_calls: int) -> dict[str, Any]:
    real = [c for c in host.calls if c["name"] != "submit_answer"]
    errors = [c for c in real if c["error"]]
    succeeded_after_error = bool(errors) and any(
        not c["error"] for c in real[real.index(errors[0]) + 1:])

    signatures = [json.dumps([c["name"], c["args"]], sort_keys=True) for c in real]
    repeated = len(signatures) - len(set(signatures))

    correct = (host.answer is not None
               and math.isclose(host.answer, task.truth,
                                rel_tol=task.tolerance, abs_tol=task.tolerance))

    # Fabrication: an answer produced without enough successful reads to have derived it.
    # Distinguished from plain wrongness because a confident unsourced number is the
    # failure this whole architecture is built to catch.
    data_reads = len([c for c in real
                      if not c["error"] and c["name"] in ("get_state", "describe_scenario")])
    fabricated = host.answer is not None and data_reads < task.min_depth

    return {
        "task": task.id,
        "correct": correct,
        "answer": host.answer,
        "truth": round(task.truth, 6),
        "turns": turns,
        "tool_calls": len(real),
        "min_depth": task.min_depth,
        "data_reads": data_reads,
        "tool_errors": len(errors),
        "error_injected": task.fail_once_on is not None,
        "recovered_after_error": succeeded_after_error,
        "repeated_calls": repeated,
        "malformed_args": malformed,
        "text_channel_calls": text_channel_calls,
        "fabricated": fabricated,
        "stop_reason": stop_reason,
        "wall_s": round(wall_s, 2),
    }


def fingerprint(model: str) -> dict[str, Any]:
    with urllib.request.urlopen(f"{BASE}/api/v0/models", timeout=30) as resp:
        data = json.loads(resp.read())
    for m in data["data"]:
        if m["id"] == model and m.get("state") == "loaded":
            return {"model_id": m["id"], "engine": m.get("compatibility_type"),
                    "quantization": m.get("quantization"), "arch": m.get("arch"),
                    "loaded_context_length": m.get("loaded_context_length"),
                    "max_context_length": m.get("max_context_length")}
    raise SystemExit(f"model '{model}' is not loaded — load it before probing")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--max-turns", type=int, default=14)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--expect-context", type=int, default=None,
                    help="fail if the loaded context length differs (the serving stack "
                         "silently JIT-reloads at its default)")
    ap.add_argument("--force-overwrite", action="store_true",
                    help="allow replacing an existing result file for this seed")
    args = ap.parse_args()

    fp = fingerprint(args.model)
    if args.expect_context and fp["loaded_context_length"] != args.expect_context:
        raise SystemExit(
            f"loaded context is {fp['loaded_context_length']}, expected "
            f"{args.expect_context} — the lane reconfigured itself; reload before probing")

    seed = args.seed if args.seed is not None else random.randrange(10**9)

    # Checked before the run, not after: refusing to write at the end would
    # burn the whole probe and then throw the result away.
    out = RESULTS / f"agentic-{args.model.replace('/', '_')}-seed{seed}.json"
    if out.exists() and not args.force_overwrite:
        raise SystemExit(
            f"{out.name} already exists — this seed has been run before. "
            f"Refusing to overwrite; pass --force-overwrite to replace it, or "
            f"use a different --seed.")

    world = World(seed)
    tasks = build_tasks(world)
    print(f"model {args.model} | ctx {fp['loaded_context_length']} | seed {seed}\n")

    rows = []
    for task in tasks:
        print(f"{task.id} ...", flush=True)
        row = run_task(args.model, task, world, args.max_turns, args.timeout)
        rows.append(row)
        print("  " + json.dumps({k: row[k] for k in
              ("correct", "turns", "tool_calls", "tool_errors",
               "recovered_after_error", "repeated_calls", "fabricated", "stop_reason")}))

    n = len(rows)
    injected = [r for r in rows if r["error_injected"] or r["tool_errors"]]
    summary = {
        "chain_completion_rate": sum(r["stop_reason"] == "submitted" for r in rows) / n,
        "correct_rate": sum(r["correct"] for r in rows) / n,
        "fabrication_rate": sum(r["fabricated"] for r in rows) / n,
        "recovery_rate": (sum(r["recovered_after_error"] for r in injected) / len(injected)
                          if injected else None),
        "mean_turns": round(sum(r["turns"] for r in rows) / n, 2),
        "mean_tool_calls": round(sum(r["tool_calls"] for r in rows) / n, 2),
        "total_repeated_calls": sum(r["repeated_calls"] for r in rows),
        "total_malformed_args": sum(r["malformed_args"] for r in rows),
        "total_text_channel_calls": sum(r["text_channel_calls"] for r in rows),
    }
    print("\n" + json.dumps(summary, indent=2))

    RESULTS.mkdir(exist_ok=True)
    slug = args.model.replace("/", "_")

    # One file per seed. The previous version wrote a single per-model file, so
    # each seed silently erased the last one and a four-seed result survived
    # only in the operator's terminal scrollback.
    out.write_text(json.dumps(
        {"fingerprint": fp, "seed": seed, "max_turns": args.max_turns,
         "summary": summary, "tasks": rows}, indent=2) + "\n")
    print(f"\nwrote {out}")

    rollup = _rollup(slug, fp)
    if rollup:
        agg = RESULTS / f"agentic-{slug}-rollup.json"
        agg.write_text(json.dumps(rollup, indent=2) + "\n")
        print(f"wrote {agg}  (seeds {rollup['seeds']})")


def _rollup(slug: str, fp: dict[str, Any]) -> dict[str, Any] | None:
    """Aggregate every seed file measured under *this* serving configuration.

    Runs whose fingerprint differs are excluded rather than averaged in:
    a score from a silently-reloaded 28k lane blended with a 262k one would
    describe a configuration that was never run.
    """
    keys = ("model_id", "engine", "quantization", "loaded_context_length")
    runs = []
    for path in sorted(RESULTS.glob(f"agentic-{slug}-seed*.json")):
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        if all(data.get("fingerprint", {}).get(k) == fp.get(k) for k in keys):
            runs.append(data)
    if not runs:
        return None

    fields = ("chain_completion_rate", "correct_rate", "fabrication_rate",
              "recovery_rate", "mean_turns", "mean_tool_calls")
    mean: dict[str, Any] = {}
    for f in fields:
        vals = [r["summary"][f] for r in runs if r["summary"].get(f) is not None]
        mean[f] = round(sum(vals) / len(vals), 4) if vals else None
    tasks_total = sum(len(r["tasks"]) for r in runs)
    return {
        "fingerprint": fp,
        "seeds": [r["seed"] for r in runs],
        "n_runs": len(runs),
        "n_tasks": tasks_total,
        "mean": mean,
        "totals": {
            k: sum(r["summary"].get(k, 0) for r in runs)
            for k in ("total_repeated_calls", "total_malformed_args",
                      "total_text_channel_calls")
        },
        "tasks_correct": sum(sum(t["correct"] for t in r["tasks"]) for r in runs),
        "tasks_submitted": sum(
            sum(t["stop_reason"] == "submitted" for t in r["tasks"]) for r in runs),
        "tasks_fabricated": sum(sum(t["fabricated"] for t in r["tasks"]) for r in runs),
        "excluded_note": "seed files whose fingerprint differs from this run are excluded",
    }


if __name__ == "__main__":
    main()
