# Global variables
$global:cachedInfo = @{}
$global:defaultLogLevel = 'quiet'
$global:validLogLevels = @("quiet", "panic", "fatal", "error", "warning", "info", "verbose", "debug")

# Function to process command-line arguments
Function ProcessCommandLineArguments {
    param (
        [string[]] $arguments
    )

    $settings = @{
        list        = $null
        resolutions = '1080'
        filename    = $null
        directory   = 'media'
        info        = $null
        log_level   = $global:defaultLogLevel
        interactive = $false
    }

    # Process each argument
    for ($i = 0; $i -lt $arguments.Count; $i++) {
        $arg = $arguments[$i]

        switch -regex ($arg) {
            "^\-list$" { $settings.list = $arguments[++$i] }
            "^\-resolutions$|^\-p$" { $settings.resolutions = $arguments[++$i] }
            "^\-directory$" { $settings.directory = $arguments[++$i] }
            "^\-filename$" { $settings.filename = $arguments[++$i] }
            "^\-info$" { $settings.info = $true }
            "^\-interactive$" { $settings.interactive = $true }
            "^\-log_level$|^-v" {
                $logLevel = $arguments[++$i].ToLower()
                if ($global:validLogLevels -contains $logLevel) {
                    $settings.log_level = $logLevel
                }
                else {
                    Write-Host "Invalid log level. Valid log levels are: $($global:validLogLevels -join ', ')"
                    exit 1
                }
            }
            "^[^-]" { $settings.list = $arg }
        }
    }

    return $settings
}

# Function to write to terminal based on log level
Function Write-Log {
    param (
        [string] $message,
        [string] $logLevel
    )

    # Valid log levels
    $validLogLevels = @("quiet", "panic", "fatal", "error", "warning", "info", "verbose", "debug")

    # Set log level to default if not provided or invalid
    if (-not $global:validLogLevels -contains $logLevel) {
        $logLevel = $global:defaultLogLevel
    }

    # Determine whether to write based on log level
    $writeLog = $validLogLevels.IndexOf($settings.log_level) -ge $validLogLevels.IndexOf($logLevel)

    if ($writeLog) {
        Write-Host $message
    }
}

# Function to increment the output filename
function GenerateOutputName {
    param (
        [string]$filename = "",
        [string]$directory = "",
        [PSCustomObject]$usedIndices
    )

    function IncrementAndGenerateFilename($prefix, $index, $extension) {
        $outputFilename = "${prefix}$("{0:D3}" -f $index)$extension"

        if ($usedIndices.Indices -notcontains $index -and -not (Test-Path (Join-Path $directory $outputFilename))) {
            $usedIndices.Indices += $index
            return $outputFilename
        }

        $index++
        return $null
    }

    $lastPartAndExtension = $filename -replace '^.*[^0-9](\d+)(\.[^.]+)$', '$1$2'
    $extension = $filename -replace '^.*(\.[^.]+)$', '$1'

    if ($lastPartAndExtension -ne $filename) {
        $prefix = $filename -replace '\d+(\.[^.]+)$', ''
        $index = [int]($lastPartAndExtension -replace '\..*$')
    
        do {
            $outputFilename = IncrementAndGenerateFilename $prefix $index $extension
    
            if ($outputFilename) {
                return $outputFilename
            }
    
            $index++
        } while ($true)
    }   
    
    $currentDate = Get-Date -Format 'y-M-d'
    $index = 1
    do {
        $outputFilename = IncrementAndGenerateFilename "${currentDate}_" $index ".mp4"

        if ($outputFilename) {
            return $outputFilename
        }

        $index++
    } while ($true)
}

# Function to get general ffprobe output
Function Get-FfprobeOutput($mpd) {
    $outputKey = $mpd + "_ffprobeOutput"

    # Check if the ffprobe output is already cached
    if ($global:cachedInfo.ContainsKey($outputKey)) {
        return $global:cachedInfo[$outputKey]
    }
    else {
        # Use ffprobe to get the general output
        $ffprobeOutput = & "ffprobe" $mpd 2>&1
    
        # Check if ffprobeOutput is empty
        if ([string]::IsNullOrWhiteSpace($ffprobeOutput)) {
            Write-Log "Error: ffprobe output is empty. Make sure ffprobe is installed and accessible." -logLevel 'error'
            exit
        }

        # Cache the ffprobe output
        $global:cachedInfo[$outputKey] = $ffprobeOutput        

        return $ffprobeOutput
    }
}

Function Get-StreamInfo($mpd) {
    # Check if the information is already cached
    $streamKey = $mpd + "_streamInfo"
    if ($cachedInfo.ContainsKey($streamKey)) {
        return $cachedInfo[$streamKey]
    }

    # Use ffprobe to get the general output
    $ffprobeOutput = Get-FfprobeOutput -mpd $mpd

    # Use a regular expression to match lines starting with "Stream #X:Y:"
    $streamLines = $ffprobeOutput -match '^Stream #\d+:\d+:'

    # Extract the stream information from each line
    $streamInfo = $streamLines | ForEach-Object {
        # Use regex to extract stream type and language code (if present)
        if ($_ -match '^Stream #\d+:\d+: (\w+)(\(\w+\))?:') {
            $streamType = $matches[1]
            $languageCode = $matches[2] -replace '(\(|\))', ''
            [PSCustomObject]@{
                Type         = $streamType
                LanguageCode = $languageCode
            }
        }
    }

    # Cache the information
    $cachedInfo[$streamKey] = $streamInfo

    return $streamInfo
}

# Function to gather information about input files
function GetInputFileInfo {
    param (
        [string]$inputFile,
        [string]$filename,
        [string]$directory,
        [PSCustomObject]$usedIndices
    )

    # Use Get-FfprobeOutput to get the general ffprobe output
    $ffprobeOutput = Get-FfprobeOutput $inputFile

    # Echo the ffprobe output
    Write-Log "FFprobe Output:" -logLevel 'debug'
    $ffprobeOutput -split "`n" | ForEach-Object { Write-Log $_ -logLevel 'debug' }

    # Split the output into lines
    $ffprobeOutputLines = $ffprobeOutput -split "`n"

    # Initialize an array to store stream details
    $streamDetails = @()

    # Loop through each line to extract stream details
    foreach ($line in $ffprobeOutputLines) {
        if ($line -match 'Stream #\d+:(\d+): (\w+): (.+), (\d+)x(\d+)') {
            $streamNumber = $matches[1]
            $streamType = $matches[2]
            $codecInfo = $matches[3]
            $width = $matches[4]
            $height = $matches[5]
    
            # Create an object for the stream and add it to the array
            $streamObject = [PSCustomObject]@{
                StreamNumber = $streamNumber
                StreamType   = $streamType
                CodecInfo    = $codecInfo
                Resolution   = "${width}x${height}"
                FullDetails  = $line.Trim()
            }
            $streamDetails += $streamObject
        }
        elseif ($line -match 'Stream #\d+:(\d+): (\w+): (.+)') {
            $streamNumber = $matches[1]
            $streamType = $matches[2]
            $codecInfo = $matches[3]
    
            # Create an object for the stream and add it to the array
            $streamObject = [PSCustomObject]@{
                StreamNumber = $streamNumber
                StreamType   = $streamType
                CodecInfo    = $codecInfo
                FullDetails  = $line.Trim()
            }
            $streamDetails += $streamObject
        }
        elseif ($line -match 'Stream #\d+:(\d+)(\(\w+\))?: (\w+): (.+)') {
            $streamNumber = $matches[1]
            $languageCode = $matches[2] -replace '(\(|\))', ''
            $streamType = $matches[3]
            $codecInfo = $matches[4]

            # Create an object for the stream and add it to the array
            $streamObject = [PSCustomObject]@{
                StreamNumber = $streamNumber
                LanguageCode = $languageCode
                StreamType   = $streamType
                CodecInfo    = $codecInfo
                FullDetails  = $line.Trim()
            }
            $streamDetails += $streamObject
        }
    }    

    # Determine the codec type from stream details
    $codecType = $streamDetails | Where-Object { $_.StreamType -eq 'Video' -or $_.StreamType -eq 'Audio' } | Select-Object -ExpandProperty StreamType

    $fileInfo = [PSCustomObject]@{
        InputFile     = $inputFile
        Filename      = $filename
        Directory     = $directory
        UsedIndices   = $usedIndices
        IsVideo       = $codecType -contains 'Video' -or $codecType -contains 'Subtitle'
        IsAudio       = [bool]($codecType -contains 'Audio' -and $codecType -notcontains 'Video')
        StreamDetails = $streamDetails
        OutputFile    = $null
        FfmpegCommand = $null
        VideoStream   = $null
    }

    # Function to get the most correct video stream number based on resolution
    Function Get-VideoStreamNumber {
        param (
            [string] $resolution,
            [array] $streamDetails
        )

        # Filter video streams
        $videoStreams = $streamDetails | Where-Object { $_.StreamType -eq 'Video' }

        # Order video streams based on height from high to low
        $videoStreams = $videoStreams | Sort-Object { [int]($_.Resolution -split 'x')[1] } -Descending

        # Check if the resolution is specified
        if (-not [string]::IsNullOrWhiteSpace($resolution)) {
            $targetHeight = [int]$resolution

            # Find the closest or equal resolution
            $closestStream = $null
            $videoStreams | ForEach-Object {
                $streamHeight = [int]($_.Resolution -split 'x')[1]
                if ($streamHeight -ge $targetHeight) {
                    $closestStream = $_
                }
            }

            if ($closestStream) {
                return $closestStream
            }
        }

        # If no matching or smaller resolution is found, return the stream number of the highest resolution
        return $videoStreams[0]
    }

    if ($fileInfo.IsVideo) {
        # Get the most correct video stream number based on resolutions
        $fileInfo.VideoStream = Get-VideoStreamNumber -resolution $settings.resolutions -streamDetails $streamDetails

        $fileInfo.OutputFile = GenerateOutputName -filename "$filename.mp4" -directory $directory -usedIndices $usedIndices
        $fileInfo.FfmpegCommand = "ffmpeg -v quiet -stats -i `"$inputFile`" -crf 0 -aom-params lossless=1 -map 0:v:$($fileInfo.VideoStream.StreamNumber) -map 0:a -c:a copy -tag:v avc1 `"$PSScriptRoot\$($fileInfo.Directory)\$($fileInfo.OutputFile)`""
    }
    elseif ($fileInfo.IsAudio) {
        $fileInfo.OutputFile = GenerateOutputName -filename "$filename.mp3" -directory $directory -usedIndices $usedIndices
        $fileInfo.FfmpegCommand = "ffmpeg -v quiet -stats -i `"$inputFile`" `"$PSScriptRoot\$($fileInfo.Directory)\$($fileInfo.OutputFile)`""
    }

    return $fileInfo
}

# Function to process input files
function ProcessInputFile {
    param (
        [PSCustomObject]$fileInfo
    )

    # Check if the media folder exists, create it if not
    if (-not (Test-Path -Path $fileInfo.Directory)) {
        New-Item -ItemType Directory -Path $fileInfo.Directory
        Write-Log "Output-folder created."  -logLevel 'verbose'
    }

    # Echo the command
    Write-Log "Running ffmpeg with the following command:" -logLevel 'verbose'
    Write-Log $fileInfo.FfmpegCommand  -logLevel 'verbose'

    # Run the ffmpeg command with variables
    Invoke-Expression $fileInfo.FfmpegCommand

    # Send a response with the path when the file has been downloaded
    Write-Host "File has been downloaded successfully to: `"$PSScriptRoot\$($fileInfo.Directory)\$($fileInfo.OutputFile)`""
}

# Function to ask a yes no question
Function AskYesOrNo {
    param (
        [string] $question
    )

    $match = [regex]::Match($question, '\(([YyNn])/[YyNn]\)')  # Extract the uppercase value between ()
    $defaultChoice = 'Y'
    if ($match.Success) {
        if ($match.Groups[0].Value.Contains('N')) {
            $defaultChoice = 'N'
        }
        else {
            $defaultChoice = 'Y'
        }
    }    

    $choice = Read-Host "$question"
    if ([string]::IsNullOrWhiteSpace($choice)) {
        $choice = $defaultChoice  # Treat Enter as default choice
    }
    $choice = $choice.ToUpper()  # Convert to uppercase for case insensitivity

    if ($choice -in 'Y', 'N') {
        return ($choice -eq 'Y')
    }
    else {
        Write-Host "Invalid input. Please enter 'Y' for Yes or 'N' for No."
        return (AskYesOrNo $question)
    }
}

# Function to split a string into an array
function SplitString($string) {
    # Split the $string string by ',' or ';' or ' ' and remove empty entries
    $array = $string -split '[,; ]' | Where-Object { $_ -ne '' }

    # Ensure $array is always an array
    if ($array -isnot [System.Array]) {
        $array = @($array)
    }

    return [System.Array]$array
}

# Function to shown info about the files that we wish to process
Function Show-FilesInfo {
    param (
        [object] $info,
        [string] $logLevel
    )

    $videoData = [array]($info | Where-Object { $_.IsVideo } | ForEach-Object { 
            $dataObject = @{
                'Output File' = $_.OutputFile
                'Directory'   = $_.Directory
                'Type'        = 'Video'
                'Resolution'  = $_.VideoStream.Resolution
            }
            if ($logLevel -eq 'debug') {
                $dataObject['Command'] = $_.FfmpegCommand
            }
            [PSCustomObject]$dataObject
        })

    $audioData = [array]($info | Where-Object { $_.IsAudio } | ForEach-Object { 
            $dataObject = @{
                'Output File' = $_.OutputFile
                'Directory'   = $_.Directory
                'Type'        = 'Audio'
            }
            if ($logLevel -eq 'debug') {
                $dataObject['Command'] = $_.FfmpegCommand
            }
            [PSCustomObject]$dataObject
        })

    Function Write-Data {
        param(
            [array] $data, 
            [string] $logLevel
        )

        if ($logLevel -eq 'debug') {
            Write-Log ($data | Format-List | Out-String) -logLevel $logLevel
        }
        else {
            Write-Log ($data | Format-Table -AutoSize | Out-String) -logLevel $logLevel
        }
    }

    if ($null -ne $videoData -and $videoData.Count -ge 0) {
        Write-Log "Video Files to be created:" -logLevel $logLevel
        Write-Data -data $videoData -logLevel $logLevel
    }

    if ($null -ne $audioData -and $audioData.Count -ge 0) {
        Write-Log "Audio Files to be created:" -logLevel $logLevel
        Write-Data -data $audioData -logLevel $logLevel
    }
}

# Function to install FFmpeg based on OS
function Install-FFmpeg {
    # Check if ffmpeg is present
    if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
        Write-Log "FFmpeg is already installed." -logLevel 'info'
        return
    }

    Write-Log "FFmpeg not found. Checking for existing package managers..." -logLevel 'warning'
    Write-Log $env:OS -logLevel 'debug'

    function Install-Dependency {
        param (
            [string]$Command,
            [string]$DependencyName,
            [string]$InstallInstructions
        )
    
        # Execute the installation command
        Invoke-Expression $Command
    
        # Check if the dependency was successfully installed
        try {
            $dependencyInstalled = Get-Command $DependencyName -ErrorAction SilentlyContinue
        }
        catch {
            $dependencyInstalled = $null
        }
    
        if ($dependencyInstalled) {
            Write-Host "Dependency '$DependencyName' was successfully installed."
        }
        else {
            # Provide instructions for manual installation
            Write-Host "Please install FFmpeg manually."
            Write-Host "After installation, please run the script again."
            Exit
        }
    }
    
    # Defaults
    $installCommand = $null
    $dependencyName = "ffmpeg"    
    
    if ($IsWindows) {
        # Install for Windows
        if (Get-Command scoop -ErrorAction SilentlyContinue) {
            $installCommand = "scoop install ffmpeg";
        }
        elseif (Get-Command winget -ErrorAction SilentlyContinue) {
            $installCommand = "winget install ffmpeg"            
        }
        elseif (Get-Command choco -ErrorAction SilentlyContinue) {          
            $installCommand = "choco install ffmpeg"
        }
        elseif (!Get-Command choco -ErrorAction SilentlyContinue) {
            # Install for Windows with Chocolately (if none of the above package managers are found)
            Write-Log "Chocolately is not installed. Installing..." -logLevel 'warning'
            Set-ExecutionPolicy Bypass -Scope Process -Force; Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
            $installCommand = "choco install ffmpeg"
        }        
   
    }
    elseif ($IsLinux) {
        # Install for Linux
        if (Get-Command apt-get -ErrorAction SilentlyContinue) {
            $installCommand = "sudo apt-get install ffmpeg"
        }
        elseif (Get-Command yum -ErrorAction SilentlyContinue) {
            $installCommand = "sudo yum install ffmpeg"
        }
        else {
            Write-Log "Package manager not found. Please install FFmpeg manually." -logLevel 'error'
        }
   
    }
    elseif ($IsMacOS) {
        # Install for Apple with Homebrew
        if (Get-Command brew -ErrorAction SilentlyContinue) {
            $installCommand = "brew install ffmpeg"
        }
        else {
            Write-Log "Homebrew not installed. Please install Homebrew and FFmpeg manually." -logLevel 'error'
        }   
    }
    else {
        Write-Log "Operating system not supported." -logLevel 'error'
    }

    if ($null -ne $installCommand) {
        Install-Dependency -Command $installCommand -DependencyName $dependencyName -InstallInstructions $instructions
    }
}    

# Call the function to install FFmpeg
Install-FFmpeg

# Process command-line arguments
$settings = ProcessCommandLineArguments -arguments $args

# Check if no input file and -list is provided
if ($settings.list -eq "" -or $null -eq $settings.list) {
    Write-Host "Error: No input file or -list provided."
    Write-Host "Usage: ./thuis.ps1 [-list <mpd_files>] [-resolutions <preferred_resolution>] [-filename <output_filename>] [-info <info_argument>] [-log_level <log_level>] [-interactive] [-directory <directory_argument>]"
    exit 1    
}

# Split the list of mpd files
$mpdFiles = SplitString $settings.list

# Define a variable to store used indices
$usedIndices = [PSCustomObject]@{ Indices = @() }

# Gather information about input files
$filesInfo = foreach ($inputFile in $mpdFiles) {
    GetInputFileInfo -inputFile $inputFile -filename $settings.filename -directory $settings.directory -usedIndices $usedIndices
}

# Show information about the files that will be created
if ($settings.info) {
    Show-FilesInfo -info $filesInfo -logLevel $settings.log_level
    exit
}

if ($settings.interactive) {
    Show-FilesInfo -info $filesInfo -logLevel "quiet"

    # If in interactive mode, ask for confirmation
    if (-not (AskYesOrNo "Are you ready to start processing these MPD-files? (Y/n)")) {
        exit
    }
}
else {
    Show-FilesInfo -info $filesInfo -logLevel "quiet"
}

# Process input files
foreach ($fileInfo in $filesInfo) {
    ProcessInputFile -fileInfo $fileInfo
}

# End of script
