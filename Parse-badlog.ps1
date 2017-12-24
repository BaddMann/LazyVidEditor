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
else {Write-Host "Set Path:", $alog; exit 1}

$dafiles.Slides = Get-ChildItem -Path $VideoSlidePath -force -Filter *Slides.mp4 | Sort-Object LastWriteTime -Descending | ? {$_.CreationTime -gt ($dafiles.Log.CreationTime).AddHours(-1)}
$dafiles.Camera = Get-ChildItem -Path $VideoCameraPath\* -force -Include "*Camera.mp4", "Untitled*.mp4" | Sort-Object LastWriteTime -Descending | ? {$_.CreationTime -gt ($dafiles.Log.CreationTime).AddHours(-1)}

if ($dafiles.Camera -like "Untitled*.mp4" ){Write-Host "Bad Camera Name, Exiting"; Exit 13}
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
        [System.Collections.ArrayList]$BatchFileContent = "@echo off", "REM Batch File For Processing Cuts", "echo testing batch File"
        $MicPattern = $_
        [timespan]$VidDiff = $dafiles.SyncDiff
        $StartStopMic | ForEach-Object {$counter = 0} {
            Write-Host " Mic=", $_.MicName, "is Equal", $MicPattern
            if ($_.MicName -eq $MicPattern) {
                if ($VidDiff -ne "00:00:00" -OR $VidDiff -ne "") {
                    [timespan]$StartTCode = ([timespan]$_.StartTCode + [timespan]$VidDiff).tostring()
                }
                else {[timespan]$StartTCode = ($_.StartTCode).tostring()}
                [timespan]$DurTCode = ($_.Duration).tostring() 
                $MicName = ($_.MicName).tostring().Replace(" ", "").Replace("Mute", "")
                Write-Host $MicName, $StartTCode, $DurTCode, " From:", $_.StartTCode $_.Duration

                [string]$ffplayexestring = "ffplay.exe", "-autoexit -ss", $StartTCode, "-t", $DurTCode, "-i", $dafiles.Camera
                [string]$askuserstring = @"
SET /p MovieCut=Do you want this Cut? (y/n):
IF "%MovieCut%" == "n" (goto end$Counter)
SET /p MovieStart=Start ($StartTCode):
IF "%MovieStart%" == "" (SET MovieStart=$StartTCode)
SET /p MovieDur=Duration ($DurTCode):
IF "%MovieDur%" == "" (SET MovieDur=$DurTCode)
"@
                [string]$ffmpegexestring = "START ffmpeg.exe", "-ss", "%MovieStart%", "-t", "%MovieDur%", "-i", $dafiles.Camera, "{0}-{1}.mp4" -f $MicName, $counter
                [string]$clearvarstring = "SET MovieStart=& SET MovieDur="
                [string]$endstring = ":end$Counter"
                Write-Host $MicName, "Executing: ", $ffmpegexestring
                $BatchFileContent.add($ffplayexestring)
                $BatchFileContent.add($askuserstring)
                $BatchFileContent.add($ffmpegexestring)
                $BatchFileContent.add($clearvarstring)
                $BatchFileContent.add($endstring)
            } 
            $counter++
        }
        $BatchFileContent | Out-File -Encoding ascii -FilePath "Z:\$MicPattern.bat" > $null
    }
}


Create-Runbooks -EditPatterns $MicstoCapture
