# Elevate and launch Saraphina as Administrator
if (-not ([bool](NET SESSION 2>$null))) {
  # Not admin — re-run StartSaraphina.cmd elevated
  Start-Process -Verb RunAs -FilePath "cmd.exe" -ArgumentList "/c ""D:\Saraphina Root\StartSaraphina.cmd"""
  exit
}
# Admin context — run the app
Push-Location "D:\Saraphina Root"
python saraphina_terminal_ultra.py
Pop-Location
