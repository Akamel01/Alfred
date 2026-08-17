"""The evidence plane's writer.

Inspector machinery (D20). Permanently outside what agents may modify, and outside the
agent tree: nothing under `src/` imports this package, and nothing here imports `src/`.
The separation is physical (D39) — a module boundary and a database role, never a
runtime field-name check.
"""
