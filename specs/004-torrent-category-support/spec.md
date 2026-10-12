# Specification: Torrent Category Support for Watchlists and CLI

## Feature Overview
Add support for specifying a qBittorrent category for torrent uploads, both via a new `--category` CLI flag and hierarchically via `[cat] Category/Subcategory` directives in watchlist files.

## User Scenarios & Testing
- **Scenario 1: CLI Category Override**
  - Given a VRT MAX episode or season download command with `--auto-upload` and `--category "Media/Tv"`
  - When the torrent is uploaded to qBittorrent
  - Then it is assigned the specified category `"Media/Tv"`

- **Scenario 2: Watchlist File Category Directive**
  - Given a watchlist file containing a `[cat] Media/Tv` directive followed by watch entries
  - When the watchlist runner processes those entries
  - Then any resulting torrent uploads inherit the specified category (`"Media/Tv"`) unless overridden

## Functional Requirements
1. **CLI Flag**: Add `--category` argument to the main CLI interface, passing it through to the torrent uploader plugin config.
2. **Watchlist Directives**: Parse `[cat] <category>` lines in watchlist files (`watchlist.py`), establishing a file-level or block-level default category.
3. **Plugin Integration**: Update `torrent_uploader.py` and `qbittorrent_client.py` to accept and pass the category parameter when calling `add_torrent()`.
4. **Backward Compatibility**: If no category is specified, default to existing behavior (empty string or show name category fallback).

## Success Criteria
- `--category "Media/Tv"` successfully assigns the category in qBittorrent during uploads.
- `[cat]` lines in watchlist files correctly propagate to all subsequent watchlist entries until overridden or reset.
- All existing tests pass.
