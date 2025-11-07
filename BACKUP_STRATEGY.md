# 🗄️ Smart Backup Strategy

## Overview

Saraphina now uses a **timestamped backup system** with automatic cleanup that works seamlessly with git integration. This prevents backup collisions and keeps the codebase clean.

---

## 🎯 Key Features

### 1. **Timestamped Backups**
Instead of generic `.bak` files, backups include:
- Timestamp: `YYYYMMDD_HHMMSS`
- Artifact ID (first 8 chars)

**Format:**
```
stt_listener.py.bak.20251106_201045.abc12345
knowledge_engine.py.bak.20251106_201530
```

This guarantees:
- ✅ No backup collisions
- ✅ Multiple versions preserved
- ✅ Traceable to specific upgrades

### 2. **Automatic Cleanup**
By default, only the **3 most recent backups** are kept per file.

When a new backup is created:
- Old backups are sorted by modification time
- Oldest backups beyond `max_backups` are deleted
- Recent backups are preserved

**Configuration:**
```python
# Default: keep 3 backups
hot_reload = HotReloadManager("path/to/saraphina", max_backups=3)

# Keep 5 backups
hot_reload = HotReloadManager("path/to/saraphina", max_backups=5)

# Keep unlimited backups (not recommended)
hot_reload = HotReloadManager("path/to/saraphina", max_backups=999)
```

### 3. **Git Integration Cleanup**
After a **successful git commit**, all `.bak.*` files are automatically deleted.

**Rationale:**
- Changes are now in git history (safe permanent storage)
- Git provides better rollback than file backups
- Keeps codebase clean

**What happens:**
```
1. Upgrade starts → Timestamped backup created
2. Changes applied → Files modified
3. Git commit succeeds → All .bak.* files deleted
4. Git commit fails → Backups retained for safety
```

---

## 📋 Backup Lifecycle

### Example: Upgrading `knowledge_engine.py`

**Before upgrade:**
```
saraphina/
  knowledge_engine.py
  knowledge_engine.py.bak.20251105_143020.xyz98765
  knowledge_engine.py.bak.20251105_150102.def45678
```

**During upgrade (backup created):**
```
saraphina/
  knowledge_engine.py
  knowledge_engine.py.bak.20251105_143020.xyz98765
  knowledge_engine.py.bak.20251105_150102.def45678
  knowledge_engine.py.bak.20251106_201045.abc12345  ← NEW
```

**After upgrade (cleanup runs):**
```
saraphina/
  knowledge_engine.py
  knowledge_engine.py.bak.20251105_150102.def45678
  knowledge_engine.py.bak.20251106_201045.abc12345
```
*Oldest backup deleted (20251105_143020)*

**After git commit (cleanup runs):**
```
saraphina/
  knowledge_engine.py
```
*All backups deleted (changes in git)*

---

## 🔧 Manual Operations

### View All Backups
```powershell
# List all backup files
Get-ChildItem "D:\Saraphina Root\saraphina\*.bak.*"

# Count backups per file
Get-ChildItem "D:\Saraphina Root\saraphina\*.bak.*" | Group-Object {$_.Name -replace '\.bak\..*$', ''} | Select Name, Count
```

### Restore From Backup
```powershell
# Restore from specific backup
Copy-Item "knowledge_engine.py.bak.20251106_201045.abc12345" "knowledge_engine.py"

# Or in Python
import shutil
shutil.copy("knowledge_engine.py.bak.20251106_201045.abc12345", "knowledge_engine.py")
```

### Clean All Backups Manually
```powershell
# Delete all .bak.* files (use with caution!)
Remove-Item "D:\Saraphina Root\saraphina\*.bak.*"
```

---

## 🚀 Upgrade Flow With Backups

```
User: "apply upgrade"
  ↓
1. Create timestamped backup
   → knowledge_engine.py.bak.20251106_201045.abc12345
   ↓
2. Cleanup old backups
   → Keep only 3 most recent
   ↓
3. Apply code changes
   → Modify knowledge_engine.py
   ↓
4. Hot-reload module
   → importlib.reload()
   ↓
5. Run tests
   → Validation
   ↓
6. Git commit (if enabled)
   ↓
7. If commit succeeds:
   → Delete all .bak.* files
   → Changes now in git history
   ↓
   If commit fails:
   → Keep .bak.* files for manual rollback
   → User can restore if needed
```

---

## 🛡️ Safety Guarantees

### Multiple Layers of Protection

1. **Timestamped Backups**: Always created before changes
2. **Local Backups**: Recent backups kept even during upgrades
3. **Git History**: Full version control after successful commits
4. **Upgrade Ledger**: Database log of all changes (`upgrade_ledger.db`)
5. **Learning Journal**: AI learns from failures (`upgrade_journal.db`)

### Rollback Options

| Scenario | Rollback Method |
|----------|-----------------|
| **Validation fails** | Changes never applied (safe) |
| **Application fails** | Automatic rollback from .bak files |
| **Git commit fails** | .bak files retained, manual restore |
| **Git commit succeeds** | `git revert <commit>` or `git reset --hard HEAD~1` |
| **Days later** | `git checkout <commit>` or `git revert` |

---

## 📊 Monitoring

### Check Backup Status
```python
from pathlib import Path
import glob

saraphina_root = Path("D:/Saraphina Root/saraphina")

# Count backups per file
backups = list(saraphina_root.glob("*.bak.*"))
print(f"Total backups: {len(backups)}")

# Group by original file
from collections import defaultdict
backup_counts = defaultdict(int)
for backup in backups:
    original_name = backup.name.split(".bak.")[0]
    backup_counts[original_name] += 1

for filename, count in backup_counts.items():
    print(f"{filename}: {count} backups")
```

### Backup Disk Usage
```powershell
# Total size of all backups
(Get-ChildItem "D:\Saraphina Root\saraphina\*.bak.*" | Measure-Object -Property Length -Sum).Sum / 1MB
# Returns: MB used by backups
```

---

## ⚙️ Configuration Options

### In `hot_reload_manager.py`:

```python
# Default configuration (recommended)
hot_reload = HotReloadManager(
    saraphina_root="D:\\Saraphina Root\\saraphina",
    max_backups=3  # Keep 3 most recent backups
)

# Conservative (more backups)
hot_reload = HotReloadManager(
    saraphina_root="D:\\Saraphina Root\\saraphina",
    max_backups=5
)

# Aggressive cleanup (minimal backups)
hot_reload = HotReloadManager(
    saraphina_root="D:\\Saraphina Root\\saraphina",
    max_backups=1  # Only keep latest backup
)
```

### Disable Git Cleanup:
To keep backups even after git commits, comment out lines 643-646 in `gui_ultra_processor.py`:

```python
# # Cleanup backups after successful commit
# ui_log("🧹 Cleaning up backups (now in git history)...")
# hot_reload._cleanup_backups_after_commit(file_paths)
# ui_log("✓ Backups cleaned")
```

---

## 🎓 Best Practices

### ✅ Recommended

1. **Use default settings** (max_backups=3)
   - Balances safety and disk space
   - Keeps recent rollback points

2. **Enable git integration**
   - Provides long-term version history
   - Automatic cleanup after commits

3. **Monitor backup counts**
   - Periodically check for stuck backups
   - Clean manually if needed

4. **Test rollback procedures**
   - Practice restoring from backups
   - Verify git revert works

### ❌ Avoid

1. **Setting max_backups too low** (e.g., 1)
   - Loses safety net during multiple upgrades
   
2. **Setting max_backups too high** (e.g., 100)
   - Wastes disk space
   - Slower cleanup operations

3. **Deleting backups during active upgrades**
   - Could lose rollback capability

4. **Ignoring backup disk usage**
   - Could fill up disk if cleanup fails

---

## 🔍 Troubleshooting

### Problem: Backups not being deleted

**Symptoms:**
- Many `.bak.*` files accumulate
- Disk space increasing

**Causes:**
- Git integration disabled or failing
- Cleanup code commented out
- File permission issues

**Solutions:**
```python
# Manual cleanup
from pathlib import Path
from saraphina.hot_reload_manager import HotReloadManager

hot_reload = HotReloadManager("D:\\Saraphina Root\\saraphina")
saraphina_root = Path("D:\\Saraphina Root\\saraphina")

# Get all Python files
for py_file in saraphina_root.glob("*.py"):
    if py_file.stem != "__init__":
        hot_reload._cleanup_old_backups(py_file)
        print(f"Cleaned backups for {py_file.name}")
```

### Problem: Backup collision errors

**Symptoms:**
- Error: "File exists" during backup creation

**Causes:**
- Multiple upgrades in same second (rare)
- Timestamp collision

**Solutions:**
- Timestamps include seconds (very rare collision)
- If it happens, wait 1 second and retry
- System automatically handles this

### Problem: Cannot restore from backup

**Symptoms:**
- Backup file exists but restore fails

**Causes:**
- File permissions
- File in use by Python process

**Solutions:**
```powershell
# Check file permissions
Get-Acl "knowledge_engine.py.bak.20251106_201045.abc12345"

# Force copy (PowerShell)
Copy-Item -Path "knowledge_engine.py.bak.*" -Destination "knowledge_engine.py" -Force
```

---

## 📈 Benefits vs. Old System

| Feature | Old System | New System |
|---------|------------|------------|
| **Backup naming** | Generic `.bak` | Timestamped with artifact ID |
| **Multiple versions** | ❌ One version only | ✅ Configurable (default: 3) |
| **Collision handling** | ❌ Error on existing .bak | ✅ Automatic timestamping |
| **Cleanup** | ❌ Manual only | ✅ Automatic after git commits |
| **Traceability** | ❌ No artifact linking | ✅ Artifact ID in filename |
| **Disk usage** | ⚠️ Can accumulate | ✅ Auto-limited |
| **Git integration** | ❌ No | ✅ Cleanup after commits |

---

## 🚦 Status Indicators

During upgrades, you'll see:
```
📦 Applying artifact 1/1: abc12345
  ✓ Created timestamped backup: stt_listener.py.bak.20251106_201045.abc12345
  ✓ Removed old backup: stt_listener.py.bak.20251105_143020.xyz98765
  ✓ Success: 1 files modified
🐛 Committing to git...
  ✓ Git commit: a7b3c912
🧹 Cleaning up backups (now in git history)...
  ✓ Cleaned up backup after git commit: stt_listener.py.bak.20251106_201045.abc12345
  ✓ Backups cleaned
```

---

## 🎯 Summary

**The new backup system provides:**
- ✅ No more backup collisions
- ✅ Multiple version preservation
- ✅ Automatic cleanup
- ✅ Git integration
- ✅ Traceability via artifact IDs
- ✅ Configurable retention policy
- ✅ Safe rollback procedures

**Default behavior:**
1. Create timestamped backup before changes
2. Keep 3 most recent backups per file
3. Delete all backups after successful git commit
4. Retain backups if git commit fails

This gives Saraphina both **safety** (multiple rollback points) and **cleanliness** (automatic cleanup).
