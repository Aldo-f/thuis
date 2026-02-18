# AGENTS.md

This document provides guidelines for agentic coding agents working in the **thuis** repository.

## Project Overview

**thuis** is a PowerShell command-line utility for downloading video or audio content from `.mpd` (Media Presentation Description), `.m3u8`, `.m3u` files or URLs pointing to these types of files. It uses FFmpeg for media processing.

## Build/Lint/Test Commands

### Running the Script

```bash
# Basic execution
pwsh ./thuis.ps1 -list <media_files_or_urls>

# With all options
pwsh ./thuis.ps1 -list <media_files_or_urls> -resolutions 1080 -filename output -directory media -info -log_level info -interactive
```

### PowerShell Syntax Validation

```bash
# Check syntax without running
pwsh -NoProfile -Command "Get-Command -Syntax ./thuis.ps1"

# Parse and check for errors
pwsh -NoProfile -Command "try { \$null = [System.Management.Automation.PSParser]::Tokenize((Get-Content ./thuis.ps1 -Raw), [ref]\$null); Write-Host 'Syntax OK' } catch { Write-Error \$_ }"
```

### Running Tests

This project does not currently have a formal test framework. Manual testing can be performed by:

```bash
# Test with a sample .mpd file
pwsh ./thuis.ps1 -list sample.mpd -info

# Test interactive mode
pwsh ./thuis.ps1 -interactive
```

## Code Style Guidelines

### Naming Conventions

- **Functions**: Use PascalCase with verb-noun naming convention
  - Good: `Get-FfprobeOutput`, `Start-DownloadingFiles`, `Install-FFmpeg`
  - Good: `ProcessCommandLineArguments`, `GenerateOutputName`
  - Avoid: `getFfprobe`, `StartDownloading`, `process_args`

- **Variables**: Use camelCase for local variables, descriptive names
  - Good: `$ffprobeOutput`, `$streamDetails`, `$inputFile`
  - Good: `$global:cachedInfo` for global variables
  - Avoid: `$x`, `$temp`, `$data1`

- **Parameters**: Use camelCase within param blocks
  ```powershell
  param (
      [string]$inputFile,
      [PSCustomObject]$videoStream,
      [bool]$isVideo
  )
  ```

- **Constants/Global Variables**: Use descriptive names with `$global:` prefix
  - `$global:defaultLogLevel`, `$global:validLogLevels`

### Formatting

- **Indentation**: Use 4 spaces (no tabs)
- **Braces**: Opening brace on same line for functions/conditionals
  ```powershell
  Function Example {
      param ([string]$param1)
      
      if ($condition) {
          # code
      }
  }
  ```

- **Line Length**: Keep lines under 120 characters where practical
- **Blank Lines**: Use single blank lines to separate logical sections and functions

### Imports and Dependencies

- This project relies on **FFmpeg** being installed on the system
- The script includes `Install-FFmpeg` function for automatic dependency installation
- No external PowerShell modules are required beyond the default PS capabilities

### Types and Data Structures

- **Hashtables**: Use `@{}` for configuration objects
  ```powershell
  $settings = @{
      list        = $null
      resolutions = '1080'
      directory   = 'media'
      ffmpeg      = @{
          '-v' = 'quiet'
      }
  }
  ```

- **PSCustomObject**: Use for structured data return values
  ```powershell
  [PSCustomObject]@{
      StreamNumber = $streamNumber
      StreamType   = $streamType
      CodecInfo    = $codecInfo
  }
  ```

- **Type Attributes**: Use for parameters when type safety is needed
  ```powershell
  param (
      [string]$inputFile,
      [array]$filesInfo,
      [PSCustomObject]$usedIndices,
      [bool]$isVideo
  )
  ```

### Error Handling

- Use `Write-Log` function with appropriate log levels
- Valid log levels: `quiet`, `panic`, `fatal`, `error`, `warning`, `info`, `verbose`, `debug`
- Use `exit 1` for error conditions
- Use `throw` for unrecoverable errors with descriptive messages

```powershell
if (-not $streamDetails) {
    Write-Log "Failed to extract stream details for '$inputFile'." -logLevel 'error'
    return $null
}

throw "Unsupported file type. Only .mpd, .m3u8 or .m3u files are supported."
```

### Logging

- Always use `Write-Log` instead of `Write-Host` for output
- Pass log level as parameter: `Write-Log "message" -logLevel 'info'`
- Use appropriate log levels:
  - `error`: For failures
  - `warning`: For non-critical issues
  - `info`: For user-facing status messages
  - `verbose`: For detailed progress information
  - `debug`: For debugging details

### Function Documentation

- Include param blocks with type annotations
- Keep functions focused on single responsibility
- Return meaningful values or `$null` on failure

```powershell
Function Get-OutputPath {
    param(
        [string]$outputFile,
        [string]$directory = $null,
        [bool]$startFromRoot = $false
    )
    # Function logic here
    return [string]$outputPath
}
```

### Cross-Platform Compatibility

- Use `$IsWindows`, `$IsLinux`, `$IsMacOS` for OS detection
- Use `[IO.Path]::DirectorySeparatorChar` for path construction
- Avoid Windows-specific paths when possible
- Use `$PSScriptRoot` for script-relative paths

### External Command Execution

- Use call operator `&` for external commands
- Capture output with `2>&1` for stderr redirection
  ```powershell
  $ffprobeOutput = & "ffprobe" $mpd 2>&1
  ```

### Cache Implementation

- Use `$global:cachedInfo` hashtable for caching
- Check cache before expensive operations:
  ```powershell
  if ($global:cachedInfo.ContainsKey($outputKey)) {
      return $global:cachedInfo[$outputKey]
  }
  ```

## Project-Specific Notes

- The script processes media files in the order provided via `-list` argument
- Default output directory is `media/` (gitignored)
- Supports both URL and local file inputs
- Interactive mode (`-interactive`) prompts user for missing configuration
