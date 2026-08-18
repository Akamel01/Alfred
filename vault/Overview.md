---
kind: index
title: "Alfred knowledge graph"
generated: true
---

# Alfred knowledge graph

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

359 nodes, 342 edges, generated from the repository. Every note is derived; nothing is authored here.

## Everything, by kind

```dataview
TABLE length(rows) AS Notes
FROM "vault"
WHERE generated AND kind
GROUP BY kind
SORT length(rows) DESC
```
