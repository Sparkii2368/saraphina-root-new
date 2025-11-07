# Saraphina Voice Setup Guide

## 🎤 Voice-Enabled AI Terminal

Your Saraphina AI now has **VJR-style UI** with **ElevenLabs voice integration**!

---

## 🚀 Quick Start

### Prerequisites

1. **Python packages**:
   ```bash
   pip install elevenlabs pygame
   ```

2. **ElevenLabs API Key**:
   - Get your API key from https://elevenlabs.io
   - Sign up for free account

3. **Set Environment Variable**:
   ```powershell
   # Windows PowerShell
   $env:ELEVENLABS_API_KEY = "your_api_key_here"
   
   # Or permanently:
   setx ELEVENLABS_API_KEY "your_api_key_here"
   ```

---

## ✅ What's Included

### VJR-Style UI
- Beautiful box-drawing interface
- 30 integrated systems display
- Clear system status
- Professional enterprise layout

### Voice Features
- ✅ Auto-detects your custom Saraphina voice
- ✅ Falls back to Rachel, Bella, or Charlotte if not found
- ✅ Synchronous & async speech generation
- ✅ Toggle voice on/off with `/voice` command
- ✅ Speaks all AI responses automatically
- ✅ Welcome greeting with voice
- ✅ Goodbye message with voice

### Enhanced Terminal
- `/help` - VJR-style help menu
- `/status` - Learning status with progress bars
- `/domains` - 7 knowledge domains
- `/export` - Export conversations
- `/voice` - Toggle voice on/off
- `/learning` - Learning progress
- `/memory` - View memory bank
- `/skills` - Skill progression bars
- `/clear` - Clear screen (maintains session)

---

## 📝 Usage

### Start Terminal
```bash
# Double-click on desktop
Launch Saraphina.bat

# Or run directly
python saraphina_terminal_voice.py
```

### With Voice
If ElevenLabs is setup correctly:
```
You: Hello Saraphina
🤖 Saraphina: [speaks] Hello! I'm Saraphina, your voice-enabled...
```

### Without Voice (Text-Only Mode)
If voice unavailable, terminal still works perfectly in text mode:
```
⚠️  Voice system not available - text-only mode
You: Hello
🤖 Saraphina: Hello! I'm Saraphina...
```

---

## 🎯 Voice Commands

| Command | Description |
|---------|-------------|
| `/voice` | Toggle voice on/off |
| Any text | Speaks the AI response |
| `/exit` | Goodbye message with voice |

---

## 🔧 Troubleshooting

### Voice Not Working?

**Check 1: API Key**
```powershell
# Verify it's set
echo $env:ELEVENLABS_API_KEY
```

**Check 2: Packages**
```bash
pip list | findstr elevenlabs
pip list | findstr pygame
```

**Check 3: Install if missing**
```bash
pip install elevenlabs pygame
```

**Check 4: Voice Logs**
Check terminal output for:
- ✅ ElevenLabs Voice System loaded
- ✅ Found Saraphina's custom voice
- ✅ Pygame audio system initialized

If you see ⚠️ warnings, they explain what's missing.

---

## 🎨 VJR-Style Features

### Beautiful UI
```
╔══════════════════════════════════════════════════════════════════════════╗
║                 🌟 SARAPHINA ENHANCED AI TERMINAL 🌟                    ║
║                   Advanced Voice-Enabled AI Assistant                   ║
╚══════════════════════════════════════════════════════════════════════════╝

🚀 UNIFIED VJR TERMINAL STARTING...
```

### System Status
```
📦 System Initialization:
  ✅ Saraphina AI Core loaded
  ✅ Persistent learning system active
  ✅ 7 Knowledge domains loaded
  ✅ ElevenLabs Voice System loaded
  ✅ All 30 Advanced Systems ready
```

### 30 Systems Grid
```
ALL 30 SYSTEMS ACTIVE:
✅ Machine Reasoning  ✅ Voice System       ✅ Plugin Ecosystem
✅ Search Engine      ✅ Collaboration     ✅ Data Visualization
...
```

---

## 📊 Voice Info

### Custom Voice
If you have a custom "Saraphina" voice in ElevenLabs:
- ✅ Automatically detected and used
- 🎤 Your personalized voice

### Fallback Voices
If no custom voice found:
1. Rachel (default)
2. Bella
3. Charlotte
4. Sarah
5. Elli

Or first available voice in your account.

---

## 💡 Pro Tips

1. **Best Experience**: Set up your ELEVENLABS_API_KEY permanently with `setx`
2. **Custom Voice**: Name your voice "Saraphina" in ElevenLabs for auto-detection
3. **Toggle Anytime**: Use `/voice` to turn voice on/off during conversation
4. **Text-Only**: Works perfectly without voice if preferred
5. **Persistent Learning**: All progress saved regardless of voice status

---

## 🎉 Features Combined

✅ **VJR-Style UI** from vjr_terminal.py  
✅ **ElevenLabs Voice** same as your original setup  
✅ **Persistent Learning** from enhanced AI  
✅ **7 Knowledge Domains** all integrated  
✅ **Progress Bars** visual feedback  
✅ **Auto-Save** every 5 conversations  
✅ **Conversation Export** full history  
✅ **30 Systems Display** enterprise features  

---

## 🆘 Support

### No Voice?
Terminal works perfectly without voice in text-only mode. Voice is optional!

### Want Voice?
1. Get free API key: https://elevenlabs.io
2. Install packages: `pip install elevenlabs pygame`
3. Set env var: `setx ELEVENLABS_API_KEY "your_key"`
4. Restart terminal

### Custom Voice?
1. Go to ElevenLabs
2. Create or rename voice to "Saraphina"
3. Restart terminal - auto-detected!

---

**Version**: 3.0 Voice Edition  
**Status**: 🟢 Production Ready  
**Voice**: 🎤 ElevenLabs Integrated  
**UI**: 🎨 VJR-Style Beautiful
