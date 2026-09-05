# This file ensures that the "src" directory is on sys.path for all tests.
import os
import sys
import tempfile

# Repository root (two levels up from this file)
repo_root = os.path.abspath(os.path.join(__file__, "..", ".."))
src_path = os.path.join(repo_root, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)


def _tmp_db_path():
    """Return a temp sqlite DB path isolated from the real ~/.thuis/state.db."""
    return os.path.join(tempfile.gettempdir(), "thuis_test_state.db")


import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def isolate_test_db():
    """Use a temporary state.db for every test so real downloads aren't affected."""
    db_path = _tmp_db_path()
    # Clean any leftover test DB
    if os.path.exists(db_path):
        os.remove(db_path)

    import thuis.watchlist as wl_module
    orig_watchlist_db = wl_module.WatchlistDB

    def make_temp_db(*args, **kwargs):
        return orig_watchlist_db(db_path=db_path)

    with patch.object(wl_module, "WatchlistDB", make_temp_db):
        yield

    if os.path.exists(db_path):
        os.remove(db_path)
