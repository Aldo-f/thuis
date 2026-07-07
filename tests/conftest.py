# This file ensures that the "src" directory is on sys.path for all tests.
import os
import sys

# Repository root (two levels up from this file)
repo_root = os.path.abspath(os.path.join(__file__, "..", ".."))
src_path = os.path.join(repo_root, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)
