import os, sys, pathlib
print(f"[DEBUG] Loading src/thuis __init__.py from {__file__}")
# Ensure the top-level 'thuis' package (containing downloader_yt) is also on the package path
project_root = pathlib.Path(__file__).resolve().parents[2]
parent_package = project_root / "thuis"
if parent_package.is_dir():
    __path__.append(str(parent_package))