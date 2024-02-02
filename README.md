# thuis

**thuis** is a command-line utility for downloading video or audio content from `.mpd` (Media Presentation Description) links. It offers flexibility by allowing users to specify custom settings for their downloads.

## Features

- **Download Video or Audio:** Easily fetch content using `.mpd` links.
- **Customizable Downloads:** Specify lists, preferred resolutions, and output filenames.
- **Detailed Logging:** Configure log levels to get the right amount of information.
- **Interactive Mode:** Optionally run in an interactive mode for dynamic configuration.

## Usage

Execute `thuis.ps1` from the terminal using the syntax below to start downloading media:

```sh

# Download with a custom list of .mpd files
pwsh thuis.ps1 -list <mpd_files> # a list of mpd-url separated by a comma

# Comprehensive options for advanced usage
pwsh thuis.ps1 -list <mpd_files> -resolutions <preferred_resolution> -filename <output_filename> -info <info_argument> -log_level <log_level> -interactive

```

## Prerequisites

### Windows

No prerequisites required. Running `pwsh thuis.ps1` will check and prompt for the installation of any missing dependencies.

### Linux

Ensure PowerShell is installed:

```sh

# Install PowerShell
sudo apt-get update
sudo apt-get install -y wget apt-transport-https software-properties-common

wget -q https://packages.microsoft.com/config/ubuntu/$(. /etc/os-release; echo $VERSION_ID)/packages-microsoft-prod.deb
sudo dpkg -i packages-microsoft-prod.deb
rm packages-microsoft-prod.deb

sudo apt-get update
sudo apt-get install -y powershell
pwsh -Version

```

### Mac

Install Homebrew, PowerShell, and FFmpeg:

```sh

# Install Homebrew
/bin/bash -c "$(curl -fsSL <https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh>)"

# Install PowerShell
brew update brew install --cask powershell pwsh -Version

# Install FFmpeg
brew update brew install ffmpeg

```


## TODO:
- [ ] Enhance interactive mode to be truly dynamic, prompting the user to update or add missing settings as needed.
