"""
Service de transcription vocale (Speech-to-Text) avec OpenAI
Version améliorée avec support streaming, timeout augmenté et gestion d'erreurs réseau
"""
import openai
import os
from typing import Optional, Dict, Any, AsyncGenerator, List
import tempfile
import time
import asyncio
from pathlib import Path
from app.core.logging import logger
from dotenv import load_dotenv

# Charge les variables d'environnement
load_dotenv()

class STTService:
    """Service de transcription vocale utilisant OpenAI Whisper"""
    
    # Formats audio supportés par Whisper
    SUPPORTED_FORMATS = ['.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm', '.ogg']
    
    # Mapping des codes de langue
    LANGUAGE_CODES = {
        'fr': 'french',
        'en': 'english',
        'ar': 'arabic',
        'es': 'spanish',
        'de': 'german',
        'it': 'italian',
        'pt': 'portuguese',
        'nl': 'dutch',
        'pl': 'polish',
        'ru': 'russian',
        'zh': 'chinese',
        'ja': 'japanese',
        'ko': 'korean'
    }
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("❌ OPENAI_API_KEY non trouvée dans .env")
            raise ValueError("OPENAI_API_KEY manquante - Vérifie ton fichier .env")
        
        # Masquer partiellement la clé dans les logs
        masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
        logger.info(f"🔑 Clé API chargée: {masked_key}")
        
        try:
            # Initialiser le client avec timeout augmenté (120 secondes)
            self.client = openai.OpenAI(
                api_key=api_key,
                timeout=120.0,  # Augmenté à 120 secondes
                max_retries=3    # Plus de tentatives
            )
            
            # Test de connexion avec timeout
            logger.info("🔄 Test de connexion à OpenAI...")
            self.client.models.list()
            logger.info("✅ Client OpenAI initialisé avec succès pour STT")
            
        except openai.AuthenticationError as e:
            logger.error(f"❌ Erreur d'authentification OpenAI - Clé API invalide: {e}")
            raise ValueError("Clé API OpenAI invalide")
            
        except openai.RateLimitError as e:
            logger.error(f"❌ Quota OpenAI dépassé - Vérifie ton compte: {e}")
            raise ValueError("Quota OpenAI dépassé")
            
        except openai.APITimeoutError as e:
            logger.error(f"❌ Timeout OpenAI - Vérifie ta connexion internet: {e}")
            raise ConnectionError("Timeout de connexion à OpenAI - Vérifie ta connexion internet")
            
        except openai.APIConnectionError as e:
            logger.error(f"❌ Erreur de connexion OpenAI - Problème réseau: {e}")
            raise ConnectionError("Impossible de se connecter à OpenAI - Vérifie ta connexion internet")
            
        except Exception as e:
            logger.error(f"❌ Erreur inattendue lors de l'initialisation: {type(e).__name__}: {e}")
            raise
    
    async def transcribe(self, audio_file: bytes, language: Optional[str] = None, 
                         prompt: Optional[str] = None, temperature: float = 0.0) -> str:
        """
        Transcrit un fichier audio en texte
        
        Args:
            audio_file: Fichier audio en bytes
            language: Langue optionnelle (auto-détection si None)
            prompt: Prompt optionnel pour guider la transcription
            temperature: Température (0.0 = plus précis, 1.0 = plus créatif)
        
        Returns:
            Texte transcrit
        """
        start_time = time.time()
        request_id = f"stt_{int(time.time())}"
        logger.info(f"🎤 [{request_id}] Début transcription - Taille audio: {len(audio_file)} bytes")
        
        # Sauvegarder temporairement avec une extension appropriée
        suffix = self._detect_format(audio_file)
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(audio_file)
            tmp_path = tmp.name
            logger.info(f"📁 [{request_id}] Fichier temporaire créé: {tmp_path} ({len(audio_file)} bytes)")
        
        try:
            # Vérifier que le fichier n'est pas vide
            if len(audio_file) < 100:  # Moins de 100 bytes = trop petit
                logger.warning(f"⚠️ [{request_id}] Fichier audio trop petit, possiblement vide")
                return "Le fichier audio semble vide ou trop court"
            
            with open(tmp_path, "rb") as f:
                logger.info(f"🔄 [{request_id}] Envoi à l'API Whisper...")
                
                # Paramètres de la requête
                params = {
                    "model": "whisper-1",
                    "file": f,
                    "response_format": "text" if not language else None,
                    "timeout": 120.0,  # Timeout spécifique pour la requête
                    "temperature": temperature
                }
                
                # Ajouter la langue si spécifiée
                if language:
                    params["language"] = language
                
                # Ajouter le prompt si spécifié
                if prompt:
                    params["prompt"] = prompt
                
                transcript = self.client.audio.transcriptions.create(**params)
            
            elapsed = time.time() - start_time
            logger.info(f"✅ [{request_id}] Transcription réussie en {elapsed:.2f}s: {transcript[:50]}...")
            return transcript
            
        except openai.RateLimitError as e:
            logger.error(f"❌ [{request_id}] Quota OpenAI dépassé: {e}")
            return "❌ Quota OpenAI dépassé - Vérifie ton compte"
            
        except openai.APITimeoutError as e:
            logger.error(f"❌ [{request_id}] Timeout OpenAI: {e}")
            return "❌ Timeout - Vérifie ta connexion internet et réessaie"
            
        except openai.APIConnectionError as e:
            logger.error(f"❌ [{request_id}] Erreur de connexion OpenAI: {e}")
            return "❌ Problème de connexion - Vérifie ta connexion internet"
            
        except openai.APIError as e:
            logger.error(f"❌ [{request_id}] Erreur API OpenAI: {e}")
            return f"❌ Erreur API: {str(e)}"
            
        except Exception as e:
            logger.error(f"❌ [{request_id}] Erreur inattendue: {type(e).__name__}: {e}")
            raise
            
        finally:
            # Nettoyage
            try:
                os.unlink(tmp_path)
                logger.info(f"🗑️ [{request_id}] Fichier temporaire supprimé: {tmp_path}")
            except Exception as e:
                logger.warning(f"⚠️ [{request_id}] Impossible de supprimer le fichier temporaire: {e}")
    
    async def transcribe_with_detection(self, audio_file: bytes, prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Transcrit et détecte la langue automatiquement avec informations détaillées
        
        Returns:
            Dict avec texte, langue, durée, segments, et source
        """
        start_time = time.time()
        request_id = f"stt_detect_{int(time.time())}"
        logger.info(f"🎤 [{request_id}] Début transcription avec détection - Taille: {len(audio_file)} bytes")
        
        # Sauvegarder temporairement
        suffix = self._detect_format(audio_file)
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(audio_file)
            tmp_path = tmp.name
            logger.info(f"📁 [{request_id}] Fichier temporaire créé: {tmp_path}")
        
        try:
            with open(tmp_path, "rb") as f:
                logger.info(f"🔄 [{request_id}] Envoi à l'API Whisper (mode verbose)...")
                
                params = {
                    "model": "whisper-1",
                    "file": f,
                    "response_format": "verbose_json",
                    "timeout": 120.0,
                    "temperature": 0.0
                }
                
                if prompt:
                    params["prompt"] = prompt
                
                transcript = self.client.audio.transcriptions.create(**params)
            
            elapsed = time.time() - start_time
            
            # ✅ CORRECTION: Les segments sont des objets avec attributs, pas des dict
            segments = []
            if hasattr(transcript, 'segments') and transcript.segments:
                for seg in transcript.segments:
                    # Utiliser getattr pour accéder aux attributs
                    segments.append({
                        "start": getattr(seg, 'start', 0),
                        "end": getattr(seg, 'end', 0),
                        "text": getattr(seg, 'text', '')
                    })
            
            result = {
                "text": transcript.text,
                "language": transcript.language,
                "language_full": self.get_language_name(transcript.language),
                "duration": transcript.duration,
                "segments": segments,
                "segments_count": len(segments),
                "source": "openai-whisper",
                "processing_time": round(elapsed, 2),
                "model": "whisper-1",
                "timestamp": time.time(),
                "request_id": request_id
            }
            
            logger.info(f"✅ [{request_id}] Transcription - Langue: {transcript.language} ({self.get_language_name(transcript.language)}), Durée: {transcript.duration}s, Temps: {elapsed:.2f}s")
            logger.info(f"📝 [{request_id}] Texte: {transcript.text[:100]}...")
            
            return result
            
        except openai.RateLimitError as e:
            logger.error(f"❌ [{request_id}] Quota OpenAI dépassé: {e}")
            return {
                "text": "❌ Quota OpenAI dépassé",
                "language": "unknown",
                "language_full": "Inconnu",
                "duration": 0,
                "segments": [],
                "segments_count": 0,
                "source": "error",
                "error": str(e),
                "error_type": "rate_limit",
                "request_id": request_id
            }
            
        except openai.APITimeoutError as e:
            logger.error(f"❌ [{request_id}] Timeout OpenAI: {e}")
            return {
                "text": "❌ Timeout - Vérifie ta connexion",
                "language": "unknown",
                "language_full": "Inconnu",
                "duration": 0,
                "segments": [],
                "segments_count": 0,
                "source": "error",
                "error": str(e),
                "error_type": "timeout",
                "request_id": request_id
            }
            
        except openai.APIConnectionError as e:
            logger.error(f"❌ [{request_id}] Erreur de connexion OpenAI: {e}")
            return {
                "text": "❌ Problème de connexion",
                "language": "unknown",
                "language_full": "Inconnu",
                "duration": 0,
                "segments": [],
                "segments_count": 0,
                "source": "error",
                "error": str(e),
                "error_type": "connection",
                "request_id": request_id
            }
            
        except openai.APIError as e:
            logger.error(f"❌ [{request_id}] Erreur API OpenAI: {e}")
            return {
                "text": f"❌ Erreur API: {str(e)}",
                "language": "unknown",
                "language_full": "Inconnu",
                "duration": 0,
                "segments": [],
                "segments_count": 0,
                "source": "error",
                "error": str(e),
                "error_type": "api_error",
                "request_id": request_id
            }
            
        except Exception as e:
            logger.error(f"❌ [{request_id}] Erreur inattendue: {type(e).__name__}: {e}")
            return {
                "text": f"❌ Erreur: {str(e)}",
                "language": "unknown",
                "language_full": "Inconnu",
                "duration": 0,
                "segments": [],
                "segments_count": 0,
                "source": "error",
                "error": str(e),
                "error_type": "unexpected",
                "request_id": request_id
            }
            
        finally:
            try:
                os.unlink(tmp_path)
                logger.info(f"🗑️ [{request_id}] Fichier temporaire supprimé")
            except Exception as e:
                logger.warning(f"⚠️ [{request_id}] Impossible de supprimer le fichier temporaire: {e}")
    
    async def transcribe_with_timestamps(self, audio_file: bytes) -> Dict[str, Any]:
        """
        Transcrit avec timestamps pour chaque mot (utile pour sous-titres)
        """
        result = await self.transcribe_with_detection(audio_file)
        
        # Si la transcription a réussi et a des segments
        if result.get('source') == 'openai-whisper' and result.get('segments'):
            # Formater les segments avec timestamps
            formatted_segments = []
            for seg in result['segments']:
                formatted_segments.append({
                    "time": f"{seg['start']:.2f}s - {seg['end']:.2f}s",
                    "text": seg['text']
                })
            result['formatted_segments'] = formatted_segments
        
        return result
    
    async def transcribe_streaming(self, audio_chunks: AsyncGenerator[bytes, None], 
                                   language: Optional[str] = None) -> str:
        """
        Transcription en streaming (accumule les chunks et transcrit à la fin)
        """
        all_audio = bytearray()
        chunk_count = 0
        async for chunk in audio_chunks:
            all_audio.extend(chunk)
            chunk_count += 1
            if chunk_count % 10 == 0:
                logger.debug(f"📦 {chunk_count} chunks reçus, total: {len(all_audio)} bytes")
        
        logger.info(f"📦 Total: {chunk_count} chunks, {len(all_audio)} bytes")
        return await self.transcribe(bytes(all_audio), language)
    
    def _detect_format(self, audio_file: bytes) -> str:
        """
        Détecte le format audio à partir des premiers bytes
        Retourne l'extension appropriée
        """
        # Détection simple basée sur les premiers bytes (magic numbers)
        if len(audio_file) < 12:
            return ".ogg"  # Format par défaut
        
        # Vérifier les signatures de fichiers courants
        if audio_file.startswith(b'RIFF') and audio_file[8:12] == b'WAVE':
            return ".wav"
        elif audio_file.startswith(b'\xff\xfb') or audio_file.startswith(b'ID3'):
            return ".mp3"
        elif audio_file.startswith(b'\x1a\x45\xdf\xa3'):  # Matroska/WebM
            return ".webm"
        elif audio_file.startswith(b'OggS'):
            return ".ogg"
        elif audio_file.startswith(b'ftyp'):
            return ".m4a"
        
        return ".ogg"  # Format par défaut
    
    def get_language_name(self, lang_code: str) -> str:
        """Retourne le nom complet de la langue"""
        return self.LANGUAGE_CODES.get(lang_code, lang_code)
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Retourne la liste des langues supportées"""
        return self.LANGUAGE_CODES.copy()
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Teste la connexion à l'API OpenAI
        Utile pour le diagnostic
        """
        try:
            start = time.time()
            models = self.client.models.list()
            elapsed = time.time() - start
            
            # Vérifier si Whisper est disponible
            whisper_available = any("whisper" in model.id for model in models.data)
            
            return {
                "success": True,
                "models_count": len(models.data),
                "whisper_available": whisper_available,
                "response_time": round(elapsed, 2),
                "supported_languages": self.get_supported_languages()
            }
        except openai.APITimeoutError as e:
            return {
                "success": False,
                "error": "Timeout - Vérifie ta connexion",
                "error_type": "timeout"
            }
        except openai.APIConnectionError as e:
            return {
                "success": False,
                "error": "Problème de connexion",
                "error_type": "connection"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }