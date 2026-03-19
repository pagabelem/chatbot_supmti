"""
Service de transcription vocale (Speech-to-Text) — Version finale
Corrections appliquées :
  - Prompt Whisper neutre et court (ne répète plus le nom de l'école)
  - Prompt darija en alphabet latin pour forcer la romanisation
  - Auto-détection langue par défaut (language=None → Whisper décide)
  - transcribe_verbose() pour récupérer la langue détectée
  - Gestion propre des fichiers temporaires
"""
import openai
import os
from typing import Optional, Dict, Any
import tempfile
import time
from pathlib import Path
from app.core.logging import logger
from dotenv import load_dotenv

load_dotenv()


class STTService:
    """Service de transcription vocale — FR / EN / Darija"""

    SUPPORTED_FORMATS = ['.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm', '.ogg']

    LANGUAGE_CODES = {
        'fr': 'french',
        'en': 'english',
        'ar': 'darija',
    }

    # Codes langue acceptés par Whisper
    WHISPER_LANGUAGE_CODES = {
        'fr': 'fr',
        'en': 'en',
        'ar': 'ar',
    }

    # ------------------------------------------------------------------ #
    # PROMPTS DE STYLE WHISPER — courts, neutres, sans nom d'école        #
    # Le prompt darija est en alphabet latin pour que Whisper romanise    #
    # (Whisper continue dans le style du prompt → darija latin en sortie) #
    # ------------------------------------------------------------------ #
    WHISPER_STYLE_PROMPTS = {
        'fr': "Bonjour, voici ma question sur les formations.",
        'en': "Hello, here is my question about the programs.",
        'ar': "Salam, bghit nssewel 3la les filières. Wach kayn chi programme f informatique?",
        None: "Hello.",
    }

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("❌ OPENAI_API_KEY manquante dans .env")
            raise ValueError("OPENAI_API_KEY manquante")

        masked = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
        logger.info(f"🔑 Clé API OpenAI: {masked}")

        try:
            self.client = openai.OpenAI(api_key=api_key, timeout=120.0, max_retries=3)
            self.client.models.list()
            logger.info("✅ Client OpenAI initialisé")
        except Exception as e:
            logger.error(f"❌ Erreur OpenAI init: {e}")
            raise

        self.darija_available = False

    # ------------------------------------------------------------------ #
    # TRANSCRIPTION PRINCIPALE                                            #
    # ------------------------------------------------------------------ #
    async def transcribe(
        self,
        audio_file: bytes,
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        temperature: float = 0.0,
    ) -> str:
        """
        Transcrit un fichier audio.

        Args:
            audio_file  : bytes de l'audio
            language    : 'fr' | 'en' | 'ar' | None (None = auto-détection Whisper)
            prompt      : prompt de style optionnel (court, sans noms propres)
            temperature : 0.0 = précis, 0.2 = un peu plus souple

        Returns:
            Texte transcrit (str)
        """
        start_time = time.time()
        req_id = f"stt_{int(time.time())}"
        logger.info(f"🎤 [{req_id}] Transcription — {len(audio_file)} bytes, langue={language!r}")

        if len(audio_file) < 100:
            logger.warning(f"⚠️ [{req_id}] Fichier trop court")
            return ""

        suffix = self._detect_format(audio_file)
        tmp_path = None

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(audio_file)
                tmp_path = tmp.name

            # None = auto-détection Whisper (ne pas forcer la langue)
            whisper_lang = self.WHISPER_LANGUAGE_CODES.get(language) if language else None

            # Prompt de style court et neutre
            if prompt:
                style_prompt = prompt
            else:
                style_prompt = self.WHISPER_STYLE_PROMPTS.get(language, self.WHISPER_STYLE_PROMPTS[None])

            logger.info(f"🌐 [{req_id}] whisper_lang={whisper_lang!r} | prompt={style_prompt!r}")

            with open(tmp_path, "rb") as f:
                params: Dict[str, Any] = {
                    "model":           "whisper-1",
                    "file":            f,
                    "response_format": "text",
                    "temperature":     temperature,
                    "prompt":          style_prompt,
                }
                if whisper_lang:
                    params["language"] = whisper_lang

                transcript = self.client.audio.transcriptions.create(**params)

            elapsed = time.time() - start_time
            result  = str(transcript).strip()
            logger.info(f"✅ [{req_id}] OK en {elapsed:.2f}s — résultat: {result[:80]!r}")
            return result

        except Exception as e:
            logger.error(f"❌ [{req_id}] Erreur transcription: {e}")
            raise
        finally:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

    # ------------------------------------------------------------------ #
    # AUTO-DÉTECTION (langue inconnue)                                    #
    # ------------------------------------------------------------------ #
    async def transcribe_with_detection(self, audio_file: bytes) -> Dict[str, Any]:
        """Transcrit en laissant Whisper détecter la langue automatiquement."""
        start  = time.time()
        req_id = f"stt_auto_{int(time.time())}"
        logger.info(f"🔍 [{req_id}] Auto-détection langue")

        text = await self.transcribe(audio_file, language=None)

        return {
            "text":            text,
            "language":        "auto",
            "language_full":   "auto-détecté par Whisper",
            "duration":        0,
            "processing_time": round(time.time() - start, 2),
            "source":          "openai-whisper",
            "request_id":      req_id,
        }

    # ------------------------------------------------------------------ #
    # VERBOSE — récupère la langue détectée par Whisper                   #
    # ------------------------------------------------------------------ #
    async def transcribe_verbose(self, audio_file: bytes) -> Dict[str, Any]:
        """
        Transcrit avec verbose_json pour récupérer la langue détectée.
        Utilisé par chat_adaptive.py quand aucune langue n'est forcée,
        pour afficher le badge de langue dans le frontend.
        """
        start  = time.time()
        req_id = f"stt_verbose_{int(time.time())}"

        if len(audio_file) < 100:
            return {
                "text":            "",
                "language":        "unknown",
                "processing_time": 0,
                "source":          "error",
                "request_id":      req_id,
            }

        suffix   = self._detect_format(audio_file)
        tmp_path = None

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(audio_file)
                tmp_path = tmp.name

            with open(tmp_path, "rb") as f:
                response = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    response_format="verbose_json",
                    temperature=0.0,
                    prompt="Hello.",  # prompt neutre minimal
                )

            detected = getattr(response, "language", "unknown")
            logger.info(f"✅ [{req_id}] Langue détectée par Whisper: {detected!r}")

            return {
                "text":            response.text.strip(),
                "language":        detected,
                "language_full":   self.get_language_name(detected),
                "duration":        getattr(response, "duration", 0),
                "processing_time": round(time.time() - start, 2),
                "source":          "openai-whisper-verbose",
                "request_id":      req_id,
            }

        except Exception as e:
            logger.error(f"❌ [{req_id}] Erreur verbose: {e}")
            raise
        finally:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

    # ------------------------------------------------------------------ #
    # UTILITAIRES                                                         #
    # ------------------------------------------------------------------ #
    def _detect_language_from_audio(self, audio_file: bytes) -> Optional[str]:
        """
        Retourne None → Whisper auto-détecte.
        Ne jamais retourner 'fr' en dur ici.
        """
        return None

    def _detect_format(self, audio_file: bytes) -> str:
        """Détecte le format audio par magic bytes."""
        if len(audio_file) < 12:
            return ".ogg"
        if audio_file.startswith(b'RIFF') and audio_file[8:12] == b'WAVE':
            return ".wav"
        if audio_file.startswith(b'\xff\xfb') or audio_file.startswith(b'ID3'):
            return ".mp3"
        if audio_file.startswith(b'\x1a\x45\xdf\xa3'):
            return ".webm"
        if audio_file.startswith(b'OggS'):
            return ".ogg"
        if audio_file[4:8] == b'ftyp':
            return ".m4a"
        return ".ogg"

    def get_language_name(self, lang_code: str) -> str:
        """Retourne le nom complet de la langue."""
        names = {
            'fr':      'français',
            'french':  'français',
            'en':      'english',
            'english': 'english',
            'ar':      'darija / arabe',
            'arabic':  'darija / arabe',
            'auto':    'auto-détecté',
            'unknown': 'inconnu',
        }
        return names.get((lang_code or '').lower(), lang_code)

    def get_supported_languages(self) -> Dict[str, str]:
        return {
            'fr':   'français',
            'en':   'english',
            'ar':   'darija (arabe)',
            'auto': 'auto-détection Whisper',
        }

    async def test_connection(self) -> Dict[str, Any]:
        """Teste la connexion OpenAI et retourne un rapport de santé."""
        result: Dict[str, Any] = {
            "success":             True,
            "supported_languages": self.get_supported_languages(),
            "whisper_supported":   True,
            "darija_available":    self.darija_available,
        }
        try:
            t0 = time.time()
            self.client.models.list()
            result["openai_available"]     = True
            result["openai_response_time"] = round(time.time() - t0, 2)
        except Exception as e:
            result["openai_available"] = False
            result["openai_error"]     = str(e)
            result["success"]          = False
        return result