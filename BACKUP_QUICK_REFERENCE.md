# 🗂️ Backup System - Quick Reference

## 📋 At a Glance

**System**: Smart Timestamped Backups with Git Integration  
**Status**: ✅ Production Ready  
**Default Retention**: 3 backups per file  
**Auto-Cleanup**: After successful git commits

---

## 🎯 Key Commands

### View All Backups
```powershell
Get-ChildItem "D:\Saraphina Root\saraphina\*.bak.*"
```

### Restore a Backup
```powershell
# Find the backup you want
Get-ChildItem "D:\Saraphina Root\saraphina\module_name.py.bak.*"

# Restore it
Copy-Item "module_name.py.bak.20251106_201045.abc12345" "module_name.py"
```

### Clean Old Backups (Manual)
```powershell
Remove-Item "D:\Saraphina Root\saraphina\*.bak.*"
```

### Check Disk Usage
```powershell
(Get-ChildItem "D:\Saraphina Root\saraphina\*.bak.*" | Measure-Object -Property Length -Sum).Sum / 1MB
```

---

## 🔧 Configuration

### Default (Recommended)
```python
from saraphina.hot_reload_manager import HotReloadManager

hot_reload = HotReloadManager("D:\\Saraphina Root\\saraphina", max_backups=3)
```

### Keep More Backups
```python
hot_reload = HotReloadManager("D:\\Saraphina Root\\saraphina", max_backups=5)
```

### Keep Fewer Backups
```python
hot_reload = HotReloadManager("D:\\Saraphina Root\\saraphina", max_backups=1)
```

---

## 🚀 How Upgrades Work

```
1. User: "apply upgrade"
   ↓
2. Create backup: module.py.bak.20251106_201045.abc12345
   ↓
3. Cleanup: Delete oldest backups (keep 3)
   ↓
4. Apply changes to module.py
   ↓
5. Hot-reload module
   ↓
6. Git commit
   ↓
7. Success? → Delete all .bak.* files
   Failure? → Keep .bak.* files for safety
```

---

## 📊 Backup Naming

**Format**: `filename.py.bak.YYYYMMDD_HHMMSS.artifact_id`

**Examples**:
- `stt_listener.py.bak.20251106_201045.abc12345`
- `knowledge_engine.py.bak.20251106_201530`

**Parts**:
- `stt_listener.py` - Original filename
- `.bak` - Backup marker
- `20251106_201045` - Timestamp (Nov 6, 2025 at 20:10:45)
- `abc12345` - First 8 chars of artifact ID (optional)

---

## 🛡️ Safety Features

✅ **Timestamped** - No collisions  
✅ **Multiple Versions** - Keep 3 recent backups  
✅ **Auto-Cleanup** - After git commits  
✅ **Git Integration** - Long-term history  
✅ **Rollback** - Multiple recovery options

---

## 🔄 Rollback Options

| Scenario | Solution |
|----------|----------|
| **During upgrade** | Automatic rollback from .bak files |
| **After failed commit** | `Copy-Item "file.py.bak.*" "file.py"` |
| **After successful commit** | `git revert <commit-hash>` |
| **Days later** | `git checkout <commit-hash>` |

---

## ⚠️ Troubleshooting

### Backups Accumulating?
```python
from pathlib import Path
from saraphina.hot_reload_manager import HotReloadManager

hot_reload = HotReloadManager("D:\\Saraphina Root\\saraphina")
for py_file in Path("D:\\Saraphina Root\\saraphina").glob("*.py"):
    hot_reload._cleanup_old_backups(py_file)
```

### Cannot Restore?
```powershell
# Force copy
Copy-Item -Path "module.py.bak.*" -Destination "module.py" -Force
```

### Check Git Status
```powershell
cd "D:\Saraphina Root"
git status
git log --oneline -5
```

---

## 📈 Monitoring

### Count Backups
```python
from pathlib import Path

saraphina_root = Path("D:/Saraphina Root/saraphina")
backups = list(saraphina_root.glob("*.bak.*"))
print(f"Total backups: {len(backups)}")
```

### Group by File
```python
from collections import defaultdict

backup_counts = defaultdict(int)
for backup in backups:
    original = backup.name.split(".bak.")[0]
    backup_counts[original] += 1

for file, count in backup_counts.items():
    print(f"{file}: {count} backups")
```

---

## 🎓 Best Practices

### ✅ DO
- Keep default `max_backups=3`
- Enable git integration
- Monitor disk usage periodically
- Test restore procedures

### ❌ DON'T
- Set `max_backups < 2`
- Delete backups during upgrades
- Ignore disk warnings
- Disable git integration

---

## 📚 Full Documentation

- **BACKUP_STRATEGY.md** - Complete guide (405 lines)
- **BACKUP_SYSTEM_COMPLETE.md** - Implementation details
- **test_backup_system.py** - Automated tests

---

## 🚦 Status Indicators

During upgrades you'll see:

```
✓ Created timestamped backup: module.py.bak.20251106_201045.abc12345
✓ Removed old backup: module.py.bak.20251105_143020.xyz98765
✓ Success: 1 files modified
✓ Git commit: a7b3c912
✓ Cleaned up backup after git commit
```

---

## 💡 Quick Tips

1. **Backups are automatic** - No manual intervention needed
2. **Max 3 backups per file** - Configurable if needed
3. **Git commits clean backups** - Long-term history in git
4. **Failed commits preserve backups** - Safety first
5. **Restore is simple** - Just copy .bak file over original

---

## 🔗 Related Systems

- **Git Integration** (`saraphina/git_integration.py`)
- **Hot Reload** (`saraphina/hot_reload_manager.py`)
- **Upgrade Ledger** (`saraphina/upgrade_ledger.py`)
- **Learning Journal** (`saraphina/upgrade_learning_journal.py`)

---

**Version**: 1.0  
**Date**: November 6, 2025  
**Status**: Production Ready ✅
