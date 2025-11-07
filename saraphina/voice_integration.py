#!/usr/bin/env python3
"""
Saraphina Voice Integration with ElevenLabs
Integrates ElevenLabs voice system for natural voice interactions
"""

import os
import asyncio
import logging
import tempfile
import time
import uuid
import hashlib
from pathlib import Path
from typing import Optional

try:
    import requests
    REQUESTS_AVAILABLE = True
except Exception:
    REQUESTS_AVAILABLE = False

logger = logging.getLogger("Saraphina_Voice")

# Try to import required modules
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    logger.warning("⚠️  pygame not available - voice playback disabled")

try:
    from elevenlabs import generate, save, set_api_key, voices
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False
    logger.warning("⚠️  elevenlabs not available - install with: pip install elevenlabs")


class SaraphinaVoice:
    """ElevenLabs voice integration for Saraphina"""
    
    def __init__(self):
        self.voice_id = None
        self.api_key = None
        self.voice_available = False
        self.pygame_initialized = False
        # Prefer app-local temp dir to avoid permission issues
        app_root = Path(__file__).resolve().parents[1]
        self.temp_dir = Path(os.getenv('SARAPHINA_VOICE_DIR', str(app_root / 'voice_tmp')))
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        # runtime voice settings (editable at runtime)
        self.settings = {
            'stability': float(os.getenv('ELEVEN_STABILITY', os.getenv('ELEVENLABS_STABILITY', '0.5')) or 0.5),
            'similarity': float(os.getenv('ELEVEN_SIMILARITY', os.getenv('ELEVENLABS_SIMILARITY', '0.7')) or 0.7),
            'style': float(os.getenv('ELEVEN_STYLE', '0.6') or 0.6),
            'speaker_boost': (os.getenv('ELEVEN_SPEAKER_BOOST', 'true').lower() in ['1','true','yes','on']),
            'pace': float(os.getenv('ELEVEN_PACE', '1.0') or 1.0),  # >1 slower, <1 faster (heuristic)
        }
        # runtime toggle for REST engine
        self.use_rest = (os.getenv('ELEVENLABS_USE_REST', 'false').lower() in ['1','true','yes','on'])
        
        if ELEVENLABS_AVAILABLE:
            self._initialize_elevenlabs()
        
        if PYGAME_AVAILABLE:
            self._initialize_pygame()
    
    def _initialize_elevenlabs(self):
        """Initialize ElevenLabs API"""
        try:
            # Get API key from environment
            self.api_key = os.getenv('ELEVENLABS_API_KEY')
            if not self.api_key:
                logger.warning("⚠️  ELEVENLABS_API_KEY not found in environment")
                logger.info("💡 Set it with: set ELEVENLABS_API_KEY=your_key_here")
                return
            
            # Set API key
            set_api_key(self.api_key)
            
            # Try to get Saraphina's voice
            try:
                voice_list = voices()
                # If explicit voice id/name provided via env, prefer it
                env_voice_id = os.getenv('ELEVENLABS_VOICE_ID')
                env_voice_name = os.getenv('ELEVENLABS_VOICE_NAME')
                if env_voice_id:
                    self.voice_id = env_voice_id
                    logger.info("✅ Using specified ElevenLabs voice_id from env")
                elif env_voice_name:
                    matches = [v for v in voice_list if env_voice_name.lower() in v.name.lower()]
                    if matches:
                        self.voice_id = matches[0].voice_id
                        logger.info(f"✅ Using specified voice by name: {matches[0].name}")
                if not self.voice_id:
                    # Look for Saraphina's custom voice
                    saraphina_voices = [v for v in voice_list if 'saraphina' in v.name.lower()]
                    if saraphina_voices:
                        self.voice_id = saraphina_voices[0].voice_id
                        logger.info(f"✅ Found Saraphina's custom voice: {saraphina_voices[0].name}")
                    else:
                        # Fallback to good female voices
                        fallback_names = ['rachel', 'bella', 'charlotte', 'sarah', 'elli']
                        fallback_voices = [v for v in voice_list if any(name in v.name.lower() for name in fallback_names)]
                        if fallback_voices:
                            self.voice_id = fallback_voices[0].voice_id
                            logger.info(f"✅ Using fallback voice: {fallback_voices[0].name}")
                        else:
                            # Use first available voice
                            self.voice_id = voice_list[0].voice_id
                            logger.info(f"✅ Using first available voice: {voice_list[0].name}")
                
                self.voice_available = True
                logger.info("🎤 ElevenLabs voice system initialized successfully")
                
            except Exception as e:
                logger.error(f"❌ Failed to get voice list: {e}")
                return
                
        except Exception as e:
            logger.error(f"❌ ElevenLabs initialization failed: {e}")
    
    def _initialize_pygame(self):
        """Initialize pygame for audio playback"""
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.pygame_initialized = True
            logger.info("🔊 Pygame audio system initialized")
        except Exception as e:
            logger.error(f"❌ Pygame initialization failed: {e}")
    
    def set_settings(self, **kwargs):
        """Update runtime voice settings (stability, similarity, style, speaker_boost, pace)."""
        for k, v in kwargs.items():
            if k in self.settings:
                self.settings[k] = v
        
    def set_use_rest(self, flag: bool):
        self.use_rest = bool(flag)
        
    def preset(self, name: str):
        """Apply a preset profile."""
        n = name.lower()
        if n in ['slow','slower']:
            self.set_settings(pace=1.3, stability=0.4, style=0.7)
        elif n in ['fast','faster']:
            self.set_settings(pace=0.85, stability=0.6, style=0.5)
        elif n in ['natural','more natural']:
            self.set_settings(stability=0.45, similarity=0.85, style=0.6)
        elif n in ['emotional','more emotional','expressive']:
            self.set_settings(stability=0.35, style=0.85)
        elif n in ['warm','softer','gentle']:
            self.set_settings(stability=0.4, style=0.7)
        elif n in ['cheerful','happy']:
            self.set_settings(style=0.85)
        
    def _apply_pace(self, text: str) -> str:
        """Heuristic: add commas to slow down; minimal changes to speed up not implemented."""
        pace = self.settings.get('pace', 1.0)
        if pace <= 1.05:
            return text
        words = text.split()
        if len(words) < 6:
            return text
        step = max(4, int(6 * (pace / 1.0)))
        out = []
        for i, w in enumerate(words, 1):
            out.append(w)
            if i % step == 0:
                out.append(',')
        return ' '.join(out)
        
    def _cache_path(self, text: str) -> Path:
        key = f"{self.voice_id}|{self.settings.get('stability')}|{self.settings.get('similarity')}|{self.settings.get('style')}|{self.settings.get('speaker_boost')}|{self.settings.get('pace')}|{text}"
        h = hashlib.sha1(key.encode('utf-8')).hexdigest()
        return self.temp_dir / f"tts_{h}.mp3"

    def _rest_generate_to_file(self, text: str, dest: Optional[Path] = None) -> Optional[str]:
        if not (REQUESTS_AVAILABLE and self.api_key and self.voice_id):
            return None
        try:
            model = os.getenv('ELEVENLABS_MODEL', 'eleven_monolingual_v1')
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
            headers = {
                'xi-api-key': self.api_key,
                'accept': 'audio/mpeg',
                'Content-Type': 'application/json'
            }
            body = {
                'text': text,
                'model_id': model
            }
            # Voice settings from runtime
            body['voice_settings'] = {
                'stability': float(self.settings.get('stability', 0.5)),
                'similarity_boost': float(self.settings.get('similarity', 0.7)),
                'style': float(self.settings.get('style', 0.6)),
                'use_speaker_boost': bool(self.settings.get('speaker_boost', True)),
            }
            r = requests.post(url, headers=headers, json=body, timeout=30)
            r.raise_for_status()
            # write to cache or temp
            target = dest or self._cache_path(text)
            with open(target, 'wb') as f:
                f.write(r.content)
            return str(target)
        except Exception as e:
            logger.error(f"❌ REST TTS failed: {e}")
            return None

    def _sanitize_for_speech(self, text: str) -> str:
        """Remove noisy symbols so TTS doesn't say 'underscore' or 'equals sign'."""
        try:
            import re
            # Remove bracketed system tags and ASCII bars
            text = re.sub(r"\[[^\]]+\]", " ", text)
            text = re.sub(r"[=_\-]{2,}", " ", text)
            # Remove standalone '=' signs
            text = text.replace('=', ' ')
            # Replace underscores with spaces
            text = text.replace('_', ' ')
            # Collapse multiple spaces
            text = re.sub(r"\s{2,}", " ", text)
            return text.strip()
        except Exception:
            return text
    
    def speak_sync(self, text: str, play_immediately: bool = True) -> Optional[str]:
        """Generate and optionally play speech synchronously"""
        if not self.voice_available:
            logger.warning("⚠️  Voice not available")
            return None
        
        # Sanitize text to avoid reading symbols
        text = self._sanitize_for_speech(text)
        
        # Choose method: REST preferred if enabled or if SDK fails
        use_rest_env = os.getenv('ELEVENLABS_USE_REST', 'false').lower() in ['1','true','yes','on']
        use_rest = self.use_rest or use_rest_env
        temp_path: Optional[str] = None
        
        cache_file = self._cache_path(self._apply_pace(text))
        if cache_file.exists():
            temp_path = str(cache_file)
        else:
            if not use_rest:
                try:
                    # Generate audio via SDK
                    audio_data = generate(
                        text=self._apply_pace(text),
                        voice=self.voice_id,
                        model=os.getenv('ELEVENLABS_MODEL', 'eleven_monolingual_v1')
                    )
                    save(audio_data, str(cache_file))
                    temp_path = str(cache_file)
                except Exception as e:
                    logger.warning(f"SDK TTS failed, falling back to REST: {e}")
                    temp_path = self._rest_generate_to_file(self._apply_pace(text), dest=cache_file)
            else:
                temp_path = self._rest_generate_to_file(self._apply_pace(text), dest=cache_file)
        
        if not temp_path:
            return None
        
        try:
            if play_immediately and self.pygame_initialized:
                self._play_audio_sync(temp_path)
            return temp_path
        except PermissionError:
            # Retry with new filename in a different dir if permission issue occurs
            alt_dir = self.temp_dir / 'alt'
            alt_dir.mkdir(exist_ok=True)
            alt_file = str(alt_dir / f"saraphina_{uuid.uuid4().hex}.mp3")
            try:
                os.replace(temp_path, alt_file)
                if play_immediately and self.pygame_initialized:
                    self._play_audio_sync(alt_file)
                return alt_file
            except Exception as e:
                logger.error(f"❌ Audio playback failed after retry: {e}")
                return None
        except Exception as e:
            logger.error(f"❌ Audio playback failed: {e}")
            return None
    
    async def speak_async(self, text: str, play_immediately: bool = True) -> Optional[str]:
        """Generate and optionally play speech asynchronously"""
        if not self.voice_available:
            logger.warning("⚠️  Voice not available")
            return None
        
        text = self._sanitize_for_speech(text)
        
        try:
            # Generate audio in a thread to avoid blocking
            loop = asyncio.get_event_loop()
            audio_data = await loop.run_in_executor(
                None, 
                lambda: generate(
                    text=text,
                    voice=self.voice_id,
                    model="eleven_monolingual_v1"
                )
            )
            
            # Save to temp file
            temp_file = self.temp_dir / f"saraphina_{abs(hash(text)) % 10000}.mp3"
            await loop.run_in_executor(
                None,
                lambda: save(audio_data, str(temp_file))
            )
            
            if play_immediately and self.pygame_initialized:
                await self._play_audio_async(str(temp_file))
            
            return str(temp_file)
            
        except Exception as e:
            logger.error(f"❌ Async speech generation failed: {e}")
            return None

    def speak_stream(self, text: str) -> Optional[str]:
        """Optional streaming TTS; falls back to synchronous if streaming not supported."""
        try:
            # ElevenLabs streaming API may provide a generator; if unavailable, fallback
            return self.speak_sync(text, play_immediately=True)
        except Exception as e:
            logger.warning(f"Streaming not available: {e}")
            return self.speak_sync(text, play_immediately=True)
    
    def stop_playback(self):
        """Stop current playback if any"""
        try:
            if self.pygame_initialized and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
        except Exception:
            pass

    def _play_audio_sync(self, audio_file: str):
        """Play audio file synchronously"""
        try:
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()
            
            # Wait for playback to complete
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
                
        except Exception as e:
            logger.error(f"❌ Audio playback failed: {e}")
    
    async def _play_audio_async(self, audio_file: str):
        """Play audio file asynchronously"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._play_audio_sync, audio_file)
        except Exception as e:
            logger.error(f"❌ Async audio playback failed: {e}")
    
    def cleanup(self):
        """Cleanup temp files"""
        try:
            for temp_file in self.temp_dir.glob("saraphina_*.mp3"):
                temp_file.unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"⚠️  Cleanup warning: {e}")


# Global voice instance
_global_voice_instance = None

def get_voice() -> SaraphinaVoice:
    """Get global voice instance"""
    global _global_voice_instance
    if _global_voice_instance is None:
        _global_voice_instance = SaraphinaVoice()
    return _global_voice_instance

def speak_text(text: str, play_immediately: bool = True) -> Optional[str]:
    """Quick function to make Saraphina speak"""
    voice = get_voice()
    return voice.speak_sync(text, play_immediately)

async def speak_text_async(text: str, play_immediately: bool = True) -> Optional[str]:
    """Quick async function to make Saraphina speak"""
    voice = get_voice()
    return await voice.speak_async(text, play_immediately)
