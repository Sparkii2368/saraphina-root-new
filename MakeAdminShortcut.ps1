$desktop=[Environment]::GetFolderPath('Desktop')
$lnk=Join-Path $desktop 'Saraphina (Admin).lnk'
$shell=New-Object -ComObject WScript.Shell
$sc=$shell.CreateShortcut($lnk)
$sc.TargetPath='powershell.exe'
$sc.Arguments='-NoProfile -ExecutionPolicy Bypass -File "D:\Saraphina Root\StartSaraphinaAdmin.ps1"'
$sc.WorkingDirectory='D:\Saraphina Root'
$sc.IconLocation="$env:SystemRoot\System32\SHELL32.dll,167"
$sc.Save()
Write-Output "Created: $lnk"