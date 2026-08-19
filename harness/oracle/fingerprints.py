"""Runs INSIDE the oracle image. Emits digests and names, and never the source itself.

Two jobs, both of which need the oracle present and neither of which may let the oracle out.

**Source hashes for C15 clause 3.** That clause compares a patch's added lines against hashes
of the oracle's source files, and it has never run against a real hash: `denied_source_hashes`
is supplied in two test cases and by nothing else, so on every real run C15 reports `PASSED —
2 of 3 clauses`. This is where the register comes from.

**The denylist's import names, verified rather than asserted.** `policy/oracle-denylist.json`
carries them flagged `UNVERIFIED` — taken from this project's records, not read from each
distribution at a pinned version. A wrong import name is an assertion that passes while naming
nothing, which is the vacuity ADR-0007 named. `importlib.metadata` at the pin answers it.

**Why the hashing happens in here rather than out there.** D54: the oracle's outputs cross the
boundary as data and its code never crosses at all. Hashing outside would mean extracting
CriMe's source text into Alfred's repository, which is the thing D54 forbids in as many words.
So only digests leave.

**And therefore the normalization exists twice.** `normalized_source_hash` in
`harness/containment/patch_side.py` is the other copy. This file cannot import it —
`extract.py`'s stated property is that nothing baked into this image imports Alfred code, and
that property is worth more than the duplication costs. Two implementations of one canonical
form is the hazard ACS-1 already met and already answered: publish vectors, make both sides
answer them. This script answers `normalization_vectors.json` in its own output, and the
driver outside refuses the run if any digest disagrees. Without that, a drift between the two
would make every hash in the register a hash of something else, and clause 3 would match
nothing while reading exactly like a clean patch.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

# Kept byte-identical to patch_side.py's pair. The vectors are what proves they still are.
_COMMENT = re.compile(r"(?m)#.*$|//.*$")
_WHITESPACE = re.compile(r"\s+")

VECTORS_PATH = Path("/oracle/normalization_vectors.json")
OUT_PATH = Path("/out/oracle_fingerprints.json")

# The oracle's measure implementations. The subtree an agent under time pressure would vendor
# from: one file per measure, each self-contained enough to paste.
MEASURE_SUBPACKAGE = "measure"

DENIED_DISTRIBUTIONS = (
    "commonroad-crime",
    "commonroad-reach",
    "commonroad-drivability-checker",
    "commonroad-clcs",
)


def _normalized(text: str) -> str:
    stripped = _COMMENT.sub(" ", text)
    collapsed = _WHITESPACE.sub(" ", stripped).strip().lower()
    return hashlib.sha256(collapsed.encode("utf-8")).hexdigest()


def _package_root(name: str) -> Path | None:
    spec = importlib.util.find_spec(name)
    if spec is None or not spec.origin:
        return None
    return Path(spec.origin).parent


def _source_hashes() -> tuple[dict[str, str], list[str]]:
    """`{digest: relative path}` over the oracle's measure sources, plus findings.

    Keyed by digest because that is the direction clause 3 looks it up in, and because two
    files with identical normalized content are the same vendoring hazard under either name.
    A collision is reported rather than silently overwritten: it would mean one of the two
    paths becomes unreportable in the finding C15 emits.
    """
    findings: list[str] = []
    root = _package_root("commonroad_crime")
    if root is None:
        return {}, ["commonroad_crime is not importable in the oracle image"]

    measure_root = root / MEASURE_SUBPACKAGE
    if not measure_root.is_dir():
        return {}, [f"{measure_root} is not a directory; the measure subpackage moved"]

    hashes: dict[str, str] = {}
    for path in sorted(measure_root.rglob("*.py")):
        if path.name == "__init__.py":
            # An `__init__` is re-exports; its normalized content matches nothing an agent
            # would vendor and would generate false positives against any short module.
            continue
        digest = _normalized(path.read_text(encoding="utf-8", errors="replace"))
        relative = str(path.relative_to(root.parent))
        if digest in hashes:
            findings.append(f"digest collision: {relative} and {hashes[digest]} normalize alike")
            continue
        hashes[digest] = relative

    if not hashes:
        # D57. A register built from zero files would disable clause 3 while looking built.
        findings.append(f"no measure source files found under {measure_root}")
    return hashes, findings


def _import_names() -> tuple[dict[str, list[str]], list[str]]:
    """The real top-level import names of each denied distribution, at this pin."""
    findings: list[str] = []
    names: dict[str, list[str]] = {}
    for distribution in DENIED_DISTRIBUTIONS:
        try:
            metadata = importlib.metadata.distribution(distribution)
        except importlib.metadata.PackageNotFoundError:
            findings.append(f"{distribution} is not installed in the oracle image")
            continue

        top: set[str] = set()
        # top_level.txt when the distribution ships one; otherwise derive from RECORD, which
        # every installed distribution has. Deriving from the module name would just restate
        # the guess this function exists to check.
        declared = metadata.read_text("top_level.txt")
        if declared:
            top |= {line.strip() for line in declared.splitlines() if line.strip()}
        else:
            for file in metadata.files or ():
                head = str(file).split("/", 1)[0]
                if head and not head.endswith((".dist-info", ".pth")) and "." not in head:
                    top.add(head)
        if not top:
            findings.append(f"{distribution} declares no resolvable top-level import name")
        names[distribution] = sorted(top)
    return names, findings


def _vectors() -> tuple[list[dict[str, str]], list[str]]:
    if not VECTORS_PATH.is_file():
        return [], [f"{VECTORS_PATH} is absent; the cross-check cannot run"]
    document = json.loads(VECTORS_PATH.read_text(encoding="utf-8"))
    answered = [
        {"name": vector["name"], "normalized_sha256": _normalized(vector["input"])}
        for vector in document.get("vectors", [])
    ]
    if not answered:
        return [], ["the vector file carries no vectors; the cross-check would pass vacuously"]
    return answered, []


def main() -> int:
    hashes, hash_findings = _source_hashes()
    names, name_findings = _import_names()
    answered, vector_findings = _vectors()

    report: dict[str, Any] = {
        "oracle_commit_sha": __import__("os").environ.get("ORACLE_COMMIT_SHA", ""),
        "source_hashes": hashes,
        "import_names": names,
        "normalization_vectors": answered,
        "findings": hash_findings + name_findings + vector_findings,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    sys.stdout.write(json.dumps({"findings": report["findings"], "files": len(hashes)}) + "\n")
    # Findings do not fail the run: the driver outside decides, and it needs the report to
    # decide with. A non-zero exit here would delete the evidence of what went wrong.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
