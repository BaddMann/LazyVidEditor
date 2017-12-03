#Powershell to parse log files

cd C:\Users\glencroftplay\Documents\GitHub\LazyVidEditor

Get-Content ".\*txt" |  Select-String "Input 1 Mute" -Context 0,1



## Commands To Work With:
cd Z:\


#Get The Log File Created Last $ hours.
$TimeCodes = Get-ChildItem -Path C:\Users\glencroftplay\Documents\GitHub\LazyVidEditor -force -Filter *Slides.txt | sort LastWriteTime -Descending | ? {$_.CreationTime -gt (Get-Date).AddHours(-3)}
$TimeCodes[0]

$fileContent = Get-Content $TimeCodes[0].FullName -Raw

$fileContent | Select-String '[0-9]{4,4}-[0-9]{2,2}-[0-9]{2,2} [0-9]{2,2}:[0-9]{2,2}:[0-9]{2,2}.*.*' -AllMatches |Foreach {$_.Matches} | Foreach {$_.Value}

$fileContent | Select-String '.*\"rec-timecode\".*\}' -AllMatches | ForEach-Object {$_.Matches} | ForEach-Object {$_.Value}  

$fileContent | Select-String '\n{.*\n}' -AllMatches | ForEach-Object {$_.Matches} | ForEach-Object {$_.Value}

$fileContent.Count

$fileContent.Length




$fileContent | Select-String 'cv.*' -AllMatches -Context 1,0 | Foreach {$_.Matches} | Foreach {$_.Value}

#Get The Mp4 File Created Called Slides withing the Last $ hours.
$Slides = Get-ChildItem -Path Z:\ -force -Filter *Slides.mp4 | Sort-Object LastWriteTime -Descending | ? {$_.CreationTime -gt (Get-Date).AddHours(-3)}

#Get The Mp4 File Created Called Camera withing the Last $ hours.
$Camera = Get-ChildItem -Path Z:\ -force -Filter *Camera.mp4 | sort-object LastWriteTime -Descending | ? {$_.CreationTime -gt (Get-Date).AddHours(-3)}

#Subtract Slides Creation Time From Camera Creation Time and put them In $Result
$Result = $Slides[0].CreationTime - $Camera[0].CreationTime

#See ReSult Deffierence
$Result

#See Result Defference in Milliseconds...
$Result.Milliseconds

