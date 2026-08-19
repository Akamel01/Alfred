"""Containment assertions: what the sandbox must prove before a run starts.

Inspector machinery (D20). Every assertion here is fail-closed, the probe erroring
included, and **`not_executed` is a failure and never a pass** (F25) — an unproven control
is a failed control.

The table lives in `docs/tier4/sandbox-specification.md`. What is here:

| Module | Assertions | Note |
|---|---|---|
| `egress.py` | C6 | canary plus the loopback control that stops it reading green |
| `image.py` | C4 | the runtime image digest, against the run fingerprint; runs outside |
| `lane.py` | C11 | the serving lane, wrapping `harness/lane/lane_fingerprint.py` |
| `oracle_absence.py` | C7 | four layers: closure, import probe, path scan, acquisition |
| `inside.py` | C8, C9, C12, C13 | no executor vocabulary needed, so written for real |
| `reassert.py` | C14 | the closed re-assertion set, after the agent stops |
| `patch_side.py` | C15 | the one control that faces the deliverable rather than the container |
| `shells.py` | C1, C2, C3, C5, C10, C16, C17 | O5 discharged (ADR-0018); a shell never passes with a hole unread (ADR-0017) |
| `handle.py` | — | the one crossing to the shape `Worker.check_handle` reads |

**C4 and C11 were absent, and not because of O5.** Both compare against a run fingerprint
record that did not exist in this repository, so writing a shell whose only hole was "the
fingerprint" would have put them on O5's worklist, where they did not belong. The record is
now `harness/fingerprint/record.py` and both are written (ADR-0020). One conjunct is still
unread and says so rather than passing: the serving API does not publish the parallel slot
count, so C11 reports `not_executed` unless the count is supplied from outside it.
"""
