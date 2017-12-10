#### Powershell Bad Log Parsing.
## Using https://foxdeploy.com/2015/01/05/walkthrough-parsing-log-or-console-output-with-powershell/
### Look into http://www.videoproductionslondon.com/blog/edl-to-html-with-thumbnails
### 

$fileContents = Get-Content $PSScriptRoot\Sampleoutput\2017-11-19_09-49-Slides.txt

[hashtable]$global:temptime = @{}

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

    ### https://anandthearchitect.com/2014/03/18/powershell-how-to-return-multiple-values-from-a-function/
    $result = @()
    $afileContents | Select-String -pattern $apattern -Context 2 | ForEach-Object {
     #Create an hashtable variable 
     [hashtable]$Return = @{}

        #standard Data in Object
        $Return.Line = $_.LineNumber
        $Return.ContextData = $_.context.precontext + $_.context.postcontext
        $Return.MatchedData = $_.Line.Trim()
        $Return.TimeStamp = $_.context.precontext + $_.context.postcontext | Select-String -pattern "([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\s([0-1]?[0-9]|2?[0-3]):([0-5]\d):([0-5]\d))" | Select-Object -First 1 | % { $_.Matches } | % { $_.Value }
        if ($aScopeType -eq "RecordTime"){
            if ($_.Line.Trim() -like "*RecordingStarting*"){ $Return.State = "Start" } else{ $Return.State = "Stop" }
            $result += $Return
        }
        if ($aScopeType -eq "SlideTime"){
            $result += $Return
        }
        if ( $aScopeType -eq "SubSlideTime" -And $aScope -And $_.LineNumber -gt $aScope[0] -And $_.LineNumber -lt $aScope[-1] ) {
            $result += $Return
        }
        if ( $aScopeType -eq "MicTime" -And $aScope -And $_.LineNumber -gt $aScope[0] -And $_.LineNumber -lt $aScope[-1] ) {
            $Return.MicName = $_.Line | % {$_.split('"')[1]}
            $Return.TimeCode = [datetime]($Return.TimeStamp) - [datetime]($global:recStart)
            if ($_.Line.Trim() -like "*unmuted*"){ 
                $Return.State = "Start"
                $global:temptime.Add($Return.MicName,$Return)
            } 
            else{
                $Return.State = "Stop"
                $Return.StartHash = $global:temptime[$Return.MicName]
                $Return.StartTCode = $Return.StartHash.TimeCode
                $global:temptime.Remove($Return.MicName)
                $result += $Return
            }
        } 
        else{
            $MicName = $_.Line | % {$_.split('"')[1]}
            if ($_.Line.Trim() -like "*unmuted*"){
                 $global:temptime.Add($MicName,[hashtable]@{TimeCode="00:00:00"; "Line"="$aScope[0]"})
            } else{
                 $global:temptime.Remove($MicName)
            }
        }
    }
    return $result
}

$pattern="RecordingStarting|RecordingStopping"
$StartStoplines = Get-TimeStamps  $fileContents  $pattern "RecordTime" $


$RecordingScope= @($StartStoplines[0].Line,$StartStoplines[1].Line)
$global:recStart=$StartStoplines[0].TimeStamp

#$global:recStart
#$RecordingScope

#Mic Time(s)
$pattern="Input .* Mute"
$StartStopMic = Get-TimeStamps  $fileContents  $pattern "MicTime" $RecordingScope

  Write-Host ""
  Write-Host "Mic1 Lines:"
  $StartStopMic

  $global:temptime


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
