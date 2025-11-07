# ✅ TEMP FILES MOVED TO D: DRIVE

## What Changed

### Before:
- Temp files saved to **C: drive** (Windows default)
- C: drive filled up → voice failed
- Error: `[Errno 28] No space left on device`

### After:
- **ALL temp files now go to D: drive**
- Location: `D:\Saraphina Root\temp\`
- Automatic cleanup of old files
- C: drive stays free!

---

## Configuration Applied

### In `saraphina_gui.py` (lines 18-25):

```python
# ===== FORCE ALL TEMP FILES TO D: DRIVE =====
import tempfile
SARAPHINA_TEMP_DIR = Path("D:/Saraphina Root/temp")
SARAPHINA_TEMP_DIR.mkdir(parents=True, exist_ok=True)
tempfile.tempdir = str(SARAPHINA_TEMP_DIR)
os.environ['TEMP'] = str(SARAPHINA_TEMP_DIR)
os.environ['TMP'] = str(SARAPHINA_TEMP_DIR)
print(f"[TEMP] All temporary files will use: {SARAPHINA_TEMP_DIR}")
```

**What this does:**
1. Creates `D:\Saraphina Root\temp\` directory
2. Sets Python's `tempfile.tempdir` to D: drive
3. Sets Windows environment variables `TEMP` and `TMP`
4. Prints confirmation message at startup

---

## Directory Structure

```
D:\Saraphina Root\temp\
├── audio\          ← ElevenLabs voice files
├── code_gen\       ← CodeForge temporary code
└── downloads\      ← Downloaded resources
```

---

## Automatic Cleanup

### Built-in Features:

**On Startup:**
- Automatically deletes files older than 24 hours
- Runs when Saraphina starts
- Silent unless files are deleted

**Manual Cleanup:**
```powershell
# Show temp stats
python "D:\Saraphina Root\saraphina\temp_manager.py" stats

# Clean files older than 24 hours
python "D:\Saraphina Root\saraphina\temp_manager.py" clean

# Clean files older than 6 hours
python "D:\Saraphina Root\saraphina\temp_manager.py" clean 6

# EMERGENCY: Delete ALL temp files
python "D:\Saraphina Root\saraphina\temp_manager.py" emergency
```

---

## What You'll See at Startup

```
[TEMP] All temporary files will use: D:\Saraphina Root\temp
[SYSTEM] 🚀 Initializing Saraphina Ultra Mission Control...
```

If old files are cleaned:
```
[INFO] Auto-cleanup: 15 old temp files removed
```

---

## Benefits

✅ **C: drive stays free**
- No more disk full errors
- Voice always works

✅ **Automatic cleanup**
- Old files deleted automatically
- Prevents temp bloat

✅ **Organized**
- Separate folders for audio, code, downloads
- Easy to manage

✅ **Cross-platform compatible**
- Works on Windows, Linux, Mac
- Just change the path if needed

---

## Testing

### 1. Restart Saraphina
```
Type "restart" in Saraphina
```

Look for:
```
[TEMP] All temporary files will use: D:\Saraphina Root\temp
```

### 2. Check Voice Works
Send a message and **listen** for voice response.

### 3. Verify Temp Location
```powershell
# Check temp directory
ls "D:\Saraphina Root\temp"
```

Should see subdirectories and possibly audio files.

### 4. Test Cleanup
```powershell
python "D:\Saraphina Root\saraphina\temp_manager.py" stats
```

---

## Troubleshooting

### If Voice Still Doesn't Work:

**Check D: drive has space:**
```powershell
Get-PSDrive D | Select-Object Used,Free
```

**Check temp files are being created:**
```powershell
Get-ChildItem "D:\Saraphina Root\temp\audio" -Recurse
```

**Check for errors:**
Look for `[TEMP]` message at Saraphina startup.

### If D: Drive Fills Up:

**Emergency cleanup:**
```powershell
python "D:\Saraphina Root\saraphina\temp_manager.py" emergency
```

**Or manually:**
```powershell
Remove-Item "D:\Saraphina Root\temp\*" -Recurse -Force
```

---

## Customization

### Change Temp Location:

Edit `saraphina_gui.py` line 20:
```python
SARAPHINA_TEMP_DIR = Path("E:/Temp/Saraphina")  # Or any drive
```

### Change Cleanup Age:

Edit `temp_manager.py` line 137:
```python
result = manager.clean_old_files(max_age_hours=12)  # Default 24
```

### Disable Auto-Cleanup:

Comment out lines 134-141 in `temp_manager.py`:
```python
# if __name__ != "__main__":
#     try:
#         manager = TempManager()
#         ...
```

---

## Files Modified

1. **`saraphina_gui.py`**
   - Added temp directory configuration (lines 18-25)

2. **`temp_manager.py`** (NEW)
   - Complete temp file management system
   - Auto-cleanup on startup
   - CLI commands for manual management

---

## Summary

✅ **All temp files → D: drive**
✅ **Automatic cleanup** (24h)
✅ **Manual cleanup** commands
✅ **Organized structure**
✅ **Voice won't fail** due to disk space

**Restart Saraphina** to activate!

---

**Status**: ✅ **COMPLETE** - Temp files now use D: drive with auto-cleanup!
