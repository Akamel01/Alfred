# Orchestration Canvas — Prototype

Throwaway artifact for wayfinder #13. Single HTML file, vanilla JS, zero deps, no CDN, no build.

## Open

- **Direct:** open `prototype/orchestration-canvas.html` via `file://` — renders, palette works, pan/zoom works. Save via download/clipboard fallback; File System Access picker is blocked on `file://` (opaque origin).
- **Full save:** `python3 -m http.server 8000` then open `http://localhost:8000/prototype/orchestration-canvas.html` — `showSaveFilePicker` available on Chromium desktop; Firefox/Safari fall through to download.
- No install step. Works offline after first load.

## Features

- Embedded `sample-topology.json` (8 nodes, 7 edges) + `node-palette.json` (21 kinds) via `script[type=application/json]`.
- Nodes: degree-scaled radius, label + kind, port dots per contract (east out, west in) colored by contract type.
- Edges: quadratic bezier with arrowhead + contract label; extra leading/trailing space label background for readability.
- Palette panel grouped by category (planning/execution/review/operator); items `draggable` → drop on canvas creates node at world position, grid snap 20px, collision nudge outward search.
- Drag-to-connect: pointerdown on output port → dashed preview follows cursor → compatible input ports (same contract) highlight with ring → release snaps → edge created with that contract (Ctrl/Cmd cycles if multiple legal between pair).
- Edge click cycles legal contracts for its endpoint pair; Esc cancels drag/selection; Del/Backspace deletes selected node (plus incident edges) or edge.
- Pan: drag empty canvas; zoom: wheel, +/- buttons/keys, fit button.
- Save: `Save` tries FS Access then download fallback; `Export` always downloads; `Copy JSON` clipboard; `Import` via file input. JSON shape matches `sample-topology.json`.
- Status bar shows node/edge counts; inspector shows selection details.

## Limitations (throwaway)

- Not production generator: no `tools/orchestration/gen_canvas.py`, no SVG export, no lint.
- No persistence of file handle in IndexedDB, no reopen-last-file.
- No multi-select, no marquee, no undo/redo, no minimap.
- No arrow key pan reuse (camera only via drag/wheel/buttons).
- `<` escaping only via JSON blocks; inline JS avoids innerHTML sinks but not formally scanned.
- Layout is manual placement only; no force simulation on load.
