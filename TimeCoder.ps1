<# This form was created using POSHGUI.com  a free online gui designer for PowerShell
.NAME
    TimeCoder
.DESCRIPTION
    Calculate Time Spans for FFmpeg cutting
Will always calculate missing value.
.EXAMPLE
    timecoder.ps1 -start "00:01:05" -end "00:04:40"
.INPUTS
    -Start -End -Duration
.OUTPUTS
    Missing TimeCode
#>

Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.Application]::EnableVisualStyles()

#region begin GUI{ 

$FfrmMain                        = New-Object system.Windows.Forms.Form
$FfrmMain.ClientSize             = '400,544'
$FfrmMain.text                   = "Form"
$FfrmMain.TopMost                = $false

$WinForm1                        = New-Object system.Windows.Forms.Form
$WinForm1.ClientSize             = '400,400'
$WinForm1.text                   = "Form"
$WinForm1.TopMost                = $false

$btn5plusstart                   = New-Object system.Windows.Forms.Button
$btn5plusstart.text              = "+5sec"
$btn5plusstart.width             = 60
$btn5plusstart.height            = 30
$btn5plusstart.location          = New-Object System.Drawing.Point(241,13)
$btn5plusstart.Font              = 'Microsoft Sans Serif,10'

$btn10plusstart                  = New-Object system.Windows.Forms.Button
$btn10plusstart.text             = "+10sec"
$btn10plusstart.width            = 60
$btn10plusstart.height           = 30
$btn10plusstart.location         = New-Object System.Drawing.Point(309,14)
$btn10plusstart.Font             = 'Microsoft Sans Serif,10'

$btn5minusstart                  = New-Object system.Windows.Forms.Button
$btn5minusstart.text             = "-5sec"
$btn5minusstart.width            = 60
$btn5minusstart.height           = 30
$btn5minusstart.location         = New-Object System.Drawing.Point(240,53)
$btn5minusstart.Font             = 'Microsoft Sans Serif,10'

$btn10minusstart                 = New-Object system.Windows.Forms.Button
$btn10minusstart.text            = "-10sec"
$btn10minusstart.width           = 60
$btn10minusstart.height          = 30
$btn10minusstart.location        = New-Object System.Drawing.Point(309,54)
$btn10minusstart.Font            = 'Microsoft Sans Serif,10'

$grpTimeCodeStart                = New-Object system.Windows.Forms.Groupbox
$grpTimeCodeStart.height         = 100
$grpTimeCodeStart.width          = 383
$grpTimeCodeStart.text           = "Start TimeCode"
$grpTimeCodeStart.location       = New-Object System.Drawing.Point(9,167)

$grpTimeCodeEnd                  = New-Object system.Windows.Forms.Groupbox
$grpTimeCodeEnd.height           = 100
$grpTimeCodeEnd.width            = 383
$grpTimeCodeEnd.text             = "End TimeCode"
$grpTimeCodeEnd.location         = New-Object System.Drawing.Point(9,280)

$btn5plusend                     = New-Object system.Windows.Forms.Button
$btn5plusend.text                = "+5sec"
$btn5plusend.width               = 60
$btn5plusend.height              = 30
$btn5plusend.location            = New-Object System.Drawing.Point(241,14)
$btn5plusend.Font                = 'Microsoft Sans Serif,10'

$btn10plusend                    = New-Object system.Windows.Forms.Button
$btn10plusend.text               = "+10sec"
$btn10plusend.width              = 60
$btn10plusend.height             = 30
$btn10plusend.location           = New-Object System.Drawing.Point(311,14)
$btn10plusend.Font               = 'Microsoft Sans Serif,10'

$btn10minusend                   = New-Object system.Windows.Forms.Button
$btn10minusend.text              = "-10sec"
$btn10minusend.width             = 60
$btn10minusend.height            = 30
$btn10minusend.location          = New-Object System.Drawing.Point(311,54)
$btn10minusend.Font              = 'Microsoft Sans Serif,10'

$btn5minusend                    = New-Object system.Windows.Forms.Button
$btn5minusend.text               = "-5sec"
$btn5minusend.width              = 60
$btn5minusend.height             = 30
$btn5minusend.location           = New-Object System.Drawing.Point(240,54)
$btn5minusend.Font               = 'Microsoft Sans Serif,10'

$grpMetaData                     = New-Object system.Windows.Forms.Groupbox
$grpMetaData.height              = 141
$grpMetaData.width               = 382
$grpMetaData.text                = "Meta Data"
$grpMetaData.location            = New-Object System.Drawing.Point(9,11)

$txtfilename                     = New-Object system.Windows.Forms.TextBox
$txtfilename.multiline           = $false
$txtfilename.width               = 359
$txtfilename.height              = 20
$txtfilename.location            = New-Object System.Drawing.Point(9,35)
$txtfilename.Font                = 'Microsoft Sans Serif,10'

$lblfilename                     = New-Object system.Windows.Forms.Label
$lblfilename.text                = "Filename"
$lblfilename.AutoSize            = $true
$lblfilename.width               = 25
$lblfilename.height              = 10
$lblfilename.location            = New-Object System.Drawing.Point(9,25)
$lblfilename.Font                = 'Microsoft Sans Serif,10'

$rdiGlencroft                    = New-Object system.Windows.Forms.RadioButton
$rdiGlencroft.text               = "Glencroft Logo"
$rdiGlencroft.AutoSize           = $true
$rdiGlencroft.width              = 104
$rdiGlencroft.height             = 20
$rdiGlencroft.location           = New-Object System.Drawing.Point(14,63)
$rdiGlencroft.Font               = 'Microsoft Sans Serif,10'

$rdiComofFaith                   = New-Object system.Windows.Forms.RadioButton
$rdiComofFaith.text              = "Community Of Faith Logo"
$rdiComofFaith.AutoSize          = $true
$rdiComofFaith.width             = 104
$rdiComofFaith.height            = 20
$rdiComofFaith.location          = New-Object System.Drawing.Point(14,91)
$rdiComofFaith.Font              = 'Microsoft Sans Serif,10'

$Label1                          = New-Object system.Windows.Forms.Label
$Label1.text                     = "Filename"
$Label1.AutoSize                 = $true
$Label1.width                    = 5
$Label1.height                   = 10
$Label1.location                 = New-Object System.Drawing.Point(14,15)
$Label1.Font                     = 'Microsoft Sans Serif,10'

$TextBox1                        = New-Object system.Windows.Forms.TextBox
$TextBox1.multiline              = $false
$TextBox1.width                  = 217
$TextBox1.height                 = 20
$TextBox1.location               = New-Object System.Drawing.Point(14,25)
$TextBox1.Font                   = 'Microsoft Sans Serif,10'

$TextBox2                        = New-Object system.Windows.Forms.TextBox
$TextBox2.multiline              = $false
$TextBox2.width                  = 217
$TextBox2.height                 = 20
$TextBox2.location               = New-Object System.Drawing.Point(14,60)
$TextBox2.Font                   = 'Microsoft Sans Serif,10'

$Label2                          = New-Object system.Windows.Forms.Label
$Label2.text                     = "Filename"
$Label2.AutoSize                 = $true
$Label2.width                    = 5
$Label2.height                   = 10
$Label2.location                 = New-Object System.Drawing.Point(14,50)
$Label2.Font                     = 'Microsoft Sans Serif,10'

$TextBox3                        = New-Object system.Windows.Forms.TextBox
$TextBox3.multiline              = $false
$TextBox3.width                  = 217
$TextBox3.height                 = 20
$TextBox3.location               = New-Object System.Drawing.Point(14,60)
$TextBox3.Font                   = 'Microsoft Sans Serif,10'

$Label3                          = New-Object system.Windows.Forms.Label
$Label3.text                     = "Filename"
$Label3.AutoSize                 = $true
$Label3.width                    = 5
$Label3.height                   = 10
$Label3.location                 = New-Object System.Drawing.Point(14,50)
$Label3.Font                     = 'Microsoft Sans Serif,10'

$TextBox4                        = New-Object system.Windows.Forms.TextBox
$TextBox4.multiline              = $false
$TextBox4.width                  = 217
$TextBox4.height                 = 20
$TextBox4.location               = New-Object System.Drawing.Point(14,25)
$TextBox4.Font                   = 'Microsoft Sans Serif,10'

$Label4                          = New-Object system.Windows.Forms.Label
$Label4.text                     = "Filename"
$Label4.AutoSize                 = $true
$Label4.width                    = 5
$Label4.height                   = 10
$Label4.location                 = New-Object System.Drawing.Point(14,15)
$Label4.Font                     = 'Microsoft Sans Serif,10'

$grpTimeCodeStart.controls.AddRange(@($btn5plusstart,$btn10plusstart,$btn5minusstart,$btn10minusstart,$TextBox3,$Label3,$TextBox4,$Label4))
$FfrmMain.controls.AddRange(@($grpTimeCodeStart,$grpTimeCodeEnd,$grpMetaData))
$grpTimeCodeEnd.controls.AddRange(@($btn5plusend,$btn10plusend,$btn10minusend,$btn5minusend,$Label1,$TextBox1,$TextBox2,$Label2))
$grpMetaData.controls.AddRange(@($txtfilename,$lblfilename,$rdiGlencroft,$rdiComofFaith))

#region gui events {
#endregion events }

#endregion GUI }


#Write your logic code here

[void]$FfrmMain.ShowDialog()