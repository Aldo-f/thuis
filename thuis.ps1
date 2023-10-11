# Global variables
$global:cachedStreamInfo = @{}
$global:argumentListFilePath = 'argumentList.txt'
$global:listFilePath = 'list.txt'
$global:settingsFilePath = 'settings.json'
$global:patternExtension = '.[a-zA-Z0-9]{2,3}';
$global:pattersResolutionFromName = "[_\-](\d{3,4}p)[_\-.]";

# Get and set settings
$global:settings = Set-Settings -filePath $global:settingsFilePath 

# Function to initialize or update settingsFunction Set-Settings {
Function Set-Settings {
    param (
        [string] $filePath
    )

    $defaults = @{
        'directory'   = 'media'
        'resolutions' = @(720, 1080)
    }

    # If settings file exists, load it; otherwise, use defaults
    if (Test-Path $filePath) {
        $settings = Get-Content $filePath | ConvertFrom-Json
    }
    else {  
        $settings = $defaults;
    }
    
    # Format resolutions for display
    $resolutionsDisplay = ($settings.resolutions -join ', ').Trim()
    $defaultResolutionsDisplay = ($defaults.resolutions -join ', ').Trim()
    
    # Prompt user to review and edit settings
    $userChoice = Read-Host "Current Settings:`nDirectory: $($settings.directory)`nResolutions: $resolutionsDisplay`n`nAre these settings okay? (y/n)"
    if ($userChoice -eq 'n') {
        $directory = Read-Host "Enter new directory (default '$($defaults.directory)')"
        if ([string]::IsNullOrWhiteSpace($directory) ) {
            $settings.directory = $defaults.directory;
        }
        else {
            $settings.directory = $directory;
        }

        $resolutions = Read-Host "Enter new resolutions (default '$($defaultResolutionsDisplay)')"
        if ([string]::IsNullOrWhiteSpace($resolutions) ) {
            $settings.resolutions = $defaults.resolutions;
        }
        else {
            $settings.resolutions = $resolutions -split ',' | ForEach-Object { [int]$_ }        
        }
    }
    
    # Save settings to file
    ConvertTo-Json -InputObject $settings | Out-File -filePath $filePath
    
    return $settings
}
    

Function Get-DefaultResolution {
    return $global:settings.resolutions[0]
}

Function Get-ResolutionFromString {
    param ($resolution); 
    return [int]($resolution -split 'x')[1]
}


# Function to generate a argumentList-item
Function Get-ArgumentList {
    param (
        [string] $mpd,
        [int] $videoStream,
        [string] $outputName,
        [string] $mediaDirectory
    )

    if ([string]::IsNullOrWhiteSpace($mediaDirectory)) {
        $mediaDirectory = $global:settings.directory;
    }

    $ArgumentList = "-v quiet -stats -i $mpd -map 0:v:$videoStream -c:v copy -map 0:a -c:a copy $mediaDirectory/$outputName";

    return $ArgumentList;
}

# Function to get the index of the closest video stream to the target resolution
Function Get-ClosestVideoStream {
    param (
        [int] $resolution,
        [array] $resolutions
    )

    $closestResolutionIndex = 0
    $closestResolutionDiff = [math]::abs((Get-ResolutionFromString $resolutions[0]) - $resolution)

    for ($i = 0; $i -lt $resolutions.Count; $i++) {
        $currentResolution = $resolutions[$i]
        $resolutionInt = Get-ResolutionFromString $currentResolution
        $diff = [math]::abs($resolutionInt - $resolution)

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
    $key = $mpd + $streamType; 

    # Check if the information is already cached
    if ($cachedStreamInfo.ContainsKey($key)) {
        return $cachedStreamInfo[$key]
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
    $global:cachedStreamInfo[$key] = $streamDetails

    return $streamDetails
}


Function Get-ChooseVideoStream($mpd, $resolution) {
    $resolutions = Get-Resolutions $mpd;
   
    # Find exact match
    $chosenVideoStream = Get-ExactVideoStream -resolution $resolution -resolutions $resolutions; 

    if (![int]::IsNullOrEmpty) {
        return $chosenVideoStream;
    }

    # If no exact match found, find the closest resolution
    return Get-ClosestVideoStream -resolution $resolution -resolutions $resolutions;
}

Function Get-ExactVideoStream() {
    param (
        [int] $resolution, 
        [array] $resolutions, 
        [string] $mpd
    )

    # If $resolutions is empty and $mpd is provided, get the resolutions from the $mpd
    if (-not $resolutions -and $mpd) {
        $resolutions = Get-Resolutions $mpd;
    }

    # If the resolution matches, return the corresponding stream number
    for ($i = 0; $i -lt $resolutions.Count; $i++) {
        $height = Get-ResolutionFromString $resolutions[$i];
        if ($height -eq $resolution) {
            return $i  # Return the index directly
        }
    }
}


# Function to process MPDs
Function ProcessMPDs {
    # Initialize an array to store argument lists
    $lists = @()
 
    $patternResolutionFromOutputName = $global:pattersResolutionFromName;

    # Check if the 'video' directory exists, if not, create it
    $mediaDirectory = $global:settings.directory;
    if (-not (Test-Path $mediaDirectory)) {
        New-Item -ItemType Directory -Path $mediaDirectory | Out-Null
    }

    # Check if 'list.txt' exists
    if (Test-Path $global:listFilePath) {
        $choice = Read-Host "Found '$($global:listFilePath)'. Do you want to continue with the existing list? (y/n)"
        if ($choice -eq 'y') {
            Write-Host "Continuing with the existing list..."
            $lists = Get-Content $global:listFilePath
        }
    }     

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

        # Prompt the user for an output name
        $outputName = Read-Host "Enter the desired output name (without extension)"

        # Ensure the user's input is not empty
        if ([string]::IsNullOrWhiteSpace($outputName)) {
            # Get the current date in the format 'y-m-d'
            $currentDate = Get-Date -Format 'y-M-d'
 
            # Get the list of files in the directory
            $existingFiles = Get-ChildItem -Path $global:settings.directory
 
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
            if ($outputName -notmatch "\$global:patternExtension$") {
                # If no extension found, add .mp4
                $outputName += ".mp4"
            }
        } 

        # Check if $outputName contains a resolution (e.g., 720p)
        $pattern = $patternResolutionFromOutputName
        if ($outputName -match $pattern) {
            $resolutionsToFind = @([int]($matches[1] -replace '[^0-9]', ''))
        }
        else {
            $resolutionsToFind = $global:settings.resolutions
        }

        # Get exact video stream if resolution is provided
        foreach ($resolution in $resolutionsToFind) {
            if ($null -ne $resolution) {
                $exactVideoStream = Get-ExactVideoStream -mpd $mpd -resolution $resolution
                if ($null -ne $exactVideoStream) {
                    break;
                }
            }
        }


        if ($null -eq $exactVideoStream) {

            # Display the available video streams to the user
            Write-Host "Available Video Streams:"

            for ($i = 0; $i -lt $resolutions.Count; $i++) {
                $resolution = Get-ResolutionFromString $resolutions[$i];
                Write-Host "$($i + 1): Resolution $resolution"           
            }

            # Get the default resolution from the array
            $defaultResolution = Get-DefaultResolution;

            do {
                # Prompt the user to choose a video stream
                $chosenVideoStream = Read-Host "Enter the number corresponding to your preferred video stream (leave empty to select closest to default $defaultResolution)";

                # If user hits enter without choosing and $outputName doesn't contain a resolution pattern, use the closest resolution to the default height
                if ([string]::IsNullOrWhiteSpace($chosenVideoStream) -and -not ($outputName -match $pattern)) {  
                    $resolution = $defaultResolution
                    $chosenVideoStream = Get-ClosestVideoStream -resolution $resolution -resolutions $resolutions
                    $chosenVideoStream += 1;
                }

                $invalidChoose = $chosenVideoStream -lt 1 -or $chosenVideoStream -gt $resolutions.Count; 
                if ($invalidChoose) {
                    Write-Host "Invalid choice. Please enter a number between 1 and $($resolutions.Count)."
                }

            } while ($invalidChoose)

            # Adjust to zero-based index
            $chosenVideoStream -= 1;
        }
        else {
            $chosenVideoStream = $exactVideoStream
        }

        # Extract the resolution from the chosen stream information using the array
        $resolutionString = $resolutions[$chosenVideoStream]

        Write-Host "You have chosen: Resolution $resolutionString"

        # Create the list
        $resolutions = Get-ResolutionFromString resolutionString
        $list = "$mpd $outputName $resolution";
        $lists += $list;
    }

    # Save content to the file
    $lists | Out-File -FilePath $global:listFilePath
    Write-Host "List saved to $($global:listFilePath)."
}


# Function to process the argumentList.txt
Function ProcessArgumentList {
    $argumentLists = Get-Content $global:argumentListFilePath | Where-Object { $_ -match '\S' }

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
        return;
    }

    $choice = Read-Host "Do you want to proceed with processing? (y/n)"
    if ($choice -eq 'y') {
        Write-Host "Starting processing..."
        $filesToProcess | ForEach-Object { Start-Process -FilePath ffmpeg.exe -ArgumentList $_ -Wait -NoNewWindow }
    }
    else {
        Write-Host "Processing aborted by user."
        return;
    }
}


# Function to process the list.txt
Function ProcessList {
    Write-Host "Processing list..."
    $listContent = Get-Content $global:listFilePath
    foreach ($line in $listContent) {

        $splitLine = $line -split '\s+', 3
        $mpd = $splitLine[0]
        $outputName = $splitLine[1]
        $resolution = $splitLine[2]
        
        if (-not [string]::IsNullOrWhiteSpace($resolution)) {
            $chosenVideoStream = Get-ChooseVideoStream $mpd $resolution
        }
        else {
            # Extract video stream based on filename pattern
            $pattern = $global:pattersResolutionFromName;
            if ($outputName -match $pattern) {
                $resolution = $matches[1] -replace '[ _-]', '' -replace 'p', ''
                $chosenVideoStream = Get-ChooseVideoStream $mpd $resolution
            }
            else {
                # Use default resolution if pattern doesn't match
                $resolution = Get-DefaultResolution;
                $chosenVideoStream = Get-ClosestVideoStream -resolution $resolution -resolutions (Get-Resolutions $mpd)
            } 
        }

        # Create the full argument list
        $ArgumentList = Get-ArgumentList -mpd $mpd -videoStream $chosenVideoStream -outputName $outputName
        $argumentLists += $ArgumentList
    }
    # Save content to the file after each iteration
    $argumentLists | Out-File -FilePath $global:argumentListFilePath
    Write-Host "List saved to $($global:argumentListFilePath)."

    $choice = Read-Host "Do you want to process the list now? (y/n)"
    if ($choice -eq 'y') {
        ProcessArgumentList
    }
    else {
        Write-Host "Processing aborted by user."
        return  # Terminate the process
    }
}


function StartProgram {

    # Check if 'list.txt' and 'argumentList.txt' does not exists
    if (-not (Test-Path $global:listFilePath) -and -not (Test-Path $global:argumentListFilePath)) {
        Write-Host "No '$($global:argumentListFilePath)' or '$($global:listFilePath)' found. Starting interactive mode..."
        ProcessMPDs
    }  

    # Check if 'list.txt' exists
    if (Test-Path $global:listFilePath) {
        $choice = Read-Host "Found '$($global:listFilePath)'. Do you want to process it? (y/n)"
        if ($choice -eq 'y') {
            ProcessList
        }
    }

    # Check if 'argumentList.txt' exists
    if (Test-Path $global:argumentListFilePath) {
        $choice = Read-Host "Found '$($global:argumentListFilePath)'. Do you want to process it? (y/n)"
        if ($choice -eq 'y') {
            ProcessArgumentList
        }
        elseif ($choice -eq 'n') {
            ProcessMPDs
            StartProgram
        }
        else {
            Write-Host "Invalid choice. Exiting."
        }
    }
}

# Start it
StartProgram