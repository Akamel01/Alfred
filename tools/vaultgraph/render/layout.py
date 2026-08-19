"""Where the nodes go. The force simulation, the isolate margin, and the container hulls.

**Seeded, deterministic, and settled rather than live.** The PRNG is a fixed-seed LCG and every
ordering is by node id, so the layout is a function of the graph and nothing else -- the same
property `cluster.py` holds for the partition, and for the same reason: a page that settled
somewhere different on every load would make two screenshots of one commit disagree.

The settling is now *animated* rather than computed in a blocking loop. That is a change of
appearance only: the same fixed number of ticks runs, in the same order, to the same positions.
It costs nothing in determinism because the layout has never been stored -- `graph.json` carries
no coordinates, so nothing a browser computes here can reach a byte-compared file.

**Containment is not a force.** `contains` is a tree -- tier holds document, gate holds step,
package holds module -- and it was 40% of the edges. Feeding a tree to a force simulation
spends the whole canvas drawing 179 spokes that say "is inside", and buries the graph that has
real structure. Containment is drawn as a hull around its members instead, which is the same
claim made once per container rather than once per member.
"""

from __future__ import annotations

JS = r"""
// ---- layout ------------------------------------------------------------
const layout = (function () {
  let seed = 20260818;
  function random() {
    seed = (seed * 1664525 + 1013904223) % 4294967296;
    return seed / 4294967296;
  }

  //: Containment is nesting, not attraction. See the module docstring.
  const CONTAINER_KINDS = new Set(['contains']);

  const relations = EDGES.filter(e => !CONTAINER_KINDS.has(e.kind));
  const containment = EDGES.filter(e => CONTAINER_KINDS.has(e.kind));

  const links = relations
    .map(e => ({ e, s: byId.get(e.src), t: byId.get(e.dst) }))
    .filter(l => l.s && l.t && l.s !== l.t);

  const holds = new Map();
  containment.forEach(e => {
    const parent = byId.get(e.src), child = byId.get(e.dst);
    if (!parent || !child) return;
    if (!holds.has(parent.id)) holds.set(parent.id, []);
    holds.get(parent.id).push(child);
    child.parent = parent.id;
  });

  NODES.forEach(n => { n.degree = 0; n.vx = 0; n.vy = 0; });
  links.forEach(l => { l.s.degree += 1; l.t.degree += 1; });

  // A node whose only edge was containment now has no edge at all, which is the honest count:
  // "is inside a tier" was never a relation, it was an address.
  const connected = NODES.filter(n => n.degree > 0);
  const isolated = NODES.filter(n => n.degree === 0);

  const KIND_ORDER = [...new Set(NODES.map(n => n.kind))].sort();
  NODES.forEach(n => {
    const ring = KIND_ORDER.indexOf(n.kind);
    const angle = random() * Math.PI * 2;
    const radius = 140 + ring * 74 + random() * 60;
    n.x = Math.cos(angle) * radius;
    n.y = Math.sin(angle) * radius;
  });

  function tick(cooling) {
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
    // Members of one container pull gently together, so a tier's documents land as a patch a
    // hull can be drawn round rather than scattered across the canvas.
    holds.forEach(members => {
      const moving = members.filter(m => m.degree > 0);
      if (moving.length < 2) return;
      let cx = 0, cy = 0;
      moving.forEach(m => { cx += m.x; cy += m.y; });
      cx /= moving.length; cy /= moving.length;
      // Strong enough to make a package a visible lobe. At a tenth of this the members drifted
      // apart under their own imports and the hull drawn round them covered half the canvas --
      // an outline that contains everything states nothing.
      moving.forEach(m => {
        m.vx += (cx - m.x) * 0.19;
        m.vy += (cy - m.y) * 0.19;
      });
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

  // A member whose only edge was containment is *placed*, not simulated. It has no forces
  // acting on it -- that is what "its only relation is the thing holding it" means -- so a
  // simulation collapses every one of them onto the origin in a single indistinguishable blob.
  // Laying them on rings around their container is the drawing making the same claim the data
  // does: this is where it lives, and living there is all that is known about it.
  function nest() {
    holds.forEach((members, parentId) => {
      const parent = byId.get(parentId);
      const loose = members.filter(m => m.degree === 0);
      if (!parent || !loose.length) return;
      const anchored = members.filter(m => m.degree > 0);
      let ax = parent.x, ay = parent.y;
      if (anchored.length) {
        ax = anchored.reduce((s, m) => s + m.x, 0) / anchored.length;
        ay = anchored.reduce((s, m) => s + m.y, 0) / anchored.length;
      }
      const ordered = [...loose].sort((a, b) => a.id.localeCompare(b.id));
      // Concentric rings, ~9 to a ring, so a tier holding 63 documents reads as a disc with a
      // drawable outline rather than as one very long arc.
      const perRing = 9;
      ordered.forEach((node, index) => {
        const ring = Math.floor(index / perRing) + 1;
        const slot = index % perRing;
        const angle = (slot / perRing) * Math.PI * 2 + ring * 0.7;
        const radius = 34 * ring;
        node.x = ax + Math.cos(angle) * radius;
        node.y = ay + Math.sin(angle) * radius;
      });
      // The container itself sits at the centre of what it holds, not wherever the ring of
      // kinds first dropped it.
      if (parent.degree === 0) { parent.x = ax; parent.y = ay; }
    });
  }

  // Nodes related to nothing *and* held by nothing are parked on an arc outside whatever the
  // simulation settled to.
  // Mixing them in buries the observation in a hairball and lets one of them wander off and
  // collapse the view; the rail states the count, and this keeps them out of the way.
  function park() {
    const placed = NODES.filter(n => n.degree > 0 || n.parent || holds.has(n.id));
    const reach = placed.length ? Math.max(...placed.map(n => Math.hypot(n.x, n.y))) : 200;
    const radius = reach + 150;
    const adrift = isolated.filter(n => !n.parent && !holds.has(n.id));
    const ordered = [...adrift].sort((a, b) => (a.kind + a.id).localeCompare(b.kind + b.id));
    ordered.forEach((n, index) => {
      const angle = (index / Math.max(1, ordered.length)) * Math.PI * 2 - Math.PI / 2;
      n.x = Math.cos(angle) * radius;
      n.y = Math.sin(angle) * radius;
    });
  }

  const STEPS = 420;

  return {
    links,
    isolated,
    holds,

    /** Run the settling across frames, calling `onTick` after each batch and `onSettled` once.
        Batched rather than one tick per frame: 420 single-tick frames is seven seconds of
        watching, which is a loading screen, not a layout. */
    settle(onTick, onSettled) {
      let step = 0;
      const batch = 12;
      const frame = () => {
        for (let i = 0; i < batch && step < STEPS; i += 1, step += 1) {
          tick(1 - step / STEPS);
        }
        if (step < STEPS) {
          onTick();
          requestAnimationFrame(frame);
        } else {
          nest();
          park();
          onSettled();
        }
      };
      requestAnimationFrame(frame);
    },

    /** Convex hulls round every container holding two or more members, largest first so a
        package's hull does not paint over the tier's it sits in.

        A hull is only drawn where it is compact enough to be a claim. A container whose members
        the simulation has pulled to opposite ends of the canvas gets none: the outline would
        enclose everything between them, most of which it does not hold, and a reader would
        take the enclosure at face value. Silence is the honest output there -- the inspector
        still lists what holds what. */
    hulls(isVisible) {
      const out = [];
      holds.forEach((members, parentId) => {
        const shown = members.filter(isVisible);
        if (shown.length < 2) return;
        const cx = shown.reduce((s, m) => s + m.x, 0) / shown.length;
        const cy = shown.reduce((s, m) => s + m.y, 0) / shown.length;
        const spread = Math.max(...shown.map(m => Math.hypot(m.x - cx, m.y - cy)));
        if (spread > 60 + 26 * Math.sqrt(shown.length)) return;
        const points = [];
        shown.forEach(m => {
          const r = 14;
          points.push([m.x - r, m.y - r], [m.x + r, m.y - r],
                      [m.x - r, m.y + r], [m.x + r, m.y + r]);
        });
        out.push({ parent: byId.get(parentId), points: convex(points), size: shown.length });
      });
      out.sort((a, b) => b.size - a.size);
      return out;
    },
  };

  /** Andrew's monotone chain. Sorted input and integer-free comparisons, so the hull is the
      same polygon on every machine -- the layout is deterministic and the outline drawn round
      it has to be too. */
  function convex(points) {
    const pts = [...points].sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    if (pts.length < 3) return pts;
    const cross = (o, a, b) =>
      (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
    const half = list => {
      const out = [];
      for (const p of list) {
        while (out.length >= 2 && cross(out[out.length - 2], out[out.length - 1], p) <= 0) {
          out.pop();
        }
        out.push(p);
      }
      out.pop();
      return out;
    };
    return half(pts).concat(half([...pts].reverse()));
  }
})();
"""
