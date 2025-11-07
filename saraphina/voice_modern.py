#!/usr/bin/env python3
"""
Modern ElevenLabs Voice Integration - Uses new client API
"""

import os
import logging
from pathlib import Path
from typing import Optional

# Load .env files
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / '.env')
except:
    pass

logger = logging.getLogger("Saraphina_Voice")

# Try imports
try:
    import pygame
    PYGAME_AVAILABLE = True
except:
    PYGAME_AVAILABLE = False
    logger.warning("pygame not available")

try:
    from elevenlabs.client import ElevenLabs
    ELEVENLABS_AVAILABLE = True
except:
    ELEVENLABS_AVAILABLE = False
    logger.warning("elevenlabs not available")

VOICE_AVAILABLE = ELEVENLABS_AVAILABLE and PYGAME_AVAILABLE


class ModernVoice:
    """Modern ElevenLabs voice using new client API"""
    
    def __init__(self):
        self.client = None
        self.voice_id = None
        self.available = False
        self.mixer_initialized = False
        
        # Initialize pygame mixer
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
                self.mixer_initialized = True
            except:
                pass
        
        if not ELEVENLABS_AVAILABLE:
            return
        
        # Get API key
        api_key = os.getenv('ELEVENLABS_API_KEY')
        if not api_key:
            logger.warning("ELEVENLABS_API_KEY not set")
            return
        
        try:
            # Initialize client
            self.client = ElevenLabs(api_key=api_key)
            
            # Get voice ID from env or use Rachel as default
            self.voice_id = os.getenv('ELEVENLABS_VOICE_ID', 'EXAVITQu4vr4xnSDxMaL')  # Rachel
            
            self.available = True
            logger.info(f"✅ ElevenLabs voice initialized (voice_id: {self.voice_id[:8]}...)")
            
        except Exception as e:
            logger.error(f"Voice init failed: {e}")
    
    def speak(self, text: str):
        """Generate and play audio"""
        if not self.available or not self.client:
            logger.warning("Voice not available")
            return
        
        try:
            # Generate audio
            audio_stream = self.client.text_to_speech.convert(
                voice_id=self.voice_id,
                text=text,
                model_id="eleven_monolingual_v1"
            )
            
            # Save to temp file and play with pygame
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
                temp_path = f.name
                for chunk in audio_stream:
                    f.write(chunk)
            
            # Play with pygame
            if PYGAME_AVAILABLE:
                pygame.mixer.music.load(temp_path)
                pygame.mixer.music.play()
                # Wait for playback to finish
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
            
            # Cleanup
            try:
                import os
                os.unlink(temp_path)
            except:
                pass
            
        except Exception as e:
            logger.error(f"Speech failed: {e}")
    
    def stop_playback(self):
        """Stop current playback"""
        try:
            if PYGAME_AVAILABLE:
                pygame.mixer.music.stop()
        except:
            pass
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop_playback()


# Global instance
_voice_instance = None


def get_voice() -> ModernVoice:
    """Get or create voice instance"""
    global _voice_instance
    if _voice_instance is None:
        _voice_instance = ModernVoice()
    return _voice_instance


def speak_text(text: str):
    """Speak text using ElevenLabs"""
    voice = get_voice()
    voice.speak(text)


# Module-level availability flag
VOICE_AVAILABLE = ELEVENLABS_AVAILABLE and PYGAME_AVAILABLE
