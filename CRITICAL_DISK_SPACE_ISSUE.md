# 🚨 CRITICAL: DISK SPACE FULL - Voice System Failure

## Problem Identified

**Voice stopped working because:**
```
Speech failed: [Errno 28] No space left on device
```

**Your disk is completely full!**

## Why This Breaks Voice

ElevenLabs TTS works by:
1. Sends text to ElevenLabs API
2. Receives audio file
3. **Saves audio to temporary file** ← FAILS HERE
4. Plays audio file

When disk is full, step 3 fails and voice is silent.

## Immediate Fixes

### Option 1: Free Up Disk Space (RECOMMENDED)

Run this to see what's using space:
```powershell
Get-PSDrive C | Select-Object Used,Free
```

Then delete:
- **Old downloads**
- **Temporary files**: `C:\Windows\Temp\*`
- **Recycle bin**: Empty it
- **Old backups**: Check `D:\Saraphina Root\.backups\`
- **Browser cache**
- **Old logs**: Check `D:\Saraphina Root\saraphina\logs\`

### Option 2: Change Voice Cache Location

Modify `voice_modern.py` to use a drive with space:
```python
# Change temp directory to drive with space
import tempfile
tempfile.tempdir = "E:/Temp"  # Or another drive
```

### Option 3: Use Streaming Audio (No Files)

Modify voice system to stream audio directly without saving files (advanced).

## Check Current Disk Space

```powershell
Get-PSDrive | Where-Object {$_.Used -ne $null} | Select-Object Name, @{Name="Used(GB)";Expression={[math]::Round($_.Used/1GB,2)}}, @{Name="Free(GB)";Expression={[math]::Round($_.Free/1GB,2)}}
```

## What Else Might Break

With full disk, these will also fail:
- ✅ **Logging**: Can't write logs
- ✅ **Backups**: Can't create .bak files  
- ✅ **Database**: SQLite can't grow
- ✅ **Code generation**: Can't save new files
- ✅ **Memory consolidation**: Can't write to DB
- ✅ **Self-upgrades**: Can't apply artifacts

**Saraphina needs disk space to function!**

## Emergency Cleanup Script

Run this to free up Saraphina-related temp files:
```powershell
# Clean Saraphina backups older than 7 days
Get-ChildItem "D:\Saraphina Root\.backups\*" -Recurse | 
  Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-7)} | 
  Remove-Item -Force

# Clean old logs
Get-ChildItem "D:\Saraphina Root\saraphina\logs\*.log" | 
  Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-30)} | 
  Remove-Item -Force

# Show how much space freed
Get-PSDrive C | Select-Object Used,Free
```

## After Freeing Space

1. **Restart Saraphina**
2. Voice should work again
3. Type "restart" to reload

## Prevention

Set up automatic cleanup:
1. Schedule weekly temp file cleanup
2. Monitor disk space
3. Set Saraphina to alert when disk < 10% free

---

**Status**: 🚨 **CRITICAL** - Free disk space immediately!
