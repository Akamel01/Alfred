# Lessons Learned — Orchestration Canvas Prototype (#13)

## What felt easy

- **Camera reuse:** copying `tools/vaultgraph/render/camera.py` JS verbatim gave pan/zoom world mapping for free; fit/zoomAt/apply covered 80% of viewport math. No changes needed.
- **Single-file HTML + JSON-in-script-block:** matches vault precedent, trivial to open on `file://` and `localhost`, no build or CORS issues.
- **Palette drag-to-create:** HTML5 `draggable` + `dataTransfer` + `camera.toWorld` + 20px grid snap is small code; collision nudge via outward spiral cheap and sufficient.
- **Edge rendering:** quadratic bezier off midpoint normal + arrowhead triangle reads well without layout-aware routing.

## What felt hard

- **Port model vs sample data:** palette declares per-contract ports (`out:["delegates-to"]`) while `sample-topology.json` uses generic `out`/`in` strings; bridging required mapping contract→port rather than literal port name. Spec should freeze whether `source_port`/`target_port` equal contract id or generic side.
- **Compatibility semantics:** spec says each (source-kind,target-kind) maps to exactly one legal contract, but palette intersections can yield 0, 1, or 2 legal types (e.g. `drafter` hands-off-to → `reviewer`? only 1). Drag-to-connect highlight must decide: per-contract dot (1 dot per contract) vs single dot with cycling. Per-contract dots chosen here; Ctrl-cycle fallback kept for generic-dot future.
- **Save fallbacks on `file://`:** FS Access blocked on opaque origin; clipboard requires secure context; download is the only reliable `file://` path. UX must not promise "Save" overwrite on `file://` — should label button Export-like on that origin.
- **Hit testing at scale:** port circles 6px/ scale need enlarged hit radius; bezier edge hit requires segment sampling, not straight-line distance.

## UX rules needing spec freeze

1. **Port naming:** `source_port`/`target_port` values — contract id vs generic `out`/`in`. Lint `TOP003/004` depends on this.
2. **Legal contract resolution:** single default per pair vs per-port choice; when to allow multiple edges between same nodes with different contracts vs forbidding duplicates.
3. **Cycle rules:** spec lists cycles forbidden for 3 of 4 types — canvas currently allows any edge creation; enforce or warn?
4. **Grid + collision policy:** snap always vs only on drop; nudge radius limit; whether edges should auto-route around nodes.

## Recommendation for production generator

- Keep camera verbatim, keep single-file output, keep palette embedded.
- Add IndexedDB handle persistence for reopen-last (Chromium) and make Save button wording origin-aware (`Save As…` vs `Download`).
- Implement lint parity: reuse `legalContracts()` in both canvas (highlight) and `scripts/lint_topology.py` (error) so compatibility cannot drift.
- Freeze port naming to contract ids before building `tools/orchestration/gen_canvas.py`; migrate `sample-topology.json` ports to contract ids at that time.
- Add force-simulation toggle for initial auto-layout of imported topologies with no positions.
