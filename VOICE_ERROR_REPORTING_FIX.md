# Voice Error Reporting Fix

## Problem
You said: "I cant hear you" and "voice did not work on this startup"

Saraphina says at startup:
```
[SYSTEM] ✓ Voice system active - Always listening
```

But she **doesn't actually speak** her responses!

## Root Cause

### Silent Failure
```python
def speak(self, text: str):
    """Speak text with emotion detection"""
    if not VOICE_AVAILABLE:
        return  # ← SILENTLY FAILS! No error message!
```

If `VOICE_AVAILABLE = False`, she just doesn't speak and gives you NO indication why.

### Why VOICE_AVAILABLE Might Be False:
1. **ElevenLabs API key missing** in `.env`
2. **voice_modern.py import failed** (missing dependencies)
3. **elevenlabs library not installed**

The error was logged with:
```python
except Exception as e:
    logger.warning(f"Voice import failed: {e}")  # ← But logger not defined yet!
    VOICE_AVAILABLE = False
```

But `logger` wasn't defined yet (line 88), so the error was lost!

## The Fix

### 1. Save Import Errors
```python
try:
    from saraphina.voice_modern import speak_text, get_voice, VOICE_AVAILABLE
    VOICE_IMPORT_ERROR = None
except Exception as e:
    # Save error for later (logger not defined yet)
    VOICE_IMPORT_ERROR = str(e)
    VOICE_AVAILABLE = False
    
    # Define dummy functions
    def speak_text(text):
        pass
    def get_voice():
        return None
```

### 2. Report Error on First Speak Attempt
```python
def speak(self, text: str):
    """Speak text with emotion detection"""
    if not VOICE_AVAILABLE:
        # Log why voice isn't working (only once)
        if not hasattr(self, '_voice_error_logged'):
            self._voice_error_logged = True
            if VOICE_IMPORT_ERROR:
                self.add_system_message(f"⚠️ Voice OUTPUT unavailable: {VOICE_IMPORT_ERROR}")
            else:
                self.add_system_message("⚠️ Voice OUTPUT unavailable: VOICE_AVAILABLE = False")
        return
```

## What You'll See Now

### If Voice Works:
```
[17:20] Saraphina: Hi! How can I help you today?
[And you HEAR her speak]
```

### If Voice Fails:
```
[17:20] Saraphina: Hi! How can I help you today?
[SYSTEM] ⚠️ Voice OUTPUT unavailable: No module named 'elevenlabs'
```

Or:
```
[SYSTEM] ⚠️ Voice OUTPUT unavailable: ELEVENLABS_API_KEY not found in environment
```

Now you'll actually **know WHY** voice isn't working!

## Testing

**Restart Saraphina** and send a message. If voice doesn't work, you should now see:
```
[SYSTEM] ⚠️ Voice OUTPUT unavailable: <actual error>
```

## Common Fixes

### If Missing API Key:
1. Check `.env` file has `ELEVENLABS_API_KEY=your_key_here`
2. Make sure `.env` is in the right location

### If Missing Library:
```bash
pip install elevenlabs
```

### If voice_modern.py Has Errors:
Check `D:\Saraphina Root\saraphina\voice_modern.py` for syntax errors

---

**Status**: ✅ Error reporting added - Now you'll see WHY voice fails!
