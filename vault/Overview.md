---
kind: index
title: "Alfred knowledge graph"
generated: true
---

# Alfred knowledge graph

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

590 nodes, 1047 edges, generated from the repository. Every note is derived; nothing is authored here.

## Everything, by kind

```dataview
TABLE length(rows) AS Notes
FROM "vault"
WHERE generated AND kind
GROUP BY kind
SORT length(rows) DESC
```

## Refresh

This vault is derived. Nothing here is authored, and a hand edit fails
`python3 tools/gen_vault.py --check`, so the way to change a note is to change what it was
read from and rebuild.

```
python3 tools/serve_vault.py
```

Then open <http://127.0.0.1:8787> and press **Regenerate from repository**. One press re-syncs the
plan mirror, re-reads the repository, and rewrites `vault/`, `graph.json` and
`docs-graph.html` together, so the three never disagree about what the repository says.

The button is a link rather than a button because a note is markdown and markdown does not
run. It is on the served page, where code can run and where the working tree is reachable.
