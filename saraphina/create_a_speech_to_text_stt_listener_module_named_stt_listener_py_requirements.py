#!/usr/bin/env python3

import threading
import logging
import speech_recognition as sr
from typing import Callable

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class STTListener:
    """
    A Speech-to-Text listener module that uses the speech_recognition library
    to convert spoken language into text using Google Speech Recognition.
    """

    def __init__(self, callback_function: Callable[[str], None]) -> None:
        """
        Initialize the STTListener with a callback function.

        :param callback_function: A function to call with the recognized text.
        """
        self.callback_function = callback_function
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.listening_thread = None
        self.stop_listening_event = threading.Event()
        logging.debug("STTListener initialized.")

    def start_listening(self) -> None:
        """
        Start the background thread for listening to speech.
        """
        if self.listening_thread is None or not self.listening_thread.is_alive():
            self.stop_listening_event.clear()
            self.listening_thread = threading.Thread(target=self._listen_loop, daemon=True)
            self.listening_thread.start()
            logging.info("Started listening for speech.")

    def stop_listening(self) -> None:
        """
        Stop the listening thread gracefully.
        """
        if self.listening_thread is not None:
            self.stop_listening_event.set()
            self.listening_thread.join()
            logging.info("Stopped listening for speech.")

    def _listen_loop(self) -> None:
        """
        The main loop that listens for speech and processes it.
        """
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
            logging.debug("Adjusted for ambient noise.")

            while not self.stop_listening_event.is_set():
                try:
                    logging.debug("Listening for speech...")
                    audio = self.recognizer.listen(source, timeout=5)
                    logging.debug("Audio captured, processing...")
                    text = self.recognizer.recognize_google(audio)
                    logging.info(f"Recognized speech: {text}")
                    self.callback_function(text)
                except sr.UnknownValueError:
                    logging.warning("Could not understand audio.")
                except sr.RequestError as e:
                    logging.error(f"Could not request results from Google Speech Recognition service; {e}")
                except Exception as e:
                    logging.error(f"An unexpected error occurred: {e}")

# Example usage:
# def on_speech(text):
#     print(f"Recognized: {text}")
#
# listener = STTListener(on_speech)
# listener.start_listening()
# # To stop listening, call listener.stop_listening()