"""The run fingerprint record — the declared configuration a run is measured on.

Inspector machinery (D20). `record.py` holds the value and compares; it reads nothing.
The two assertions that read the live world against it are C4 and C11 in
`harness/containment/image.py`, which were blocked on this module's absence rather than
on O5 (ADR-0018, ADR-0019, closed by ADR-0020).

`FieldDiff` lives here and `harness/lane/lane_fingerprint.py` imports it, so the shape a
difference is reported in has exactly one definition.
"""
