$ErrorActionPreference='Stop'
$root = 'D:\Saraphina Root'
$cmdPath = Join-Path $root 'StartSaraphina.cmd'
$cmdContent = @"
@echo off
setlocal
pushd "D:\Saraphina Root"
python saraphina_terminal_ultra.py
popd
endlocal
"@
Set-Content -LiteralPath $cmdPath -Encoding ASCII -Value $cmdContent
$desktop = [Environment]::GetFolderPath('Desktop')
$lnk = Join-Path $desktop 'Saraphina.lnk'
$shell = New-Object -ComObject WScript.Shell
$sc = $shell.CreateShortcut($lnk)
$sc.TargetPath = $cmdPath
$sc.WorkingDirectory = $root
$sc.WindowStyle = 1
$sc.IconLocation = "$env:SystemRoot\System32\SHELL32.dll,167"
$sc.Save()
Write-Output "Created: $lnk"
