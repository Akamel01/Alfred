"""What is on screen. Five filter dimensions behind one predicate.

The filters grew one at a time -- kind, then edge confidence, then cluster, then the search box,
then relations-only -- and each arrived as another clause inside `matches` and another field on
a shared state object that four other parts of the page also wrote to. Five dimensions is where
that stops being readable: the question "why is this node not drawn" had five answers in four
files.

Everything a node's visibility depends on lives here, and the rest of the page asks rather than
reads. `nodes()` and `links()` are the whole interface; the state behind them is deliberately
not exported.

**`hidden` sets hold what is off, never what is on.** A kind or cluster appearing in a later
build is then visible by default rather than silently absent -- the failure mode being designed
out is a new node kind that nobody notices is missing.
"""

from __future__ import annotations

JS = r"""
// ---- view --------------------------------------------------------------
const view = (function () {
  const hiddenKinds = new Set();
  const hiddenClusters = new Set();
  const hiddenConfidence = new Set();
  let query = '';
  let colourBy = 'kind';
  //: On by default. Two thirds of this graph is either related to nothing or related only to
  //: the thing that holds it, and drawing all of it answers "what is in the repository" at the
  //: cost of never answering "how does it fit together". The toggle restores the full census.
  let relationsOnly = true;

  //: A node earns its place by having a relation that is not containment. Computed once:
  //: membership cannot change without a rebuild, and recomputing it per frame was measurable.
  const related = new Set();
  layout.links.forEach(l => { related.add(l.s.id); related.add(l.t.id); });

  function matches(node) {
    if (hiddenKinds.has(node.kind)) return false;
    if (colourBy === 'cluster' && hiddenClusters.has(node.cluster)) return false;
    if (relationsOnly && !related.has(node.id)) return false;
    if (!query) return true;
    const q = query.toLowerCase();
    return node.title.toLowerCase().includes(q) || node.id.toLowerCase().includes(q);
  }

  return {
    get colourBy() { return colourBy; },
    get relationsOnly() { return relationsOnly; },
    isRelated(node) { return related.has(node.id); },
    relatedCount() { return related.size; },

    matches,
    nodes() { return NODES.filter(matches); },
    links() {
      const shown = new Set(view.nodes().map(n => n.id));
      return layout.links.filter(l =>
        !hiddenConfidence.has(l.e.confidence) && shown.has(l.s.id) && shown.has(l.t.id));
    },

    setQuery(text) { query = text; },
    toggleKind(kind, on) { if (on) hiddenKinds.delete(kind); else hiddenKinds.add(kind); },
    toggleCluster(ordinal, on) {
      if (on) hiddenClusters.delete(ordinal); else hiddenClusters.add(ordinal);
    },
    toggleConfidence(level, on) {
      if (on) hiddenConfidence.delete(level); else hiddenConfidence.add(level);
    },
    setRelationsOnly(on) { relationsOnly = on; },
    setColourBy(mode) { colourBy = mode; },
  };
})();
"""
