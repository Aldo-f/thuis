---
sidebar_position: 1
---

# What is thuis? (v3.0.0)

**thuis version 3.0.0** represents a major milestone in the thuis project, released in February 2026. This version introduced significant new features and architectural improvements while maintaining backward compatibility with previous versions.

## Major Features Introduced in v3.0.0

### 1. Enhanced User Interface
- **Interactive mode** - Added a menu-driven interface for easier navigation
- **Progress bars** - Improved visual feedback during downloads
- **Color-coded output** - Better distinction between different types of messages
- **Interactive prompts** - Guided setup for first-time users

### 2. Advanced Download Capabilities
- **Playlist support** - Native handling of VRT MAX playlists and series
- **Episode detection** - Automatic identification and ordering of TV show episodes
- **Smart naming** - Intelligent file naming based on show title, season, and episode
- **Duplicate detection** - Prevents downloading the same content multiple times

### 3. Improved Metadata Handling
- **Extended metadata extraction** - Additional fields like genre, air date, and ratings
- **Thumbnail selection** - Option to choose from multiple available thumbnails
- **Chapter information** - Extraction and storage of chapter markers when available
- **Series information** - Links to related content and recommendations

### 4. Configuration Management
- **Config file support** - Persistent settings via `config.ini`
- **Profile management** - Save and switch between different download preferences
- **Default value customization** - Set personal preferences for format, quality, etc.
- **Environment variable override** - All settings can be overridden via env vars

### 5. Developer Experience Improvements
- **Modular architecture** - Better separation of concerns for easier maintenance
- **Enhanced logging** - Structured logging with multiple output formats
- **Improved error reporting** - More detailed error messages with troubleshooting hints
- **Test coverage expansion** - Increased unit test coverage for core components

## Continuing Features from Previous Versions

v3.0.0 retains all the core functionality from earlier versions:
- Secure VRT MAX authentication with credential management
- Format selection and quality control
- Subtitle download and embedding options
- Metadata file generation (JSON, XML, etc.)
- Batch processing capabilities
- Resume capability for interrupted downloads
- Comprehensive logging and error handling

## Target Use Cases

v3.0.0 is particularly well-suited for:
- Users who want a more interactive and guided experience
- Those downloading entire series or seasons with consistent naming
- Collectors who value detailed metadata and thumbnails
- Users who prefer to save their preferences for repeated use
- Anyone who appreciates polished user experience in CLI tools

## Migration Notes

Users upgrading from v2.x will notice:
- New interactive features available via `--interactive` flag
- Enhanced default behaviors for series and playlist handling
- Additional metadata fields in output files
- New configuration options in the optional config file
- Improved error messages and troubleshooting guidance

The core command-line interface remains familiar, ensuring a smooth transition for existing users.
