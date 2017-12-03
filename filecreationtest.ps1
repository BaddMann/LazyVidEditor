##Good Method of monitoring for changes, now make it a terminal or websocket.
## Source: https://social.technet.microsoft.com/Forums/scriptcenter/en-US/c75c7bbd-4e32-428a-b3dc-815d5c42fd36/powershell-check-folder-for-new-files?forum=ITCG

$folder = 'Z:\'
$filter = '*.mp4'                             # <-- set this according to your requirements
$destination = 'C:\Users\Glencroft\Documents\filecreation.csv'
$fsw = New-Object IO.FileSystemWatcher $folder, $filter -Property @{
 IncludeSubdirectories = $false              # <-- set this according to your requirements
 NotifyFilter = [IO.NotifyFilters]'FileName, LastWrite'
}
$onCreated = Register-ObjectEvent $fsw Created -SourceIdentifier FileCreated -Action {
 $path = $Event.SourceEventArgs.FullPath
 $name = $Event.SourceEventArgs.Name
 $changeType = $Event.SourceEventArgs.ChangeType
 $timeStamp = $Event.TimeGenerated
 Write-Host "The file '$name' was $changeType at $timeStamp"
 #Move-Item $path -Destination $destination -Force -Verbose # Force will overwrite files with same name
}


##Unregister-Event -SourceIdentifier FileCreated
