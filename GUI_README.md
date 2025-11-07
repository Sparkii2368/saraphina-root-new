# Saraphina Ultra GUI - Mission Control Interface

## 🚀 Features

### ✅ Stable Futuristic Interface
- **No terminal glitching** - Proper windowed GUI application
- **Dark futuristic theme** - Cyan/magenta neon accents
- **Smooth animations** - Pulsing status indicators
- **Modern layout** - Conversation panel + status sidebar

### ✅ Always-On Voice Listening
- **Background listening** - Saraphina constantly listens for wake word
- **Say "Saraphina" then speak** - Natural conversation flow
- **Auto-response** - She speaks back automatically
- **Barge-in support** - Interrupt her by speaking

### ✅ Full AI Integration
- **Enhanced AI Core** - Persistent learning, Level/XP system
- **Ultra AI Core** - Meta-learning, emotional intelligence, code generation
- **Knowledge Engine** - Remembers conversations and facts
- **Memory Manager** - Semantic memory recall
- **Trust & Security** - Firewall, ethical reasoning

### ✅ Additional Features
- **Settings Panel** - Configure name, wake word, voice
- **Chat History** - View past conversations
- **Animated Status** - Live XP, Level, KB stats
- **Voice indicators** - Visual feedback for listening/speaking

## 🎯 How to Use

### Launch
Double-click: `Launch Saraphina GUI.bat`

Or run directly:
```bash
python saraphina_gui.py
```

### Interact
1. **Type** - Enter text in the input box and press Enter or click SEND
2. **Speak** - Say "Saraphina" followed by your question
3. **Settings** - Click the ⚙ icon in the status panel
4. **History** - Click "📜 View Chat History" button

### Voice Commands
- "Saraphina, what's the weather?"
- "Saraphina, help me with Python code"
- "Saraphina, remind me to call John at 3:00"

## 🛠️ Technical Details

### Requirements
- Python 3.8+
- Tkinter (included with Python)
- All Saraphina dependencies (see main README)

### Components Used
- **GUI Framework**: Tkinter
- **Voice**: ElevenLabs TTS + Whisper STT
- **AI**: Enhanced AI + Ultra AI Core
- **Database**: SQLite with Knowledge Engine
- **Threading**: Background voice processing

### Architecture
```
SaraphinaGUI
├── Main Window (Tkinter)
├── Conversation Panel (ScrolledText)
├── Status Sidebar (Stats + Controls)
├── Input Area (Entry + Send Button)
├── Background Voice Thread (Always Listening)
├── AI Processing Threads (Non-blocking)
└── Animation Loop (Status Pulse)
```

## 🎨 Customization

### Colors
Edit `self.colors` in `saraphina_gui.py`:
```python
self.colors = {
    'bg': '#0a0e1a',       # Background
    'accent': '#00d9ff',   # Cyan
    'accent2': '#ff00ff',  # Magenta
    ...
}
```

### Wake Word
Change in Settings panel or directly:
```python
set_preference(conn, 'wake_word', 'hey sara')
```

## ⚠️ Known Limitations

1. **Database Threading** - SQLite access limited to main thread for stability
2. **Voice Latency** - ~1-2 second delay for Whisper processing
3. **Memory** - Full conversation history stored in memory during session

## 🔧 Troubleshooting

### GUI doesn't open
- Check Python installed: `python --version`
- Verify Tkinter: `python -c "import tkinter"`

### Voice not working
- Check microphone permissions
- Verify ElevenLabs API key in `.env`
- Test STT: `python -c "from saraphina.stt import STT; print(STT().available)"`

### Crashes on startup
- Check logs in console
- Verify `ai_data` directory exists
- Run: `python saraphina_gui.py` from terminal for errors

## 📝 Future Enhancements

- [ ] Web-based GUI (FastAPI + React)
- [ ] Multiple conversation tabs
- [ ] Voice input volume indicator
- [ ] Export conversation history
- [ ] Dark/Light theme toggle
- [ ] Customizable shortcuts

## 🎉 Success!

The GUI provides a **stable, professional, futuristic interface** for Saraphina without terminal glitching. Enjoy your AI mission control!
