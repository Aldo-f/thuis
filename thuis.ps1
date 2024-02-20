# Global variables
$global:cachedInfo = @{}
$global:defaultLogLevel = 'info'
$global:defaultLogLevelFfmpeg = 'quiet'
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

    # Prompt for missing settings if in interactive mode
    if ($settings.interactive) {

        $confirmation = $false
        do {
            if ($null -ne $settings.list) {
                $mpdFiles = SplitString $settings.list
            }
            else {
                $settings.list = Read-Host "Enter the list of .mpd files (separated by commas)"
                $mpdFiles = SplitString $settings.list
            }

            $fileCount = $mpdFiles.Count
            $confirmation = AskYesOrNo "You've requested to download $fileCount file(s). Is this correct? (Y/n)"
            if (-not $confirmation) {
                $settings.list = Read-Host "Enter the list of .mpd files (separated by commas)"
            }

        } while (-not $confirmation)
    
        if (-not (AskYesOrNo "Resolution is currently '$($settings.resolutions)'. Is this correct? (Y/n)")) {
            Write-Host "Enter the preferred resolution. Example values: 1080 (Full HD), 720 (HD), 480 (SD), 360, 270."
            $settings.resolutions = Read-Host "Available resolutions: 1080, 720, 480, 360, 270"
        }

        if (-not (AskYesOrNo "Output directory is currently '$($settings.directory)'; is this correct? (Y/n)")) {
            $settings.directory = Read-Host "Enter the output directory"
        }    
            
        if ($null -ne $settings.list) {
            if (-not (AskYesOrNo "The output filename is currently '$($settings.filename)'; is this correct? (Y/n)")) {
                $settings.filename = Read-Host "Enter the output filename"
            }
        }
        else {
            $settings.filename = Read-Host "Enter the output filename"
        }  

        do {
            if (-not (AskYesOrNo "Log level is currently '$($settings.log_level)'; is this correct? (Y/n)")) {
                Write-Host "Enter the log level. Possible values: quiet, panic, fatal, error, warning, info, verbose, debug."
                $inputLogLevel = Read-Host "Enter log level"
                    
                if ($global:validLogLevels -contains $inputLogLevel.ToLower()) {
                    $settings.log_level = $inputLogLevel.ToLower()
                    $isValidLogLevel = $true
                }
                else {
                    Write-Host "Invalid log level entered. Please enter one of the valid log levels: quiet, panic, fatal, error, warning, info, verbose, debug."
                    $isValidLogLevel = $false
                }
            }
            else {
                $isValidLogLevel = $true
            }
        } while (-not $isValidLogLevel)
    }

    return $settings
}

# Function to write to terminal based on log level
Function Write-Log {
    param (
        [string] $message,
        [string] $logLevel = 'info'
    )

    # Set log level to default if not provided or invalid
    if (-not $global:validLogLevels -contains $logLevel) {
        $logLevel = $global:defaultLogLevel
    }

    # Determine whether to write based on log level
    $writeLog = $global:validLogLevels.IndexOf($settings.log_level) -ge $global:validLogLevels.IndexOf($logLevel)

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
        $outputFilename = "${prefix}$("{0:D3}" -f $index).$extension"

        if ($usedIndices.Indices -notcontains $index -and -not (Test-Path (Join-Path $directory $outputFilename))) {
            $usedIndices.Indices += $index
            return $outputFilename
        }

        $index++
        return $null
    }

    # Extract parts from the filename 
    $filenameParts = $filename -split '\.'
    $extension = $filenameParts[-1]
    $filenameBase = $filenameParts[-2]

    if ($filenameBase -eq "") {
        # No filename provided, generate some based current time
        $currentDate = Get-Date -Format 'yyyy-MM-dd'
        $index = 1
        do {
            $outputFilename = IncrementAndGenerateFilename "${currentDate}-" $index $extension
 
            if ($outputFilename) {
                return $outputFilename
            }
 
            $index++
        } while ($true)
    }
    
    # If no numbers were found at the end, add '-001'
    if (-not ($filenameBase -match '\d+$')) {
        $filename = "$filenameBase-001.$extension"
    }

    $lastPartAndExtension = $filename -replace '^.*[^0-9](\d+)(\.[^.]+)$', '$1$2'
    if ($lastPartAndExtension -ne $filename) {
        # The filename is structured with numbers at the end
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

# Function to build the command in a safe manner
function Get-FfmpegArguments {
    param (
        [string]$inputFile,
        [PSCustomObject]$videoStream,
        [PSCustomObject]$audioStream = $null,
        [string]$outputFile,
        [string]$directory,
        [bool]$isVideo,
        [bool]$isAudio, 
        [bool]$includeSubtitle = $true
    )

    $outputPath = Get-OutputPath -outputFile $outputFile -directory $directory
    $argumentsList = @(
        '-v', $global:defaultLogLevelFfmpeg,
        '-stats',
        '-i', "`"$inputFile`""
    )

    if ($isVideo) {
        $argumentsList += (
            '-crf', '0',
            '-aom-params', 'lossless=1',
            "-map", "0:v:$($videoStream.StreamNumber)",
            '-map', '0:a',
            '-c:a', 'copy',
            '-tag:v', 'avc1'
        )
        if ($includeSubtitle) {
            $argumentsList += '-c:s', 'mov_text'
        }
    }
    elseif ($isAudio) {
        if ($null -ne $audioStream) {
            $argumentsList += "-map", "0:a:$($audioStream.StreamNumber)"
        }
    }

    $argumentsList += $outputPath

    return [PSCustomObject]@{
        Arguments = $argumentsList
    }
}

# Function to get the base OutputPath
Function Get-OutputPath {
    param(
        [string] $outputFile,
        [string] $directory = $null, 
        [bool] $startFromRoot = $false
    )

    if (-not $directory) {
        $directory = $settings.directory
    }

    $pathComponents = @()
    
    if ($startFromRoot) {
        $pathComponents += $PSScriptRoot
    }

    $pathComponents += $directory, $outputFile

    $outputPath = $pathComponents -join [IO.Path]::DirectorySeparatorChar
    return [string] $outputPath
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

    # Initialize file variables
    $duration = $null

    # Initialize an array to store stream details
    $streamDetails = @()

    # Loop through each line to extract stream details
    foreach ($line in $ffprobeOutputLines) {
        if ($line -match 'Duration: (\d+:\d+:\d+\.\d+)') {
            # Extract duration
            $duration = $matches[1]
        }
        elseif ($line -match 'Stream #\d+:(\d+): (\w+): (.+), (\d+)x(\d+)') {
            # Video
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
            # Audio
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
            # Subtitles
            $streamNumber = $matches[1]
            $languageCode = $matches[2] -replace '(\(|\))', ''
            $streamType = $matches[3]
            $codecInfo = $matches[4]

            # Create an object for the stream and add it to the array
            $streamObject = [PSCustomObject]@{
                StreamNumber = $streamNumber
                StreamType   = $streamType
                CodecInfo    = $codecInfo
                LanguageCode = $languageCode
                FullDetails  = $line.Trim()
            }
            $streamDetails += $streamObject
        }
    }

    # Determine the codec type from stream details
    $codecType = $streamDetails | Where-Object { $_.StreamType -eq 'Video' -or $_.StreamType -eq 'Audio' } | Select-Object -ExpandProperty StreamType

    $fileInfo = [PSCustomObject]@{
        InputFile      = $inputFile
        Filename       = $filename
        Directory      = $directory
        Duration       = $duration 
        UsedIndices    = $usedIndices
        IsVideo        = $codecType -contains 'Video' -or $codecType -contains 'Subtitle'
        IsAudio        = [bool]($codecType -contains 'Audio' -and $codecType -notcontains 'Video')
        StreamDetails  = $streamDetails
        OutputFile     = $null
        OutputPath     = $null
        RootOutputPath = $null
        FfmpegCommand  = $null
        VideoStream    = $null
        AudioStream    = $null
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

    if ($fileInfo.InputFile -match '\.mpd') {
        # .mpd
        if ($fileInfo.IsVideo) {
            # Get the most correct video stream based on resolutions
            $fileInfo.VideoStream = Get-VideoStreamNumber -resolution $settings.resolutions -streamDetails $streamDetails
            $fileInfo.OutputFile = GenerateOutputName -filename "$filename.mp4" -directory $directory -usedIndices $usedIndices
        
            # Generate FFmpeg arguments
            $ffmpegArgs = Get-FfmpegArguments -inputFile $fileInfo.InputFile -videoStream $fileInfo.VideoStream -outputFile $fileInfo.OutputFile -directory $fileInfo.Directory -isVideo $true -isAudio $false
            $fileInfo.FfmpegCommand = $ffmpegArgs.Arguments -join ' '
        }
        elseif ($fileInfo.IsAudio) {    
            # Get the first audio stream
            $fileInfo.AudioStream = ($streamDetails | Where-Object { $_.StreamType -eq 'Audio' } )
            $fileInfo.OutputFile = GenerateOutputName -filename "$filename.mp3" -directory $directory -usedIndices $usedIndices
    
            # Generate FFmpeg arguments
            $ffmpegArgs = Get-FfmpegArguments -inputFile $fileInfo.InputFile -audioStream $fileInfo.AudioStream -outputFile $fileInfo.OutputFile -directory $fileInfo.Directory -isVideo $false -isAudio $true
            $fileInfo.FfmpegCommand = $ffmpegArgs.Arguments -join ' '
        }
    }
    elseif ($fileInfo.InputFile -match '\.m3u8?$') {
        # .m3u8 (playlist)
        $fileInfo.OutputFile = GenerateOutputName -filename "$filename.mp4" -directory $directory -usedIndices $usedIndices
        $fileInfo.OutputPath = Get-OutputPath -outputFile $fileInfo.OutputFile -directory $fileInfo.Directory
        $fileInfo.FfmpegCommand = "-v $($global:defaultLogLevelFfmpeg) -i $($fileInfo.InputFile) -bsf:a aac_adtstoasc -vcodec copy -c copy -crf 50 $($fileInfo.OutputPath)"
    }
    else {
        throw "Unsupported file type. Only .mpd, .m3u8 or .m3u files are supported."
    }    

    # Get the OutputPath
    if (-not $fileInfo.OutputPath) {
        $fileInfo.OutputPath = Get-OutputPath -outputFile $fileInfo.OutputFile -directory $fileInfo.Directory
    }

    $fileInfo.RootOutputPath = Get-OutputPath -outputFile $fileInfo.OutputFile -directory $fileInfo.Directory -startFromRoot $true

    return $fileInfo
}

# Function to start downloading the files after getting all required data
function Start-DownloadingFiles {
    param (
        [array] $filesInfo
    )

    # Create the output folder if it doesn't exist
    if (-not (Test-Path -Path $settings.Directory)) {
        New-Item -ItemType Directory -Path $settings.Directory | Out-Null
        Write-Log "Output folder created at $($settings.Directory)." -logLevel 'verbose'
    }

    $fileCount = $filesInfo.Count
    if ($fileCount -eq 1) {
        Write-Log "1 file queued for download." -logLevel 'info'
    }
    else {
        Write-Log "$fileCount files queued for download." -logLevel 'info'
    }

    $i = 0
    foreach ($fileInfo in $filesInfo) {
        $i++
        $fileName = $fileInfo.OutputFile
        Write-Log "Fetching information and starting download ($i/$fileCount): $fileName" -logLevel 'info'
        $progressPercentage = (($i / $fileCount) * 100) - 1
        Write-Progress -Activity "Downloading Files" -Status "$i of $fileCount" -PercentComplete $progressPercentage
    
        # Start ffmpeg process and wait for it to complete
        Start-Process -FilePath ffmpeg -ArgumentList $fileInfo.FfmpegCommand -Wait -NoNewWindow
    
        Write-Log "Completed download ($i/$fileCount): $($fileInfo.OutputFile)" -logLevel 'info'
    }   

    Write-Progress -Activity "Downloading Files" -Status "Complete" -PercentComplete 100
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

# Function to show info about the files that we wish to process
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
                'Duration'    = $_.Duration
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
                'Duration'    = $_.Duration
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

    if ($null -ne $videoData -and $videoData.Count -ge 1) {
        Write-Log "Video Files to be created:" -logLevel $logLevel
        Write-Data -data $videoData -logLevel $logLevel
    }

    if ($null -ne $audioData -and $audioData.Count -ge 1) {
        Write-Log "Audio Files to be created:" -logLevel $logLevel
        Write-Data -data $audioData -logLevel $logLevel
    }
}

# Function to install FFmpeg based on OS
function Install-FFmpeg {
    # Check if ffmpeg is present
    if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
        Write-Log "FFmpeg is already installed." -logLevel 'verbose'
        return
    }

    Write-Log "FFmpeg not found. Checking for existing package managers..." -logLevel "warning"
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
    Write-Host "Usage: pwsh thuis.ps1 [-list <mpd_files>] [-resolutions <preferred_resolution>] [-filename <output_filename>] [-info <info_argument>] [-log_level <log_level>] [-interactive] [-directory <directory_argument>]"
    exit 1    
}

Write-Log "Fetching data for each specified file..." -logLevel "info"
Write-Log "This process can take a while, depending on the number of files and the download speed." -logLevel "verbose"

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
    if (-not (AskYesOrNo "Are you ready to start downloading? (Y/n)")) {
        exit
    }
}
else {
    Show-FilesInfo -info $filesInfo -logLevel "quiet"
}

# Call the function to start downling all files
Start-DownloadingFiles -filesInfo $filesInfo

# Display the list of downloaded file locations
Write-Log "All files have been downloaded successfully. Here are the locations:" -logLevel "info"
$filesInfo | ForEach-Object {
    Write-Log "- $($_.RootOutputPath)"
}

# End of script
