# Global variables
$global:cachedStreamInfo = @{}
$global:argumentListFilePath = 'argumentList.txt'
$global:listFilePath = 'list.txt'
$global:settingsFilePath = 'settings.json'
$global:patternExtension = '.[a-zA-Z0-9]{2,3}';
$global:pattersResolutionFromName = "[_\-](\d{3,4}p)[_\-.]";

# Function to initialize or update settings
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

    do {
        # Prompt user to review and edit settings
        $correct = AskYesOrNo "Current Settings:`nDirectory: $($settings.directory)`nResolutions: $resolutionsDisplay`n`nAre these settings okay? (Y/n)"
        if (!$correct) {
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
            
            # Format resolutions for display
            $resolutionsDisplay = ($settings.resolutions -join ', ').Trim()
        }
    } while (!$correct)

    # Save settings to file
    ConvertTo-Json -InputObject $settings | Out-File -filePath $filePath
    
    return $settings
}

# Function to get the default resolution from settings
Function Get-DefaultResolution {
    return $global:settings.resolutions[0]
}

# Function to get the resolution from string
Function Get-ResolutionFromString {
    param ([string] $resolution); 
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

# Function to get all available resolution from MPD
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

# Function to stream info by MPD and streamType
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

# Function to get exact video-stream; or the closest one
Function Get-ChooseVideoStream() {
    param (
        [string] $mpd,
        [int] $resolution,
        [string] $outputName = ""
    )

    $resolutions = Get-Resolutions $mpd;
   
    # Find exact match
    $chosenVideoStream = Get-ExactVideoStream -resolution $resolution -resolutions $resolutions; 

    if (![string]::IsNullOrEmpty($chosenVideoStream)) {
        return $chosenVideoStream;
    }    

    # If no exact match found, ask the user to choose
    return Get-UserChosenVideoStream -resolutions $resolutions -outputName $outputName
}

# Function to get exact video stream
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
            return $i # Return the index directly
        }
    }
}

# Function to process MPDs
Function ProcessMPDs {
    # Initialize an array to store argument lists
    $lists = @()
 
    # Check if the 'video' directory exists, if not, create it
    $mediaDirectory = $global:settings.directory;
    if (-not (Test-Path $mediaDirectory)) {
        New-Item -ItemType Directory -Path $mediaDirectory | Out-Null
    }

    # Check if 'list.txt' exists
    if (Test-Path $global:listFilePath) {
        if (AskYesOrNo "Found '$($global:listFilePath)'. Do you want to continue with the existing list? (Y/n)") {
            Write-Host "Continuing with the existing list..."
            $lists = Get-CleanFileContent $global:listFilePath
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
        $pattern = $global:pattersResolutionFromName
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
            $chosenVideoStream = Get-UserChosenVideoStream -resolutions $resolutions -outputName $outputName
        }
        else {
            $chosenVideoStream = $exactVideoStream
        }

        # Extract the resolution from the chosen stream information using the array
        $resolutionString = $resolutions[$chosenVideoStream]

        Write-Host "You have chosen: Resolution $resolutionString"

        # Create the list
        $resolution = Get-ResolutionFromString $resolutionString
        $list = "$mpd $outputName $resolution";
        $lists += $list;
    }

    # Save content to the file
    $lists | Out-File -FilePath $global:listFilePath
    Write-Host "List saved to $($global:listFilePath)."
}

Function Get-UserChosenVideoStream {
    param (
        [string[]]$resolutions,
        [string]$outputName = ""
    )

    # Display the available video streams to the user
    $message = "Available Video Streams"
    if (![string]::IsNullOrWhiteSpace($outputName)) {
        $message += " for $outputName"
    }
    Write-Host "{$message}:"

    # $optionResolutionTable = @()
    # for ($i = 0; $i -lt $resolutions.Count; $i++) {
    #     $resolution = Get-ResolutionFromString $resolutions[$i];
    #     $optionResolutionTable += [PSCustomObject]@{
    #         Option     = ($i + 1).ToString()
    #         Resolution = $resolution.ToString()
    #     }
    # }
    # $optionResolutionTable | Format-Table -Property Option, Resolution

    for ($i = 0; $i -lt $resolutions.Count; $i++) {
        $resolution = Get-ResolutionFromString $resolutions[$i];
        Write-Host "$($i + 1): Resolution $resolution"           
    }

    # Get the default resolution from the array
    $defaultResolution = Get-DefaultResolution;

    # Prompt the user to choose a video stream
    $streamPrompt = "Enter the number corresponding to your preferred video stream"
    if (![string]::IsNullOrWhiteSpace($outputName)) {
        $streamPrompt += " for $outputName"
    }
    $streamPrompt += " (leave empty to select closest to default $defaultResolution)"

    do {
        $chosenVideoStream = Read-Host "$streamPrompt"

        # If user hits enter without choosing and $outputName doesn't contain a resolution pattern, use the closest resolution to the default height
        if ([string]::IsNullOrWhiteSpace($chosenVideoStream) -and -not ($outputName -match $global:pattersResolutionFromName)) {  
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

    return $chosenVideoStream
}

# Function to process the argumentList.txt
Function ProcessArgumentList {
    $argumentLists = Get-Content $global:argumentListFilePath | Where-Object { $_ -match '\S' }

    $filesToProcess = @()
    $tableData = @()

    foreach ($command in $argumentLists) {
        # Extract the $outputName from the command
        $outputName = $command -replace '.*\s(\S+\.\w+)', '$1'

        # Check if the file already exists
        if (Test-Path $outputName) {
            if (-not (AskYesOrNo "File $outputName already exists. Do you want to overwrite it? (Y/n)")) {
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
        # Write-Host "File: $outputName; Resolution: $resolution"

        # Add data to table
        $tableData += [PSCustomObject]@{
            Filename   = $outputName
            Resolution = $resolution
        }

        $filesToProcess += $command
    }

    # Display table
    $tableData | Format-Table -Property Filename, Resolution

    if ($filesToProcess.Count -eq 0) {
        Write-Host "No files to process."
        return;
    }

    if (AskYesOrNo "Do you want to proceed with processing? (Y/n)") {
        Write-Host "Starting processing..."
        $filesToProcess | ForEach-Object { Start-Process -FilePath ffmpeg.exe -ArgumentList $_ -Wait -NoNewWindow }
    }
    else {
        do {
            if (AskYesOrNo "Exit program? (Y/n)") {
                Exit
            }
            elseif (AskYesOrNo "Do you want to start again? (Y/n)") {
                StartProgram
            }
        } while ($true)
    }
}

# Function to process the list.txt
Function ProcessList {
    # Check if $global:argumentListFilePath has existing data    
    if ((Get-CleanFileContent $global:argumentListFilePath).Count -gt 0) {
        if (AskYesOrNo "There is existing data inside $($global:argumentListFilePath). Do you want to clear all data before processing? (Y/n)") {
            Set-Content -Path $global:argumentListFilePath -Value ''
            Write-Host "Cleared existing data."
        }
        else {
            Write-Host "We will add new data to the list."
        }
    }

    Write-Host "Processing list..."
    $listContent = Get-CleanFileContent $global:listFilePath
    foreach ($line in $listContent) {

        $splitLine = $line -split '\s+', 3
        $mpd = $splitLine[0]
        $outputName = $splitLine[1]
        $resolution = $splitLine[2]
        
        if (-not [string]::IsNullOrWhiteSpace($resolution)) {
            $chosenVideoStream = Get-ChooseVideoStream -mpd $mpd -resolution $resolution -outputName $outputName
        }
        else {
            # Extract video stream based on filename pattern
            $pattern = $global:pattersResolutionFromName;
            if ($outputName -match $pattern) {
                $resolution = $matches[1] -replace '[ _-]', '' -replace 'p', ''
                $chosenVideoStream = Get-ChooseVideoStream -mpd $mpd -resolution $resolution -outputName  $outputName
            }
            else {
                # Use default resolution if pattern doesn't match
                $resolution = Get-DefaultResolution;
                $chosenVideoStream = Get-ClosestVideoStream -resolution $resolution -resolutions (Get-Resolutions $mpd)
            } 
        }

        # Create the full argument list
        $ArgumentList = Get-ArgumentList -mpd $mpd -videoStream $chosenVideoStream -outputName $outputName
  
        # Save content to the file after each iteration
        Add-Content -Path $global:argumentListFilePath -Value $ArgumentList
    }
    Write-Host "List saved to $($global:argumentListFilePath)."   
}

# Function to get clen file content
Function Get-CleanFileContent {
    param (
        [string]$filePath
    )

    # Check if file exists
    if (Test-Path $filePath) {
        $fileContent = Get-Content $filePath | ForEach-Object { $_.Trim() } | Where-Object { $_ -notmatch '^\s*[-#;](?=\s|$)' -and $_ -ne '' }

        return [string[]]$fileContent    
    }
    else {
        return [string[]]@()
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

# Function to check and try to install dependencies using multiple package managers, provide instructions if not successful

Function CheckAndInstallDependency {
    param (
        [string] $dependencyName,
        [string[]] $installCommands,
        [string] $installInstructions
    )

    $dependencyInstalled = $null

    try {
        $dependencyInstalled = Get-Command $dependencyName -ErrorAction SilentlyContinue
    }
    catch {
        $dependencyInstalled = $null
    }

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




# Function to start the program
function StartProgram {
    # Check if 'list.txt' and 'argumentList.txt' exists
    $argumentListExists = (Get-CleanFileContent $global:argumentListFilePath).Count -gt 0
    $listExists = (Get-CleanFileContent $global:listFilePath).Count -gt 0

    if (-not ($listExists -or $argumentListExists)) {
        Write-Host "No '$($global:argumentListFilePath)' or '$($global:listFilePath)' found."
        Write-Host "Starting interactive mode..."
        ProcessMPDs
    }
    else {
        if ($listExists) {
            Write-Host "Found '$($global:listFilePath)'."
        }
        if ($argumentListExists) {
            Write-Host "Found '$($global:argumentListFilePath)'."
        }
        if (AskYesOrNo "Do you still want to start interactive mode? (y/N)") {
            ProcessMPDs
        }
    }

    # Check if 'list.txt' exists
    if ((Get-CleanFileContent $global:listFilePath).Count -gt 0) {
        if (AskYesOrNo "Found '$($global:listFilePath)'. Do you want to process it? (Y/n)") {
            ProcessList
        }
    }

    # Check if 'argumentList.txt' exists
    if ((Get-CleanFileContent $global:argumentListFilePath).Count -gt 0) {
        if (AskYesOrNo "Found '$($global:argumentListFilePath)'. Do you want to process it? (Y/n)") {
            ProcessArgumentList
        }
        else {
            if (AskYesOrNo "Exit program? (Y/n)") {
                Exit
            }
            else {
                StartProgram
            }
        }
    }    
}

# Get and set settings
$global:settings = Set-Settings -filePath $global:settingsFilePath 

# Check if all dependencies are met
CheckAndInstallDependency -dependencyName "ffmpeg.exe" `
    -installCommands @(
    "choco install ffmpeg",
    "scoop install ffmpeg",
    "winget install ffmpeg"
) `
    -installInstructions "If package managers are not available, please download and install ffmpeg from https://www.ffmpeg.org/download.html"

# Start it
StartProgram