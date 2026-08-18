"""Containment assertions: what the sandbox must prove before a run starts.

Inspector machinery (D20). Every assertion here is fail-closed, the probe erroring
included, and **`not_executed` is a failure and never a pass** (F25) — an unproven control
is a failed control.
"""
