#### Powershell Bad Log Parsing.
## Using https://foxdeploy.com/2015/01/05/walkthrough-parsing-log-or-console-output-with-powershell/
### Look into http://www.videoproductionslondon.com/blog/edl-to-html-with-thumbnails
### Look into http://www.itprotoday.com/management-mobility/user-friendly-time-spans-windows-powershell

# Log To Parse
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

if (-Not($alog) -or (-Not(Test-Path $alog))) {
    $TimeLog = Get-ChildItem -Path $PSScriptRoot -recurse -force -Filter *Slides.txt | sort LastWriteTime -Descending 
    #| ? {$_.CreationTime -gt (Get-Date).AddHours(-3)}
    $dafile = ($TimeLog[0].FullName).tostring() | Resolve-Path
    $dafile.Path
    $fileContents = Get-Content -path $dafile.Path
    #$fileContents #= Get-Content $PSScriptRoot\Sampleoutput\2017-12-10_16-50-Slides.txt
}
else {Write-Host $alog; exit 1}

## readup on:
#$PSDefaultParameterValues=@{ "Invoke-Command:ScriptBlock"={{Get-Process}} }

[hashtable]$global:temptime = @{}

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
    $afileContents | Select-String -pattern $apattern -Context 5 | ForEach-Object {
        #Create an hashtable variable 
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
                $Return.StartTCode = $Return.StartHash.TimeCode
                $Return.Duration = $Return.TimeCode - $Return.StartTCode
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
                $global:temptime.Add($MicName, [hashtable]@{TimeCode = "00:00:00"; "Line" = "$aline"})
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
Write-Host "Mic1 Lines:"
#$StartStopMic
$StartStopMic | Export-Clixml -path C:\Temp\test.xml

#$global:temptime

[System.Collections.ArrayList]$BatchFileContent = "REM Batch File For Testing", "echo testing batch"
$MicPattern = "Input 2 Mute"
[timespan]$VidDiff = "00:00:00"
$StartStopMic | ForEach-Object {$counter = 0}{  
    if ($_.MicName -eq $MicPattern) {
        if ($VidDiff -ne "00:00:00" -OR $VidDiff -ne "") {
        [timespan]$StartTCode = ([timespan]$_.StartTCode + [timespan]$VidDiff).tostring()} else {[timespan]$StartTCode = ($_.StartTCode).tostring()}
        [timespan]$DurTCode = ($_.Duration).tostring() 
        $MicName = ($_.MicName).tostring().Replace(" ", "").Replace("Mute", "")
        Write-Host $MicName, $StartTCode, $DurTCode, " From:", $_.StartTCode $_.Duration

        [string]$ffplayexestring = "ffplay.exe", "-autoexit -ss", $StartTCode, "-t", $DurTCode, "-i 2017-12-10-pm-SoundsofSouthwestSingers-Camera.mp4"
        [string]$askuserstring = @"
        SET /p MovieCut=Do you want this Cut? (y/n):
        IF "%MovieCut%" == "n" (goto end$Counter)
        SET /p MovieStart=Start ($StartTCode):
        IF "%MovieStart%" == "" (SET MovieStart=$StartTCode)
        SET /p MovieDur=Duration ($DurTCode):
        IF "%MovieDur%" == "" (SET MovieDur=$DurTCode)
"@
        [string]$ffmpegexestring = "START ffmpeg.exe", "-ss", "%MovieStart%", "-t", "%MovieDur%", "-i 2017-12-10-pm-SoundsofSouthwestSingers-Camera.mp4", "{0}-{1}.mp4" -f $MicName, $counter
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


#Mic1 Calculate Recorded time
# Write-host "Mic1 Calculate Recorded time"

# Write-host ($StartStopMic[0]) - ($StartStopLines[0])
# $mic1start = [datetime]($StartStopMic[0]) - [datetime]($StartStopLines[0])
# $mic1start

# Write-host ($StartStopMic[3]) - ($StartStopLines[0])
# $mic1end = [datetime]($StartStopMic[3]) - [datetime]($StartStopLines[0])
# $mic1end


# Write-host $mic1end - $mic1start
# $mic1end - $mic1start

# $StartStop | Format-Table

# $StartStop.GetType()

# $StartStop[0]

# $StartStop[1]

# $StartStop.Length

# $pattern="Evt00001"
# [array]$ExtronEvents = Get-TimeStamps  -afileContents  $fileContents -apattern $pattern -aScope $StartStop -aScopeType "SubSlideTime"

# $pattern="\{|\}"
# [array]$SlideEvents = Get-TimeStamps  -afileContents  $fileContents -apattern $pattern -aScope $StartStop -aScopeType "SlideTime"

# #$SlideEvents
