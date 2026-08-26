#!/usr/bin/env python3
"""Factory generator for orchestration canvas.

Reads `orchestration/topology.json` + `policy/node-palette.json`, validates via
same logic as `scripts/lint_topology.py`, emits two outputs:

  1. orchestration-canvas.html — single-file HTML with embedded JSONs + vanilla JS
  2. orchestration-graph.svg   — static preview (pure function of topology)

Outputs default to `vault/orchestration/` but respect --output-dir.

Import-safe; tested with --check (byte-identical check).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
# vault/ is generated-only (managed by gen_vault.py); emitting there would make the
# canvas an orphan. Spec allows orchestration/ fallback in that case, so default there.
DEFAULT_OUT = REPO_ROOT / "orchestration"
PALETTE_PATH = REPO_ROOT / "policy" / "node-palette.json"
TOPOLOGY_PATH = REPO_ROOT / "orchestration" / "topology.json"

CONTRACT_COLOR: dict[str, str] = {
    "delegates-to": "#2563eb",
    "hands-off-to": "#059669",
    "reviews": "#d97706",
    "feeds": "#7c3aed",
}

CATEGORY_COLOR: dict[str, str] = {
    "planning": "#3b82f6",
    "execution": "#059669",
    "review": "#d97706",
    "operator": "#7c3aed",
}


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _embed(payload: dict) -> str:
    """JSON safe inside script element."""
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return (
        raw.replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def _build_svg(topology: dict, palette: dict) -> str:
    nodes = topology.get("nodes", [])
    edges = topology.get("edges", [])
    palette_by_id = {n["id"]: n for n in palette.get("nodes", [])}
    if not nodes:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="400"><text x="10" y="20">empty topology</text></svg>'
    # compute bounds
    xs = [n["position"]["x"] for n in nodes]
    ys = [n["position"]["y"] for n in nodes]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    pad = 60
    span_x = (max_x - min_x) or 200
    span_y = (max_y - min_y) or 200
    width = 900
    height = 600
    scale_x = (width - 2 * pad) / (span_x + 20)
    scale_y = (height - 2 * pad) / (span_y + 20)
    scale = min(scale_x, scale_y, 2.0)

    def to_svg(n: dict) -> tuple[float, float]:
        x = pad + (n["position"]["x"] - min_x) * scale + (width - 2 * pad - span_x * scale) / 2
        y = pad + (n["position"]["y"] - min_y) * scale + (height - 2 * pad - span_y * scale) / 2
        return x, y

    by_id = {n["id"]: n for n in nodes}
    parts: list[str] = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')
    parts.append('<rect width="100%" height="100%" fill="#f8f6f1"/>')
    # edges first
    for e in edges:
        src = by_id.get(e["source"])
        tgt = by_id.get(e["target"])
        if not src or not tgt:
            continue
        x1, y1 = to_svg(src)
        x2, y2 = to_svg(tgt)
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        dx, dy = x2 - x1, y2 - y1
        leng = (dx * dx + dy * dy) ** 0.5 or 1
        nx, ny = -dy / leng, dx / leng
        off = leng * 0.12
        cx, cy = mx + nx * off, my + ny * off
        col = CONTRACT_COLOR.get(e.get("contract", ""), "#999")
        parts.append(
            f'<path d="M{x1:.1f},{y1:.1f} Q{cx:.1f},{cy:.1f} {x2:.1f},{y2:.1f}" fill="none" stroke="{col}" stroke-width="2" opacity="0.85"/>'
        )
        # arrowhead
        import math

        ang = math.atan2(y2 - cy, x2 - cx)
        ah = 10
        aw = 6
        x3 = x2 - math.cos(ang) * ah + math.sin(ang) * aw
        y3 = y2 - math.sin(ang) * ah - math.cos(ang) * aw
        x4 = x2 - math.cos(ang) * ah - math.sin(ang) * aw
        y4 = y2 - math.sin(ang) * ah + math.cos(ang) * aw
        parts.append(f'<polygon points="{x2:.1f},{y2:.1f} {x3:.1f},{y3:.1f} {x4:.1f},{y4:.1f}" fill="{col}"/>')
        # label at quarter
        qx = 0.25 * x1 + 0.5 * cx + 0.25 * x2
        qy = 0.25 * y1 + 0.5 * cy + 0.25 * y2
        contract = e.get("contract", "")
        parts.append(f'<g transform="translate({qx:.1f},{qy:.1f})"><rect x="-30" y="-8" width="60" height="10" rx="3" fill="white" opacity="0.9"/><text text-anchor="middle" font-size="7" font-family="ui-monospace,monospace" fill="{col}">{contract}</text></g>')
    # nodes
    for n in nodes:
        x, y = to_svg(n)
        pal = palette_by_id.get(n.get("kind", ""), {})
        col = CATEGORY_COLOR.get(pal.get("category", ""), "#6b7280")
        r = 18
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{col}" stroke="white" stroke-width="2"/>')
        label = (n.get("label") or n.get("kind") or "")[:14]
        parts.append(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" dy="4" font-size="8" font-family="system-ui" font-weight="700" fill="white">{label}</text>')
        parts.append(f'<text x="{x:.1f}" y="{y+24:.1f}" text-anchor="middle" font-size="6" font-family="ui-monospace,monospace" fill="#6b7280">{n.get("kind","")}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def _build_html(topology: dict, palette: dict) -> str:
    """Minimal faithful HTML shell embedding JSONs."""
    topo_json = _embed(topology)
    pal_json = _embed(palette)
    # Reuse prototype canvas JS? For now embed lean viewer + reuse camera pattern inline.
    # Keep zero deps, inline CSS, vanilla JS.
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Orchestration Canvas — Production</title>
<style>
:root{{--bg:#f8f6f1;--ink:#1a1a1a;--ink-faint:#9a9590;--ground:#ffffff;--border:#e8e2d9;--accent:#3b82f6;--panel:#fdfcfa}}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{height:100%;font:13px/1.4 ui-sans,system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--ink)}}
#app{{display:flex;flex-direction:column;height:100%}}
#toolbar{{display:flex;gap:8px;padding:8px 12px;border-bottom:1px solid var(--border);background:var(--panel);align-items:center;flex-wrap:wrap}}
#toolbar button,#toolbar label.btn{{font:12px ui-monospace,monospace;padding:6px 10px;border:1px solid var(--border);background:var(--ground);border-radius:6px;cursor:pointer}}
#toolbar .hint{{font:11px ui-monospace,monospace;color:var(--ink-faint);margin-left:auto}}
#main{{flex:1;display:flex;min-height:0}}
#palette{{width:220px;min-width:180px;border-right:1px solid var(--border);background:var(--panel);overflow:auto;padding:10px;display:flex;flex-direction:column;gap:12px}}
#palette h2{{font:11px ui-monospace,monospace;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-faint)}}
.cat{{border:1px solid var(--border);border-radius:8px;overflow:hidden;background:var(--ground)}}
.cat-head{{font:11px ui-monospace,monospace;padding:6px 8px;background:var(--bg);border-bottom:1px solid var(--border);text-transform:uppercase;letter-spacing:.04em}}
.cat-items{{display:flex;flex-direction:column}}
.p-item{{display:flex;align-items:center;gap:8px;padding:7px 8px;cursor:grab;border-bottom:1px solid #f0ece5;font-size:12px}}
#stage-wrap{{flex:1;position:relative;overflow:hidden;background:var(--bg)}}
#stage-canvas{{position:absolute;inset:0;width:100%;height:100%;outline:none}}
#status{{padding:6px 12px;border-top:1px solid var(--border);background:var(--panel);font:11px ui-monospace,monospace;color:var(--ink-faint);display:flex;gap:16px}}
</style>
</head>
<body>
<div id="app">
  <div id="toolbar">
    <button id="btn-save">Save</button>
    <button id="btn-download">Export</button>
    <label class="btn">Import<input id="file-input" type="file" accept=".json,application/json" hidden></label>
    <button id="btn-copy">Copy JSON</button>
    <span id="save-hint" class="hint">Production canvas — generated</span>
  </div>
  <div id="main"><div id="palette"></div><div id="stage-wrap"><canvas id="stage-canvas" tabindex="0"></canvas></div></div>
  <div id="status"><span id="stat-nodes"></span><span id="stat-edges"></span><span id="stat-msg">generated from orchestration/topology.json</span></div>
</div>
<script type="application/json" id="topology-data">{topo_json}</script>
<script type="application/json" id="palette-data">{pal_json}</script>
<script>
'use strict';
const TOPO = JSON.parse(document.getElementById('topology-data').textContent);
const PAL = JSON.parse(document.getElementById('palette-data').textContent);
const paletteById = new Map(PAL.nodes.map(n=>[n.id,n]));
const nodes = TOPO.nodes.map(n=>({{id:n.id,kind:n.kind,label:n.label||n.kind,x:n.position.x,y:n.position.y}}));
const edges = TOPO.edges.map(e=>({{id:e.id,source:e.source,target:e.target,contract:e.contract}}));
const byId = new Map(nodes.map(n=>[n.id,n]));
const canvas = document.getElementById('stage-canvas');
const ctx = canvas.getContext('2d');
const CONTRACT_COLOR = {{"delegates-to":"#2563eb","hands-off-to":"#059669","reviews":"#d97706","feeds":"#7c3aed"}};
const CATEGORY_COLOR = {{"planning":"#3b82f6","execution":"#059669","review":"#d97706","operator":"#7c3aed"}};
let tx=0,ty=0,scale=1;
function fit(){{ if(!nodes.length) return; const xs=nodes.map(n=>n.x), ys=nodes.map(n=>n.y); const minX=Math.min(...xs), maxX=Math.max(...xs), minY=Math.min(...ys), maxY=Math.max(...ys); const w=canvas.clientWidth,h=canvas.clientHeight; const sx=(w-80)/((maxX-minX)||200), sy=(h-80)/((maxY-minY)||200); scale=Math.min(sx,sy,2.4); tx=w/2-((maxX+minX)/2)*scale; ty=h/2-((maxY+minY)/2)*scale; }}
function draw(){{ const ratio=window.devicePixelRatio||1; const w=canvas.clientWidth,h=canvas.clientHeight; if(canvas.width!==w*ratio||canvas.height!==h*ratio){{canvas.width=w*ratio;canvas.height=h*ratio;}} ctx.setTransform(ratio,0,0,ratio,0,0); ctx.clearRect(0,0,w,h); ctx.save(); ctx.translate(tx,ty); ctx.scale(scale,scale);
  edges.forEach(e=>{{ const s=byId.get(e.source), t=byId.get(e.target); if(!s||!t) return; const col=CONTRACT_COLOR[e.contract]||'#999'; ctx.beginPath(); ctx.moveTo(s.x,s.y); const mx=(s.x+t.x)/2,my=(s.y+t.y)/2, dx=t.x-s.x, dy=t.y-s.y, len=Math.hypot(dx,dy)||1, nx=-dy/len, ny=dx/len; const cx=mx+nx*len*0.15, cy=my+ny*len*0.15; ctx.quadraticCurveTo(cx,cy,t.x,t.y); ctx.strokeStyle=col; ctx.lineWidth=1.4/scale; ctx.stroke(); }});
  nodes.forEach(n=>{{ const pal=paletteById.get(n.kind); const col=CATEGORY_COLOR[pal?pal.category:'']||'#6b7280'; ctx.beginPath(); ctx.arc(n.x,n.y,16,0,Math.PI*2); ctx.fillStyle=col; ctx.fill(); ctx.fillStyle='#fff'; ctx.font='700 10px system-ui'; ctx.textAlign='center'; ctx.fillText((n.label||n.kind).slice(0,14),n.x,n.y+3); }});
  ctx.restore();
}}
function refresh(){{ document.getElementById('stat-nodes').textContent=nodes.length+' nodes'; document.getElementById('stat-edges').textContent=edges.length+' edges'; }}
canvas.addEventListener('wheel', e=>{{ e.preventDefault(); const rect=canvas.getBoundingClientRect(); const f=Math.exp(-e.deltaY*0.0016); const nx=Math.min(6,Math.max(0.18,scale*f)); tx=e.clientX-rect.left-(e.clientX-rect.left-tx)*(nx/scale); ty=e.clientY-rect.top-(e.clientY-rect.top-ty)*(nx/scale); scale=nx; draw(); }},{{passive:false}});
let drag=null; canvas.addEventListener('pointerdown', e=>{{drag={{x:e.clientX,y:e.clientY}}; canvas.setPointerCapture(e.pointerId);}}); canvas.addEventListener('pointermove', e=>{{if(!drag) return; tx+=e.clientX-drag.x; ty+=e.clientY-drag.y; drag.x=e.clientX; drag.y=e.clientY; draw();}}); canvas.addEventListener('pointerup', ()=>{{drag=null;}});
document.getElementById('btn-download').addEventListener('click', ()=>{{ const blob=new Blob([JSON.stringify(TOPO,null,2)],{{type:'application/json'}}); const url=URL.createObjectURL(blob); const a=document.createElement('a'); a.href=url; a.download='topology.json'; a.click(); setTimeout(()=>URL.revokeObjectURL(url),500);}});
document.getElementById('btn-copy').addEventListener('click', async()=>{{ const txt=JSON.stringify(TOPO,null,2); try{{await navigator.clipboard.writeText(txt);}}catch(_e){{}} }});
document.getElementById('btn-save').addEventListener('click', async()=>{{ const data=JSON.stringify(TOPO,null,2); if('showSaveFilePicker' in window){{try{{const h=await window.showSaveFilePicker({{suggestedName:'topology.json',types:[{{description:'JSON',accept:{{'application/json':['.json']}}}}]}}); const w=await h.createWritable(); await w.write(data); await w.close(); return;}}catch(_e){{}}}} document.getElementById('btn-download').click(); }});
(function(){{ const pal=document.getElementById('palette'); const cats={{}}; PAL.nodes.forEach(n=>{{(cats[n.category]=cats[n.category]||[]).push(n);}}); Object.entries(cats).forEach(([cat,items])=>{{const box=document.createElement('div'); box.className='cat'; const head=document.createElement('div'); head.className='cat-head'; head.textContent=cat; box.append(head); const list=document.createElement('div'); list.className='cat-items'; items.forEach(it=>{{const row=document.createElement('div'); row.className='p-item'; row.textContent=it.icon+' '+it.label; row.title=it.description; list.append(row);}}); box.append(list); pal.append(box);}});}})();
refresh(); fit(); draw(); window.addEventListener('resize', ()=>{{fit();draw();}});
</script>
</body>
</html>
"""


def _validate_or_exit() -> tuple[dict, dict]:
    # reuse lint logic without import to avoid circular deps; import locally
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    try:
        import lint_topology  # type: ignore[import-not-found]

        findings = lint_topology.check_topology(base=REPO_ROOT)
        if findings.violations:
            for v in findings.violations:
                print(f"FAIL {v}", file=sys.stderr)
            sys.exit(1)
    finally:
        if str(REPO_ROOT / "scripts") in sys.path:
            sys.path.remove(str(REPO_ROOT / "scripts"))
    return _load_json(PALETTE_PATH), _load_json(TOPOLOGY_PATH)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate orchestration canvas HTML + SVG")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT, help="output directory")
    parser.add_argument("--check", action="store_true", help="fail if committed output is stale")
    args = parser.parse_args(argv)

    palette = _load_json(PALETTE_PATH)
    topology = _load_json(TOPOLOGY_PATH)

    # validate
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    try:
        import lint_topology  # type: ignore[import-not-found]

        findings = lint_topology.check_topology(base=REPO_ROOT)
        if findings.violations:
            for v in findings.violations:
                print(f"FAIL {v}", file=sys.stderr)
            if args.check:
                print("lint failed — not generating", file=sys.stderr)
            return 1
    finally:
        if str(REPO_ROOT / "scripts") in sys.path:
            sys.path.remove(str(REPO_ROOT / "scripts"))

    html = _build_html(topology, palette)
    svg = _build_svg(topology, palette)

    out_dir = args.output_dir
    if isinstance(out_dir, str):
        out_dir = Path(out_dir)
    if not out_dir.is_absolute():
        out_dir = REPO_ROOT / out_dir

    # Determine expected paths
    html_path = out_dir / "orchestration-canvas.html"
    svg_path = out_dir / "orchestration-graph.svg"

    if args.check:
        problems: list[str] = []
        if not html_path.is_file():
            problems.append(f"missing {html_path}")
        else:
            existing = html_path.read_text(encoding="utf-8")
            if existing != html:
                problems.append(f"{html_path} is stale — run python3 tools/orchestration/gen_canvas.py")
        if not svg_path.is_file():
            problems.append(f"missing {svg_path}")
        else:
            existing_svg = svg_path.read_text(encoding="utf-8")
            if existing_svg != svg:
                problems.append(f"{svg_path} is stale — run python3 tools/orchestration/gen_canvas.py")
        if problems:
            for p in problems:
                print(p, file=sys.stderr)
            return 1
        print(f"OK canvas current ({len(topology.get('nodes', []))} nodes, {len(topology.get('edges', []))} edges)")
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    html_path.write_text(html, encoding="utf-8")
    svg_path.write_text(svg, encoding="utf-8")
    print(f"OK wrote {html_path.relative_to(REPO_ROOT)} and {svg_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
