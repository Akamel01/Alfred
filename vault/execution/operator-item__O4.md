---
kind: operator-item
id: "operator-item:O4"
title: "Phase 0 exit — **decision half spent** by ADR-0022 (2026-08-19), which narrowed along the ownership seam and dated the residue. Remaining, against ADR-0022's narrowed list: **P0-4** egress canary firi"
status: "open"
shape: "table-row"
due: "2026-10-07 (ADR-0022's residue date)"
number: "O4"
source: "docs/tier2/execution-order.md:393"
extractor: "stages"
aliases:
  - "O4"
  - "Phase 0 exit — **decision half spent** by ADR-0022 (2026-08-19), which narrowed along the "
generated: true
---

# Phase 0 exit — **decision half spent** by ADR-0022 (2026-08-19), which narrowed along the ownership seam and dated the residue. Remaining, against ADR-0022's narrowed list: **P0-4** egress canary firi

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier2/execution-order.md:393`

## Statement

Phase 0 exit — **decision half spent** by ADR-0022 (2026-08-19), which narrowed along the ownership seam and dated the residue. Remaining, against ADR-0022's narrowed list: **P0-4** egress canary firing against real enforcement (`nftables` default-drop in the host network namespace, not the probe alone); **P0-6** a recorded **D-production** restore (a green CI run is D-synthetic and proves the mechanism only); **P0-7** no unreviewed inspector patch enforces any of the above (tracked as O9). P0-1/2/3 were met at ADR-0022; **P0-5** byte-identical deterministic replay met by ADR-0025.

## Fields

| Field | Value |
|---|---|
| `blocks` | Everything |
