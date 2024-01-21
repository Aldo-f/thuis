# thuis

'thuis', or 'download video or audio by a `.mpd` link'.


## Terminal Usage:

```sh

# Interactive Mode (script prompts for MPD's)
./thuis.ps1 -interactive

# Custom List
./thuis.ps1 .mpd,.mpd

# All options
./thuis.ps1 [-list <mpd_files>] [-resolutions <preferred_resolution>] [-filename <output_filename>] [-info <info_argument>] [-log_level <log_level>] [-interactive]

```


## TODO:
- [ ] Make interactive mode truly interactive (ask to update/add missing settings)