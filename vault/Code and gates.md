---
kind: index
title: "Code and gates"
generated: true
---

# Code and gates

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

What the product tree's lint and type gates actually reach is narrower than the tree. `lint_gated` records it rather than letting the graph imply otherwise.

## Modules outside ruff and pyright

```dataview
TABLE tree, protected
FROM "vault/code"
WHERE kind = "module" AND lint_gated = "false" AND present = "true"
SORT tree ASC, title ASC
```

## D20-protected — inspector machinery

```dataview
TABLE tree
FROM "vault/code"
WHERE contains(tags, "protected")
SORT title ASC
```

## Declared and absent

```dataview
TABLE source
FROM "vault/code"
WHERE present = "false"
```

## Gate steps, in order

```dataview
TABLE job, ordinal, kind
FROM "vault/gates"
WHERE kind = "gate-step"
SORT job ASC, ordinal ASC
```
