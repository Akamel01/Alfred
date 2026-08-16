"""Mutation control for the ACS-1 conformance suite.

    python3 harness/acs/mutate.py            # every mutant, both implementations
    python3 harness/acs/mutate.py --list     # what would run
    python3 harness/acs/mutate.py --only js-nfc-dropped
    python3 harness/acs/mutate.py --threshold 12

**What this answers.** A conformance suite reporting 395/395 is indistinguishable from
a vacuous one that asserts nothing. The only way to tell them apart is to break the
implementation on purpose and check that the suite notices — and to make the margin,
not merely the fact of detection, something a future contributor cannot quietly erode.
ADR-0004 recorded the first run of this control as an ad-hoc shell loop and recorded
its thin margins honestly: duplicate detection failed 3 checks and the lone-surrogate
check failed 1. This script is that loop, committed, so that widening the suite and
weakening it are no longer the same commit.

**Contract.** Every mutant must fail at least `--threshold` checks (default 8). A
mutant that fails fewer is not a passing test — it is a rule the vector file is
sampling too thinly, and the fix is more vectors, never a lower threshold. Removing a
mutant to make this script pass is the same act with more steps.

**Method.** Each mutant is applied to a *copy* of `harness/acs/` in a temporary
directory, never in place. This is not fastidiousness: an earlier in-place mutation
harness in this repo, combined with a stale `__pycache__`, produced a false corruption
signal that cost an afternoon. The copy carries no `__pycache__`, and the child
interpreter is told not to write one.

Each mutation is a literal string substitution whose original text must occur exactly
the expected number of times. A mutation that silently fails to apply would report
"detected 0 failures" and read as a hole in the suite, so a mutant that does not apply
is an error here rather than a finding.

**The control's own control.** Before any mutant runs, the pristine copy must pass
both suites *and* regenerate `vectors.json` byte for byte. Detection counts mean
nothing if the baseline is already red, and a hand-edited vector file would make every
count below unreproducible.
"""

from __future__ import annotations

import argparse
import filecmp
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent

DEFAULT_THRESHOLD = 8

JS = "acs1.mjs"
PY = "acs1.py"

IGNORED = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", ".claude-flow")


@dataclass(frozen=True)
class Mutant:
    """A deliberate defect. `edits` are (original, replacement, expected occurrences);
    the count is stated so that a refactor which duplicates a line cannot turn a
    mutation into a partial one."""

    id: str
    target: str
    note: str
    edits: tuple[tuple[str, str, int], ...]


def _e(old: str, new: str, count: int = 1) -> tuple[str, str, int]:
    return (old, new, count)


# --------------------------------------------------------------------- the mutants
#
# Grouped by the rule each one breaks. The five at the top are the original ADR-0004
# set, kept with their names so the numbers in that record stay comparable.

MUTANTS: list[Mutant] = [
    # ---------------------------------------------------------------- ADR-0004 five
    Mutant(
        "js-exponent-plus", JS,
        "the exponent keeps the host's '+' sign, which ADR-0004 forbids",
        (_e("e${parseInt(exponent, 10)}`", "e${exponent}`"),),
    ),
    Mutant(
        "js-nfc-dropped", JS,
        "strings are not normalized, so composed and decomposed forms hash differently",
        (_e('  return text.normalize("NFC");', "  return text;"),),
    ),
    Mutant(
        "js-key-order-utf16", JS,
        "keys ordered by UTF-16 code unit, which is what RFC 8785 specifies and "
        "ACS-1 rejects: it disagrees with byte order on astral characters",
        (_e(
            "  items.sort((a, b) => compareBytes(a[0], b[0]));",
            "  items.sort((a, b) => (a[1] < b[1] ? -1 : a[1] > b[1] ? 1 : 0));",
        ),),
    ),
    Mutant(
        "js-dup-detection-off", JS,
        "the encoder emits both members of a colliding key pair",
        (_e(
            '      throw new AcsError("DUPLICATE_KEY", `duplicate object key after NFC: ${key}`);',
            "      /* mutant: duplicate accepted */",
        ),),
    ),
    Mutant(
        "js-surrogate-check-off", JS,
        "TextEncoder substitutes U+FFFD for a lone surrogate and reports nothing, so "
        "without the explicit check the corruption is silent",
        (_e(
            "function checkSurrogates(text) {",
            "function checkSurrogates(text) {\n  if (text !== null) return; // mutant",
        ),),
    ),
    # ------------------------------------------------------------------ escape table
    Mutant(
        "js-escape-uppercase-hex", JS,
        "control escapes in uppercase hex: valid JSON, different bytes, different hash",
        (_e(
            '    else if (cp < 0x20) out += "\\\\u" + cp.toString(16).padStart(4, "0");',
            '    else if (cp < 0x20) out += "\\\\u" '
            '+ cp.toString(16).toUpperCase().padStart(4, "0");',
        ),),
    ),
    Mutant(
        "js-escape-tab-missing", JS,
        "tab loses its two-character form and is emitted as \\u0009",
        (_e('  [0x09, "\\\\t"],\n', ""),),
    ),
    Mutant(
        "js-escape-b-f-swapped", JS,
        "two entries of the escape table transposed — the defect a hand-typed table "
        "actually produces",
        (_e('  [0x08, "\\\\b"],', '  [0x08, "\\\\f"],'),
         _e('  [0x0c, "\\\\f"],', '  [0x0c, "\\\\b"],')),
    ),
    Mutant(
        "js-escape-del", JS,
        "0x7f escaped, which ACS-1 does not do",
        (_e("    else if (cp < 0x20) out", "    else if (cp < 0x20 || cp === 0x7f) out"),),
    ),
    Mutant(
        "js-escape-solidus", JS,
        "'/' escaped, which JSON permits and ACS-1 forbids",
        (_e('  [0x22, \'\\\\"\'],', '  [0x2f, "\\\\/"],\n  [0x22, \'\\\\"\'],'),),
    ),
    Mutant(
        "js-escape-non-ascii", JS,
        "non-ASCII emitted as \\uXXXX instead of raw UTF-8",
        (_e(
            "    else out += ch;",
            '    else if (cp < 0x80) out += ch;\n'
            '    else out += "\\\\u" + cp.toString(16).padStart(4, "0");',
        ),),
    ),
    # -------------------------------------------------------------------- key order
    Mutant(
        "js-key-order-prefix-tie", JS,
        "byte comparison treats a prefix as equal to what it prefixes, so keys "
        "differing only past a common prefix fall back to insertion order",
        (_e("  return a.length - b.length;", "  return 0;"),),
    ),
    Mutant(
        "js-key-order-first-byte", JS,
        "key comparison stops after the first byte",
        (_e(
            "  const n = Math.min(a.length, b.length);",
            "  const n = Math.min(a.length, b.length, 1);",
        ),),
    ),
    Mutant(
        "js-array-sorted", JS,
        "arrays sorted like objects; array order is data, not presentation",
        (_e(
            '  if (Array.isArray(value)) return "[" + value.map(encode).join(",") + "]";',
            '  if (Array.isArray(value)) return "[" + value.map(encode).sort().join(",") + "]";',
        ),),
    ),
    # ---------------------------------------------------------------- normalization
    Mutant(
        "js-nfkc-instead-of-nfc", JS,
        "NFKC instead of NFC: it folds compatibility characters, destroying "
        "distinctions the source data made",
        (_e('  return text.normalize("NFC");', '  return text.normalize("NFKC");'),),
    ),
    # ------------------------------------------------------------------ float grammar
    Mutant(
        "js-neg-zero-kept", JS,
        "-0.0 rendered as -0.0e0 instead of normalizing to 0.0e0",
        (_e(
            '  if (x === 0) return "0.0e0"; // also normalizes -0',
            '  if (x === 0) return Object.is(x, -0) ? "-0.0e0" : "0.0e0";',
        ),),
    ),
    Mutant(
        "js-mantissa-no-fraction", JS,
        "a single-digit mantissa emitted without its fractional part",
        (_e(
            '  const tail = dot === -1 ? "0" : mantissa.slice(dot + 1);',
            '  const tail = dot === -1 ? "" : mantissa.slice(dot + 1);',
        ),),
    ),
    # ------------------------------------------------------------- int64 boundaries
    Mutant(
        "js-int64-loose", JS,
        "encoder range widened by one in both directions",
        (_e(
            "    if (value < INT64_MIN || value > INT64_MAX) {",
            "    if (value < INT64_MIN - 1n || value > INT64_MAX + 1n) {",
        ),),
    ),
    Mutant(
        "js-int64-tight", JS,
        "encoder range narrowed by one in both directions, so the boundary values "
        "themselves are refused",
        (_e(
            "    if (value < INT64_MIN || value > INT64_MAX) {",
            "    if (value <= INT64_MIN || value >= INT64_MAX) {",
        ),),
    ),
    Mutant(
        "js-parse-int64-loose", JS,
        "parser range widened by one in both directions",
        (_e(
            "    if (n < INT64_MIN || n > INT64_MAX) fail",
            "    if (n < INT64_MIN - 1n || n > INT64_MAX + 1n) fail",
        ),),
    ),
    Mutant(
        "js-parse-int64-tight", JS,
        "parser range narrowed by one, so a stored row holding int64 max is refused",
        (_e(
            "    if (n < INT64_MIN || n > INT64_MAX) fail",
            "    if (n <= INT64_MIN || n >= INT64_MAX) fail",
        ),),
    ),
    # ------------------------------------------------------------------ parse side
    Mutant(
        "js-parse-dup-off", JS,
        "the parser keeps the last of a duplicate key pair, which is what every stock "
        "JSON parser does and what parseStrict exists to refuse",
        (_e(
            "      if (map.has(key)) fail(\"DUPLICATE_KEY\", `duplicate object key '${key}'`);",
            "      /* mutant: duplicate accepted */",
        ),),
    ),
    Mutant(
        "js-parse-dup-no-nfc", JS,
        "the parser compares keys before normalizing, so a row whose keys collide "
        "only after NFC is accepted although no encoder could have produced it",
        (_e(
            "      const key = normalize(parseString());",
            "      const key = parseString();",
        ),),
    ),
    # ----------------------------------------------------------------- hash preimage
    Mutant(
        "js-hash-separators-dropped", JS,
        "the NUL separators removed, so a record_type/payload boundary can be forged",
        (_e("    Buffer.from([0]),", "    Buffer.alloc(0),", 2),),
    ),
    Mutant(
        "js-hash-record-type-raw", JS,
        "record_type not normalized, so the same record type stored composed and "
        "decomposed produces two chains",
        (_e(
            '    Buffer.from(normalize(recordType), "utf8"),',
            '    Buffer.from(recordType, "utf8"),',
        ),),
    ),
    Mutant(
        "js-hash-nul-unchecked", JS,
        "a record_type containing NUL accepted, which is the forgery the separators "
        "are there to prevent",
        (_e('  if (recordType.includes("\\u0000")) {', "  if (false) {"),),
    ),
    # ============================================================ Python side
    # The Python implementation gets its own mutants rather than translations of the
    # above, because its hazards are not JavaScript's: bool is an int here, and the
    # parser is the standard library's with hooks rather than one written by hand.
    Mutant(
        "py-bool-after-int", PY,
        "bool tested after int, so True serializes as 1 — isinstance(True, int) is "
        "true in Python and this is the defect that follows",
        (_e(
            '    if value is True:\n        return "true"\n'
            '    if value is False:\n        return "false"\n'
            "    if isinstance(value, int):",
            "    if isinstance(value, int):",
        ),),
    ),
    Mutant(
        "py-nfc-dropped", PY,
        "strings are not normalized",
        (_e(
            '    return unicodedata.normalize("NFC", text)',
            "    return text",
        ),),
    ),
    Mutant(
        "py-nfkc-instead-of-nfc", PY,
        "NFKC instead of NFC",
        (_e(
            '    return unicodedata.normalize("NFC", text)',
            '    return unicodedata.normalize("NFKC", text)',
        ),),
    ),
    Mutant(
        "py-key-order-utf16", PY,
        "keys ordered by UTF-16 code unit rather than UTF-8 byte",
        (_e(
            "        items.sort(key=lambda it: it[0])",
            '        items.sort(key=lambda it: it[1].encode("utf-16-be", "surrogatepass"))',
        ),),
    ),
    Mutant(
        "py-dup-detection-off", PY,
        "the encoder emits both members of a colliding key pair",
        (_e(
            '                raise DuplicateKey(f"duplicate object key after NFC: {key!r}")',
            "                pass  # mutant: duplicate accepted",
        ),),
    ),
    Mutant(
        "py-surrogate-check-off", PY,
        "the lone-surrogate refusal removed; Python raises on encode, so this one "
        "fails loudly rather than silently — but it must still be the suite that says so",
        (_e(
            '    try:\n        text.encode("utf-8")\n'
            "    except UnicodeEncodeError as exc:  # lone surrogate\n"
            '        raise LoneSurrogate(f"string is not encodable as UTF-8: {exc}") from exc',
            '    text.encode("utf-8", "surrogatepass")  # mutant: refusal removed',
        ),),
    ),
    Mutant(
        "py-escape-uppercase-hex", PY,
        "control escapes in uppercase hex",
        (_e('            out.append(f"\\\\u{cp:04x}")',
            '            out.append(f"\\\\u{cp:04X}")'),),
    ),
    Mutant(
        "py-escape-tab-missing", PY,
        "tab loses its two-character form",
        (_e('    0x09: "\\\\t",\n', ""),),
    ),
    Mutant(
        "py-escape-del", PY,
        "0x7f escaped, which ACS-1 does not do",
        (_e("        elif cp < 0x20:", "        elif cp < 0x20 or cp == 0x7F:"),),
    ),
    Mutant(
        "py-neg-zero-kept", PY,
        "-0.0 rendered as -0.0e0",
        (_e(
            '        return "0.0e0"  # also the normalization of -0.0',
            '        return "-0.0e0" if str(value)[0] == "-" else "0.0e0"',
        ),),
    ),
    Mutant(
        "py-mantissa-no-fraction", PY,
        "a single-digit mantissa emitted without its fractional part",
        (_e(
            '    mantissa = ds[0] + "." + (ds[1:] or "0")',
            '    mantissa = ds[0] + "." + ds[1:]',
        ),),
    ),
    Mutant(
        "py-float-repr-presentation", PY,
        "the host's repr used directly, which is precisely what ADR-0004 exists to "
        "forbid: 1.0 becomes \"1.0\" and 1e16 becomes \"1e+16\"",
        (_e(
            "    if value == 0.0:",
            "    return repr(value)  # mutant\n    if value == 0.0:",
        ),),
    ),
    Mutant(
        "py-int64-loose", PY,
        "encoder range widened by one in both directions",
        (_e(
            "        if not INT64_MIN <= value <= INT64_MAX:",
            "        if not INT64_MIN - 1 <= value <= INT64_MAX + 1:",
        ),),
    ),
    Mutant(
        "py-int64-tight", PY,
        "encoder range narrowed by one, so the boundary values are refused",
        (_e(
            "        if not INT64_MIN <= value <= INT64_MAX:",
            "        if not INT64_MIN + 1 <= value <= INT64_MAX - 1:",
        ),),
    ),
    Mutant(
        "py-parse-dup-hook-off", PY,
        "object_pairs_hook removed, so json.loads keeps the last duplicate silently",
        (_e("        object_pairs_hook=_no_duplicates,\n", ""),),
    ),
    Mutant(
        "py-parse-dup-no-nfc", PY,
        "the parser compares keys before normalizing",
        (_e(
            "    keys = [_normalize(k) for k, _ in pairs]",
            "    keys = [k for k, _ in pairs]",
        ),),
    ),
    Mutant(
        "py-parse-int-hook-off", PY,
        "parse_int hook removed, so a stored row can carry an integer no encoder "
        "could have written",
        (_e("        parse_int=_check_int,\n", ""),),
    ),
    Mutant(
        "py-parse-float-hook-off", PY,
        "parse_float hook removed, so a JSON float literal is accepted although "
        "canonical form carries floats as strings",
        (_e("        parse_float=_reject_float,\n", ""),),
    ),
    Mutant(
        "py-hash-separators-dropped", PY,
        "the NUL separators removed from the preimage",
        (_e('        + b"\\x00"\n', "", 2),),
    ),
    Mutant(
        "py-hash-record-type-raw", PY,
        "record_type not normalized before hashing",
        (_e(
            '        + _normalize(record_type).encode("utf-8")',
            '        + record_type.encode("utf-8")',
        ),),
    ),
    Mutant(
        "py-hash-nul-unchecked", PY,
        "a record_type containing NUL accepted",
        (_e('    if "\\x00" in record_type:', "    if False:"),),
    ),
]


# ------------------------------------------------------------------------- running


def _copy_suite(dest: Path) -> None:
    shutil.copytree(HERE, dest, ignore=IGNORED)


def _child_env() -> dict[str, str]:
    env = dict(os.environ)
    # No .pyc anywhere near a mutated copy. A stale __pycache__ next to an in-place
    # mutation is how this project once manufactured a corruption scare.
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = ""
    return env


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd, cwd=cwd, env=_child_env(), capture_output=True, text=True, check=False
    )


def run_js(cwd: Path) -> tuple[int, int, str]:
    """(passed, failed, raw output) for the JavaScript suite."""
    proc = _run(["node", "verify_js.mjs"], cwd)
    m = re.search(r"(\d+) checks passed, (\d+) failed", proc.stdout)
    if not m:
        raise SystemExit(
            f"could not read the JS suite's result line:\n{proc.stdout}\n{proc.stderr}"
        )
    return int(m.group(1)), int(m.group(2)), proc.stdout


def run_py(cwd: Path) -> tuple[int, int, str]:
    """(passed, failed, raw output) for the pytest suite. Collection errors count as
    failures rather than as a crash: a mutant that breaks the module at import time is
    still a mutant the suite detected."""
    proc = _run(
        [sys.executable, "-m", "pytest", "test_acs1.py", "-q", "--tb=no",
         "-p", "no:cacheprovider"],
        cwd,
    )
    out = proc.stdout + proc.stderr
    failed = sum(int(n) for n in re.findall(r"(\d+) failed", out))
    failed += sum(int(n) for n in re.findall(r"(\d+) errors?\b", out))
    passed = sum(int(n) for n in re.findall(r"(\d+) passed", out))
    if not failed and not passed:
        raise SystemExit(f"could not read pytest's result line:\n{out}")
    return passed, failed, out


RUNNERS = {JS: run_js, PY: run_py}


def apply_mutant(root: Path, mutant: Mutant) -> None:
    path = root / mutant.target
    text = path.read_text(encoding="utf-8")
    for old, new, count in mutant.edits:
        found = text.count(old)
        if found != count:
            raise SystemExit(
                f"{mutant.id}: expected {count} occurrence(s) of\n  {old!r}\n"
                f"in {mutant.target}, found {found}. The mutation harness has drifted "
                f"from the implementation; fix the mutant, do not delete it."
            )
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")


def control(verbose: bool) -> None:
    """The baseline. Detection counts are meaningless if the unmutated suite is red,
    and unreproducible if the vector file was hand-edited."""
    with tempfile.TemporaryDirectory(prefix="acs1-control-") as tmp:
        root = Path(tmp) / "acs"
        _copy_suite(root)

        for target, runner in RUNNERS.items():
            passed, failed, out = runner(root)
            if failed:
                raise SystemExit(f"baseline is not green ({target}):\n{out}")
            print(f"  baseline {target:9s} {passed} checks passed, 0 failed")

        proc = _run([sys.executable, "gen_vectors.py"], root)
        if proc.returncode != 0:
            raise SystemExit(f"regenerating vectors.json failed:\n{proc.stdout}{proc.stderr}")
        if not filecmp.cmp(root / "vectors.json", HERE / "vectors.json", shallow=False):
            raise SystemExit(
                "vectors.json does not regenerate byte-identically. Either "
                "gen_vectors.py is non-deterministic or the file was edited by hand; "
                "either way the counts below would not be reproducible."
            )
        print("  baseline vectors.json regenerates byte-identically")
        if verbose:
            print("  " + proc.stdout.strip())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD,
                    help="minimum checks each mutant must fail (default %(default)s)")
    ap.add_argument("--only", action="append", default=[], metavar="ID",
                    help="run just this mutant; repeatable")
    ap.add_argument("--target", choices=sorted(RUNNERS), help="only mutants of one file")
    ap.add_argument("--list", action="store_true", help="list mutants and exit")
    ap.add_argument("-v", "--verbose", action="store_true",
                    help="print each suite's output")
    args = ap.parse_args()

    selected = [m for m in MUTANTS
                if (not args.only or m.id in args.only)
                and (not args.target or m.target == args.target)]
    unknown = set(args.only) - {m.id for m in MUTANTS}
    if unknown:
        raise SystemExit(f"unknown mutant(s): {', '.join(sorted(unknown))}")

    if args.list:
        for m in selected:
            print(f"{m.id:32s} {m.target:9s} {m.note}")
        return 0

    print(f"ACS-1 mutation control — {len(selected)} mutants, "
          f"threshold {args.threshold} checks\n")
    control(args.verbose)
    print()

    thin: list[tuple[Mutant, int]] = []
    undetected: list[Mutant] = []

    for mutant in selected:
        with tempfile.TemporaryDirectory(prefix="acs1-mutant-") as tmp:
            root = Path(tmp) / "acs"
            _copy_suite(root)
            apply_mutant(root, mutant)
            _, failed, out = RUNNERS[mutant.target](root)

        if failed == 0:
            undetected.append(mutant)
            verdict = "UNDETECTED"
        elif failed < args.threshold:
            thin.append((mutant, failed))
            verdict = "THIN"
        else:
            verdict = "ok"
        print(f"  {mutant.id:32s} {mutant.target:9s} {failed:4d} failed  {verdict}")
        if args.verbose:
            print("\n".join("      " + line for line in out.splitlines()))

    print()
    if undetected:
        print("UNDETECTED — the suite does not constrain these rules at all:")
        for m in undetected:
            print(f"  {m.id}: {m.note}")
    if thin:
        print(f"THIN — detected, but on fewer than {args.threshold} checks. The fix is "
              f"more vectors for the rule, not a lower threshold:")
        for m, n in thin:
            print(f"  {m.id} ({n}): {m.note}")
    if undetected or thin:
        return 1

    print(f"all {len(selected)} mutants fail at least {args.threshold} checks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
