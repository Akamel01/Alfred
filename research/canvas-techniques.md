# Canvas Technique Survey

**Ticket:** #10 (wayfinder:research)
**Branch:** `research/canvas-techniques`
**Date:** 2026-08-26

---

## 1. Pointer Event Handling — Existing vs. Needed

### What `script.py` Already Does (Lines 311-372)

**`atPoint(event)` (L311-320):** Hit-testing against nodes
- Converts pointer event to world coordinates via `camera.toWorld()`
- Iterates all visible nodes, finds closest within `radiusOf(n) + 7/scale`
- Returns node or null

**Pointer State Machine (L322-372):**
```javascript
// pointerdown → sets dragging={x,y,moved:false}, captures pointer
// pointermove → if dragging: pan camera; else: hover hit-test → cursor change
// pointerup → if not moved: select(node); else: pan done
// pointerleave → cancel drag
// wheel → zoomAt(cursor, factor) with preventDefault
// keydown → Arrow keys pan; Escape deselects
```

**Key Patterns Reusable:**
- `camera.toWorld()` — world coordinates from pointer events (L41-47 in camera.py)
- `dragging.moved` threshold (3px) — distinguishes click from drag
- `pointerCapture` — ensures drag continues outside canvas
- Hover state in `focusState.hover` — drives cursor + redraw
- `select(node)` — single selection, opens inspector, deselect on Escape

### What Drag-Connect Needs (Gaps)

| Need | Missing From Current | Implementation Hint |
|------|---------------------|---------------------|
| **Port hit-testing** | Nodes only, no ports | Add port positions to node render data; hit-test against port circles |
| **Drag preview line** | None | On `pointerdown` on output port → `dragging = {type:'connect', fromPort, fromNode, previewLine}` |
| **Compatible port highlighting** | None | On drag move: compute compatible target ports → add `hover: true` to their render data |
| **Snap on release** | None | On `pointerup` over compatible target port → create edge with default contract |
| **Edge type cycling** | None | Click edge → cycle through legal types for that (source,target) pair |
| **Multi-select** | Single select only | Shift+click or marquee → `focusState.selected` becomes `Set` |

---

## 2. Zoom/Pan Math — Reusable Core

### Camera Module (camera.py — 98 lines)

**Transform (L35-38):**
```javascript
apply(ctx) {
  ctx.translate(tx, ty);
  ctx.scale(scale, scale);
}
```

**World↔Screen (L41-47):**
```javascript
toWorld(event, element) {
  const rect = element.getBoundingClientRect();
  return { x: (event.clientX - rect.left - tx) / scale,
           y: (event.clientY - rect.top - ty) / scale };
}
```

**Pan (L65):**
```javascript
panBy(dx, dy) { tx += dx; ty += dy; }
```

**Zoom at Point (L68-73):**
```javascript
zoomAt(px, py, factor) {
  const next = Math.min(6, Math.max(0.18, scale * factor));
  tx = px - (px - tx) * (next / scale);
  ty = py - (py - ty) * (next / scale);
  scale = next;
}
```

**Fit (L49-58):** Trimmed extent (1% outliers trimmed), 90px margin, max scale 2.4

**Tween Animation (L77-95):** 380ms cubic easing to target node+scale, cancellable

### Reusable for Prototype
- **All of camera.py** — copy verbatim, it's self-contained
- Add: `constrainToBounds()` for palette panel / toolbar collision
- Add: `zoomToFit(nodes)` variant for "fit selection"

---

## 3. Node Rendering — Extension Points

### Current Render (script.py L159-187)
```javascript
shown.forEach(n => {
  ctx.globalAlpha = lit ? 1 : 0.10;
  ctx.beginPath();
  ctx.arc(n.x, n.y, radiusOf(n) + (chosen ? 2 : 0), 0, 2π);
  ctx.fillStyle = chosen ? ground : colourOf(n);
  ctx.fill();
  ctx.strokeStyle = chosen ? colourOf(n) : ground;
  ctx.stroke();
});
```
- `radiusOf(node)` = `4 + min(13, sqrt(degree) * 2.6)` (L61)
- Selected node inverts: ground fill + kind ring (L165-170)
- Labels only at `scale > 0.85 || focus` (L176-187)

### Extension for Ports
**Port positions** need to be computed and stored on node render object:
```javascript
// During render, compute and cache port positions
function computePortPositions(node) {
  const r = radiusOf(node);
  const ports = node.kindData.ports; // from palette
  const outPorts = ports.out || [];
  const inPorts = ports.in || [];
  // Distribute evenly around circle
  outPorts.forEach((p, i) => {
    const angle = (i / outPorts.length) * 2π - π/2;
    p.x = node.x + (r + 8) * Math.cos(angle);
    p.y = node.y + (r + 8) * Math.sin(angle);
    p.side = 'out';
  });
  inPorts.forEach((p, i) => {
    const angle = (i / inPorts.length) * 2π + π/2;
    p.x = node.x + (r + 8) * Math.cos(angle);
    p.y = node.y + (r + 8) * Math.sin(angle);
    p.side = 'in';
  });
  return { out: outPorts, in: inPorts };
}
```
**Render ports** as small circles on node perimeter (hit radius ~10px scaled).

---

## 4. Edge Rendering — Extension Points

### Current Render (script.py L144-155)
```javascript
view.links().forEach(l => {
  ctx.beginPath();
  ctx.setLineDash(dashes[l.e.confidence]...);
  ctx.strokeStyle = palette[l.e.confidence];
  ctx.globalAlpha = lit ? 0.62 : 0.05;
  ctx.lineWidth = (lit && focus ? 1.8 : 0.8) / scale;
  ctx.moveTo(l.s.x, l.s.y);
  ctx.lineTo(l.t.x, l.t.y);
  ctx.stroke();
});
```
- Straight lines only
- Dashes encode confidence (structural/derived/prose)
- Alpha/lit based on focus + neighbourhood

### Needed for Prototype
| Feature | Implementation |
|---------|----------------|
| **Curved edges** (avoid node overlap) | Quadratic Bezier with control point offset perpendicular to line midpoint |
| **Arrowheads** | Draw triangle at target end: `ctx.moveTo(t.x, t.y); ctx.lineTo(...)` |
| **Edge labels** | Contract type at midpoint, rotated along line |
| **Hit-testing** | Distance from point to line segment < threshold (scaled) |
| **Port-to-port** | Source = output port position, Target = input port position (not node center) |

---

## 5. Drag-to-Connect UX — Design

### State Machine
```
IDLE
  └─ pointerdown on output port → DRAGGING_PREVIEW
DRAGGING_PREVIEW
  ├─ pointermove → update preview line end = cursor world pos
  │                highlight compatible input ports (port.hover = true)
  ├─ pointerup over compatible input port → create edge, IDLE
  ├─ pointerup elsewhere → cancel, IDLE
  └─ Escape → cancel, IDLE
```

### Compatible Port Highlighting
- On drag start: compute all target ports where `isCompatible(sourceKind, sourcePort, targetKind, targetPort)`
- Set `port.hover = true` on those; render with glow/highlight ring
- On drag move: update preview line end = `camera.toWorld(event)`

### Default Contract by Port Pair
```javascript
function defaultContract(sourceKind, sourcePort, targetKind, targetPort) {
  const compat = COMPATIBILITY[sourceKind]?.[sourcePort]?.[targetKind]?.[targetPort];
  return compat?.[0] || null; // first legal type
}
```

---

## 6. Node Creation — Palette Panel

### Palette Data Source
- Load `policy/node-palette.json` embedded in HTML (like graph-data)
- Group by `category` for UI sections

### Drag-from-Palette
```javascript
// Palette item: <div draggable="true" data-kind="code-writer">...</div>
// ondragstart: e.dataTransfer.setData('application/x-node-kind', kind)
// Canvas ondragover: e.preventDefault() (allow drop)
// Canvas ondrop: const kind = e.dataTransfer.getData('application/x-node-kind')
//                createNodeAt(kind, camera.toWorld(e))
```

### Auto-Layout Assist
- Grid snap: round position to 20px grid
- Avoid overlap: if drop position collides, nudge to nearest free slot
- Initial edges: none (operator connects manually)

---

## 7. Code Reuse Summary

| Module | Reuse Strategy |
|--------|----------------|
| `camera.py` | **Full copy** — self-contained, 98 lines |
| `layout.py` | **Adapt** — force sim for auto-layout on load; not for live editing |
| `view.py` | **Full copy** — filter predicates (kind, query, relations) |
| `script.py` BODY | **Fork & extend** — add port hit-testing, drag-connect, edge curves, arrowheads, palette panel |
| `PRELUDE` | **Copy** — data loading pattern, confidence hues, CSS tokens |

---

## 8. Prototype File Structure

```
prototype/
├── orchestration-canvas.html    # Single file: HTML + embedded JS + CSS
├── sample-topology.json         # Hand-written fixture
└── README.md                    # How to run
```

**HTML Structure:**
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Orchestration Canvas</title>
  <style>/* inlined CSS tokens + canvas + rail + palette */</style>
</head>
<body>
  <canvas id="stage-canvas" tabindex="0"></canvas>
  <div id="rail">...</div>           <!-- filters, palette panel -->
  <div id="inspector">...</div>      <!-- node/edge details -->
  <script type="application/json" id="topology-data">...</script>
  <script type="application/json" id="palette-data">...</script>
  <script>/* inlined JS: camera + layout + view + extended BODY */</script>
</body>
</html>
```

---

## 9. Gaps to Implement (Prototype Scope)

| Gap | Priority | Effort |
|-----|----------|--------|
| Port hit-testing + positions | High | Medium |
| Drag-preview line + compatible port highlight | High | Medium |
| Snap-to-port on release + edge creation | High | Medium |
| Arrowheads + curved edges | Medium | Low |
| Edge label (contract type) | Medium | Low |
| Palette panel + drag-create | High | Medium |
| Save/load via FS Access API + fallback | High | Medium |
| Keyboard: Del/Escape | Low | Trivial |
| Grid snap + collision avoid on create | Low | Low |

---

## 10. Recommendations for Prototype Ticket (#13)

1. **Start from `script.py` fork** — not from scratch
2. **Embed everything** — single HTML file, no build
3. **Use `browser-fs-access` ponyfill** (from research #9) for save/load
3. **Sample topology** with 8-10 nodes covering all 4 contract types
4. **Test matrix**: Chrome (full), Firefox (fallback), Safari (fallback)
5. **Lessons-learned doc** — what felt easy/hard, what UX rules need spec