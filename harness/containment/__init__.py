"""Containment assertions: what the sandbox must prove before a run starts.

Inspector machinery (D20). Every assertion here is fail-closed, the probe erroring
included, and **`not_executed` is a failure and never a pass** (F25) — an unproven control
is a failed control.

The table lives in `docs/tier4/sandbox-specification.md`. What is here:

| Module | Assertions | Note |
|---|---|---|
| `egress.py` | C6 | canary plus the loopback control that stops it reading green |
| `oracle_absence.py` | C7 | four layers: closure, import probe, path scan, acquisition |
| `inside.py` | C8, C9, C12, C13 | no executor vocabulary needed, so written for real |
| `reassert.py` | C14 | the closed re-assertion set, after the agent stops |
| `patch_side.py` | C15 | the one control that faces the deliverable rather than the container |
| `shells.py` | C1, C2, C3, C5, C10 | blocked on O5; a shell never passes (ADR-0017) |
| `handle.py` | — | the one crossing to the shape `Worker.check_handle` reads |

**C4 and C11 are absent, and not because of O5.** Both compare against a run fingerprint
record that does not exist in this repository. Writing a shell whose only hole is "the
fingerprint" would put them on O5's worklist, where they do not belong.
"""
