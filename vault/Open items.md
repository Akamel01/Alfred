---
kind: index
title: "Open items board"
generated: true
---

# Open items board

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

What is not done, and who owns it. Operator items are non-delegable by definition; four of them block stages.

## Stages not finished

```dataview
TABLE status, completion, clause
FROM "vault/execution"
WHERE kind = "stage" AND status != "done"
SORT number ASC
```

## Operator-owned, non-delegable

```dataview
TABLE due, blocks
FROM "vault/execution"
WHERE kind = "operator-item"
SORT due ASC
```

## Kill criteria

```dataview
TABLE status, consequence
FROM "vault/charter"
WHERE kind = "kill-criterion"
SORT number ASC
```

## Risks not accepted

```dataview
TABLE status
FROM "vault/charter"
WHERE kind = "risk" AND status != "accepted"
SORT number ASC
```

## Targets nothing has defined yet

```dataview
TABLE source
FROM "vault/execution"
WHERE kind = "unresolved"
```
