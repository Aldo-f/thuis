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
            "^\-filename$" { $settings.filename = $arguments[++$i] }
            "^\-info$" { $settings.filename = $arguments[++$i] }
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

Function Get-Resolutions($mpd) {
    # Get Video streams
    $videoStreams = Get-StreamsInfo $mpd "Video"

    # Initialize an array to store resolutions
    $resolutions = @()

    for ($i = 0; $i -lt $videoStreams.Count; $i++) {
        $line = $videoStreams[$i].ToString()
        $extractedResolution = $line -match '\d{3,4}x\d{3,4}' | Out-Null
        if ($matches.Count -gt 0) {
            $extractedResolution = $matches[0]
            $resolutions += $extractedResolution  # Store resolution in the array
        }
    }

    return $resolutions
}

# Function to get all available audio from MPD
Function Get-Audios($mpd) {
    # Get Audio streams
    $audioStream = Get-StreamsInfo $mpd "Audio"

    # Initialize an array to store audios
    $audios = @()

    for ($i = 0; $i -lt $audioStream.Count; $i++) {
        $line = $audioStream[$i].ToString()
        $extractedAudio = $line -match '\d{3,4}x\d{3,4}' | Out-Null
        if ($matches.Count -gt 0) {
            $extractedAudio = $matches[0]
            $audios += $extractedAudio  # Store audio in the array
        }
    }

    return $audios
}

# Function to stream info by MPD and streamType
Function Get-StreamsInfo($mpd, $streamType) {
    # Key for cached stream information
    $streamKey = $mpd + "_$streamType"

    # Check if the information is already cached
    if ($cachedInfo.ContainsKey($streamKey)) {
        return $cachedInfo[$streamKey]
    }

    # Get general ffprobe output
    $ffprobeOutput = Get-FfprobeOutput $mpd

    # Parse the ffprobe output to extract stream information
    $streamsInfo = $ffprobeOutput | Select-String "Stream #\d+:\d+: ${streamType}:"

    # Initialize an array to store stream information
    $streamDetails = @()

    foreach ($streamInfo in $streamsInfo) {
        $line = $streamInfo.ToString()
        $streamDetails += $line
    }

    # Cache the information
    $global:cachedInfo[$streamKey] = $streamDetails

    return $streamDetails
}

function Show-MPDInfo {
    param (        
        [string] $mpd
    )

    [array]$mpdArray = Get-MPDArray $mpd

    # Process each MPD in the array
    for ($index = 0; $index -lt $mpdArray.Count; $index++) {
        $mpd = $mpdArray[$index]

        Write-Output ""
        Write-Output "Data for MPD-file: $($index + 1)"

        $ffprobeOutput = Get-FfprobeOutput $mpd

        # Extract relevant information from ffprobe output
        $videoInfo = $ffprobeOutput | Select-String "Stream #\d+:\d+: Video:"
        $audioInfo = $ffprobeOutput | Select-String "Stream #\d+:\d+: Audio:"
        $subtitleInfo = $ffprobeOutput | Select-String "Stream #\d+:\d+: Subtitle:"

        # Display information in a table
        $tableData = [PSCustomObject]@{
            'Video Streams'    = $videoInfo.Count
            'Audio Streams'    = $audioInfo.Count
            'Subtitle Streams' = $subtitleInfo.Count
        }

        $tableData | Format-Table -AutoSize | Write-Output

        # Display detailed information for each stream type
        if ($videoInfo.Count -gt 0) {
            Write-Output ""
            Write-Output "Video Streams:"
            $videoInfo | Write-Output
        }

        if ($audioInfo.Count -gt 0) {
            Write-Output ""
            Write-Output "Audio Streams:"
            $audioInfo | Write-Output
        }

        if ($subtitleInfo.Count -gt 0) {
            Write-Output ""
            Write-Output "Subtitle Streams:"
            $subtitleInfo | Write-Output
        }

        if ($false) {
            # Display detailed information for each stream type
            Write-Output ""
            Write-Output "Full ffprobe Output:"
            $ffprobeOutput | Format-List | Out-String | Write-Output
        }        
    }
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
        $ffprobeOutput = & ffprobe.exe $mpd 2>&1

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
        $fileInfo.FfmpegCommand = "ffmpeg.exe -v quiet -stats -i `"$inputFile`" -crf 0 -aom-params lossless=1 -map 0:v:$($fileInfo.VideoStream.StreamNumber) -map 0:a -c:a copy -tag:v avc1 `"$($fileInfo.Directory)/$($fileInfo.OutputFile)`""
    }
    elseif ($fileInfo.IsAudio) {
        $fileInfo.OutputFile = GenerateOutputName -filename "$filename.mp3" -directory $directory -usedIndices $usedIndices
        $fileInfo.FfmpegCommand = "ffmpeg.exe -v quiet -stats -i `"$inputFile`" `"$($fileInfo.Directory)/$($fileInfo.OutputFile)`""
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
        Write-Host "Output-folder created."
    }

    # Echo the command
    Write-Log "Running ffmpeg with the following command:" -logLevel 'verbose'
    Write-Log $fileInfo.FfmpegCommand  -logLevel 'verbose'

    # Uncomment the line below to run your custom ffmpeg command with variables
    Invoke-Expression $fileInfo.FfmpegCommand

    # Send a response with the path when the file has been downloaded
    Write-Host "File has been downloaded successfully to: $($fileInfo.OutputFile)"
}

# Function to check and try to install dependencies using multiple package managers, provide instructions if not successful
Function CheckAndInstallDependency {
    param (
        [string] $dependencyName,
        [string[]] $installCommands,
        [string] $installInstructions
    )    
    Function DependencyInstalled() {
        param(
            [string] $dependencyName
        )

        $dependencyInstalled = $null

        try {
            $dependencyInstalled = Get-Command $dependencyName -ErrorAction SilentlyContinue
        }
        catch {
            $dependencyInstalled = $null
        }

        return $dependencyInstalled;
    }

    $dependencyInstalled = DependencyInstalled -dependencyName $dependencyName

    if (-not $dependencyInstalled) {
        Write-Host "Dependency '$dependencyName' is not installed. Attempting to install..."

        # Try to install the dependency using multiple package managers
        foreach ($command in $installCommands) {
            Invoke-Expression $command
            # Check if the installation was successful
            try {
                $dependencyInstalled = Get-Command $dependencyName -ErrorAction SilentlyContinue
            }
            catch {
                $dependencyInstalled = $null
            }
            if ($dependencyInstalled) {
                Write-Host "Dependency '$dependencyName' was successfully installed."
                break
            }
        }

        if (-not $dependencyInstalled) {
            # Provide instructions for manual installation
            Write-Host $installInstructions
            Write-Host "After installation, please run the script again."
            Exit
        }
    }
    else {
        # Dependency is already installed.
    }
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

# Check if all dependencies are met
$ffmpegVersion = '6.1'
CheckAndInstallDependency -dependencyName "ffmpeg.exe" `
    -installCommands @(
    "choco install ffmpeg --version $ffmpegVersion -y",
    "winget install ffmpeg -v $ffmpegVersion"
    "scoop install ffmpeg@$ffmpegVersion",
    "(irm get.scoop.sh | iex) -and (scoop install ffmpeg@$ffmpegVersion)"
) `
    -installInstructions "If package managers are not available, please download and install ffmpeg from https://www.ffmpeg.org/download.html"


# Process command-line arguments
$settings = ProcessCommandLineArguments -arguments $args

# Check if no input file and -list is provided
if ($settings.list -eq "" -or $null -eq $settings.list) {
    Write-Host "Error: No input file or -list provided."
    Write-Host "Usage: ./thuis.ps1 [-list <mpd_files>] [-resolutions <preferred_resolution>] [-filename <output_filename>] [-info <info_argument>] [-log_level <log_level>] [-interactive]"
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

Function Show-FilesInfo {
    param (
        [object] $info,
        [string] $logLevel
    )

    $videoData = [array]($info | Where-Object { $_.IsVideo } | ForEach-Object { 
            [PSCustomObject]@{
                'Output File' = $_.OutputFile
                'Directory'   = $_.Directory
                'Type'        = 'Video'
                'Resolution'  = $_.VideoStream.Resolution
                'Command'     = $_.FfmpegCommand
            }
        })

    $audioData = [array]($info | Where-Object { $_.IsAudio } | ForEach-Object { 
            [PSCustomObject]@{
                'Output File' = $_.OutputFile
                'Directory'   = $_.Directory
                'Type'        = 'Audio'
                'Command'     = $_.FfmpegCommand
            }
        })

    if ($videoData.Count -ge 0) {
        Write-Log "Video Files to be created:" -logLevel $logLevel
        Write-Log ($videoData | Format-Table -AutoSize | Out-String) -logLevel $logLevel
    }

    if ($audioData.Count -ge 0) {
        Write-Log "Audio Files to be created:" -logLevel $logLevel
        Write-Log ($audioData | Format-Table -AutoSize | Out-String) -logLevel $logLevel
    }
}

# Show information about the files that will be created
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
