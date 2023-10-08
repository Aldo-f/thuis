# Settings
$defaults = @{
    'height'    = 270
    'directory' = 'media';
}

# Global variables
$global:cachedStreamInfo = @{}
$global:ArgumentListFilePath = 'argumentList.txt'


# Function to get the index of the closest video stream to the target resolution
Function Get-ClosestVideoStream {
    param (
        [int] $targetResolution,
        [array] $resolutions
    )

    $closestResolutionIndex = 0
    $closestResolutionDiff = [math]::abs([int]($resolutions[0] -split 'x')[1] - $targetResolution)

    for ($i = 0; $i -lt $resolutions.Count; $i++) {
        $resolution = $resolutions[$i]
        $resolutionInt = [int]($resolution -split 'x')[1]
        $diff = [math]::abs($resolutionInt - $targetResolution)

        if ($diff -lt $closestResolutionDiff) {
            $closestResolutionIndex = $i
            $closestResolutionDiff = $diff
        }
    }

    return $closestResolutionIndex
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


Function Get-StreamsInfo($mpd, $streamType) {
    # Check if the information is already cached
    if ($cachedStreamInfo.ContainsKey($mpd)) {
        return $cachedStreamInfo[$mpd]
    }

    # Use ffprobe to get specific streams and capture output
    $ffprobeOutput = & ffprobe.exe $mpd 2>&1

    # Check if ffprobeOutput is empty
    if ([string]::IsNullOrWhiteSpace($ffprobeOutput)) {
        Write-Host "Error: ffprobe output is empty. Make sure ffprobe is installed and accessible."
        exit
    }

    # Parse the ffprobe output to extract stream information
    $streamsInfo = $ffprobeOutput | Select-String "Stream #\d+:\d+: ${streamType}:"

    # Initialize an array to store stream information
    $streamDetails = @()

    foreach ($streamInfo in $streamsInfo) {
        $line = $streamInfo.ToString()
        $streamDetails += $line
    }

    # Cache the information
    $global:cachedStreamInfo[$mpd] = $streamDetails

    return $streamDetails
}


Function ChooseVideoStream($mpd, $resolution) {
    $resolutions = Get-Resolutions $mpd;    

    # If the resolution matches, return the corresponding stream number
    for ($i = 0; $i -lt $resolutions.Count; $i++) {
        $height = [int]($resolutions[$i] -split 'x')[1]
        if ($height -eq $resolution) {
            return $i  # Return the index directly
        }
    }

    # If no exact match found, find the closest resolution
    $chosenVideoStream = 0  # Initialize to 0
    $closestResolutionDiff = [math]::abs([int]($resolutions[0] -split 'x')[1] - [int]$resolution)

    for ($i = 1; $i -lt $resolutions.Count; $i++) {
        $resolutionInt = [int]($resolutions[$i] -split 'x')[1]
        $diff = [math]::abs($resolutionInt - $resolution)

        if ($diff -lt $closestResolutionDiff) {
            $chosenVideoStream = $i  # Update chosen stream index
            $closestResolutionDiff = $diff
        }
    }

    return $chosenVideoStream
}


# Function to process MPDs
Function ProcessMPDs {
    # Initialize an array to store argument lists
    $argumentLists = @()
    $index = 1

    while ($true) {
        # Prompt user for MPD URL
        $mpd = Read-Host "Enter the .mpd (leave empty to finish)"

        # Check if user wants to stop adding MPDs
        if ([string]::IsNullOrEmpty($mpd)) {
            break
        }
   
        # Get Video streams and resolutions
        $resolutions = Get-Resolutions $mpd

        # Check if there are available video streams
        if ($resolutions.Count -eq 0) {
            Write-Host "No valid video streams found. Please try a different .mpd-file"
            continue # Start the loop again
        }

        # Display the available video streams to the user
        Write-Host "Available Video Streams:"

        for ($i = 0; $i -lt $resolutions.Count; $i++) {
            $resolution = $resolutions[$i] -match '\d{3,4}x\d{3,4}' | Out-Null
            if ($matches.Count -gt 0) {
                $resolution = $matches[0]
                Write-Host "$($i + 1): Resolution $resolution"
            }
        }

        # Prompt the user to choose a video stream
        $chosenVideoStream = Read-Host "Enter the number corresponding to your preferred video stream"

        # If user hits enter without choosing, use the closest resolution to the default height
        if ([string]::IsNullOrWhiteSpace($chosenVideoStream)) {
            $defaultHeight = $defaults['height']
            $chosenVideoStream = Get-ClosestVideoStream -targetResolution $defaultHeight -resolutions $resolutions
            $chosenVideoStream += 1;
        }

        # Ensure the user's choice is within the valid range
        if ($chosenVideoStream -lt 1 -or $chosenVideoStream -gt $resolutions.Count) {
            Write-Host "Invalid choice. Please enter a number between 1 and $($resolutions.Count)."
            exit
        }

        # Extract the resolution from the chosen stream information using the array
        $chosenResolution = $resolutions[$chosenVideoStream - 1]

        Write-Host "You have chosen: Resolution $chosenResolution"

        # Prompt the user for an output name
        $outputName = Read-Host "Enter the desired output name (without extension)"

        # Check if the 'video' directory exists, if not, create it
        $mediaDirectory = $defaults['directory'];
        if (-not (Test-Path $mediaDirectory)) {
            New-Item -ItemType Directory -Path $mediaDirectory | Out-Null
        }

        # Ensure the user's input is not empty
        if ([string]::IsNullOrWhiteSpace($outputName)) {
            # Get the current date in the format 'y-m-d'
            $currentDate = Get-Date -Format 'y-M-d'

            # Get the list of files in the directory
            $existingFiles = Get-ChildItem -Path $defaults['directory']

            # Find the next available index
            $index = 1
            $filename = "${currentDate}_{0:D3}.mp4" -f $index

            while ($existingFiles | Where-Object { $_.Name -eq $filename }) {
                $index++
                $filename = "${currentDate}_{0:D3}.mp4" -f $index

            }

            $outputName = $filename
        }
        else {
            # Check if the provided output name has an extension
            if ($outputName -notmatch '\.[a-zA-Z]{2,3}$') {
                # If no extension found, add .mp4
                $outputName += ".mp4"
            }
        }

        # Create the full argument list
        $mediaDirectory = $defaults['directory'];
        $ArgumentList = "-i $mpd -map 0:v:$chosenVideoStream -c:v copy -map 0:a -c:a copy $mediaDirectory/$outputName"
        $argumentLists += $ArgumentList
        $index++
    }

    # Save content to the file
    $argumentLists | Out-File -FilePath $global:ArgumentListFilePath
    Write-Host "List saved to $($global:ArgumentListFilePath)."

    $choice = Read-Host "Do you want to proceed with processing? (y/n)"
    if ($choice -eq 'y') {
        ProcessArgumentList
    }
    else {
        Write-Host "Processing aborted by user."
        exit # Terminate the process
    }
}


# Function to process the argumentList.txt
Function ProcessArgumentList {
    $argumentLists = Get-Content $global:ArgumentListFilePath | Where-Object { $_ -match '\S' }

    $filesToProcess = @()

    foreach ($command in $argumentLists) {
        # Extract the $outputName from the command
        $outputName = $command -replace '.*\s(\S+\.\w+)', '$1'

        # Check if the file already exists
        if (Test-Path $outputName) {
            $overwriteChoice = Read-Host "File $outputName already exists. Do you want to overwrite it? (y/n)"
            if ($overwriteChoice -eq 'n') {
                continue # Skip this file
            }
        }

        # Extract the directory from the $outputName and create it if not exists
        $mediaDirectory = $outputName -replace '/.*', ''
        if (-not (Test-Path $mediaDirectory)) {
            New-Item -ItemType Directory -Path $mediaDirectory | Out-Null
        }     

        # Extract the video stream index from the command
        $streamIndex = [regex]::Match($command, '0:v:(\d+)').Groups[1].Value
        
        # Extract the $mpd from the command
        $mpd = $command -replace '.*-i\s+([^\s]+).*', '$1'
        
        $resolutions = Get-Resolutions $mpd;
        
        # Retrieve the resolution based on the stream index
        $resolution = $resolutions[$streamIndex]

        # Print the resolution and filename for this command
        $outputName = $outputName -replace '.*/', ''
        Write-Host "File: $outputName; Resolution: $resolution"

        $filesToProcess += $command
    }

    if ($filesToProcess.Count -eq 0) {
        Write-Host "No files to process."
        exit
    }

    $choice = Read-Host "Do you want to proceed with processing? (y/n)"
    if ($choice -eq 'y') {
        Write-Host "Starting processing..."
        $filesToProcess | ForEach-Object { Start-Process -FilePath ffmpeg.exe -ArgumentList $_ -Wait -NoNewWindow }
    }
    else {
        Write-Host "Processing aborted by user."
        exit
    }
}


# Function to process the list.txt
Function ProcessList {
    Write-Host "Processing list..."
    $listContent = Get-Content 'list.txt'
    foreach ($line in $listContent) {
        $splitLine = $line -split '\s+', 2
        $mpd = $splitLine[0]
        $outputName = $splitLine[1]
 
        # Extract video stream based on filename pattern
        $pattern = '.*[ _-](\d+p)\.mp4$'
        if ($outputName -match $pattern) {
            $resolution = $matches[1] -replace '[ _-]', '' -replace 'p', ''
            $chosenVideoStream = ChooseVideoStream $mpd $resolution
        }
        else {
            # Use default resolution if pattern doesn't match
            $resolution = $defaults['height']
            $chosenVideoStream = Get-ClosestVideoStream -targetResolution $resolution -resolutions (Get-Resolutions $mpd)
        }     

        # Create the full argument list
        $mediaDirectory = $defaults['directory'];
        $ArgumentList = "-i $mpd -map 0:v:$chosenVideoStream -c:v copy -map 0:a -c:a copy $mediaDirectory/$outputName"
        $argumentLists += $ArgumentList
        $argumentLists += "`n"
    }
    # Save content to the file after each iteration
    $argumentLists | Out-File -FilePath $global:ArgumentListFilePath
    Write-Host "List saved to $($global:ArgumentListFilePath)."

    $choice = Read-Host "Do you want to process the list now? (y/n)"
    if ($choice -eq 'y') {
        ProcessArgumentList
    }
    else {
        Write-Host "Processing aborted by user."
        return  # Terminate the process
    }
}

# Check if 'list.txt' exists
if (Test-Path 'list.txt') {
    $processList = Read-Host "Found 'list.txt'. Do you want to process it? (y/n)"
    if ($processList -eq 'y') {
        ProcessList
    }
}


# Check if $($global:ArgumentListFilePath) exists
if (Test-Path $global:ArgumentListFilePath) {
    $choice = Read-Host "Found $($global:ArgumentListFilePath). Do you want to process the list? (y/n)"
    if ($choice -eq 'y') {
        ProcessArgumentList
        return  # Exit the program after processing
    }
    elseif ($choice -eq 'n') {
        $choice = Read-Host "Do you want to start again? (y/n)"
        if ($choice -eq 'y') {
            Write-Host "Starting from scratch..."
            ProcessMPDs
        }
        elseif ($choice -eq 'n') {
            Write-Host "Continuing..."
            ProcessMPDs
        }
        else {
            Write-Host "Invalid choice. Exiting."
        }
    }
    else {
        Write-Host "Invalid choice. Exiting."
    }
}
else {
    Write-Host "No $($global:ArgumentListFilePath) or list.txt found. Starting interactive mode..."
    ProcessMPDs
}
