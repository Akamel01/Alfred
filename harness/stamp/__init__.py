"""Inspector-side reading of product result stamps.

**Named `stamp` and not `provenance`, deliberately.** `harness/` has no `__init__.py` — it is
a namespace package — so pytest prepends `harness/` itself to `sys.path` when collecting a
test inside one of its subpackages. Any subpackage here whose name matches a package under
`src/` therefore becomes importable as that top-level name and shadows the product module:
`harness/provenance/` made `import provenance.encoding` fail across eleven test modules while
`pytest tests` on its own stayed green. A directory name in this tree is a global name.
"""
