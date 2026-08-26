---
status:        provisional
owner:         human
enforcement:   review-cadence
evidence:      none — written as destination deliverable of wayfinder map #8; generated evidence is orchestration/topology.json + policy/node-palette.json + tools/orchestration/gen_canvas.py + scripts/lint_topology.py
falsifies_if:  The topology file contains a structure the lint does not reject, or the canvas emits a contract the palette does not declare.
review_after:  Phase 3
---

# Orchestration Canvas Specification

---

## 1. Surface Behavior

### 1.1 Artifact Class

The orchestration canvas is an **operator-local generated artifact** — a self-contained HTML file emitted by a factory generator, opened from disk (`file://` origin), and edited exclusively through its own interface. It is not a served page; no server, no auth, no CSP.

### 1.2 Precedent

Follows the `docs-graph.html` pattern established in `tools/vaultgraph/render/`: vanilla JS, zero dependencies, no CDN, no build step, JSON-in-`<script type="application/json">` block, `<` escaped to `\u003c`.

### 1.3 Save Mechanics

**Primary:** File System Access API (`showSaveFilePicker`) — writes `topology.json` directly to disk where the operator chooses.

**Fallback 1 (API unavailable):** Download → operator saves → next session uses upload (`<input type="file">`) to load.

**Fallback 2 (file:// origin blocks FS Access):** Clipboard copy/paste of JSON (least preferred, documented).

**No network requests ever.** No telemetry, no phoning home.

### 1.4 Security Model

- No secrets in topology (only role graph structure)
- No credentials in palette
- CSP not applicable (local file origin)
- No external resources (fonts, scripts, images — all inline)
- Sanitization: operator authors topology; no untrusted input path

---

## 2. Palette Schema

### 2.1 Source of Truth

`policy/node-palette.json` — machine-readable, protected by `policy/` prefix (D20/ADR-0031), bound to code via lint.

### 2.2 Entry Fields

```json
{
  "id": "string (unique, stable, kebab-case)",
  "label": "string (human-readable)",
  "description": "string (one sentence)",
  "ports": {
    "in": ["contract-type-id", ...],
    "out": ["contract-type-id", ...]
  },
  "defaults": {
    "out:contract-type-id": "default-contract-type"
  },
  "icon": "string (emoji or inline SVG path, optional)",
  "category": "string (planning | execution | review | operator, optional)"
}
```

### 2.3 Binding Lint

Extends `harness/patch/test_protected_binding.py` pattern: every code-side node-kind enum must be bijective with a palette `id`. One spelling each. Drift fails CI.

### 2.4 Seed List (Authoritative)

Finalized in ticket #12. Includes:

| Category | Node Kinds (Illustrative) |
|---|---|
| planning | planner, wayfinder, architect, product-manager |
| execution | code-writer, researcher, drafter, domain-expert |
| review | reviewer, verifier, validator, examiner, tester |
| operator | operator-gate, harness-runner, criterion-runner, evidence-store, worker-port, fingerprint-capture, mutation-controller, restore-drill |

Source and sink kinds intentionally have an empty side (e.g., `planner` has no `in`, `evidence-store` has no `out`); every intermediate kind has at least one in-port and one out-port. No orphan kinds.

---

## 3. Edge Contract Types

### 3.1 Vocabulary (Authoritative)

Finalized in ticket #11. Each type declares legal source/target node-kinds:

| Contract Type | Semantics | Source Kinds | Target Kinds | Default For |
|---|---|---|---|---|
| `delegates-to` | Authority to execute sub-task | planner, wayfinder, architect | code-writer, researcher, drafter, domain-expert | planner→code-writer |
| `hands-off-to` | Work product flows | researcher, drafter, code-writer | reviewer, verifier, validator, examiner, tester | researcher→drafter |
| `reviews` | Verdict relationship (inspector) | reviewer, verifier, validator, architect | code-writer, drafter, planner | reviewer→code-writer |
| `feeds` | Artifact/criterion input | criterion-runner, evidence-store, fingerprint-capture | verifier, validator, examiner, tester | criterion-runner→evidence-store |

### 3.2 Compatibility Matrix

A (source-kind, target-kind) pair maps to exactly one legal contract type (or empty = no edge allowed). The canvas enforces this structurally: only compatible ports highlight on drag.

### 3.3 Multiplicity & Cycles

- `delegates-to`: multiple outgoing allowed; cycles forbidden (delegation tree)
- `hands-off-to`: multiple allowed both directions; cycles allowed (feedback loops)
- `reviews`: multiple reviewers per target allowed; cycles forbidden
- `feeds`: multiple producers → multiple consumers allowed; cycles forbidden

---

## 4. Topology File Format

### 4.1 File Location

`orchestration/topology.json` — hand-authored source, edited only through the canvas.

### 4.2 Schema

```json
{
  "version": 1,
  "metadata": {
    "created_at": "ISO8601",
    "updated_at": "ISO8601",
    "author": "operator",
    "description": "string"
  },
  "nodes": [
    {
      "id": "string (UUID)",
      "kind": "node-kind-id (from palette)",
      "label": "string (optional override)",
      "position": { "x": 0, "y": 0 }
    }
  ],
  "edges": [
    {
      "id": "string (UUID)",
      "source": "node-id",
      "source_port": "port-name",
      "target": "node-id",
      "target_port": "port-name",
      "contract": "contract-type-id",
      "label": "string (optional)"
    }
  ]
}
```

### 4.3 Invariants (Lint-Enforced)

- All node `id`s unique
- All edge `source`/`target` reference existing nodes
- `source_port` declared in source node's palette `out` ports
- `target_port` declared in target node's palette `in` ports
- `contract` legal for `(source_kind, target_kind)` per compatibility matrix
- No duplicate edges (same source+port+target+port+contract)
- Multiplicity/cycle rules per contract type (lint checks)

---

## 5. Generator Contract

### 5.1 Module

`tools/orchestration/gen_canvas.py` — factory generator, no external deps.

### 5.2 Inputs

- `orchestration/topology.json` (required)
- `policy/node-palette.json` (required)
- Optional: `--output-dir` (default: `orchestration/` — `vault/` is generated-only, so `vault/orchestration/` would be a second generated layer; code uses `orchestration/` fallback, spec updated to match)

### 5.3 Outputs

1. **Interactive canvas:** `orchestration-canvas.html` — single-file HTML with embedded topology + palette + vanilla JS editor
2. **Static preview:** `orchestration-graph.svg` — server-generated inline SVG (pure function of topology, for docs/read-model)

### 5.4 Canvas HTML Structure

- Embedded topology JSON in `<script type="application/json" id="topology-data">`
- Embedded palette JSON in `<script type="application/json" id="palette-data">`
- Inline CSS (scoped, no external)
- Inline JS (vanilla, zero deps, `<` escaped, follows `script.py` patterns)
- `<canvas id="stage-canvas">` for rendering
- Palette panel (sidebar), toolbar (save/export/import/zoom)
- Accessible: keyboard navigation, ARIA labels

---

## 6. Lint Contract

### 6.1 Module

`scripts/lint_topology.py` — runs in integrity job (gates.yml).

### 6.2 Rules

| Rule | Code | Severity |
|---|---|---|
| Unique node IDs | `TOP001` | ERROR |
| Edge references valid nodes | `TOP002` | ERROR |
| Source port declared in palette | `TOP003` | ERROR |
| Target port declared in palette | `TOP004` | ERROR |
| Contract legal for endpoint kinds | `TOP005` | ERROR |
| No duplicate edges | `TOP006` | ERROR |
| Multiplicity/cycle rules | `TOP007` | ERROR |
| Palette conformance (all nodes from palette) | `TOP008` | ERROR |
| Schema version present | `TOP009` | ERROR |

### 6.3 Self-Test

`lint_topology.py --self-test` plants violations and asserts they are caught.

---

## 7. Save/Export Mechanics (Canvas)

### 7.1 Save (FS Access API)

```javascript
async function saveTopology(topology) {
  const handle = await window.showSaveFilePicker({
    suggestedName: 'topology.json',
    types: [{ description: 'JSON', accept: { 'application/json': ['.json'] } }]
  });
  const writable = await handle.createWritable();
  await writable.write(JSON.stringify(topology, null, 2));
  await writable.close();
}
```

### 7.2 Export (Download)

```javascript
function downloadTopology(topology) {
  const blob = new Blob([JSON.stringify(topology, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = 'topology.json'; a.click();
  URL.revokeObjectURL(url);
}
```

### 7.3 Import (Upload)

```javascript
async function loadTopologyFromFile() {
  const [handle] = await window.showOpenFilePicker({
    types: [{ description: 'JSON', accept: { 'application/json': ['.json'] } }]
  });
  const file = await handle.getFile();
  return JSON.parse(await file.text());
}
```

### 7.4 Clipboard Fallback

Copy JSON to clipboard (`navigator.clipboard.writeText`); paste via prompt + `JSON.parse`.

---

## 8. Security Model

- Topology file contains no secrets, credentials, or network endpoints
- Palette contains no secrets
- Canvas makes no network requests (no fetch, no WebSocket, no WebRTC)
- CSP not applicable (local file)
- Sanitization: operator is the sole author; no untrusted input enters the topology
- Generator runs in factory (trusted); output is deterministic function of inputs

---

## 9. Glossary

| Term | Definition |
|---|---|
| **Orchestration Node** | A vertex in the topology graph representing a role/agent kind (from palette). |
| **Node Kind** | The `id` of a palette entry; the type of a node. |
| **Contract Edge** | A directed typed connection between two nodes representing a hand-off or authority relationship. |
| **Port Compatibility** | The rule that an edge's contract type must be legal for the (source-kind, target-kind) pair per the compatibility matrix. |
| **Topology Source** | The hand-authored `orchestration/topology.json` file — the single source of truth for the graph. |
| **Canvas Artifact** | The generated interactive HTML file (`orchestration-canvas.html`) that edits the topology source. |

---

## 10. Versioning

- Topology schema `version` integer (starts at 1)
- Breaking change → version bump → migration script in `tools/orchestration/migrate/`
- Palette schema versioned separately via `policy/node-palette.json` `version` field
- Generator emits its own version in output metadata

---

*This specification is the destination deliverable of wayfinder map #8. When merged, the map closes.*