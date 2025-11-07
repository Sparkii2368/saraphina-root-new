#!/usr/bin/env python3
"""
Speech-to-Text (STT) integration.
Backends:
- speech_recognition + openai-whisper (recognize_whisper)
- speech_recognition + Google (fallback, network)
If dependencies missing, returns None and logs guidance.
"""
import logging
from typing import Optional, Callable

logger = logging.getLogger("Saraphina_STT")

try:
    import webrtcvad
    _VAD_AVAILABLE = True
except Exception:
    _VAD_AVAILABLE = False

try:
    import speech_recognition as sr  # requires PyAudio or compatible
    SR_AVAILABLE = True
except Exception:
    SR_AVAILABLE = False
    logger.warning("speech_recognition not available - install with: pip install SpeechRecognition pyaudio")

# Optional local faster-whisper backend
try:
    from faster_whisper import WhisperModel
    _FW_AVAILABLE = True
except Exception:
    _FW_AVAILABLE = False


class STT:
    def __init__(self):
        self.available = SR_AVAILABLE
        self._rec = sr.Recognizer() if SR_AVAILABLE else None
        self._bg_stop = None

    def _recognize_audio(self, audio, engine: str = "whisper") -> Optional[str]:
        # Prefer offline whisper if available
        if engine == "whisper":
            try:
                text = self._rec.recognize_whisper(audio, model="base")  # requires openai-whisper
                return text.strip()
            except Exception:
                pass
        try:
            text = self._rec.recognize_google(audio)
            return text.strip()
        except Exception:
            return None

    def transcribe_once(self, timeout: int = 5, phrase_time_limit: int = 10, engine: str = "whisper") -> Optional[str]:
        """Capture one utterance from microphone and transcribe."""
        if not self.available:
            return None
        try:
            with sr.Microphone() as source:
                self._rec.adjust_for_ambient_noise(source, duration=0.5)
                audio = self._rec.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            if engine == 'faster' and _FW_AVAILABLE:
                # write wav temp and run faster-whisper
                import tempfile, os
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                tmp.write(audio.get_wav_data())
                tmp.close()
                try:
                    model = WhisperModel("base", compute_type="int8")
                    segments, _info = model.transcribe(tmp.name)
                    text = " ".join(s.text for s in segments).strip()
                    os.unlink(tmp.name)
                    return text or None
                except Exception:
                    try:
                        os.unlink(tmp.name)
                    except Exception:
                        pass
                    return self._recognize_audio(audio, engine='whisper')
            else:
                return self._recognize_audio(audio, engine=engine)
        except Exception:
            return None

    def _is_speech(self, audio) -> bool:
        if not _VAD_AVAILABLE:
            return True
        try:
            vad = webrtcvad.Vad(2)
            raw = audio.get_raw_data(convert_rate=16000, convert_width=2)
            # 20ms frames
            frame_len = int(16000 * 0.02) * 2
            if len(raw) < frame_len:
                return True
            voiced = 0
            total = 0
            for i in range(0, len(raw) - frame_len, frame_len):
                chunk = raw[i:i+frame_len]
                total += 1
                if vad.is_speech(chunk, 16000):
                    voiced += 1
            return voiced >= max(1, total // 3)
        except Exception:
            return True

    def start_background(self, callback, engine: str = "whisper", wake_word: Optional[str] = None):
        """Start background listening; callback(text) is called per phrase.
        Returns True if started. Use stop_background() to stop.
        """
        if not self.available or self._bg_stop is not None:
            return False
        try:
            import time
            def _cb(recognizer, audio):
                try:
                    if not self._is_speech(audio):
                        return
                    text = self._recognize_audio(audio, engine=engine)
                    if not text:
                        return
                    t = text.strip()
                    if wake_word:
                        if wake_word.lower() not in t.lower():
                            return
                        # strip wake word
                        idx = t.lower().find(wake_word.lower())
                        if idx != -1:
                            t = (t[:idx] + t[idx+len(wake_word):]).strip()
                    if t:
                        callback(t)
                except Exception:
                    pass
            self._bg_stop = self._rec.listen_in_background(sr.Microphone(), _cb, phrase_time_limit=10)
            return True
        except Exception:
            self._bg_stop = None
            return False

    def stop_background(self):
        if self._bg_stop:
            try:
                self._bg_stop(wait_for_stop=False)
            except Exception:
                pass
            self._bg_stop = None
