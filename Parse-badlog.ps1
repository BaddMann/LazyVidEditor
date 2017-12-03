#### Powershell Bad Log Parsing.
## Using https://foxdeploy.com/2015/01/05/walkthrough-parsing-log-or-console-output-with-powershell/
### More Examples:

$fileContents = Get-Content C:\Users\glencroftplay\Documents\GitHub\LazyVidEditor\Sampleoutput\2017-12-03_09-41-Slides.txt

##$filecontents = $filecontents.Split("`n")

## $fileContents.GetType()

function Get-TimeStamps () {
    Param(
    # File Contents Handler
    [Parameter(Position=0)]
    [Array]
    $afileContents,

     # Pattern to Search for
    [Parameter(Position=1)]
    [String]
    $apattern,

    # File Contents Handler
    [Parameter(Position=2)]
    [ValidateSet("RecordTime","MicTime","SlideTime","SubSlideTime")]
    [String]
    $aScopeType,

    # File Contents Handler
    [Parameter(Position=3)]
    [Array]
    $aScope
    )

    $result = @()
    $afileContents | Select-String -pattern $apattern -Context 2 | ForEach-Object {
        if ($aScopeType -eq "RecordTime"){
            ###$Datetime = $afileContents | Select-String -pattern  Somehow Retrieve Datetime before and After line.....
            $Datecode = $_.context.precontext + $_.context.postcontext | Select-String -pattern "([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\s([0-1]?[0-9]|2?[0-3]):([0-5]\d):([0-5]\d))" | Select-Object -First 1 | % { $_.Matches } | % { $_.Value }
            ##($_.context.postcontext | Select-String -pattern "(?:rec-timecode)").ToString().split(":")
            $result += $Datecode, $_.LineNumber, $_.Line.Trim()
        }
        if ($aScopeType -eq "SlideTime"){
            $result += $_.LineNumber
            #Write-Host $_.LineNumber ":" $_.Line.Trim()
        }
        if ( $aScopeType -eq "SubSlideTime" -And $aScope -And $_.LineNumber -gt $aScope[0] -And $_.LineNumber -lt $aScope[-1] ) {
            $result += $_.LineNumber
            #Write-Host $_.LineNumber ":" $_.Line.Trim()
        }
        if ( $aScopeType -eq "MicTime" -And $aScope -And $_.LineNumber -gt $aScope[0] -And $_.LineNumber -lt $aScope[-1] ) {
            $Datecode = $_.context.precontext + $_.context.postcontext | Select-String -pattern "([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\s([0-1]?[0-9]|2?[0-3]):([0-5]\d):([0-5]\d))" | Select-Object -First 1 | % { $_.Matches } | % { $_.Value }
            $result += $Datecode, $_.LineNumber, $_.Line.Trim()
            #Write-Host $_.LineNumber ":" $_.Line.Trim()
        }
    }
    return $result
}

$pattern="RecordingStarting|RecordingStopping"
$StartStoplines = Get-TimeStamps  $fileContents  $pattern "RecordTime" $

$StartStoplines

$RecordingScope= @($StartStoplines[1],$StartStoplines[4])

#Lav1 Time(s)
$pattern="Input 1 Mute"
$StartStopMic = Get-TimeStamps  $fileContents  $pattern "MicTime" $RecordingScope

Write-Host "Mic1 Lines:"
$StartStopMic


#Mic1 Calculate Recorded time
Write-host "Mic1 Calculate Recorded time"

Write-host ($StartStopMic[0]) - ($StartStopLines[0])
$mic1start = [datetime]($StartStopMic[0]) - [datetime]($StartStopLines[0])
$mic1start

Write-host ($StartStopMic[3]) - ($StartStopLines[0])
$mic1end = [datetime]($StartStopMic[3]) - [datetime]($StartStopLines[0])
$mic1end


Write-host $mic1end - $mic1start
$mic1end - $mic1start

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
