#!/usr/bin/env python3

import logging
import tkinter as tk
from dataclasses import dataclass
from typing import Optional
from saraphina.stt_listener import STTListener

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@dataclass
class SaraphinaGUI:
    root: tk.Tk
    message_entry: tk.Entry
    stt_listener: Optional[STTListener] = None

    def __init__(self, root: tk.Tk):
        """Initialize the Saraphina GUI with STT integration."""
        self.root = root
        self.message_entry = tk.Entry(self.root)
        self.message_entry.pack()

        # Initialize STTListener
        try:
            self.stt_listener = STTListener(self._on_speech_detected)
            self.stt_listener.start_listening()
            self.log_message("[SYSTEM] 🎤 Voice input active - speak naturally")
        except Exception as e:
            logging.error(f"Failed to initialize STTListener: {e}")
            self.log_message("[ERROR] Failed to activate voice input")

        # Set up window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _on_speech_detected(self, text: str):
        """Handle speech input from STT."""
        try:
            self.message_entry.delete(0, tk.END)
            self.message_entry.insert(0, text)
            # Optionally auto-send
            # self.send_message()
        except Exception as e:
            logging.error(f"Error handling speech input: {e}")

    def log_message(self, message: str):
        """Log a message to the GUI or console."""
        logging.info(message)

    def on_close(self):
        """Handle the window close event."""
        if self.stt_listener:
            try:
                self.stt_listener.stop_listening()
            except Exception as e:
                logging.error(f"Failed to stop STTListener: {e}")
        self.root.destroy()

def main():
    root = tk.Tk()
    app = SaraphinaGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()