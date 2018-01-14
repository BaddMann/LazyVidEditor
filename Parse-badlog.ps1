#### Powershell Bad Log Parsing.
## Using https://foxdeploy.com/2015/01/05/walkthrough-parsing-log-or-console-output-with-powershell/
### Look into http://www.videoproductionslondon.com/blog/edl-to-html-with-thumbnails
### Look into http://www.itprotoday.com/management-mobility/user-friendly-time-spans-windows-powershell

##### Parameters. ####
Param(
    [ValidateScript( {
            if (-Not ($_ | Test-Path) ) {
                throw "File or folder does not exist" 
            }
            if (-Not ($_ | Test-Path -PathType Leaf) ) {
                throw "The Path argument must be a file. Folder paths are not allowed."
            }
            return $true
        })]
    [System.IO.FileInfo]$alog
)

#### INIT:  Find and Grab Files - Someday Configure with ini or xml files####
$LogPath = $PSScriptRoot
$VideoCameraPath = "Z:\"
$VideoSlidePath = "Z:\"
$OutPutPath = "Z:\"
$WorkingPath = "C:\Temp"
$MicstoCapture = "Input 1 Mute", "Input 2 Mute", "Input 3 Mute", "Input 4 Mute", "Input 7 Mute", "Input 14 Mute"

[hashtable]$dafiles = @{}

## IF Path is not a parameter find latest log and continue, else use path (Still Working on that else)
if (-Not($alog) -or (-Not(Test-Path $alog))) {
    $TimeLog = Get-ChildItem -Path $LogPath -recurse -force -Filter *Slides.txt | Sort-Object LastWriteTime -Descending 
    $dafiles.Log = $TimeLog[0]
    $fileContents = Get-Content -path $dafiles.Log.FullName
    #$fileContents #= Get-Content $PSScriptRoot\Sampleoutput\2017-12-10_16-50-Slides.txt
}
else {
    $dafiles.Log = $alog
    $fileContents = Get-Content -path $dafiles.Log.FullName
}

$dafiles.Slides = Get-ChildItem -Path $VideoSlidePath\* -force -Include "*Slides.mp4" | Sort-Object LastWriteTime -Descending | ? {($_.CreationTime -gt ($dafiles.Log.CreationTime).AddMinutes(-15)) -and ($_.CreationTime  -lt ($dafiles.Log.CreationTime).AddMinutes(15))} | Select-Object -first 1
$dafiles.Camera = Get-ChildItem -Path $VideoCameraPath\* -force -Include "*Camera.mp4", "Untitled*.mp4" | Sort-Object LastWriteTime -Descending | ? {($_.CreationTime -gt ($dafiles.Log.CreationTime).AddMinutes(-30)) -and ($_.CreationTime  -lt ($dafiles.Log.CreationTime).AddMinutes(30))} | Select-Object -first 1

Write-Host "Log Found:", $dafiles.Log
Write-Host "Camera Found:", $dafiles.Camera
Write-Host "Slides Found:", $dafiles.Slides

if ($dafiles.Camera -contains "Untitled" ){Write-Host "Bad Camera Name, Exiting"; Exit 13}
if ($dafiles.Camera -eq $null ){Write-Host "No Camera Detected, Exiting"; Exit 12}
if ($dafiles.Slides -eq $null ){Write-Host "No Slides Detected, Exiting"; Exit 11}

#Subtract Slides Creation Time From Camera Creation Time and put them In
$daSyncDiff = [timespan]($dafiles.Slides.CreationTime - $dafiles.Camera.CreationTime)

## Making New Timspan without milliseconds the dumb way as I've not found the best way to round miliseconds in my google-fu
$dafiles.SyncDiff = New-TimeSpan -Hour $daSyncDiff.Hours -Minute $daSyncDiff.Minutes -Second $daSyncDiff.Seconds

Write-Host "The Sync Difference is", $dafiles.SyncDiff

#exit 0
## readup on:
#$PSDefaultParameterValues=@{ "Invoke-Command:ScriptBlock"={{Get-Process}} }

[hashtable]$global:temptime = @{}
## Main Function Processing Log ##
function Get-TimeStamps () {
    Param(
        # File Contents Handler
        [Parameter(Position = 0)]
        [Array]
        $afileContents,

        # Pattern to Search for
        [Parameter(Position = 1)]
        [String]
        $apattern,

        # File Contents Handler
        [Parameter(Position = 2)]
        [ValidateSet("RecordTime", "MicTime", "SlideTime", "SubSlideTime")]
        [String]
        $aScopeType,

        # File Contents Handler
        [Parameter(Position = 3)]
        [Array]
        $aScope
    )

    ### https://anandthearchitect.com/2014/03/18/powershell-how-to-return-multiple-values-from-a-function/
    $result = @()
    #### FOR LOOP Starts Here ####
    $afileContents | Select-String -pattern $apattern -Context 5 | ForEach-Object {
        #Create an hashtable object for returns
        [hashtable]$Return = @{}

        #standard Data in Object
        $Return.Line = $_.LineNumber
        $Return.ContextData = $_.context.precontext + $_.context.postcontext
        $Return.MatchedData = $_.Line.Trim()
        $Return.TimeStamp = $_.context.precontext | Select-String -pattern "([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\s([0-1]?[0-9]|2?[0-3]):([0-5]\d):([0-5]\d))" | Select-Object -Last 1 | % { $_.Matches } | % { $_.Value }
        if ($Return.TimeStamp -eq $null) {$Return.TimeStamp = $_.context.postcontext | Select-String -pattern "([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\s([0-1]?[0-9]|2?[0-3]):([0-5]\d):([0-5]\d))" | Select-Object -First 1 | % { $_.Matches } | % { $_.Value } }
        if ($aScopeType -eq "RecordTime") {
            if ($_.Line.Trim() -like "*RecordingStarting*") { $Return.State = "Start" } else { $Return.State = "Stop" }
            $result += $Return
        }
        ## Slides start appearing timecodes, from OBS records, need to add end timecodes, somehow...
        if ($aScopeType -eq "SlideTime" -And $aScope -And $_.LineNumber -gt [int]$aScope[0] -And $_.LineNumber -lt [int]$aScope[1]) {
            [timespan]$Return.TimeCode = [datetime]($Return.TimeStamp) - [datetime]($global:recStart)
            # Write-host "TimeCode: " $Return.TimeCode
            $Return.RecTCode = $_.context.precontext | % {$_.split('"')[3]}
            # Write-host "RECTimeCode: " $Return.RecTCode
            $result += $Return
        }
        if ( $aScopeType -eq "SubSlideTime" -And $aScope -And $_.LineNumber -gt $aScope[0] -And $_.LineNumber -lt $aScope[-1] ) {
            $result += $Return 
        }
        ## Parse Q-SYS data for microphone "hot" events()within recorded time, 
        ## build other hashes from within each mic's hot period into a heirachy of events.
        if ( $aScopeType -eq "MicTime" -And $aScope -And $_.LineNumber -gt $aScope[0] -And $_.LineNumber -lt $aScope[-1] ) {
            $Return.MicName = $_.Line | % {$_.split('"')[1]}
            $Return.TimeCode = [datetime]($Return.TimeStamp) - [datetime]($global:recStart)
            if ($_.Line.Trim() -like "*unmuted*") { 
                $Return.State = "Start"
                $global:temptime.Add($Return.MicName, $Return)
            } 
            else {
                $Return.State = "Stop"
                $Return.StartHash = $global:temptime[$Return.MicName]
                if($Return.StartHash.TimeCode -ne $null) {
                    $Return.StartTCode = $Return.StartHash.TimeCode
                    $Return.Duration = [timespan]$Return.TimeCode - [timespan]$Return.StartTCode
                }
                $global:temptime.Remove($Return.MicName)

                ## Go Fetch Slide Display Times from OBS Data, add as hash Slidehash on each Return Hash for each mic
                $pattern = "SwitchScenes"
                $MicScope = @($Return.StartHash.Line, $Return.Line)
                $Return.SlideHash = Get-TimeStamps  $fileContents  $pattern "SlideTime" $MicScope
                $result += $Return
            }
        } 
        else {
            $MicName = $_.Line | % {$_.split('"')[1]}
            if ($_.Line.Trim() -like "*unmuted*") {
                $aline = [int]$aScope[0]
                $global:temptime.Add($MicName, [hashtable]@{TimeCode = [timespan]"00:00:00"; "Line" = "$aline"})
            }
            else {
                $global:temptime.Remove($MicName)
            }
        }
    }
    return $result
}

$pattern = "RecordingStarting|RecordingStopping"
$StartStoplines = Get-TimeStamps  $fileContents  $pattern "RecordTime"


$RecordingScope = @($StartStoplines[0].Line, $StartStoplines[1].Line)
$global:recStart = $StartStoplines[0].TimeStamp

#$global:recStart
#$RecordingScope

#Mic Time(s)
$pattern = "Input .* Mute"
$StartStopMic = Get-TimeStamps  $fileContents  $pattern "MicTime" $RecordingScope

Write-Host ""
#Write-Host "Data:"
#$StartStopMic
$StartStopMic | Export-Clixml -path C:\Temp\test.xml

#$global:temptime
function Create-Runbooks () {
    Param(
        # Mics To Create RunBooks For
        [Parameter(Position = 0)]
        [Array]
        $EditPatterns
    )
    #### FOR LOOP Starts Here ####
    $EditPatterns | ForEach-Object {
        Write-Host " Mic Pattern=", $_
        [System.Collections.ArrayList]$BatchFileContent = "@echo off", "REM Batch File For Processing Cuts", "echo testing batch File", "SET PATH=%PATH%;C:\Program Files (x86)\VideoLAN\VLC\", "SET vlcCommand=vlc.exe  --video-x=-1288 --video-y=86 --width=300 --height=300 --fullscreen --no-video-title-show --no-embedded-video --no-qt-fs-controller --one-instance --playlist-enqueue", "START %vlcCommand% Z:\Progress.mp4"
        $MicPattern = $_
        [timespan]$VidDiff = $dafiles.SyncDiff
        $StartStopMic | ForEach-Object {$counter = 0} {
            #Write-Host " Mic=", $_.MicName, "is Equal", $MicPattern
            if ($_.MicName -eq $MicPattern) {
                if ($VidDiff -ne "00:00:00" -OR $VidDiff -ne "") {
                    [timespan]$MovieStartTCode = [timespan]$_.StartTCode - [timespan]$VidDiff
                    [timespan]$SlidesStartTCode = [timespan]$_.StartTCode 
                }
                else {
                    [timespan]$MovieStartTCode = ($_.StartTCode)
                    [timespan]$SlidesStartTCode = ([timespan]$_.StartTCode)
                }
                [timespan]$DurTCode = ($_.Duration).tostring() 
                [timespan]$EndTCode = ($_.TimeCode).tostring()
                Write-Host " Start Time: ", $MovieStartTCode.ToString()
                Write-Host " End Time: ", $EndTCode.ToString()
                Write-Host " Duration: ", $DurTCode.ToString()
                $MicName = ($_.MicName).tostring().Replace(" ", "").Replace("Mute", "")
                #Write-Host $MicName, $MovieStartTCode, $DurTCode, " From:", $_.StartTCode $_.Duration

                #Old, Simple [string]$ffplayexestring = "ffplay.exe", "-autoexit -ss", $MovieStartTCode, "-t", $DurTCode, "-i", $dafiles.Camera
                [string]$ffplayexestring = @"
ffmpeg -ss $MovieStartTCode -t 00:00:30 -i $($dafiles.Camera.tostring()) -ss $SlidesStartTCode -t 00:00:30 -i $($dafiles.Slides.tostring()) -filter_complex "[1]crop=in_w-70:in_h-120:35:60,scale=iw/2:-1,format=yuva420p,colorchannelmixer=aa=0.7[low3]; [vid][low3] overlay=(main_w/2)-(overlay_w/2):main_h-(overlay_h*0.90) [out]" -map "[out]" -map 0:a -c:a copy -f avi - | ffplay -autoexit -window_title "$ffmpegOutFileName-$counter Preview" - >> $ffmpegOutFileName-$counter.bat
"@
                [string]$askuserstring = @"
SET /p MovieCut=Do you want this Cut? (y/n):
IF "%MovieCut%" == "n" (goto end$Counter)
SET /p MovieStart=Start ($MovieStartTCode):
IF "%MovieStart%" == "" (SET MovieStart=$MovieStartTCode)
SET /p SlidesStart=Start ($SlidesStartTCode a Time Diff of $($VidDiff.tostring())):
IF "%SlidesStart%" == "" (SET SlidesStart=$SlidesStartTCode)
SET /p MovieDur=Duration ($DurTCode):
IF "%MovieDur%" == "" (SET MovieDur=$DurTCode)
SET logo="Z:\CoF-logo.png"
SET vlcCommand=vlc.exe  --video-x=-1288 --video-y=86 --width=300 --height=300 --fullscreen --no-video-title-show --no-embedded-video --no-qt-fs-controller --one-instance --playlist-enqueue
"@
                [string]$ffmpegOutFileName = (($dafiles.Camera).tostring().Replace("Camera.mp4", "-")+($MicPattern).tostring().Replace(" ", "").Replace("Mute", ""))
                ##Simple[string]$ffmpegexestring = "START ffmpeg.exe", "-ss", "%MovieStart%", "-t", "%MovieDur%", "-i", $dafiles.Camera, "{0}-{1}.mp4" -f $ffmpegOutFileName, $counter
                [string]$ffmpegexestring = @"
echo timeout /t 120 >>$ffmpegOutFileName-$counter.bat
echo (ffmpeg.exe -y -ss %SlidesStart% -t %MovieDur% -i "$($dafiles.Slides)" -i %logo% -ss 00:00:00 -c:v libx264 -pix_fmt yuv420p -preset faster -r 30 -g 60 -b:v 4500k -an -movflags +faststart "$ffmpegOutFileName-$counter-Slides.mp4")>>$ffmpegOutFileName-$counter.bat
echo (ffmpeg.exe -y -ss %MovieStart% -t %MovieDur% -i "$($dafiles.Camera)" -i %logo% -ss 00:00:00 -c:v libx264 -pix_fmt yuv420p -preset faster -r 30 -g 60 -b:v 4500k -c:a aac -strict -2 -filter_complex "[1]scale=iw/2:-1[pip]; [0:a]compand=.3|.3:1|1:-90/-60|-60/-40|-40/-30|-20/-20:6:0:-90:0.2[audio];[vid][pip] overlay=main_w-overlay_w-10:main_h-overlay_h-10[out]" -map "[out]" -map "[audio]" -movflags +faststart "$ffmpegOutFileName-$counter-Camera.mp4")>>$ffmpegOutFileName-$counter.bat
echo START %vlcCommand% "$ffmpegOutFileName-$counter-Camera.mp4" >> $ffmpegOutFileName-$counter.bat
echo (ffmpeg.exe -y -i "$ffmpegOutFileName-$counter-Camera.mp4" -i "$ffmpegOutFileName-$counter-Slides.mp4" -filter_complex "[0:v]setpts=PTS-STARTPTS, pad=iw*2:ih[bg];[1:v]setpts=PTS-STARTPTS[fg]; [bg][fg]overlay=w" -map 0:a -c:a copy "$ffmpegOutFileName-$counter-Both.mp4") >> $ffmpegOutFileName-$counter.bat
echo (ffmpeg.exe -y -i "$ffmpegOutFileName-$counter-Camera.mp4" -i "$ffmpegOutFileName-$counter-Slides.mp4" -filter_complex "[1]crop=in_w-70:in_h-120:35:60,scale=iw/2:-1,format=yuva420p,colorchannelmixer=aa=0.7[low3]; [vid][low3] overlay=(main_w/2)-(overlay_w/2):main_h-(overlay_h*0.90)[out]" -map "[out]" -map 0:a -c:a copy "$ffmpegOutFileName-$counter-ovl.mp4") >> $ffmpegOutFileName-$counter.bat
echo START %vlcCommand% "$ffmpegOutFileName-$counter-ovl.mp4" >> $ffmpegOutFileName-$counter.bat
echo (exit) >> $ffmpegOutFileName-$counter.bat
  START $ffmpegOutFileName-$counter.bat                  
"@
                [string]$clearvarstring = "SET MovieStart=& SET MovieDur=& SET SlidesStart="
                [string]$endstring = ":end$Counter"
                #Write-Host $MicName, "Executing: ", $ffmpegexestring
                if($DurTCode.TotalSeconds -gt 15){
                    $BatchFileContent.add($ffplayexestring)
                    $BatchFileContent.add($askuserstring)
                    $BatchFileContent.add($ffmpegexestring)
                    $BatchFileContent.add($clearvarstring)
                    $BatchFileContent.add($endstring)
                }
                Else{Write-Host "Cut is too Short. Ignoring" }
            } 
            $counter++ > $null
        }
        [string]$OutFileName = (($dafiles.Camera).tostring().Replace(".mp4", "-")+($MicPattern).tostring().Replace(" ", "").Replace("Mute", "")+".bat")
        Write-Host $MicPattern
        Write-Host $OutFileName
        $BatchFileContent | Out-File -Encoding ascii -FilePath $OutFileName > $null
    }
}


Create-Runbooks -EditPatterns $MicstoCapture
