# Saraphina Cleanup Script
# Removes duplicate files, old backups, and unnecessary cache files

Write-Host "=== Saraphina Cleanup Script ===" -ForegroundColor Cyan
Write-Host "This script will clean up unnecessary Saraphina files across your system."
Write-Host ""

$cleaned = 0
$totalSizeFreed = 0

# Function to safely remove directory
function Remove-SafeDirectory {
    param($path, $description)
    
    if (Test-Path $path) {
        try {
            $size = (Get-ChildItem $path -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB
            Remove-Item -Path $path -Recurse -Force -ErrorAction Stop
            Write-Host "[OK] Removed: $description ($([math]::Round($size, 2)) MB)" -ForegroundColor Green
            $script:cleaned++
            $script:totalSizeFreed += $size
        }
        catch {
            Write-Host "[ERROR] Failed to remove: $description - $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

# Function to safely remove file
function Remove-SafeFile {
    param($path, $description)
    
    if (Test-Path $path) {
        try {
            $size = (Get-Item $path).Length / 1MB
            Remove-Item -Path $path -Force -ErrorAction Stop
            Write-Host "[OK] Removed: $description ($([math]::Round($size, 2)) MB)" -ForegroundColor Green
            $script:cleaned++
            $script:totalSizeFreed += $size
        }
        catch {
            Write-Host "[ERROR] Failed to remove: $description - $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

Write-Host "`n1. Removing duplicate src/ directory..." -ForegroundColor Yellow
Remove-SafeDirectory "D:\Saraphina Root\src" "Old src directory (duplicate)"

Write-Host "`n2. Cleaning __pycache__ directories..." -ForegroundColor Yellow
Get-ChildItem -Path "D:\Saraphina Root\saraphina" -Recurse -Directory -Filter "__pycache__" | ForEach-Object {
    Remove-SafeDirectory $_.FullName "__pycache__ at $($_.FullName)"
}

Write-Host "`n3. Removing old backups (keeping most recent 2)..." -ForegroundColor Yellow
$backups = Get-ChildItem -Path "D:\Saraphina Root\backups" -Filter "*.db" -ErrorAction SilentlyContinue | 
    Sort-Object LastWriteTime -Descending

if ($backups.Count -gt 2) {
    $backups | Select-Object -Skip 2 | ForEach-Object {
        Remove-SafeFile $_.FullName "Old backup: $($_.Name)"
    }
}

Write-Host "`n4. Removing old encrypted backups (keeping most recent 2)..." -ForegroundColor Yellow
$encBackups = Get-ChildItem -Path "D:\Saraphina Root\backups" -Filter "*.enc" -ErrorAction SilentlyContinue | 
    Sort-Object LastWriteTime -Descending

if ($encBackups.Count -gt 2) {
    $encBackups | Select-Object -Skip 2 | ForEach-Object {
        Remove-SafeFile $_.FullName "Old encrypted backup: $($_.Name)"
    }
}

Write-Host "`n5. Cleaning old log files (keeping most recent 5)..." -ForegroundColor Yellow
$logs = Get-ChildItem -Path "D:\Saraphina Root\logs" -Filter "*.log*" -ErrorAction SilentlyContinue | 
    Sort-Object LastWriteTime -Descending

if ($logs.Count -gt 5) {
    $logs | Select-Object -Skip 5 | ForEach-Object {
        Remove-SafeFile $_.FullName "Old log: $($_.Name)"
    }
}

Write-Host "`n6. Removing test offline data..." -ForegroundColor Yellow
Remove-SafeDirectory "D:\Saraphina Root\test_offline_data" "Test offline data directory"

Write-Host "`n7. Cleaning downloads directory (remove RAR archives)..." -ForegroundColor Yellow
Get-ChildItem -Path "D:\Saraphina Root\downloads" -Filter "*.rar" -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-SafeFile $_.FullName "Download archive: $($_.Name)"
}

Write-Host "`n8. Cleaning user Desktop old Saraphina files..." -ForegroundColor Yellow

# Old batch files
$desktopBatch = @(
    "C:\Users\Jacques\Desktop\Launch Saraphina.bat",
    "C:\Users\Jacques\Desktop\Saraphina App.bat",
    "C:\Users\Jacques\Desktop\Saraphina Bridge (Debug).bat",
    "C:\Users\Jacques\Desktop\Saraphina Bridge (Pinned).bat",
    "C:\Users\Jacques\Desktop\Saraphina Bridge UI.bat",
    "C:\Users\Jacques\Desktop\Saraphina Chat.bat",
    "C:\Users\Jacques\Desktop\Saraphina UI.bat"
)

foreach ($file in $desktopBatch) {
    Remove-SafeFile $file "Desktop batch file: $(Split-Path $file -Leaf)"
}

# Old shortcuts
$desktopLinks = @(
    "C:\Users\Jacques\Desktop\Saraphina Bridge.lnk",
    "C:\Users\Jacques\Desktop\Saraphina Terminal.lnk",
    "C:\Users\Jacques\Desktop\Saraphina.lnk"
)

foreach ($file in $desktopLinks) {
    Remove-SafeFile $file "Desktop shortcut: $(Split-Path $file -Leaf)"
}

# Old documentation on desktop
$desktopDocs = @(
    "C:\Users\Jacques\Desktop\Saraphina Guardian UI Spec.md",
    "C:\Users\Jacques\Desktop\Saraphina Phase 0 Plan.md",
    "C:\Users\Jacques\Desktop\Saraphina Phase 4 Completion Plan.md",
    "C:\Users\Jacques\Desktop\Saraphina Vision & Roadmap.md",
    "C:\Users\Jacques\Desktop\Saraphina XP & Personality Upgrade Plan.md"
)

foreach ($file in $desktopDocs) {
    Remove-SafeFile $file "Desktop doc: $(Split-Path $file -Leaf)"
}

Write-Host "`n9. Cleaning old Saraphina user directory..." -ForegroundColor Yellow
Remove-SafeDirectory "C:\Users\Jacques\Saraphina" "Old Saraphina user directory"

Write-Host "`n10. Cleaning old Blender scripts..." -ForegroundColor Yellow
Remove-SafeDirectory "C:\Users\Jacques\BlenderScripts" "Old Blender scripts directory"

Write-Host "`n11. Removing old Saraphina root scripts..." -ForegroundColor Yellow
$rootScripts = @(
    "C:\Users\Jacques\saraphina_step1_base_mesh.py",
    "C:\Users\Jacques\saraphina_step2_rigging.py",
    "C:\Users\Jacques\saraphina_step3_animations.py"
)

foreach ($file in $rootScripts) {
    Remove-SafeFile $file "Root script: $(Split-Path $file -Leaf)"
}

Write-Host "`n12. Cleaning duplicate playwright profiles..." -ForegroundColor Yellow
# Keep the one in root, remove duplicates
if (Test-Path "D:\Saraphina Root\.saraphina_playwright_profile") {
    Write-Host "[INFO] Main playwright profile exists, no cleanup needed" -ForegroundColor Blue
}

Write-Host "`n=== Cleanup Complete ===" -ForegroundColor Cyan
Write-Host "Files/Directories cleaned: $cleaned" -ForegroundColor Green
Write-Host "Total space freed: $([math]::Round($totalSizeFreed, 2)) MB" -ForegroundColor Green

Write-Host "`n=== Remaining Saraphina Structure ===" -ForegroundColor Cyan
Write-Host "Main project: D:\Saraphina Root\" -ForegroundColor White
Write-Host "  ├── saraphina/ (core modules)" -ForegroundColor White
Write-Host "  ├── deployment/ (Docker, K8s)" -ForegroundColor White
Write-Host "  ├── mobile/ (React Native)" -ForegroundColor White
Write-Host "  ├── tests/ (test suite)" -ForegroundColor White
Write-Host "  ├── .github/ (CI/CD)" -ForegroundColor White
Write-Host "  ├── web/ (dashboard)" -ForegroundColor White
Write-Host "  ├── backups/ (recent only)" -ForegroundColor White
Write-Host "  ├── logs/ (recent only)" -ForegroundColor White
Write-Host "  └── configs/ (configuration)" -ForegroundColor White

Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
