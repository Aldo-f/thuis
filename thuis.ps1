# Global variables
$global:cachedInfo = @{}
$global:dataFolder = 'data';
$global:argumentListFilePath = "$global:dataFolder/argumentList.txt"
$global:listFilePath = "$global:dataFolder/list.txt"
$global:settingsFilePath = "$global:dataFolder/settings.json"
$global:cachedFilePath = "$global:dataFolder/cached_data.xml"
$global:patternExtension = '.[a-zA-Z0-9]{2,3}';
$global:pattersResolutionFromName = "[_\-](\d{3,4}p)[_\-.]";
$global:filename = '';

# Function to initialize or update settings
Function Initialize-OrUpdateSettings {
    param (
        [string] $filePath,
        [bool] $promptUser = $true
    )

    $defaults = @{
        'directory'   = 'media'
        'resolutions' = @(720, 1080)
        'filename'    = ''
    }
    
    # If settings file exists, load it; otherwise, use defaults
    if (Test-Path $filePath) {
        # Convert JSON content to PowerShell object
        $loadedSettings = Get-Content $filePath | Out-String | ConvertFrom-Json

        # Convert the loaded settings to a hashtable
        $loadedSettingsHashtable = @{}
        foreach ($property in $loadedSettings.PSObject.Properties) {
            $loadedSettingsHashtable[$property.Name] = $property.Value
        }

        # Merge loaded settings with defaults
        $settings = $defaults.Clone()

        foreach ($key in $defaults.Keys) {
            if ($loadedSettingsHashtable.ContainsKey($key)) {
                $settings[$key] = $loadedSettingsHashtable[$key]
            }
        }

        # Convert the merged settings back to an object
        $settings = New-Object PSObject -Property $settings
    }
    else {
        $settings = $defaults
    }

    if ($promptUser) {
        # Format resolutions for display
        $resolutionsDisplay = ($settings.resolutions -join ', ').Trim()
        $defaultResolutionsDisplay = ($defaults.resolutions -join ', ').Trim()

        do {
            # Prompt user to review and edit settings
            $correct = AskYesOrNo "Current Settings:`nDirectory: $($settings.directory)`nResolutions: $resolutionsDisplay`nFilename: $($settings.filename)`n`nAre these settings okay? (Y/n)"
            if (!$correct) {
                $directory = Read-Host "Enter new directory (default '$($defaults.directory)')"
                if ([string]::IsNullOrWhiteSpace($directory)) {
                    $settings.directory = $defaults.directory;
                }
                else {
                    $settings.directory = $directory;
                }

                $resolutions = Read-Host "Enter new resolutions (default '$($defaultResolutionsDisplay)')"
                if ([string]::IsNullOrWhiteSpace($resolutions)) {
                    $settings.resolutions = $defaults.resolutions;
                }
                else {
                    $settings.resolutions = $resolutions -split ',' | ForEach-Object { [int]$_ }        
                }

                $filename = Read-Host "Enter new filename (default '$($defaults.filename)')"
                if ([string]::IsNullOrWhiteSpace($filename)) {
                    $settings.filename = $defaults.filename;
                }
                else {
                    $settings.filename = $filename;
                }
                
                # Format resolutions for display
                $resolutionsDisplay = ($settings.resolutions -join ', ').Trim()
            }
        } while (!$correct)

        # Save settings to file
        ConvertTo-Json -InputObject $settings | Out-File -filePath $filePath
    }

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

    $ArgumentList = "-v quiet -stats -i $mpd -crf 0 -aom-params lossless=1 -map 0:v:$videoStream -c:v copy -map 0:a -c:a copy -tag:v avc1 $mediaDirectory/$outputName";

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

# Function to get general ffprobe output
Function Get-FfprobeOutput($mpd) {
    $outputKey = $mpd + "_ffprobeOutput"

    # Check if the ffprobe output is already cached
    if ($cachedInfo.ContainsKey($outputKey)) {
        return $cachedInfo[$outputKey]
    }
    else {
        # Use ffprobe to get the general output
        $ffprobeOutput = & ffprobe.exe $mpd 2>&1

        # Check if ffprobeOutput is empty
        if ([string]::IsNullOrWhiteSpace($ffprobeOutput)) {
            Write-Host "Error: ffprobe output is empty. Make sure ffprobe is installed and accessible."
            exit
        }

        # Cache the ffprobe output
        $global:cachedInfo[$outputKey] = $ffprobeOutput

        # Save cached data to a file
        Save-CachedData

        return $ffprobeOutput
    }
}

# Function to save cached data to a file
Function Save-CachedData {
    $cachedInfo | Export-Clixml -Path $global:cachedFilePath
}

# Function to import cached data from a file
Function Import-CachedData {
    if (Test-Path $global:cachedFilePath) {
        $global:cachedInfo = Import-Clixml -Path $global:cachedFilePath 
        $null = $cachedInfo
    }
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

    # Save cached data to a file
    Save-CachedData

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
    # Create an object to store used indices
    $usedIndices = [PSCustomObject]@{ Indices = @() }
 
    # Check if the output directory exists, if not, create it
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

        [array]$mdArray = Get-MPDArray $mpd;
        foreach ($mpd in $mdArray) {
            $list = Get-ProcessVideoStreams -mpd $mpd -usedIndices $usedIndices
            $lists += $list
        }
    }

    # Save content to the file
    $lists | Out-File -FilePath $global:listFilePath
    Write-Host "List saved to $($global:listFilePath)."
}

function Get-MPDArray($mpd) {
    # Split the $mpd string by ',' or ';' or ' ' and remove empty entries
    $mpdArray = $mpd -split '[,; ]' | Where-Object { $_ -ne '' }

    # Ensure $mpdArray is always an array
    if ($mpdArray -isnot [System.Array]) {
        $mpdArray = @($mpdArray)
    }

    return [System.Array]$mpdArray
}

# Function to process video streams and obtain output name
Function Get-ProcessVideoStreams() {
    param (
        [string] $mpd,
        [PSCustomObject] $usedIndices,
        [bool] $askQuestions = $true
    )

    # Get Video streams and resolutions
    $resolutions = Get-Resolutions $mpd

    # Check if there are available video streams
    if ($resolutions.Count -eq 0) {
        Write-Host "No valid video streams found. Please try a different .mpd-file"
        return $null
    }

    if ($askQuestions) {
        # Prompt the user for an output name
        $outputName = Read-Host "Enter the desired output name (without extension)"

        # Ensure the user's input is not empty
        if ([string]::IsNullOrWhiteSpace($outputName)) {
            # Generate the output name
            $outputName = GenerateOutputName -usedIndices $usedIndices -filename $global:settings.filename
        }
        else {
            # Check if the provided output name has an extension
            if ($outputName -notmatch "$global:patternExtension$") {
                # If no extension found, add .mp4
                $outputName += ".mp4"
            }
        } 
    }
    else {
        # Generate the output name
        $outputName = GenerateOutputName -usedIndices $usedIndices -filename $global:settings.filename
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
                break
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

    if ($askQuestions) {
        Write-Host "You have chosen: Resolution $resolutionString"
    }

    # Create the list
    $resolution = Get-ResolutionFromString $resolutionString
    return "$mpd $outputName $resolution"
}

# Function to generate the output name
function GenerateOutputName {
    param (
        [string]$filename = "",
        [PSCustomObject]$usedIndices
    )

    # Function to increment index and generate filename
    function IncrementAndGenerateFilename($prefix, $index) {
        $outputFilename = "${prefix}$("{0:D3}" -f $index).mp4"

        if ($usedIndices.Indices -notcontains $index -and -not (Test-Path (Join-Path $global:settings.directory $outputFilename))) {
            $usedIndices.Indices += $index
            return $outputFilename
        }

        $index++
        return $null
    }

    if ($filename) {
        # Check if the last part is a digit
        $lastPart = $filename -replace '^.*[^0-9](\d+)$', '$1'

        if ($lastPart -ne $filename) {
            # Remove the last part from the filename
            $filename = $filename -replace '\d+$'

            # If the last part is a digit, use it as the starting index
            $index = [int]$lastPart

            do {
                $outputFilename = IncrementAndGenerateFilename $filename $index

                if ($outputFilename) {
                    return $outputFilename
                }

                $index++
            } while ($true)
        }
    }

    # If no filename provided, use the existing logic
    $currentDate = Get-Date -Format 'y-M-d'
    $index = 1
    do {
        $outputFilename = IncrementAndGenerateFilename "${currentDate}_" $index

        if ($outputFilename) {
            return $outputFilename
        }

        $index++
    } while ($true)
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
    $message += ':'
    Write-Host $message

    $tableData = @()
    for ($i = 0; $i -lt $resolutions.Count; $i++) {
        # $resolution = Get-ResolutionFromString $resolutions[$i];
        $tableData += [PSCustomObject]@{
            Option     = ($i + 1).ToString()
            Resolution = $resolutions[$i]
        }
    }
    $tableData | Format-Table -Property Option, Resolution | Out-String | Write-Host

    # Get the default resolution from the array
    $defaultResolution = Get-DefaultResolution;

    # Prompt the user to choose a video stream
    $streamPrompt = "Enter the number corresponding to your preferred video stream"
    if (![string]::IsNullOrWhiteSpace($outputName)) {
        $streamPrompt += " for $outputName"
    }
    if (-not ($outputName -match $global:pattersResolutionFromName)) {
        $streamPrompt += " (leave empty to select closest to default $defaultResolution)"
    }

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
        $outputName = GetOutputName -command $command;     

        # Check if the file already exists
        if (Test-Path $outputName) {
            if (-not (AskYesOrNo "File $outputName already exists. Do you want to overwrite it? (Y/n)")) {
                continue # Skip this file
            }
        }

        # Extract the directory from the $outputName and create it if not exists
        $directory = GetDirectory -command $command -outputName $outputName; 
        if (-not (Test-Path $directory)) {
            New-Item -ItemType Directory -Path $directory | Out-Null
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
    $tableData | Format-Table -Property Filename, Resolution | Out-String | Write-Host

    if ($filesToProcess.Count -eq 0) {
        Write-Host "No files to process."
        return;
    }

    if (AskYesOrNo "Do you want to proceed with processing? (Y/n)") {
        Write-Host "Starting processing..."
        $filesToProcess | ForEach-Object {
            Start-Process -FilePath ffmpeg.exe -ArgumentList $_ -Wait -NoNewWindow
        }
          
        # Notify the user when processing is complete
        Write-Host "Processing complete. Check the output directory: $($global:settings.directory)"

        # Ask if the user wants to remove the list files
        if (AskYesOrNo "Do you want to remove the argumentList.txt and list.txt files? (Y/n)") {
            Remove-Item -Path $global:argumentListFilePath, $global:listFilePath -Force
            Write-Host "Textfiles removed."
        }

        # Ask if the user wants to open the folder
        AskAndOpenOutputFolder -directory $directory
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

# Function to ask if the user wants to open the output folder
Function AskAndOpenOutputFolder {
    param (
        [string] $directory
    )

    # Check if the directory exists
    if (-not (Test-Path $directory -PathType Container)) {
        Write-Host "Error: The specified directory does not exist: $directory"
        return
    }

    # Ask if the user wants to open the folder
    if (AskYesOrNo "Do you want to open the output folder? (Y/n)") {
        if (-not $directory.StartsWith('/')) {
            $directory = Join-Path (Get-Location) $directory
        }

        Invoke-Item $directory
    }
}

Function GetOutputName() {
    param (
        [string]$command
    )

    # Explode by space
    $parts = $command -split ' '

    # Get the last part
    $lastPart = $parts[-1]

    return $lastPart;
}

# Function to extract media directory from a URL
Function GetDirectory() {
    param (
        [string]$command,
        [string]$outputName = ""
    )

    if ($outputName -eq "") {
        $outputName = GetOutputName -command $command
    }

    # Remove all after the last '/'
    $directory = $outputName -replace '/.*', ''

    return $directory
}

# Function to process the list.txt
Function ProcessList {
    param (
        [bool] $askQuestions = $true
    )

    # Check if $global:argumentListFilePath has existing data    
    if ((Get-CleanFileContent $global:argumentListFilePath).Count -gt 0) {
        if ($askQuestions) {            
            if (AskYesOrNo "There is existing data inside $($global:argumentListFilePath). Do you want to clear all data before processing? (Y/n)") {
                Set-Content -Path $global:argumentListFilePath -Value ''
                Write-Host "Cleared existing data."
            }
            else {
                Write-Host "We will add new data to the list."
            }
        }
        else {
            # Clear without question
            Set-Content -Path $global:argumentListFilePath -Value ''
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

# Function to get clean file content
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

# Function to check and try to install dependencies using multiple package managers, provide instructions if not successful
Function CheckAndInstallDependency {
    param (
        [string] $dependencyName,
        [string[]] $installCommands,
        [string] $installInstructions
    )

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

# Function to process MPDs from command-line arguments
Function ProcessCommandLineMPDs {
    param (
        [string[]] $mpdArray,
        [bool] $askQuestions
    )

    # Initialize an array to store argument lists
    $lists = @()
    # Create an object to store used indices
    $usedIndices = [PSCustomObject]@{ Indices = @() }

    # Check if the output directory exists, if not, create it
    $mediaDirectory = $global:settings.directory;
    if (-not (Test-Path $mediaDirectory)) {
        New-Item -ItemType Directory -Path $mediaDirectory | Out-Null
    }

    foreach ($mpd in $mpdArray) {
        $list = Get-ProcessVideoStreams -mpd $mpd -usedIndices $usedIndices -askQuestions $askQuestions
        $lists += $list
    }

    # Save content to the file
    $lists | Out-File -FilePath $global:listFilePath
    Write-Host "List saved to $($global:listFilePath)."
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

# Function to process command-line arguments
Function ProcessCommandLineArguments {
    param (
        [string[]] $arguments
    )

    $listIndex = $arguments.IndexOf("-list")
    $infoIndex = $arguments.IndexOf("-info")

    # Process -info if found
    if ($infoIndex -ge 0) {
        $mdsIndex = $infoIndex + 1
        if ($mdsIndex -lt $arguments.Count) {
            $mpd = $arguments[$mdsIndex]
            Show-MPDInfo $mpd;
            Exit;
        }
        else {
            Write-Host "Missing MPDs after -info argument."
            Exit
        }
    }

    # Process each argument
    for ($i = 0; $i -lt $arguments.Count; $i++) {
        if ($i -eq $listIndex) {
            # Skip -list, it will be processed at the end
            $i++;
            continue
        }

        $arg = $arguments[$i]

        switch ($arg) {
            { $_ -in "-directory", "-output", "-o" } {
                $i++
                if ($i -lt $arguments.Count) {
                    $global:settings.directory = $arguments[$i]
                    Write-Host "Output directory updated to $($global:settings.directory)"
                }
                else {
                    Write-Host "Missing value for $arg."
                    Exit
                }
            }

            { $_ -in "-resolutions", "-p" } {
                $i++
                if ($i -lt $arguments.Count) {
                    $global:settings.resolutions = @($arguments[$i] -split ',' | ForEach-Object { [int]$_ })
                    Write-Host "Resolutions updated to $($global:settings.resolutions -join ', ')"
                }
                else {
                    Write-Host "Missing value for $arg."
                    Exit
                }
            }

            { $_ -in "-filename" } {
                $i++
                if ($i -lt $arguments.Count) {
                    $global:settings.filename = $arguments[$i]
                    Write-Host "Filename updated to $($global:settings.filename)"
                }
                else {
                    Write-Host "Missing value for $arg."
                    Exit
                }
            }
        }
    }

    # Process -list if found
    if ($listIndex -ge 0) {
        $mdsIndex = $listIndex + 1
        if ($mdsIndex -lt $arguments.Count) {
            $mpd = $arguments[$mdsIndex]
            [array]$mpdArray = Get-MPDArray $mpd
            ProcessCommandLineMPDs -mpdArray $mpdArray -askQuestions $false
            ProcessList -askQuestions $false
            ProcessArgumentList
            Exit
        }
        else {
            Write-Host "Missing MPDs after -list argument."
            Exit
        }
    }
}

# Check if arguments are provided
$global:settings = Initialize-OrUpdateSettings -filePath $global:settingsFilePath -promptUser ($args.Count -eq 0)

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

# Import cached data when the script starts
Import-CachedData

# Process command-line arguments before starting the program
ProcessCommandLineArguments $args

# Start it
StartProgram