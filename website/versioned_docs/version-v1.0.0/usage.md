---
sidebar_position: 3
---

# Usage (v1.0.0)

## How to Use

Version 1.0.0 of thuis is designed to be simple and direct. It provides two ways to run the tool:

### Method 1: PowerShell Script (Recommended)

The primary way to use thuis v1.0.0 is via the PowerShell script:

```powershell
.\thuis.ps1 <arguments>
```

### Method 2: Batch File (Windows CMD)

For Windows Command Prompt users:

```cmd
thuis.bat <arguments>
```

## Basic Usage

The tool accepts .mpd (Media Presentation Description) links as input:

```powershell
.\thuis.ps1 https://example.com/video.mpd
```

### Multiple URLs

You can process multiple URLs in sequence:

```powershell
.\thuis.ps1 https://example.com/video1.mpd https://example.com/video2.mpd
```

### Help Information

To see all available options:

```powershell
.\thuis.ps1 --help
```

## Command Line Options

The following flags are available in v1.0.0:

| Option | Description |
| --- | Description |
|--------------|-------------|
| `--help` | Show help message and exit |
| `--dry-run` | Show what would be downloaded without actually downloading |
| `--verbose` | Enable verbose output |
| `--no-color` | Disable colored output |

## Examples

### Single Video Download

```powershell
.\thuis.ps1 https://example.com/video.mpd
```

### Batch Download from File

Create a text file `urls.txt` with one URL per line:

```
https://example.com/video1.mpd
https://example.com/video2.mpd
https://example.com/video3.mpd
```

Then run:

```powershell
Get-Content urls.txt | ForEach-Object { .\thuis.ps1 $_ }
```

### Dry Run Mode

Preview downloads without actually downloading anything:

```powershell
.\thuis.ps1 --dry-run https://example.com/video.mpd
```

### Verbose Output

Get detailed information about the download process:

```powershell
.\thuis.ps1 --verbose https://example.com/video.mpd
```

## Output Files

By default, downloaded files are saved in the current directory with their original filenames from the .mpd manifest.

## Error Handling

If an invalid .mpd link is provided, the tool will display an error message and exit with a non-zero status code.

## Notes

- This version does not include VRT MAX integration - it works with direct .mpd links only
- No account and password are not required or used
- For help with specific .mpd links, consult the documentation of the content provider
