"""Where the page is looking. The only thing that knows how world coordinates become pixels.

Before this module, `tx`, `ty` and `scale` were three fields on a shared state object, read and
written from six places: the fit, the recentre, the hit test, the wheel handler, the drag
handler, and the transform at the top of every frame. Each of those re-derived the screen-to-world
conversion by hand, which meant the conversion existed six times and had to agree six times.

The interface is five verbs and no fields. Nothing outside this file may touch the transform,
so a seventh place that needs the conversion gets it rather than writing a seventh copy.

**`fit` takes the nodes to fit, rather than reaching for them.** A camera that called the view's
filter would make the two modules mutually dependent for no gain -- the caller already knows
which nodes are on screen, and passing them keeps this file testable against a plain array.
"""

from __future__ import annotations

JS = r"""
// ---- camera ------------------------------------------------------------
const camera = (function () {
  let tx = 0, ty = 0, scale = 1;
  let animation = null;

  //: A single outlier should cost a little clipping at the edge, never the readability of
  //: everything else -- so the extent is trimmed at both ends rather than taken from min/max.
  function trimmed(values) {
    const sorted = [...values].sort((a, b) => a - b);
    const cut = Math.floor(sorted.length * 0.01);
    return [sorted[cut], sorted[sorted.length - 1 - cut]];
  }

  return {
    get scale() { return scale; },

    apply(context) {
      context.translate(tx, ty);
      context.scale(scale, scale);
    },

    /** Pixel coordinates from a pointer event, as world coordinates. */
    toWorld(event, element) {
      const rect = element.getBoundingClientRect();
      return {
        x: (event.clientX - rect.left - tx) / scale,
        y: (event.clientY - rect.top - ty) / scale,
      };
    },

    fit(nodes, width, height) {
      if (!nodes.length) return;
      const [minX, maxX] = trimmed(nodes.map(n => n.x));
      const [minY, maxY] = trimmed(nodes.map(n => n.y));
      const spanX = (maxX - minX) || 1;
      const spanY = (maxY - minY) || 1;
      scale = Math.min(width / (spanX + 90), height / (spanY + 90), 2.4);
      tx = width / 2 - ((maxX + minX) / 2) * scale;
      ty = height / 2 - ((maxY + minY) / 2) * scale;
    },

    centre(node, width, height) {
      tx = width / 2 - node.x * scale;
      ty = height / 2 - node.y * scale;
    },

    panBy(dx, dy) { tx += dx; ty += dy; },

    /** Zoom about a pixel, so the point under the cursor stays under the cursor. */
    zoomAt(px, py, factor) {
      const next = Math.min(6, Math.max(0.18, scale * factor));
      tx = px - (px - tx) * (next / scale);
      ty = py - (py - ty) * (next / scale);
      scale = next;
    },

    /** Ease to a node at a chosen zoom. Cancels any tween already running, so two fast jumps
        do not fight each other over the same three numbers. */
    tween(node, targetScale, width, height, onFrame) {
      if (animation) cancelAnimationFrame(animation);
      const fromX = tx, fromY = ty, fromScale = scale;
      const toScale = Math.min(6, Math.max(0.18, targetScale));
      const toX = width / 2 - node.x * toScale;
      const toY = height / 2 - node.y * toScale;
      const started = performance.now();
      const span = 380;
      const step = now => {
        const t = Math.min(1, (now - started) / span);
        const eased = t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
        tx = fromX + (toX - fromX) * eased;
        ty = fromY + (toY - fromY) * eased;
        scale = fromScale + (toScale - fromScale) * eased;
        onFrame();
        animation = t < 1 ? requestAnimationFrame(step) : null;
      };
      animation = requestAnimationFrame(step);
    },
  };
})();
"""
