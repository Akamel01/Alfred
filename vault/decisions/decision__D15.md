---
kind: decision
id: "decision:D15"
title: "LangGraph as the graph engine"
shape: "table-row"
number: "15"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:59"
extractor: "decisions"
aliases:
  - "D15"
  - "LangGraph as the graph engine"
generated: true
---

# LangGraph as the graph engine

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:59`

## Statement

**LangGraph as the graph engine**, with Pydantic state schemas and the Postgres checkpointer.

## Fields

| Field | Value |
|---|---|
| `rationale` | Battle-tested implementation of typed channels, reducers, and conditional edges. Adopting the model directly avoids designing it from scratch. |
