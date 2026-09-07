---
status:        provisional
owner:         executable
enforcement:   ci-gate
evidence:      Reclassified from frozen by ADR-0063. Three D28 waivers landed against this fence's frozen status — ADR-0033, ADR-0040, and ADR-0050 once #78 reclassified it — tripping the three-waiver falsification clause at docs/tier0/operating-principles.md:6, which concludes that the principle is wrong rather than the situations. The fence itself is not wrong: tools/vaultgraph/extract/layout.py floors it at eighteen and surfaces layout-miss and layout-ghost anomalies that fire. What was wrong is freezing a list that tracks a directory tree, because the tree grows and a frozen list cannot follow it without a waiver each time.
falsifies_if:  A top-level directory exists in the tree and neither a fence line nor a committed layout-miss anomaly accounts for it; or a fence line names a directory that does not exist and no layout-ghost anomaly is committed for it; or a D28 waiver is spent against this fence at any point after ADR-0063, which would mean the reclassification did not remove the waiver source.
review_after:  Phase 2
---

# Structure Fence

The declared top-level layout. This is a **hand-authored** declaration checked against the
tree, not a generated view of it — a fence generated from the thing it fences can never
disagree with it, so `layout-miss` and `layout-ghost` could never fire and the check would
scan itself. It is `provisional` rather than `frozen` because the tree grows; it keeps its
`ci-gate` because the gate is what gives it value.

Split out of `docs/tier2/coding-standards.md` by ADR-0063 so that the fence can move as the
tree moves without dragging that document's strict-typing commitments — which remain frozen —
along with it.

## Structure

```
src/
  domain/        Pydantic trajectory and scenario schemas — the load-bearing abstraction
  metrics/       metric implementations; formulas pinned to citations
  provenance/    result stamping
  thresholds/    declared, cited, versioned config — never agent-authored
  ingest/        dataset adapters
  replay/        deterministic harness
  api/           FastAPI surface
  mission_control/  the operator read model — SELECT-only, agent-writable; the command
                    surface is harness/mission_control/ and is protected (ADR-0050)
tests/
  properties/    Hypothesis property tests over composed operations
  reference/     oracle reproduction fixtures
  heldout/       composed and perturbed criteria — never in agent context
migrations/
harness/         OUTSIDE the agent tree — CriterionRunner, egress canary, floor test
scripts/
docs/
.github/         CI — the five-job gate; protected
bench/           Phase −1 inference measurements — immutable per-seed records
deploy/          release machinery — identity-baked image, ledger, rollback
plan/            the plan-of-record mirror — sha256-pinned; history, not instruction
policy/          machine-readable tier 4 — allowlists, denylists, the protected set
tools/           vaultgraph and the generators — CI-gated, not the protected set
vault/           generated read model — byte-compared in CI; never hand-edited
projects/        one nested git repository per product Alfred builds — git-ignored subdirectories
_archive/        dead material superseded but kept for provenance — not the protected set
_templates/      blank templates instantiated by copy — never edited in place
orchestration/   protected topology source (ADR-0039) — hand-authored, palette-bound
stages/          numbered pipeline 01_s0 … 10_s9 — one folder per stage, evidence in output/exit.md
```

`harness/` sits outside the agent tree deliberately and is in the protected set. No file
under it is ever agent-writable.

