"""The script, inlined at build time.

**The read model is untrusted in the browser (ADR-0008).** Every value that reaches the page
goes through `textContent` or a created text node. There is no `innerHTML` anywhere in this
file and no string concatenated into markup -- a generated note's body is repository text, and
repository text is not markup.

**Confidence is encoded twice**, in hue and in stroke style. A dashed line is a mechanical
match inside a comment span; a dotted line is a guess from free prose. Colour alone would lose
that distinction in greyscale and for a colourblind reader, and it is the most important thing
this graph has to say.

**The layout is computed once from a fixed seed, then frozen.** A live simulation would keep
the page busy forever and settle somewhere different on every load. The graph is static data,
so its layout is too.
"""

from __future__ import annotations

JS = r"""
'use strict';

// The read model is untrusted in the browser (ADR-0008). Every value that reaches the page
// goes through textContent or a created text node. No markup-writing sink appears below, and
// no string is concatenated into markup.
//
// test_render.py scans this whole block for those sink names, comments included. Naming one
// here -- even to say it is absent -- reds the suite. That is deliberate: a scan that skipped
// comments would need a JavaScript parser to be right about which text is a comment, and the
// cost of being over-strict is one reworded sentence, visibly.
const DATA = JSON.parse(document.getElementById('graph-data').textContent);
const NODES = DATA.nodes;
const EDGES = DATA.edges;
const byId = new Map(NODES.map(n => [n.id, n]));

const CONFIDENCE = [
  ['structural', 'parsed from a fixed grammar', []],
  ['derived', 'matched inside a comment or docstring', [5, 3]],
  ['prose', 'read from free text, unverified', [1.5, 3]],
];

const canvas = document.getElementById('stage-canvas');
const ctx = canvas.getContext('2d');
const inspector = document.getElementById('inspector');

const state = {
  kinds: new Set(NODES.map(n => n.kind)),
  confidences: new Set(CONFIDENCE.map(c => c[0])),
  query: '',
  selected: null,
  hover: null,
  tx: 0, ty: 0, scale: 1,
};

function token(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

// ---- layout ------------------------------------------------------------
// Seeded, deterministic placement then a fixed number of relaxation ticks. A live simulation
// would keep the page busy forever and would settle somewhere different on every load; the
// graph is static data, so the layout should be too.
let seed = 20260818;
function random() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}

const KIND_ORDER = [...new Set(NODES.map(n => n.kind))].sort();
NODES.forEach(n => {
  const ring = KIND_ORDER.indexOf(n.kind);
  const angle = random() * Math.PI * 2;
  const radius = 140 + ring * 74 + random() * 60;
  n.x = Math.cos(angle) * radius;
  n.y = Math.sin(angle) * radius;
  n.vx = 0; n.vy = 0;
  n.degree = 0;
});
const links = EDGES
  .map(e => ({ e, s: byId.get(e.src), t: byId.get(e.dst) }))
  .filter(l => l.s && l.t && l.s !== l.t);
links.forEach(l => { l.s.degree += 1; l.t.degree += 1; });

// A third of this graph is connected to nothing: ADRs no code cites, amendments naming no
// decision, risks and kill criteria that only prose refers to. Mixing them into the
// simulation buries the observation in a hairball and lets one of them wander off and
// collapse the view. They are parked on their own arc instead, which states the fact.
const connected = NODES.filter(n => n.degree > 0);
const isolated = NODES.filter(n => n.degree === 0);

function relax(steps) {
  for (let step = 0; step < steps; step += 1) {
    const cooling = 1 - step / steps;
    for (let i = 0; i < connected.length; i += 1) {
      const a = connected[i];
      for (let j = i + 1; j < connected.length; j += 1) {
        const b = connected[j];
        let dx = b.x - a.x, dy = b.y - a.y;
        let d2 = dx * dx + dy * dy;
        if (d2 < 0.01) { dx = 0.1; dy = 0.1; d2 = 0.02; }
        if (d2 > 250000) continue;
        const force = 2600 / d2;
        const d = Math.sqrt(d2);
        a.vx -= (dx / d) * force; a.vy -= (dy / d) * force;
        b.vx += (dx / d) * force; b.vy += (dy / d) * force;
      }
    }
    links.forEach(({ s, t }) => {
      const dx = t.x - s.x, dy = t.y - s.y;
      const d = Math.sqrt(dx * dx + dy * dy) || 1;
      // Hubs get longer spokes: a module cited by twelve decisions should sit away from them,
      // not inside the cloud they form.
      const rest = 60 + Math.min(70, (s.degree + t.degree) * 1.6);
      const force = (d - rest) * 0.05;
      s.vx += (dx / d) * force; s.vy += (dy / d) * force;
      t.vx -= (dx / d) * force; t.vy -= (dy / d) * force;
    });
    connected.forEach(n => {
      // Gravity is weak: the links already hold these nodes, and a strong pull collapses
      // low-degree ones into an unreadable core.
      const pull = n.degree > 2 ? 0.0026 : 0.0045;
      n.vx -= n.x * pull; n.vy -= n.y * pull;
      const speed = Math.hypot(n.vx, n.vy);
      if (speed > 60) { n.vx = (n.vx / speed) * 60; n.vy = (n.vy / speed) * 60; }
      n.x += n.vx * cooling; n.y += n.vy * cooling;
      n.vx *= 0.82; n.vy *= 0.82;
    });
  }
}
relax(420);

// Park the unrelated on a ring outside whatever the simulation settled to, grouped by kind so
// the arc reads as a margin rather than a scatter.
(function parkIsolated() {
  const reach = connected.length
    ? Math.max(...connected.map(n => Math.hypot(n.x, n.y))) : 200;
  const radius = reach + 130;
  const ordered = [...isolated].sort((a, b) =>
    (a.kind + a.id).localeCompare(b.kind + b.id));
  ordered.forEach((n, index) => {
    const angle = (index / Math.max(1, ordered.length)) * Math.PI * 2 - Math.PI / 2;
    n.x = Math.cos(angle) * radius;
    n.y = Math.sin(angle) * radius;
  });
})();

// ---- filtering ---------------------------------------------------------

function matches(node) {
  if (!state.kinds.has(node.kind)) return false;
  if (!state.query) return true;
  const q = state.query.toLowerCase();
  return node.title.toLowerCase().includes(q) || node.id.toLowerCase().includes(q);
}
function visibleNodes() { return NODES.filter(matches); }
function visibleLinks() {
  const shown = new Set(visibleNodes().map(n => n.id));
  return links.filter(l =>
    state.confidences.has(l.e.confidence) && shown.has(l.s.id) && shown.has(l.t.id));
}

// ---- drawing -----------------------------------------------------------

function radiusOf(node) { return 3 + Math.min(6, Math.sqrt(node.degree)); }

function fit() {
  const shown = visibleNodes();
  if (!shown.length) return;
  // Trimmed extent, not min/max. A single outlier should cost a little clipping at the edge,
  // never the readability of everything else.
  const trim = values => {
    const sorted = [...values].sort((a, b) => a - b);
    const cut = Math.floor(sorted.length * 0.01);
    return [sorted[cut], sorted[sorted.length - 1 - cut]];
  };
  const [minX, maxX] = trim(shown.map(n => n.x));
  const [minY, maxY] = trim(shown.map(n => n.y));
  const xs = [minX, maxX], ys = [minY, maxY];
  const w = canvas.clientWidth, h = canvas.clientHeight;
  const spanX = Math.max(...xs) - Math.min(...xs) || 1;
  const spanY = Math.max(...ys) - Math.min(...ys) || 1;
  state.scale = Math.min(w / (spanX + 90), h / (spanY + 90), 2.4);
  state.tx = w / 2 - ((Math.max(...xs) + Math.min(...xs)) / 2) * state.scale;
  state.ty = h / 2 - ((Math.max(...ys) + Math.min(...ys)) / 2) * state.scale;
}

function draw() {
  const ratio = window.devicePixelRatio || 1;
  const w = canvas.clientWidth, h = canvas.clientHeight;
  if (canvas.width !== w * ratio || canvas.height !== h * ratio) {
    canvas.width = w * ratio; canvas.height = h * ratio;
  }
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  ctx.clearRect(0, 0, w, h);
  ctx.save();
  ctx.translate(state.tx, state.ty);
  ctx.scale(state.scale, state.scale);

  const focus = state.selected || state.hover;
  const near = new Set();
  if (focus) {
    near.add(focus.id);
    links.forEach(l => {
      if (l.s.id === focus.id) near.add(l.t.id);
      if (l.t.id === focus.id) near.add(l.s.id);
    });
  }

  const palette = {
    structural: token('--structural'),
    derived: token('--derived'),
    prose: token('--prose'),
  };
  const dashes = Object.fromEntries(CONFIDENCE.map(c => [c[0], c[2]]));

  visibleLinks().forEach(l => {
    const lit = !focus || near.has(l.s.id) && near.has(l.t.id);
    ctx.beginPath();
    ctx.setLineDash(dashes[l.e.confidence].map(v => v / state.scale));
    ctx.strokeStyle = palette[l.e.confidence] || palette.structural;
    ctx.globalAlpha = lit ? 0.62 : 0.07;
    ctx.lineWidth = (lit && focus ? 1.5 : 0.8) / state.scale;
    ctx.moveTo(l.s.x, l.s.y);
    ctx.lineTo(l.t.x, l.t.y);
    ctx.stroke();
  });
  ctx.setLineDash([]);

  const inkFaint = token('--ink-faint');
  const ink = token('--ink');
  const ground = token('--ground');
  visibleNodes().forEach(n => {
    const lit = !focus || near.has(n.id);
    ctx.globalAlpha = lit ? 1 : 0.12;
    ctx.beginPath();
    ctx.arc(n.x, n.y, radiusOf(n), 0, Math.PI * 2);
    ctx.fillStyle = KIND_COLOURS[n.kind] || inkFaint;
    ctx.fill();
    if (state.selected && state.selected.id === n.id) {
      ctx.lineWidth = 2 / state.scale;
      ctx.strokeStyle = ink;
      ctx.stroke();
    } else {
      ctx.lineWidth = 1 / state.scale;
      ctx.strokeStyle = ground;
      ctx.stroke();
    }
  });

  // Labels only where they can be read: a zoomed-out hairball of overlapping text says less
  // than no text at all.
  if (state.scale > 0.85 || focus) {
    ctx.font = `${11 / state.scale}px ui-monospace, SFMono-Regular, Menlo, monospace`;
    ctx.textAlign = 'center';
    visibleNodes().forEach(n => {
      const lit = focus ? near.has(n.id) : state.scale > 1.3 || n.degree > 6;
      if (!lit) return;
      ctx.globalAlpha = 1;
      ctx.fillStyle = ink;
      const label = n.short || n.title;
      ctx.fillText(label.slice(0, 26), n.x, n.y - radiusOf(n) - 4 / state.scale);
    });
  }
  ctx.restore();
  ctx.globalAlpha = 1;
}

// ---- inspector ---------------------------------------------------------

function text(tag, value, className) {
  const el = document.createElement(tag);
  if (className) el.className = className;
  el.textContent = value;
  return el;
}

function select(node) {
  state.selected = node;
  inspector.replaceChildren();
  if (!node) {
    inspector.dataset.open = 'false';
    draw();
    return;
  }

  const close = text('button', 'close', 'close');
  close.setAttribute('aria-label', 'Close inspector');
  close.addEventListener('click', () => select(null));
  inspector.append(close);

  inspector.append(text('p', node.kind.replace(/-/g, ' '), 'kicker'));
  const heading = text('h2', node.title, 'serif');
  inspector.append(heading);
  inspector.append(text('p', node.source, 'source'));

  if (node.falsifies) {
    inspector.append(text('h3', 'Falsifies if'));
    inspector.append(text('p', node.falsifies, 'falsifies serif'));
  }
  if (node.body) {
    inspector.append(text('h3', 'Statement'));
    inspector.append(text('p', node.body, 'statement serif'));
  }

  const related = links
    .filter(l => l.s.id === node.id || l.t.id === node.id)
    .map(l => ({
      other: l.s.id === node.id ? l.t : l.s,
      outgoing: l.s.id === node.id,
      edge: l.e,
    }));

  CONFIDENCE.forEach(([level, blurb]) => {
    const group = related.filter(r => r.edge.confidence === level);
    if (!group.length) return;
    inspector.append(text('h3', level + ' — ' + blurb));
    group
      .sort((a, b) => (a.edge.kind + a.other.title).localeCompare(b.edge.kind + b.other.title))
      .forEach(({ other, outgoing, edge }) => {
        const row = document.createElement('div');
        row.className = 'rel';
        row.append(text('span', outgoing ? edge.kind + ' →' : '← ' + edge.kind, 'verb'));
        const body = document.createElement('span');
        const jump = text('button', other.title);
        jump.addEventListener('click', () => { select(other); centre(other); });
        body.append(jump);
        // Evidence is shown for anything not parsed from a fixed grammar, so a reader can
        // check the claim against the clause that produced it rather than taking it on trust.
        if (edge.evidence && level !== 'structural') {
          body.append(text('span', edge.evidence, 'evidence'));
        }
        row.append(body);
        inspector.append(row);
      });
  });

  inspector.dataset.open = 'true';
  inspector.scrollTop = 0;
  draw();
}

function centre(node) {
  state.tx = canvas.clientWidth / 2 - node.x * state.scale;
  state.ty = canvas.clientHeight / 2 - node.y * state.scale;
  draw();
}

// ---- interaction -------------------------------------------------------

function atPoint(event) {
  const rect = canvas.getBoundingClientRect();
  const x = (event.clientX - rect.left - state.tx) / state.scale;
  const y = (event.clientY - rect.top - state.ty) / state.scale;
  let best = null, bestDistance = Infinity;
  visibleNodes().forEach(n => {
    const d = (n.x - x) ** 2 + (n.y - y) ** 2;
    const reach = (radiusOf(n) + 7 / state.scale) ** 2;
    if (d < reach && d < bestDistance) { best = n; bestDistance = d; }
  });
  return best;
}

let dragging = null;
canvas.addEventListener('pointerdown', event => {
  dragging = { x: event.clientX, y: event.clientY, moved: false };
  canvas.setPointerCapture(event.pointerId);
});
canvas.addEventListener('pointermove', event => {
  if (dragging) {
    const dx = event.clientX - dragging.x, dy = event.clientY - dragging.y;
    if (Math.abs(dx) + Math.abs(dy) > 3) dragging.moved = true;
    state.tx += dx; state.ty += dy;
    dragging.x = event.clientX; dragging.y = event.clientY;
    draw();
    return;
  }
  const found = atPoint(event);
  if (found !== state.hover) { state.hover = found; canvas.title = found ? found.title : ''; draw(); }
});
canvas.addEventListener('pointerup', event => {
  const wasDrag = dragging && dragging.moved;
  dragging = null;
  if (!wasDrag) select(atPoint(event));
});
canvas.addEventListener('pointerleave', () => {
  dragging = null;
  if (state.hover) { state.hover = null; draw(); }
});
canvas.addEventListener('wheel', event => {
  event.preventDefault();
  const rect = canvas.getBoundingClientRect();
  const px = event.clientX - rect.left, py = event.clientY - rect.top;
  const factor = Math.exp(-event.deltaY * 0.0016);
  const next = Math.min(6, Math.max(0.18, state.scale * factor));
  state.tx = px - (px - state.tx) * (next / state.scale);
  state.ty = py - (py - state.ty) * (next / state.scale);
  state.scale = next;
  draw();
}, { passive: false });
canvas.addEventListener('keydown', event => {
  const step = 40;
  const moves = { ArrowLeft: [step, 0], ArrowRight: [-step, 0], ArrowUp: [0, step], ArrowDown: [0, -step] };
  if (moves[event.key]) {
    event.preventDefault();
    state.tx += moves[event.key][0]; state.ty += moves[event.key][1];
    draw();
  }
  if (event.key === 'Escape') select(null);
});
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && state.selected) select(null);
});

// ---- rail --------------------------------------------------------------

function buildRail() {
  const rail = document.getElementById('rail');
  const counts = {};
  NODES.forEach(n => { counts[n.kind] = (counts[n.kind] || 0) + 1; });

  rail.append(text('p', 'Node kinds', 'rail-heading'));
  KIND_ORDER.forEach(kind => {
    const button = document.createElement('button');
    button.className = 'toggle';
    button.type = 'button';
    button.setAttribute('aria-pressed', 'true');
    const swatch = document.createElement('span');
    swatch.className = 'swatch';
    swatch.style.background = KIND_COLOURS[kind] || 'var(--ink-faint)';
    button.append(swatch, text('span', kind.replace(/-/g, ' ')), text('span', String(counts[kind]), 'count'));
    button.addEventListener('click', () => {
      const on = button.getAttribute('aria-pressed') === 'true';
      button.setAttribute('aria-pressed', on ? 'false' : 'true');
      if (on) state.kinds.delete(kind); else state.kinds.add(kind);
      draw();
    });
    rail.append(button);
  });

  rail.append(text('p', 'Edge confidence', 'rail-heading'));
  const edgeCounts = {};
  EDGES.forEach(e => { edgeCounts[e.confidence] = (edgeCounts[e.confidence] || 0) + 1; });
  CONFIDENCE.forEach(([level, blurb]) => {
    const button = document.createElement('button');
    button.className = 'toggle';
    button.type = 'button';
    button.setAttribute('aria-pressed', 'true');
    button.title = blurb;
    const swatch = document.createElement('span');
    swatch.className = 'swatch';
    swatch.style.background = 'var(--' + level + ')';
    button.append(swatch, text('span', level), text('span', String(edgeCounts[level] || 0), 'count'));
    button.addEventListener('click', () => {
      const on = button.getAttribute('aria-pressed') === 'true';
      button.setAttribute('aria-pressed', on ? 'false' : 'true');
      if (on) state.confidences.delete(level); else state.confidences.add(level);
      draw();
    });
    rail.append(button);
  });
}

document.getElementById('search').addEventListener('input', event => {
  state.query = event.target.value.trim();
  draw();
});
document.getElementById('refit').addEventListener('click', () => { fit(); draw(); });

buildRail();
fit();
draw();
window.addEventListener('resize', () => { fit(); draw(); });
const themeWatcher = window.matchMedia('(prefers-color-scheme: dark)');
themeWatcher.addEventListener('change', draw);

"""
