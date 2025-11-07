#!/usr/bin/env python3

import logging
import threading
import speech_recognition as sr
from typing import Callable

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class STTListener:
    """
    A class to handle speech-to-text listening using the Google Speech Recognition API.
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

    def start_listening(self) -> None:
        """
        Start the background listening thread.
        """
        if self.listening_thread is None or not self.listening_thread.is_alive():
            logging.info("Starting the listening thread.")
            self.stop_listening_event.clear()
            self.listening_thread = threading.Thread(target=self._listen_loop, daemon=True)
            self.listening_thread.start()

    def stop_listening(self) -> None:
        """
        Stop the listening thread gracefully.
        """
        if self.listening_thread and self.listening_thread.is_alive():
            logging.info("Stopping the listening thread.")
            self.stop_listening_event.set()
            self.listening_thread.join()

    def _listen_loop(self) -> None:
        """
        The main loop that listens for speech and processes it.
        """
        with self.microphone as source:
            logging.info("Adjusting for ambient noise.")
            self.recognizer.adjust_for_ambient_noise(source)

        while not self.stop_listening_event.is_set():
            try:
                with self.microphone as source:
                    logging.info("Listening for speech.")
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)

                logging.info("Recognizing speech.")
                text = self.recognizer.recognize_google(audio)
                logging.info(f"Recognized speech: {text}")
                self.callback_function(text)

            except sr.UnknownValueError:
                logging.warning("Google Speech Recognition could not understand audio.")
            except sr.RequestError as e:
                logging.error(f"Could not request results from Google Speech Recognition service; {e}")
            except Exception as e:
                logging.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    def on_speech(text: str) -> None:
        """
        Example callback function to process recognized speech.

        :param text: The recognized speech as text.
        """
        print(f"Recognized text: {text}")

    listener = STTListener(on_speech)
    listener.start_listening()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        listener.stop_listening()
        logging.info("Listener stopped.")