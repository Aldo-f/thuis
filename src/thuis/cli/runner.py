"""CLI runner that delegates to the main orchestration logic.

This is a thin wrapper; the full pipeline lives in thuis.main for now.
As refactoring continues, logic will migrate from main.py → here.
"""
from thuis.main import main


def run_cli(args):
    """Run with parsed args (currently delegates to main for compatibility)."""
    # The original main() builds its own parser; for incremental migration,
    # we call the original entry point. Once the parser is fully externalized,
    # this will use args directly.
    main()
