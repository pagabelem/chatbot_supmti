"""
Service de synthèse vocale (Text-to-Speech) avec cache
"""
from gtts import gTTS
import io
import os
import hashlib
from typing import Optional
import asyncio
from pathlib import Path

class TTSService:
    """Service de synthèse vocale avec cache"""
    
    SUPPORTED_LANGUAGES = {
        'fr': 'Français',
        'en': 'English',
        'ar': 'العربية',
        'es': 'Español',
        'de': 'Deutsch'
    }
    
    def __init__(self, cache_dir: str = "cache/tts"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, text: str, lang: str, slow: bool) -> str:
        """Génère une clé de cache unique"""
        content = f"{text}:{lang}:{slow}".encode('utf-8')
        return hashlib.md5(content).hexdigest()
    
    async def synthesize(self, text: str, lang: str = 'fr', slow: bool = False) -> bytes:
        """
        Synthétise du texte en audio (avec cache)
        """
        if lang not in self.SUPPORTED_LANGUAGES:
            lang = 'fr'
        
        # Vérifier le cache
        cache_key = self._get_cache_key(text, lang, slow)
        cache_file = self.cache_dir / f"{cache_key}.mp3"
        
        if cache_file.exists():
            # Retourner depuis le cache
            with open(cache_file, 'rb') as f:
                return f.read()
        
        # Générer l'audio
        loop = asyncio.get_event_loop()
        audio_bytes = await loop.run_in_executor(
            None, self._synthesize_sync, text, lang, slow
        )
        
        # Sauvegarder dans le cache
        with open(cache_file, 'wb') as f:
            f.write(audio_bytes)
        
        return audio_bytes
    
    def _synthesize_sync(self, text: str, lang: str, slow: bool) -> bytes:
        """Version synchrone de la synthèse"""
        tts = gTTS(text=text, lang=lang, slow=slow)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        return audio_buffer.read()