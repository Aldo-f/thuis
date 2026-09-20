#!/usr/bin/env python3
"""Top‑level wrapper for the original ``extract_cdm`` implementation.
The real code lives in ``archive/drm/extract_cdm.py``; this module simply
loads it and re‑exports its public symbols so that the test suite can
``import extract_cdm`` without needing the package prefix.
"""

import importlib.util
import pathlib

_impl_path = pathlib.Path(__file__).resolve().parents[1] / "archive" / "drm" / "extract_cdm.py"
_spec = importlib.util.spec_from_file_location("_extract_cdm_impl", _impl_path)
_impl = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_impl)

# Re‑export everything that does not start with an underscore.
for _name in dir(_impl):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_impl, _name)

__all__ = [n for n in globals() if not n.startswith("_")]
