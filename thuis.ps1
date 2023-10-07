# $name = Read-Host 'What is your name?'
# $response = Read-Host "Hey $name, how do yo feel?"; 
# Write-Output = "Nice to hear $name that you are feeling '$response'";

$mpd = Read-Host "What .mpd file do you wish to download?"
$ArgumentList = "-i $mpd -c copy video/test.mp4"
Start-Process -FilePath ffmpeg.exe -ArgumentList $ArgumentList -Wait -NoNewWindow