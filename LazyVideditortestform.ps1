#region function fillDetailedListView
function fillDetailedListView
{
    <#
        .Synopsis
            Creates columns if they are missing and adds a row of data
        .Description
            This function creates add a row based from a string array. It also optionally clear columns and 
            adds missing columns
        .Parameter ListView
            A reference to a listview control
        .Parameter CleanUp
            An optional flag to clear columns and data before adding a new row
        .Parameter ColumnName
            A string array used as a list of header names
        .Parameter Data
            A string array used as a list of data to be added to a new row
        .Parameter Color
            A flag of the [System.Drawing.SystemColors]::Window type to apply to the newly created row
        .Example
            fillListView ([ref]$lv) $false (,'Name') (,$key) $null; 
        .Notes
            Author: Alexander Petrovskiy
    #>
    param(
        [ref]$ListView,
        [bool]$CleanUp = $false,
        [string[]]$ColumnName,
        [string[]]$Data,
        $Color,
        [int]$ImageIndex = $null,
        [string]$NodeKey = ''
    )
    if ($cleanUp) #if clean-up is required
    {
        ($ListView.Value).Columns.Clear();
    }
    for ($i = 0; $i -lt $ColumnName.Length; $i++)
    {#check whether the Current column exists or not
        if ( -not ([System.Windows.Forms.ListView] `
            ($ListView.Value)).Columns[$ColumnName[$i]])
        {#add only if it's a new one
            ($ListView.Value).Columns.AddRange(
                (($header = New-Object System.Windows.Forms.ColumnHeader) `
                    | %{$header.Text = $ColumnName[$i]; 
                        $header.Name = $ColumnName[$i]; 
                        $header;}));
        }
    }
    if ($Color -eq $null -or `
        $Color.GetType().ToString() -ne 'System.Drawing.SystemColors')
    {#input test of the $Color variable
        $Color = [System.Drawing.SystemColors]::Window;
    }
    #adding items aka rows (an item is a single element of a row,
    #a place where a row and a column are intercrossed
    $listViewItem1 = (($listViewItem = New-Object "System.Windows.Forms.ListViewItem") `
        | %{$listViewItem.Text = $Data[0]; 
            if ($Color -ne [System.Drawing.SystemColors]::Window)
            {#set $Color to all items in the row
                $listViewItem.BackColor = $Color;
                $listViewItem.UseItemStyleForSubItems = $true;
            }
            if ($ImageIndex -ne $null)
            {#if you have an ImageList control in your form
                $listViewItem.ImageIndex = $ImageIndex + 1;
            }
            if ($NodeKey -ne $null -and $NodeKey.Length -gt 0)
            {
                $listViewItem.Tag = $NodeKey;
            }
        #more columns
        for ($i = 1; $i -lt $Data.Length; $i++)
        {#adding data to the row items
            $listViewItem.SubItems.Add((([System.Windows.Forms.ListViewItem`+ListViewSubItem]$subItem = `
                New-Object System.Windows.Forms.ListViewItem`+ListViewSubItem) `
                | %{$subItem.Text = $Data[$i]; 
                    $subItem;}));
        }
        $listViewItem;}
        )
    ($ListView.Value).Items.Add($listViewItem);
    #setting AutoREsize property
    if ($Data -ne $null -and $Data.Length -gt 1)
    {
        ($ListView.Value).AutoResizeColumns([System.Windows.Forms.ColumnHeaderAutoResizeStyle]::ColumnContent);
    }
    else
    {
        ($ListView.Value).AutoResizeColumns([System.Windows.Forms.ColumnHeaderAutoResizeStyle]::HeaderSize);
    }
}
#endregion function fillDetailedListView


#region GUI Design
Add-Type -AssemblyName System.Windows.Forms

$LazyVidEditorGUI = New-Object system.Windows.Forms.Form
$LazyVidEditorGUI.Text = "Lazy Vid Editor"
$LazyVidEditorGUI.BackColor = "#ffffff"
$LazyVidEditorGUI.TopMost = $true
$LazyVidEditorGUI.Width = 490
$LazyVidEditorGUI.Height = 425

$txtStartRecTime = New-Object system.windows.Forms.TextBox
$txtStartRecTime.Text = "00:00:00"
$txtStartRecTime.Width = 72
$txtStartRecTime.Height = 20
$txtStartRecTime.location = new-object system.drawing.point(106,30)
$txtStartRecTime.Font = "Microsoft Sans Serif,10"
$LazyVidEditorGUI.controls.Add($txtStartRecTime)

$txtEndRecTime = New-Object system.windows.Forms.TextBox
$txtEndRecTime.Text = "00:00:00"
$txtEndRecTime.Width = 72
$txtEndRecTime.Height = 20
$txtEndRecTime.location = new-object system.drawing.point(335,30)
$txtEndRecTime.Font = "Microsoft Sans Serif,10"
$LazyVidEditorGUI.controls.Add($txtEndRecTime)

## The list Box Contains all Unique events Recognized in the BadLog
$lstEvents = New-Object system.windows.Forms.ComboBox
$lstEvents.Text = "All Events"
$lstEvents.AutoSize
$lstEvents.Width = 100
$lstEvents.Height = 50
$lstEvents.location = new-object system.drawing.point(57,75)
$LazyVidEditorGUI.controls.Add($lstEvents)


$lstEventCodes = New-Object system.windows.Forms.ListView
$lstEventCodes.Text = "Events listView"
$lstEventCodes.View = 'Details'
$lstEventCodes.GridLines = 'True'
$lstEventCodes.FullRowSelect = 'True'
#$lstEventCodes.CheckBoxes = 'True'
$lstEventCodes.AutoSize = 'True'
$lstEventCodes.Width = 198
$lstEventCodes.Height = 235
$lstEventCodes.location = new-object system.drawing.point(10,135)
$lstEventCodes.AutoResizeColumn
$LazyVidEditorGUI.controls.Add($lstEventCodes)


$lstCuts = New-Object system.windows.Forms.ListView
$lstCuts.Text = "listView"
$lstCuts.View = 'Details'
$lstCuts.GridLines = 'True'
$lstCuts.FullRowSelect = 'True'
$lstCuts.Width = 198
$lstCuts.Height = 195
$lstCuts.location = new-object system.drawing.point(268,135)
$lstCuts.AutoSize = 'True'
$lstCuts.AutoResizeColumn
$LazyVidEditorGUI.controls.Add($lstCuts)


$btnStartStamp = New-Object system.windows.Forms.Button
$btnStartStamp.Text = "Start >>"
$btnStartStamp.Width = 60
$btnStartStamp.Height = 40
$btnStartStamp.Add_Click({
#add here code triggered by the event
})
$btnStartStamp.location = new-object system.drawing.point(208,163)
$btnStartStamp.Font = "Microsoft Sans Serif,10"
$LazyVidEditorGUI.controls.Add($btnStartStamp)


$btnStopStamp = New-Object system.windows.Forms.Button
$btnStopStamp.Text = "Stop >>"
$btnStopStamp.Width = 60
$btnStopStamp.Height = 40
$btnStopStamp.Add_Click({
#add here code triggered by the event
})
$btnStopStamp.location = new-object system.drawing.point(208,201)
$btnStopStamp.Font = "Microsoft Sans Serif,10"
$LazyVidEditorGUI.controls.Add($btnStopStamp)


$btnBothStamps = New-Object system.windows.Forms.Button
$btnBothStamps.Text = "Both >>"
$btnBothStamps.Width = 60
$btnBothStamps.Height = 40
$btnBothStamps.Add_Click({
#add here code triggered by the event
})
$btnBothStamps.location = new-object system.drawing.point(208,240)
$btnBothStamps.Font = "Microsoft Sans Serif,10"
$LazyVidEditorGUI.controls.Add($btnBothStamps)


$btnSubmit = New-Object system.windows.Forms.Button
$btnSubmit.Text = "Cut Clip"
$btnSubmit.Width = 90
$btnSubmit.Height = 30
$btnSubmit.location = new-object system.drawing.point(268,343)
$btnSubmit.Font = "Microsoft Sans Serif,10"
$LazyVidEditorGUI.controls.Add($btnSubmit)

$btnSubmitAll = New-Object system.windows.Forms.Button
$btnSubmitAll.Text = "Cut All Clips"
$btnSubmitAll.Width = 90
$btnSubmitAll.Height = 30
$btnSubmitAll.location = new-object system.drawing.point(376,343)
$btnSubmitAll.Font = "Microsoft Sans Serif,10"
$LazyVidEditorGUI.controls.Add($btnSubmitAll)


## All Labels Go Here....

$lblCutTimeCodes = New-Object system.windows.Forms.Label
$lblCutTimeCodes.Text = "Time Codes to Cut"
$lblCutTimeCodes.AutoSize = $true
$lblCutTimeCodes.Width = 25
$lblCutTimeCodes.Height = 10
$lblCutTimeCodes.location = new-object system.drawing.point(268,119)
$lblCutTimeCodes.Font = "Microsoft Sans Serif,10"
$LazyVidEditorGUI.controls.Add($lblCutTimeCodes)

$lblStartRecording = New-Object system.windows.Forms.Label
$lblStartRecording.Text = "Start TimeCode"
$lblStartRecording.AutoSize = $true
$lblStartRecording.Width = 25
$lblStartRecording.Height = 10
$lblStartRecording.location = new-object system.drawing.point(9,30)
$lblStartRecording.Font = "Microsoft Sans Serif,10"
$LazyVidEditorGUI.controls.Add($lblStartRecording)

$lblEndRecording = New-Object system.windows.Forms.Label
$lblEndRecording.Text = "End TimeCode"
$lblEndRecording.AutoSize = $true
$lblEndRecording.Width = 25
$lblEndRecording.Height = 10
$lblEndRecording.location = new-object system.drawing.point(240,30)
$lblEndRecording.Font = "Microsoft Sans Serif,10"
$LazyVidEditorGUI.controls.Add($lblEndRecording)

$lblTimeStamps = New-Object system.windows.Forms.Label
$lblTimeStamps.Text = "Time Codes for Selected Events"
$lblTimeStamps.AutoSize = $true
$lblTimeStamps.Width = 25
$lblTimeStamps.Height = 10
$lblTimeStamps.location = new-object system.drawing.point(9,119)
$lblTimeStamps.Font = "Microsoft Sans Serif,10"
$LazyVidEditorGUI.controls.Add($lblTimeStamps)

$lblEvents = New-Object system.windows.Forms.Label
$lblEvents.Text = "Events"
$lblEvents.AutoSize = $true
$lblEvents.Width = 25
$lblEvents.Height = 10
$lblEvents.location = new-object system.drawing.point(10,76)
$lblEvents.Font = "Microsoft Sans Serif,10"
$LazyVidEditorGUI.controls.Add($lblEvents)

#endregion

#region root code
# Pretty Icon... May go in Form Creation Region...
$Icon = [system.drawing.icon]::ExtractAssociatedIcon($PSHOME + "\powershell.exe")
$LazyVidEditorGUI.Icon = $Icon
$LazyVidEditorGUI.AutoSize = $True
$LazyVidEditorGUI.AutoSizeMode = "GrowAndShrink"
$LazyVidEditorGUI.SizeGripStyle = "Hide"
$LazyVidEditorGUI.StartPosition = "CenterScreen"

### Unique Event Friendly names from Array, Sorted by appearence in Recording.
$lstEvents.Items.Add('HeadSet')
$lstEvents.Items.Add('Handheld1')
$lstEvents.Items.Add('Handheld2')
$lstEvents.Items.Add('Lav 2')
$lstEvents.Items.Add('Lav 3')
$lstEvents.Items.Add('Piano')
$lstEvents.Items.Add('Organ')
$lstEvents.Items.Add('PlayPc')

## Columns for Events List, From Array
$lstEventCodes.Columns.Add('Start')
$lstEventCodes.Columns.Add('End')


## Events in Events List, From Array
$starttime01 = New-Object System.Windows.Forms.ListViewItem('00:00:00')
$starttime01.SubItems.Add('00:00:05')

$starttime02 = New-Object System.Windows.Forms.ListViewItem('01:00:00')
$starttime02.SubItems.Add('01:00:05')

$lstEventCodes.Items.AddRange(($starttime01, $starttime02))


## Columns for Cuts List, From Array
$lstCuts.Columns.Add('Start')
$lstCuts.Columns.Add('End')

## Show Dialog
[void]$LazyVidEditorGUI.ShowDialog()
$LazyVidEditorGUI.Dispose()

#endregion
