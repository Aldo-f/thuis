import importlib.util
from pathlib import Path

# Load the real implementation from archive
_module_path = Path(__file__).resolve().parents[1] / "archive" / "drm" / "extract_cdm.py"
_spec = importlib.util.spec_from_file_location("_extract_cdm_impl", _module_path)
_impl = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_impl)

# Re-export public API expected by tests
__all__ = [
    "print_extraction_guide",
    "validate_cache",
    "get_cdm_cache_dir",
    "find_wvd_files",
    "validate_wvd",
    "main",
    "DEFAULT_CDM_CACHE",
    "DEFAULT_CDM_FILENAME",
    "PYWIDEVINE_AVAILABLE",
]
for name in __all__:
    globals()[name] = getattr(_impl, name)
