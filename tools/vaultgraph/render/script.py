"""The script, composed at build time from four modules and inlined into one page.

**The read model is untrusted in the browser (ADR-0008).** Every value that reaches the page
goes through `textContent` or a created text node. No markup-writing sink appears in any of the
four fragments -- a generated note's body is repository text, and repository text is not markup.

**Four fragments, in dependency order.** `camera` owns where the page is looking, `layout` owns
where the nodes are, `view` owns which of them are drawn. This file keeps what is irreducibly
wide: a canvas painter and a control panel, both of which touch every concept by nature. The
order below is load-bearing -- `layout` reads the prelude's arrays, `view` reads `layout`.

**Confidence is encoded twice**, in hue and in stroke style. A dashed line is a mechanical
match inside a comment span; a dotted line is a guess from free prose. Colour alone would lose
that distinction in greyscale and for a colourblind reader, and it is the most important thing
this graph has to say.
"""

from __future__ import annotations

from . import camera, layout, view

PRELUDE = r"""
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

const focusState = { selected: null, hover: null };

function token(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}
"""


BODY = r"""
// ---- drawing -----------------------------------------------------------

// Degree-scaled, and scaled wider than it was. A hub cited by twenty decisions and a leaf cited
// by one were four pixels apart, which spent the whole size channel on nothing.
function radiusOf(node) { return 4 + Math.min(13, Math.sqrt(node.degree) * 2.6); }

// Cluster hues walk the golden angle, so adjacent ordinals are never adjacent colours and no
// palette has to be authored or maintained. Singletons share one muted colour: giving each its
// own hue would spend the whole spectrum on the part of the graph that has no structure.
function clusterColour(ordinal) {
  const group = CLUSTERS[ordinal];
  if (!group || group.size < 2) return 'var(--ink-faint)';
  return 'hsl(' + ((ordinal * 137.508) % 360).toFixed(1) + ' 58% 58%)';
}

function colourOf(node) {
  if (view.colourBy === 'cluster') return clusterColour(node.cluster);
  return KIND_COLOURS[node.kind] || 'var(--ink-faint)';
}

function fit() {
  camera.fit(view.nodes(), canvas.clientWidth, canvas.clientHeight);
}

function neighbourhood(node) {
  const near = new Set([node.id]);
  layout.links.forEach(l => {
    if (l.s.id === node.id) near.add(l.t.id);
    if (l.t.id === node.id) near.add(l.s.id);
  });
  return near;
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
  camera.apply(ctx);

  const scale = camera.scale;
  const focus = focusState.selected || focusState.hover;
  const near = focus ? neighbourhood(focus) : null;
  const shown = view.nodes();
  const onScreen = new Set(shown.map(n => n.id));

  // Hulls first, beneath everything. Containment is stated once per container here, where it
  // used to cost one line per member and 40% of the edges.
  ctx.lineJoin = 'round';
  layout.hulls(node => onScreen.has(node.id)).forEach(hull => {
    if (hull.points.length < 3) return;
    ctx.beginPath();
    ctx.moveTo(hull.points[0][0], hull.points[0][1]);
    for (let i = 1; i < hull.points.length; i += 1) {
      const [px, py] = hull.points[i];
      const [qx, qy] = hull.points[(i + 1) % hull.points.length];
      ctx.quadraticCurveTo(px, py, (px + qx) / 2, (py + qy) / 2);
    }
    ctx.closePath();
    ctx.globalAlpha = focus ? 0.04 : 0.09;
    ctx.fillStyle = KIND_COLOURS[hull.parent.kind] || 'var(--ink-faint)';
    ctx.fill();
    ctx.globalAlpha = focus ? 0.10 : 0.24;
    ctx.lineWidth = 1 / scale;
    ctx.strokeStyle = KIND_COLOURS[hull.parent.kind] || 'var(--ink-faint)';
    ctx.stroke();
    if (scale > 0.5) {
      ctx.globalAlpha = focus ? 0.25 : 0.62;
      ctx.font = `${10 / scale}px ui-monospace, SFMono-Regular, Menlo, monospace`;
      ctx.textAlign = 'left';
      const top = hull.points.reduce((a, p) => (p[1] < a[1] ? p : a), hull.points[0]);
      ctx.fillText((hull.parent.short || hull.parent.title).slice(0, 30),
                   top[0], top[1] - 6 / scale);
    }
  });

  const palette = {
    structural: token('--structural'),
    derived: token('--derived'),
    prose: token('--prose'),
  };
  const dashes = Object.fromEntries(CONFIDENCE.map(c => [c[0], c[2]]));

  view.links().forEach(l => {
    const lit = !focus || (near.has(l.s.id) && near.has(l.t.id));
    ctx.beginPath();
    ctx.setLineDash(dashes[l.e.confidence].map(v => v / scale));
    ctx.strokeStyle = palette[l.e.confidence] || palette.structural;
    ctx.globalAlpha = lit ? 0.62 : 0.05;
    ctx.lineWidth = (lit && focus ? 1.8 : 0.8) / scale;
    ctx.moveTo(l.s.x, l.s.y);
    ctx.lineTo(l.t.x, l.t.y);
    ctx.stroke();
  });
  ctx.setLineDash([]);

  const ink = token('--ink');
  const ground = token('--ground');
  shown.forEach(n => {
    const lit = !focus || near.has(n.id);
    const chosen = focusState.selected && focusState.selected.id === n.id;
    ctx.globalAlpha = lit ? 1 : 0.10;
    ctx.beginPath();
    ctx.arc(n.x, n.y, radiusOf(n) + (chosen ? 2 : 0), 0, Math.PI * 2);
    // The selected node inverts: ground fill inside its own kind's ring. It reads at any zoom
    // and it costs no second colour channel, which a glow or a halo would.
    ctx.fillStyle = chosen ? ground : colourOf(n);
    ctx.fill();
    ctx.lineWidth = (chosen ? 2.4 : 1) / scale;
    ctx.strokeStyle = chosen ? colourOf(n) : ground;
    ctx.stroke();
  });

  // Labels only where they can be read: a zoomed-out hairball of overlapping text says less
  // than no text at all.
  if (scale > 0.85 || focus) {
    ctx.font = `${11 / scale}px ui-monospace, SFMono-Regular, Menlo, monospace`;
    ctx.textAlign = 'center';
    shown.forEach(n => {
      const lit = focus ? near.has(n.id) : scale > 1.3 || n.degree > 6;
      if (!lit) return;
      ctx.globalAlpha = 1;
      ctx.fillStyle = ink;
      const label = n.short || n.title;
      ctx.fillText(label.slice(0, 26), n.x, n.y - radiusOf(n) - 4 / scale);
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

function jumpTo(node) {
  select(node);
  camera.tween(node, Math.max(1.4, camera.scale), canvas.clientWidth, canvas.clientHeight, draw);
}

function select(node) {
  focusState.selected = node;
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
  inspector.append(text('h2', node.title, 'serif'));
  inspector.append(text('p', node.source, 'source'));

  if (node.falsifies) {
    inspector.append(text('h3', 'Falsifies if'));
    inspector.append(text('p', node.falsifies, 'falsifies serif'));
  }
  if (node.body) {
    inspector.append(text('h3', 'Statement'));
    inspector.append(text('p', node.body, 'statement serif'));
  }

  const related = layout.links
    .filter(l => l.s.id === node.id || l.t.id === node.id)
    .map(l => ({
      other: l.s.id === node.id ? l.t : l.s,
      outgoing: l.s.id === node.id,
      edge: l.e,
    }));

  // Where it sits, and what sits in it. Containment left the canvas as an edge, so the address
  // it carried has to be readable somewhere -- and a list is a better place for a tree than a
  // drawing is.
  const parent = node.parent ? byId.get(node.parent) : null;
  const children = layout.holds.get(node.id) || [];
  if (parent || children.length) {
    inspector.append(text('h3', 'contains'));
    if (parent) {
      const row = document.createElement('div');
      row.className = 'rel';
      row.append(text('span', 'inside', 'verb'));
      const body = document.createElement('span');
      const jump = text('button', parent.title);
      jump.addEventListener('click', () => jumpTo(parent));
      body.append(jump);
      row.append(body);
      inspector.append(row);
    }
    if (children.length) {
      const row = document.createElement('div');
      row.className = 'rel';
      row.append(text('span', 'holds', 'verb'));
      const body = document.createElement('span');
      body.className = 'chips';
      children
        .slice()
        .sort((a, b) => a.title.localeCompare(b.title))
        .forEach(child => {
          const chip = text('button', child.short || child.title, 'chip-link');
          chip.title = child.title;
          chip.style.borderLeftColor = colourOf(child);
          chip.addEventListener('click', () => jumpTo(child));
          body.append(chip);
        });
      row.append(body);
      inspector.append(row);
    }
  }

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
        jump.addEventListener('click', () => jumpTo(other));
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

// ---- interaction -------------------------------------------------------

function atPoint(event) {
  const { x, y } = camera.toWorld(event, canvas);
  let best = null, bestDistance = Infinity;
  view.nodes().forEach(n => {
    const d = (n.x - x) ** 2 + (n.y - y) ** 2;
    const reach = (radiusOf(n) + 7 / camera.scale) ** 2;
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
    camera.panBy(dx, dy);
    dragging.x = event.clientX; dragging.y = event.clientY;
    draw();
    return;
  }
  const found = atPoint(event);
  if (found !== focusState.hover) {
    focusState.hover = found;
    canvas.title = found ? found.title : '';
    canvas.style.cursor = found ? 'pointer' : 'default';
    draw();
  }
});
canvas.addEventListener('pointerup', event => {
  const wasDrag = dragging && dragging.moved;
  dragging = null;
  if (!wasDrag) select(atPoint(event));
});
canvas.addEventListener('pointerleave', () => {
  dragging = null;
  if (focusState.hover) { focusState.hover = null; draw(); }
});
canvas.addEventListener('wheel', event => {
  event.preventDefault();
  const rect = canvas.getBoundingClientRect();
  camera.zoomAt(event.clientX - rect.left, event.clientY - rect.top,
                Math.exp(-event.deltaY * 0.0016));
  draw();
}, { passive: false });
canvas.addEventListener('keydown', event => {
  const step = 40;
  const moves = { ArrowLeft: [step, 0], ArrowRight: [-step, 0], ArrowUp: [0, step], ArrowDown: [0, -step] };
  if (moves[event.key]) {
    event.preventDefault();
    camera.panBy(moves[event.key][0], moves[event.key][1]);
    draw();
  }
  if (event.key === 'Escape') select(null);
});
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && focusState.selected) select(null);
});

// ---- rail --------------------------------------------------------------

function toggleButton(label, count, colour, pressed, onChange) {
  const button = document.createElement('button');
  button.className = 'toggle';
  button.type = 'button';
  button.setAttribute('aria-pressed', pressed ? 'true' : 'false');
  const swatch = document.createElement('span');
  swatch.className = 'swatch';
  if (colour) swatch.style.background = colour;
  button.append(swatch, text('span', label));
  if (count !== null) button.append(text('span', String(count), 'count'));
  button.addEventListener('click', () => {
    const on = button.getAttribute('aria-pressed') === 'true';
    button.setAttribute('aria-pressed', on ? 'false' : 'true');
    onChange(!on);
  });
  return button;
}

function buildRail() {
  const rail = document.getElementById('rail');
  const counts = {};
  NODES.forEach(n => { counts[n.kind] = (counts[n.kind] || 0) + 1; });
  const KIND_ORDER = [...new Set(NODES.map(n => n.kind))].sort();

  rail.append(text('p', 'What is drawn', 'rail-heading'));
  const relationsToggle = toggleButton(
    'relations only', view.relatedCount(), 'var(--structural)', view.relationsOnly,
    on => { view.setRelationsOnly(on); fit(); draw(); refreshIsolates(); });
  relationsToggle.title =
    'Hide everything whose only relation is the thing that holds it, or that has none at all';
  rail.append(relationsToggle);

  const isolateNote = document.createElement('div');
  rail.append(isolateNote);

  // The nodes related to nothing are a fact about the register, not a picture. Stating the
  // count and listing them beats drawing 84 unlabelled dots on a ring.
  function refreshIsolates() {
    isolateNote.textContent = '';
    if (!layout.isolated.length) return;
    const summary = document.createElement('button');
    summary.className = 'toggle';
    summary.type = 'button';
    summary.setAttribute('aria-pressed', 'false');
    summary.append(text('span', '', 'swatch'),
                   text('span', 'no relation at all'),
                   text('span', String(layout.isolated.length), 'count'));
    const list = document.createElement('div');
    list.className = 'isolate-list';
    summary.addEventListener('click', () => {
      const open = summary.getAttribute('aria-pressed') === 'true';
      summary.setAttribute('aria-pressed', open ? 'false' : 'true');
      list.textContent = '';
      if (open) return;
      const byKind = new Map();
      layout.isolated.forEach(n => {
        if (!byKind.has(n.kind)) byKind.set(n.kind, []);
        byKind.get(n.kind).push(n);
      });
      [...byKind.keys()].sort().forEach(kind => {
        list.append(text('p', kind.replace(/-/g, ' '), 'rail-note'));
        byKind.get(kind)
          .slice()
          .sort((a, b) => a.title.localeCompare(b.title))
          .forEach(node => {
            const chip = text('button', node.short || node.title, 'chip-link');
            chip.title = node.title;
            chip.style.borderLeftColor = colourOf(node);
            chip.addEventListener('click', () => {
              if (view.relationsOnly) {
                view.setRelationsOnly(false);
                relationsToggle.setAttribute('aria-pressed', 'false');
              }
              jumpTo(node);
            });
            list.append(chip);
          });
      });
    });
    isolateNote.append(summary, list);
  }
  refreshIsolates();

  rail.append(text('p', 'Node kinds', 'rail-heading'));
  KIND_ORDER.forEach(kind => {
    rail.append(toggleButton(
      kind.replace(/-/g, ' '), counts[kind], KIND_COLOURS[kind] || 'var(--ink-faint)', true,
      on => { view.toggleKind(kind, on); draw(); }));
  });

  const grouped = CLUSTERS.filter(c => c.size > 1);
  const loose = CLUSTERS.length - grouped.length;
  rail.append(text('p', 'Clusters', 'rail-heading'));

  const mode = document.createElement('button');
  mode.className = 'toggle';
  mode.type = 'button';
  mode.setAttribute('aria-pressed', 'false');
  mode.title = 'Colour by what a node sits with, rather than by what it is';
  const modeLabel = text('span', 'colour by cluster');
  mode.append(text('span', '', 'swatch'), modeLabel, text('span', String(grouped.length), 'count'));
  mode.addEventListener('click', () => {
    const next = view.colourBy === 'cluster' ? 'kind' : 'cluster';
    view.setColourBy(next);
    mode.setAttribute('aria-pressed', next === 'cluster' ? 'true' : 'false');
    modeLabel.textContent = next === 'cluster' ? 'colour by kind' : 'colour by cluster';
    buildClusterList();
    draw();
  });
  rail.append(mode);

  const list = document.createElement('div');
  rail.append(list);

  // The cluster names are node titles -- repository prose -- so every one goes on the page
  // through textContent, like every other value from the read model (ADR-0008).
  function buildClusterList() {
    list.textContent = '';
    if (view.colourBy !== 'cluster') return;
    grouped.slice(0, 12).forEach((group, ordinal) => {
      const row = toggleButton(group.name, group.size, clusterColour(ordinal), true,
                               on => { view.toggleCluster(ordinal, on); draw(); });
      row.title = group.name;
      list.append(row);
    });
    if (loose) {
      list.append(text('p', loose + ' nodes sit in no cluster — they have no relation at all',
                       'rail-note'));
    }
  }
  buildClusterList();

  rail.append(text('p', 'Edge confidence', 'rail-heading'));
  const edgeCounts = {};
  EDGES.forEach(e => { edgeCounts[e.confidence] = (edgeCounts[e.confidence] || 0) + 1; });
  CONFIDENCE.forEach(([level, blurb]) => {
    const button = toggleButton(level, edgeCounts[level] || 0, 'var(--' + level + ')', true,
                                on => { view.toggleConfidence(level, on); draw(); });
    button.title = blurb;
    rail.append(button);
  });
}

// ---- wiring ------------------------------------------------------------

document.getElementById('search').addEventListener('input', event => {
  view.setQuery(event.target.value.trim());
  draw();
});
document.getElementById('refit').addEventListener('click', () => { fit(); draw(); });

buildRail();
// Watched rather than computed behind a frozen frame. The settling is the page explaining how
// it arrived at the arrangement, and it costs nothing: the layout has never been stored, so
// what the browser computes here can never reach a byte-compared file.
layout.settle(
  () => { fit(); draw(); },
  () => { fit(); draw(); },
);
window.addEventListener('resize', () => { fit(); draw(); });
const themeWatcher = window.matchMedia('(prefers-color-scheme: dark)');
themeWatcher.addEventListener('change', draw);
"""

JS = PRELUDE + layout.JS + view.JS + camera.JS + BODY
