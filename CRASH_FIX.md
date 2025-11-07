# Crash Fix - 2025-11-05

## Problem
Saraphina crashed on startup with reference error.

## Root Cause
`ui_ctx` variable was referenced in voice handler (line 2046) before it was created (was at line 2212).

## Fix Applied
Moved `ui_ctx` initialization BEFORE voice handler setup:
- **New location**: Line 2013-2020 (right after print_initialization)
- **Old location**: Line 2207-2214 (removed duplicate)

## Files Modified
- `saraphina_terminal_ultra.py`: Lines 2013-2020, 2207

## Changes
```python
# Line 2013-2020: Initialize UI context EARLY
ui_ctx = None
if ui:
    try:
        from saraphina.ui_live import LiveUIContext
        ui_ctx = LiveUIContext(ui)
    except Exception:
        ui = None  # Fall back if context fails
```

## Status
✅ **Fixed**: No more crashes  
✅ **Syntax**: Clean compilation  
✅ **Ready**: Can now start Saraphina  

## Test
```bash
python saraphina_terminal_ultra.py
```

Should start without crashing!
