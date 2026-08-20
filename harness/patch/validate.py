"""Validates a patch before anything touches a tree. Runs outside the container.

A2: the container holds no VCS credential and emits a patch file to a mounted volume; a
separate uncontaminated process validates it and opens the pull request. The deliverable
channel and the exfiltration channel must not be the same channel — AsyncAPI is the worked
example, where a pull request opened at 05:08 was followed by a token exfiltrated at 05:16.

**This module reads the diff. It never applies it.** Rejection happens before any byte
reaches a working tree, because a check that runs after application is a check whose
failure mode is a dirty tree, and because `git apply` following a symlink is exactly the
escape the path rules exist to prevent.

---------------------------------------------------------------- what it refuses, and why

**Protected paths (D20).** The set is policy configuration, not code:
`policy/protected-paths.json`, versioned, and under `policy/` itself — the gate protects
its own policy file. That is the CVE-2025-53773 shape, where an agent wrote
`"chat.tools.autoApprove": true` into `.vscode/settings.json` and disabled its own
approval gate because the gate lived in a file it could write. The human-readable form is
`docs/tier4/protected-paths-policy.md`, bound to the file by `test_protected_set.py`
in both directions (ADR-0029). An agent editing the judge collapses every control
beneath it at once, silently, with the tests green — because the tests are downstream of
the edit.

**Invisible characters (A10).** Zero-width, bidi and control characters outside declared
string literals. TrapDoor planted `CLAUDE.md` and `.cursorrules` carrying zero-width
encoded instructions and opened pull requests against LangChain, MetaGPT and OpenHands.
GitHub flags bidi and does **not** flag zero-width, so a reviewer looking at the rendered
diff sees nothing. Scanned on added lines only: context lines are already in the tree, and
flagging them would report the same finding on every later patch.

**Import hooks and instruction files.** `conftest.py`, `sitecustomize.py`, `.pth` files
and agent-instruction files are the two channels that change behaviour without changing
any code the reviewer is reading. BenchJack forced 100% resolve on all 500 SWE-bench
Verified instances with a seven-line `conftest.py`, touching no test file.

**Symlinks and traversal.** A patch creating a symlink, or naming a path that leaves the
repository, is refused on the name alone. A symlink names one file and delivers another.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Final, cast

# The protected set as policy configuration (ADR-0029). The file is under `policy/` —
# a protected prefix — so the gate protects its own policy file.
DEFAULT_PROTECTED_PATH: Final = (
    Path(__file__).resolve().parents[2] / "policy" / "protected-paths.json"
)


class ProtectedSetError(RuntimeError):
    """The protected set could not be loaded. Fail closed: no set, no dispatch (F25).

    An unreadable policy is treated exactly as a mismatched one — the caller must not be
    able to tell them apart by whether a value came back.
    """


@dataclass(frozen=True)
class ProtectedEntry:
    path: str
    contains: str


@dataclass(frozen=True)
class ProtectedSet:
    version: int
    prefixes: tuple[ProtectedEntry, ...]
    files: tuple[ProtectedEntry, ...]

    @property
    def all_paths(self) -> frozenset[str]:
        return frozenset(e.path for e in (*self.prefixes, *self.files))


def load_protected_set(path: Path = DEFAULT_PROTECTED_PATH) -> ProtectedSet:
    """Read the protected set, refusing every way it can be missing.

    Failing open is not an option for the file a gate reads: a gate that cannot state its
    own policy has no policy. D57 closes the last loophole — a set that enumerates nothing
    protects nothing, and passes everything it exists to stop.
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ProtectedSetError(
            f"{path} is unreadable ({exc}); refusing without a protected set"
        ) from exc
    try:
        parsed: object = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ProtectedSetError(
            f"{path} is not valid JSON ({exc}); refusing without a protected set"
        ) from exc
    if not isinstance(parsed, dict):
        raise ProtectedSetError(f"{path} is not a JSON object; refusing")

    # `json.loads` yields an untyped dict. The casts — backed by the isinstance guard
    # above and the per-field checks below — type it as `dict[str, object]` so every
    # value is `object` until an isinstance check narrows it; no untyped value reaches
    # a decision.
    data = cast("dict[str, object]", parsed)
    version: object = data.get("version")
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        raise ProtectedSetError(f"{path} carries no usable version ({version!r}); refusing")

    def entries(key: str) -> tuple[ProtectedEntry, ...]:
        rows: object = data.get(key)
        if not isinstance(rows, list):
            raise ProtectedSetError(f"{path} is missing {key!r}; refusing")
        typed_rows = cast("list[object]", rows)
        out: list[ProtectedEntry] = []
        seen: set[str] = set()
        for row in typed_rows:
            if not isinstance(row, dict):
                raise ProtectedSetError(f"{path} {key} entry is not an object; refusing")
            row_map = cast("dict[str, object]", row)
            entry_path: object = row_map.get("path")
            contains: object = row_map.get("contains")
            if not isinstance(entry_path, str) or not entry_path.strip():
                raise ProtectedSetError(f"{path} {key} entry carries no path; refusing")
            if not isinstance(contains, str) or not contains.strip():
                raise ProtectedSetError(
                    f"{path} {key} entry for {entry_path!r} carries no rationale; refusing"
                )
            if ".." in entry_path.split("/"):
                raise ProtectedSetError(f"{path} entry {entry_path!r} traverses; refusing")
            if key == "prefixes" and not entry_path.endswith("/"):
                raise ProtectedSetError(
                    f"{path} prefix {entry_path!r} does not end in '/'; a prefix that is a "
                    "file matches one path and is probably a typo"
                )
            if key == "files" and entry_path.endswith("/"):
                raise ProtectedSetError(
                    f"{path} file entry {entry_path!r} is a directory; refusing"
                )
            if entry_path in seen:
                raise ProtectedSetError(
                    f"{path} names {entry_path!r} twice; one path, one entry"
                )
            seen.add(entry_path)
            out.append(ProtectedEntry(entry_path, contains))
        return tuple(out)

    prefixes = entries("prefixes")
    files = entries("files")
    if not prefixes and not files:
        raise ProtectedSetError(
            f"{path} enumerates nothing. A set that protects nothing passes everything, "
            "and a gate that passes everything is a formality (D57)"
        )
    return ProtectedSet(version=version, prefixes=prefixes, files=files)


# Behaviour-changing files that are not code the reviewer reads as code.
IMPORT_HOOK_NAMES: Final = frozenset({"conftest.py", "sitecustomize.py", "usercustomize.py"})
IMPORT_HOOK_SUFFIXES: Final = (".pth",)

# Files whose content is read as instructions by an agent, by a tool, or by both.
INSTRUCTION_FILE_NAMES: Final = frozenset(
    {"CLAUDE.md", "AGENTS.md", ".cursorrules", ".windsurfrules", "GEMINI.md", ".clinerules"}
)

# git's file mode for a symbolic link.
SYMLINK_MODE: Final = "120000"

# Zero-width and bidi-control code points. Named individually rather than by category
# because `Cf` also contains benign formatting, and a category-wide ban would reject
# legitimate text while teaching everyone to bypass the check.
INVISIBLE_CODEPOINTS: Final = frozenset(
    {
        "​", "‌", "‍", "⁠", "﻿",   # zero width
        "‎", "‏",                                   # LRM / RLM
        "‪", "‫", "‬", "‭", "‮",     # embedding / override
        "⁦", "⁧", "⁨", "⁩",               # isolates
        "­",                                             # soft hyphen
    }
)

_DIFF_GIT = re.compile(r'^diff --git (?P<a>.+?) (?P<b>.+)$')
_NEW_MODE = re.compile(r"^(?:new file mode|new mode) (?P<mode>\d{6})$")
_ADDED = re.compile(r"^\+(?!\+\+ )")


class PatchRefused(RuntimeError):
    """The patch does not qualify. Nothing is applied and no pull request is opened."""


@dataclass(frozen=True)
class Finding:
    rule: str
    path: str
    detail: str
    line_number: int | None = None


@dataclass
class ValidationReport:
    paths: list[str] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    added_lines_scanned: int = 0

    @property
    def clean(self) -> bool:
        return not self.findings


def _unquote(raw: str) -> str:
    """git quotes paths containing unusual bytes as a C string. Decode before deciding.

    Load-bearing rather than cosmetic: a protected path written as `"harness/\\150.py"`
    would not prefix-match `harness/` in its quoted form, so a check running on the raw
    token would pass it. Decide on the decoded name or do not decide at all.
    """
    if not (raw.startswith('"') and raw.endswith('"')):
        return raw
    body = raw[1:-1]
    out = bytearray()
    i = 0
    while i < len(body):
        if body[i] == "\\" and i + 1 < len(body):
            nxt = body[i + 1]
            if nxt.isdigit():
                out.append(int(body[i + 1 : i + 4], 8))
                i += 4
                continue
            out.extend({"n": b"\n", "t": b"\t", '"': b'"', "\\": b"\\"}.get(nxt, nxt.encode()))
            i += 2
            continue
        out.extend(body[i].encode("utf-8"))
        i += 1
    return out.decode("utf-8", errors="replace")


def _strip_prefix(token: str) -> str | None:
    """`a/path` and `b/path` become `path`. `/dev/null` becomes None."""
    token = _unquote(token)
    if token == "/dev/null":
        return None
    if token.startswith(("a/", "b/")):
        return token[2:]
    return token


def _path_findings(path: str, protected: ProtectedSet) -> list[Finding]:
    findings: list[Finding] = []
    pure = PurePosixPath(path)

    if pure.is_absolute():
        findings.append(Finding("absolute-path", path, "a patch may not name an absolute path"))
    if ".." in pure.parts:
        findings.append(
            Finding("traversal", path, "the path leaves the repository through a parent reference")
        )
    for entry in protected.prefixes:
        if path.startswith(entry.path) or f"{path}/" == entry.path:
            findings.append(
                Finding(
                    "protected-path",
                    path,
                    f"{entry.path} is protected ({entry.contains}); the set is policy "
                    "configuration and never agent-writable (D20)",
                )
            )
    for entry in protected.files:
        if path == entry.path:
            findings.append(
                Finding(
                    "protected-path",
                    path,
                    f"{entry.path} is protected ({entry.contains}); the set is policy "
                    "configuration and never agent-writable (D20)",
                )
            )
    if pure.name in IMPORT_HOOK_NAMES or pure.name.endswith(IMPORT_HOOK_SUFFIXES):
        findings.append(
            Finding(
                "import-hook",
                path,
                "collection and import configuration comes from trusted provenance, never "
                "from the tree under test",
            )
        )
    if pure.name in INSTRUCTION_FILE_NAMES:
        findings.append(
            Finding(
                "instruction-file",
                path,
                "content here is read as instructions by a later agent; it is the D32 "
                "register's business, not a patch's",
            )
        )
    return findings


def _invisible_findings(path: str, line_number: int, text: str) -> list[Finding]:
    findings: list[Finding] = []
    for index, char in enumerate(text):
        if char in INVISIBLE_CODEPOINTS:
            findings.append(
                Finding(
                    "invisible-character",
                    path,
                    f"U+{ord(char):04X} ({unicodedata.name(char, 'unnamed')}) at column {index}",
                    line_number,
                )
            )
        elif char != "\t" and unicodedata.category(char) == "Cc":
            findings.append(
                Finding(
                    "control-character",
                    path,
                    f"U+{ord(char):04X} at column {index}",
                    line_number,
                )
            )
    return findings


def validate_patch(diff_text: str) -> ValidationReport:
    """Read a unified diff and report every reason it must not be applied.

    Every finding is collected rather than raising on the first: a reviewer handed one
    refusal at a time re-runs the gate N times and learns the rule set by exhaustion,
    which is how a rule set gets treated as an obstacle instead of a boundary.

    The protected set loads per call and fails closed: a missing or corrupt policy file
    raises `ProtectedSetError` rather than narrowing the set (F25, D57).
    """
    protected = load_protected_set()
    report = ValidationReport()
    current: str | None = None
    line_number = 0

    for raw_line in diff_text.splitlines():
        header = _DIFF_GIT.match(raw_line)
        if header:
            line_number = 0
            for token in (header.group("a"), header.group("b")):
                path = _strip_prefix(token)
                if path is None:
                    continue
                current = path
                if path not in report.paths:
                    report.paths.append(path)
                    report.findings.extend(_path_findings(path, protected))
            continue

        mode = _NEW_MODE.match(raw_line)
        if mode and mode.group("mode") == SYMLINK_MODE and current:
            report.findings.append(
                Finding("symlink", current, "a symlink names one file and delivers another")
            )
            continue

        if raw_line.startswith("@@"):
            line_number = 0
            continue

        if current and _ADDED.match(raw_line):
            line_number += 1
            report.added_lines_scanned += 1
            report.findings.extend(_invisible_findings(current, line_number, raw_line[1:]))

    return report


def require_clean(diff_text: str) -> ValidationReport:
    """Validate and refuse. The vacuity guard is here, not in the caller.

    A patch that parsed to zero files is refused rather than passed. An empty report and a
    clean report are the same object, and the difference between "nothing was wrong" and
    "nothing was read" is the difference between a gate and a formality.

    A protected set that fails to load raises `ProtectedSetError` rather than falling
    back: a gate that cannot state its own policy has no policy, and no dispatch runs on
    it.
    """
    report = validate_patch(diff_text)
    if not report.paths:
        raise PatchRefused(
            "no file was parsed out of the patch. A validator that read nothing reports "
            "the same result as one that found nothing wrong."
        )
    if report.findings:
        summary = "; ".join(f"{f.rule} {f.path}: {f.detail}" for f in report.findings[:8])
        raise PatchRefused(f"{len(report.findings)} finding(s): {summary}")
    return report
