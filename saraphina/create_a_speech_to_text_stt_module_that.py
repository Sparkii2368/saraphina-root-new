#!/usr/bin/env python3

import logging
import threading
import speech_recognition as sr
from dataclasses import dataclass
from typing import Callable
from pathlib import Path
from saraphina_gui import update_gui_with_text
from saraphina.db import save_transcription

# Configure logging
logging.basicConfig(
    filename=Path('D:/Saraphina Root/saraphina/logs/stt_module.log'),
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

@dataclass
class SpeechToTextConfig:
    wake_word: str = "saraphina"
    energy_threshold: int = 300
    pause_threshold: float = 0.8

class SpeechToText:
    def __init__(self, config: SpeechToTextConfig, on_text_callback: Callable[[str], None]):
        self.config = config
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.on_text_callback = on_text_callback
        self.listening = False

    def start_listening(self) -> None:
        """Start the background listening process."""
        self.listening = True
        threading.Thread(target=self._listen_in_background).start()
        logging.info("Started background listening.")

    def stop_listening(self) -> None:
        """Stop the background listening process."""
        self.listening = False
        logging.info("Stopped background listening.")

    def _listen_in_background(self) -> None:
        """Continuously listen in the background for the wake word."""
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
            logging.debug("Adjusted for ambient noise with energy threshold: %d", self.recognizer.energy_threshold)
            while self.listening:
                try:
                    logging.debug("Listening for wake word...")
                    audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=5)
                    logging.debug("Audio captured, processing...")
                    self._process_audio(audio)
                except sr.WaitTimeoutError:
                    logging.warning("Listening timed out, retrying...")
                except Exception as e:
                    logging.error("Error during listening: %s", str(e))

    def _process_audio(self, audio: sr.AudioData) -> None:
        """Process the captured audio and convert it to text."""
        try:
            text = self.recognizer.recognize_google(audio).lower()
            logging.debug("Recognized text: %s", text)
            if self.config.wake_word in text:
                logging.info("Wake word detected.")
                self.on_text_callback(text)
        except sr.UnknownValueError:
            logging.warning("Could not understand audio.")
        except sr.RequestError as e:
            logging.error("Could not request results from Google Speech Recognition service; %s", e)

def message_processing_system(text: str) -> None:
    """Process the transcribed text."""
    logging.info("Processing text: %s", text)
    update_gui_with_text(text)
    save_transcription(text)

if __name__ == "__main__":
    config = SpeechToTextConfig()
    stt = SpeechToText(config, message_processing_system)
    stt.start_listening()