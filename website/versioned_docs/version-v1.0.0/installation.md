---
sidebar_position: 2
---

# Installation (v1.0.0)

## Getting Started

Version 1.0.0 of thuis is distributed as a simple package containing:

- `thuis.ps1` - PowerShell script for Linux/macOS/Windows PowerShell
- `thuis.bat` - Batch file for Windows Command Prompt
- `README.md` - This documentation

## System Requirements

- **Windows**: PowerShell 5.1+ or Command Prompt
- **Linux/macOS**: PowerShell Core 6+ (for the .ps1 script)
- **No additional dependencies** - the script is self-contained

## Installation Steps

1. **Download the release** - Get the v1.0.0 source code from the [releases page](https://github.com/Aldo-f/thuis/releases/tag/v1.0.0)
2 **Extract the files** - Unzip the downloaded archive to your desired location
3. **Ensure execute permissions** (Linux/macOS): 
   ```bash
   chmod +x thuis.ps1
   ```
4. **Verify PowerShell is available**:
   ```bash
   pwsh --version  # PowerShell Core
   # OR
   powershell --version  # Windows PowerShell
   ```

## Verification

To verify your installation works, run:
```bash
./thuis.ps1 --help
```
or
```bash
.\thuis.bat --help
```

You should see usage information for the tool.
