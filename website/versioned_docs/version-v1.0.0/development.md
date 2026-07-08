---
sidebar_position: 5
---

# Development (v1.0.0)

## Overview

Version 1.0.0 of thuis was designed as a simple, self-contained tool with minimal development complexity. Unlike later versions, it did not use Python packages, virtual environments, or formal testing frameworks.

## Source Files

The entire v1.0.0 release consisted of just three files:

- `thuis.ps1` - PowerShell implementation (primary)
- `thuis.bat` - Windows Batch file wrapper
- `README.md` - Documentation

There was no separate `src/` directory, `requirements.txt`, or formal project structure.

## How It Worked

The PowerShell script (`thuis.ps1`) contained all the logic:
1. Parse command-line arguments
2. Validate the provided .mpd link
3. Process the link for download (in v1.0.0, this was a simple pass-through to the user's preferred download method)
4. Provide usage information and error handling

The Batch file (`thuis.bat`) was a simple wrapper that called the PowerShell script:
```batch
@echo off
powershell -ExecutionPolicy Bypass -File "%~dp0thuis.ps1" %*
```

## Making Changes

To modify v1.0.0 behavior:

1. **Edit the PowerShell script** - Open `thuis.ps1` in any text editor
2. **Test changes** - Run the script with various .mpd links to verify behavior
3. **Update documentation** - Modify `README.md` if needed
4. **Update the Batch file** - Only if changing the interface or calling convention

## Testing Approach

V1.0.0 used manual testing:
- Try different .mpd links to ensure they're handled correctly
- Test edge cases like malformed URLs, missing files, etc.
- Verify help text displays correctly
- Check that error messages are informative

There were no automated tests in this version.

## Building Distributions

To create a v1.0.0 release package:
1. Ensure `thuis.ps1`, `thuis.bat`, and `README.md` are present in the directory
2. Create a ZIP archive containing these three files
3. Tag the release as `v1.0.0` in Git
4. Upload the ZIP to the GitHub release

## Dependencies

**v1.0.0 had zero external dependencies.** The PowerShell script used only built-in PowerShell functionality and did not call any external programs (beyond expecting the user to have their own download method for .mpd files).

This made it extremely portable - any Windows machine with PowerShell, or any *nix system with PowerShell Core, could run it immediately.

## Limitations to Consider When Modifying

When extending or modifying v1.0.0 behavior, keep in mind:

1. **No error handling framework** - You'll need to add your own
2. **No logging system** - Debug output must be implemented manually
3. **No configuration system** - All settings come from command-line arguments or hardcoded values
4. **Cross-platform considerations** - Remember that .bat files won't work on *nix systems, and vice-versa for .ps1 without PowerShell

## Comparison with Later Versions

Starting with v2.0.0, the project evolved to:
- Use Python as the primary implementation language
- Introduce dependency management (requirements.txt)
- Add automated testing
- Implement proper configuration and credential handling
- Add structured logging
- Integrate with yt-dlp for actual downloading

v1.0.0 remains the simplest version - ideal for understanding the core concept or as a starting point for minimal implementations.
