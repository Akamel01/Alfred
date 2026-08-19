"""The stylesheet, inlined at build time.

The artifact CSP blocks every external host, so a CDN link or a webfont URL is a silent
failure rather than a fallback. The type stack is therefore deliberate rather than defaulted:
system monospace for every label and datum, system serif for statements. A register of code
should read like one.

Tokens are defined three times over, because the viewer has three theme states and not two.
The bare `:root` carries the complete light palette; `prefers-color-scheme` redefines only the
tokens, guarded so an explicit light choice beats a dark OS; `[data-theme="dark"]` redefines
them again so the toggle wins in the other direction. No component rule sets a colour outside
that token set -- a colour whose only definition sits behind a media query never applies in
the unstamped state, which is how an artifact ends up rendering one theme's text on the
other theme's ground.
"""

from __future__ import annotations

CSS = """
:root {
  color-scheme: light dark;
  --ground: #EBEDE9;
  --panel: #F5F7F3;
  --sunk: #E1E4DF;
  --ink: #161B1E;
  --ink-soft: #55605F;
  --ink-faint: #808B89;
  --rule: #CFD5D1;
  --rule-strong: #A9B2AE;
  --structural: #2D4BC7;
  --derived: #5B7FD4;
  --prose: #9A7414;
  --alarm: #A8331F;
  --good: #2F6B4F;
  --focus: #2D4BC7;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --ground: #12171A;
    --panel: #182025;
    --sunk: #0D1215;
    --ink: #DCE4E2;
    --ink-soft: #97A5A3;
    --ink-faint: #6B7A78;
    --rule: #2A353A;
    --rule-strong: #445055;
    --structural: #7E9DF5;
    --derived: #5C7CC4;
    --prose: #D2A63C;
    --alarm: #E0705A;
    --good: #6BBF95;
    --focus: #7E9DF5;
  }
}
:root[data-theme="dark"] {
  --ground: #12171A;
  --panel: #182025;
  --sunk: #0D1215;
  --ink: #DCE4E2;
  --ink-soft: #97A5A3;
  --ink-faint: #6B7A78;
  --rule: #2A353A;
  --rule-strong: #445055;
  --structural: #7E9DF5;
  --derived: #5C7CC4;
  --prose: #D2A63C;
  --alarm: #E0705A;
  --good: #6BBF95;
  --focus: #7E9DF5;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--ground);
  color: var(--ink);
  font-family: ui-monospace, "SF Mono", SFMono-Regular, "Cascadia Mono", "Roboto Mono",
               "Liberation Mono", Menlo, Consolas, monospace;
  font-size: 13px;
  line-height: 1.5;
  font-variant-numeric: tabular-nums;
}

.serif {
  font-family: ui-serif, "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
  font-variant-numeric: normal;
}

/* ---- readout ---------------------------------------------------------- */

header {
  border-bottom: 1px solid var(--rule-strong);
  background: var(--panel);
  padding: 14px 20px 0;
}
.masthead { display: flex; flex-wrap: wrap; align-items: baseline; gap: 6px 16px; }
h1 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.subtitle { color: var(--ink-soft); font-size: 12px; max-width: 62ch; }

/* A grid rather than a wrapping flex row: eight gauges on one line at desktop width and an
   even two-row block below it, never a single orphan gauge on a row of its own. */
.readout {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(158px, 1fr));
  margin: 12px -20px 0;
  border-top: 1px solid var(--rule);
}
.gauge {
  padding: 9px 20px 10px;
  border-right: 1px solid var(--rule);
  border-top: 1px solid var(--rule);
  margin-top: -1px;
}
.gauge dt {
  font-size: 10px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ink-faint);
  line-height: 1.35;
  /* Wrapping beats truncating: a gauge labelled "FALSIFICATION CONDITION" with the last
     word cut off is a readout that has stopped being a readout. */
  text-wrap: balance;
}
.gauge dd { margin: 2px 0 0; font-size: 20px; font-weight: 600; }
.gauge.alarm dd { color: var(--alarm); }
.gauge.good dd { color: var(--good); }

/* ---- frame ------------------------------------------------------------ */

/* The frame is a flex column, so the canvas takes whatever the readout and footer leave
   rather than a hardcoded offset that goes wrong the moment the readout wraps. */
main {
  flex: 1;
  display: grid;
  grid-template-columns: 210px minmax(0, 1fr);
  min-height: 440px;
}
@media (max-width: 820px) {
  main { grid-template-columns: 1fr; }
  #stage { min-height: 62vh; }
}

aside {
  border-right: 1px solid var(--rule);
  background: var(--panel);
  overflow-y: auto;
  padding: 14px 0 28px;
}
.rail-heading {
  font-size: 10px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--ink-faint);
  padding: 0 16px 6px;
  margin-top: 14px;
}
.rail-heading:first-child { margin-top: 0; }

/* How to refresh is a fact about the page, not a key to the drawing. On its own row, after
   the legend: wedged in beside the legend keys at 548px it read as a fourth key. */
.footer-status {
  flex-basis: 100%;
  padding-top: 8px;
  border-top: 1px solid var(--rule);
  color: var(--ink-faint);
}
.footer-status code { color: var(--ink-soft); }

.rail-note {
  font-size: 11px;
  line-height: 1.45;
  color: var(--ink-faint);
  padding: 8px 16px 0;
}

.toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 4px 16px;
  border: 0;
  background: none;
  color: var(--ink);
  font: inherit;
  text-align: left;
  cursor: pointer;
}
/* A cluster is named after its busiest member, and a document title is a sentence. One line
   each, elided: a rail whose rows are three lines tall stops being scannable, which is the
   only thing a rail is for. The full name is on the row's title attribute. */
.toggle > span:not(.swatch):not(.count) {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  min-width: 0;
}
.toggle:hover { background: var(--sunk); }
.toggle:focus-visible { outline: 2px solid var(--focus); outline-offset: -2px; }
.toggle[aria-pressed="false"] { color: var(--ink-faint); }
.toggle[aria-pressed="false"] .swatch { opacity: 0.25; }
.swatch { width: 9px; height: 9px; flex: none; border: 1px solid var(--rule-strong); }
.toggle .count { margin-left: auto; font-size: 11px; color: var(--ink-faint); }

#stage { position: relative; background: var(--ground); }
canvas { display: block; width: 100%; height: 100%; cursor: grab; }
canvas:active { cursor: grabbing; }
canvas:focus-visible { outline: 2px solid var(--focus); outline-offset: -2px; }

.stage-controls {
  position: absolute; top: 12px; left: 12px; right: 12px;
  display: flex; gap: 8px; flex-wrap: wrap; align-items: center;
  pointer-events: none;
}
.stage-controls > * { pointer-events: auto; }
input[type="search"] {
  flex: 1 1 180px; max-width: 300px;
  padding: 5px 9px;
  border: 1px solid var(--rule-strong);
  background: var(--panel);
  color: var(--ink);
  font: inherit;
}
input[type="search"]:focus-visible { outline: 2px solid var(--focus); outline-offset: -1px; }
button.chip {
  padding: 5px 10px;
  border: 1px solid var(--rule-strong);
  background: var(--panel);
  color: var(--ink);
  font: inherit;
  font-size: 11px;
  letter-spacing: 0.04em;
  cursor: pointer;
}
button.chip:hover { background: var(--sunk); }
/* The staleness chip is an alert, not a third control. It borrows the alarm token the gauges
   use for a count that should not be there, so "something is wrong" reads the same in both
   places on the page. */
button.chip.stale {
  border-color: var(--alarm); color: var(--alarm); font-weight: 600;
}
button.chip.stale:hover { background: var(--alarm); color: var(--panel); }
button.chip:focus-visible { outline: 2px solid var(--focus); outline-offset: 1px; }

/* ---- inspector -------------------------------------------------------- */

#inspector {
  position: absolute; top: 0; right: 0; bottom: 0;
  width: min(400px, 88%);
  background: var(--panel);
  border-left: 1px solid var(--rule-strong);
  overflow-y: auto;
  padding: 16px 18px 40px;
  transform: translateX(101%);
  transition: transform 160ms ease;
}
#inspector[data-open="true"] { transform: none; }
@media (prefers-reduced-motion: reduce) { #inspector { transition: none; } }

.kicker {
  font-size: 10px; letter-spacing: 0.11em; text-transform: uppercase;
  color: var(--ink-faint);
}
#inspector h2 { margin: 4px 0 8px; font-size: 19px; line-height: 1.28; font-weight: 600; }
#inspector .source { color: var(--ink-soft); font-size: 11px; word-break: break-all; }
#inspector h3 {
  margin: 20px 0 6px; font-size: 10px; letter-spacing: 0.11em;
  text-transform: uppercase; color: var(--ink-faint);
  border-top: 1px solid var(--rule); padding-top: 10px;
}
.falsifies {
  margin: 10px 0 0; padding: 9px 12px;
  border-left: 2px solid var(--alarm); background: var(--sunk);
  font-size: 13px; line-height: 1.45;
}
.statement { margin: 10px 0 0; font-size: 13.5px; line-height: 1.5; }
.rel { display: flex; gap: 7px; padding: 3px 0; align-items: baseline; }
.rel button {
  border: 0; background: none; padding: 0; color: var(--structural);
  font: inherit; text-align: left; cursor: pointer; text-decoration: underline;
  text-underline-offset: 2px;
}
.rel button:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; }
.rel .verb { color: var(--ink-faint); font-size: 11px; white-space: nowrap; }
.rel .evidence {
  display: block; color: var(--ink-soft); font-size: 11px; margin-top: 1px;
}
/* Neighbours and container members, as a wrapping strip of chips rather than one row each.
   A tier holding 63 documents is a list nobody scrolls; the same 63 as chips is a shape.

   Selectors are written to out-specify `.rel button`, which sets a borderless underlined link
   and would otherwise win on specificity and leave these looking like the rows above them. */
.chips { display: flex; flex-wrap: wrap; gap: 4px; min-width: 0; }
.rel .chips button, .isolate-list button.chip-link {
  border: 1px solid var(--rule); border-left-width: 3px; border-left-color: var(--ink-faint);
  background: var(--panel); color: var(--ink); font: inherit; font-size: 11px;
  padding: 2px 6px; cursor: pointer; max-width: 190px; text-decoration: none;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; display: block;
}
.rel .chips button:hover, .isolate-list button.chip-link:hover { background: var(--sunk); }
.rel .chips button:focus-visible, .isolate-list button.chip-link:focus-visible {
  outline: 2px solid var(--focus); outline-offset: 1px;
}
/* A block, not a flex column. As a flex column the 188 chips inherited `flex-shrink: 1` and
   every one of them was squeezed to 6px inside the scroll cap -- present, outlined, and
   unreadable. */
.isolate-list {
  max-height: 240px; overflow-y: auto; padding: 0 16px 6px;
}
.isolate-list button.chip-link { margin: 0 0 3px; }
.isolate-list .rail-note { margin: 6px 0 1px; }

.close {
  position: absolute; top: 12px; right: 14px;
  border: 1px solid var(--rule-strong); background: var(--panel); color: var(--ink);
  font: inherit; font-size: 11px; padding: 3px 8px; cursor: pointer;
}
.close:focus-visible { outline: 2px solid var(--focus); outline-offset: 1px; }

footer {
  border-top: 1px solid var(--rule-strong);
  background: var(--panel);
  padding: 8px 20px;
  font-size: 11px;
  color: var(--ink-faint);
  display: flex; flex-wrap: wrap; gap: 4px 18px; align-items: baseline;
}
.legend-key { display: inline-flex; align-items: center; gap: 6px; }
.legend-key svg { display: block; }
"""
