"""
Route de chat adaptative (texte/vocal selon préférences) — Version finale
Corrections appliquées :
  - detected_language transmis à OpenAI → réponse dans la bonne langue
  - Validation UUID avant tout appel UserPreferenceService
  - preferred_lang='auto' ou absent → Whisper auto-détecte
  - transcribe_verbose() utilisé pour récupérer la langue Whisper
  - Fallback JSON propre si TTS échoue
"""
from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.database.connection import get_db
from app.services.openai_service import OpenAIService
from app.services.stt_service import STTService
from app.services.tts_service import TTSService
from app.services.user_preferences import UserPreferenceService
from app.core.logging import logger
from fastapi.responses import JSONResponse, Response
import time
import traceback
import re

router = APIRouter(prefix="/chat-adaptive", tags=["chat adaptatif"])

# Services globaux (initialisés une seule fois au démarrage)
stt = STTService()
tts = TTSService()


# ------------------------------------------------------------------ #
# UTILITAIRE : validation UUID                                        #
# ------------------------------------------------------------------ #
UUID_RE = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE
)

def is_valid_uuid(value: Optional[str]) -> bool:
    """Retourne True uniquement si la valeur est un UUID valide."""
    return bool(value and UUID_RE.match(value))


# ------------------------------------------------------------------ #
# MODÈLES PYDANTIC                                                    #
# ------------------------------------------------------------------ #
class TextChatRequest(BaseModel):
    message:        str
    student_id:     Optional[str] = None
    preferred_lang: Optional[str] = None   # 'fr' | 'en' | 'ar' | None


class VoiceChatResponse(BaseModel):
    success:           bool
    transcribed:       Optional[str] = None
    detected_language: Optional[str] = None
    data:              Optional[Dict[str, Any]] = None
    error:             Optional[str] = None


# ------------------------------------------------------------------ #
# HELPER : résolution de la langue de réponse                        #
# ------------------------------------------------------------------ #
def resolve_language(
    preferred_lang: Optional[str],
    detected_lang:  Optional[str],
) -> Optional[str]:
    """
    Priorité : preferred_lang (choix explicite de l'utilisateur)
             > detected_lang (détecté par Whisper)
             > None (OpenAI détecte depuis le texte)
    'auto' est traité comme None.
    """
    valid = {'fr', 'en', 'ar'}
    if preferred_lang and preferred_lang in valid:
        return preferred_lang
    if detected_lang and detected_lang in valid:
        return detected_lang
    return None


# ------------------------------------------------------------------ #
# ENDPOINT : CHAT TEXTE                                               #
# ------------------------------------------------------------------ #
@router.post("/text")
async def chat_text(
    request: TextChatRequest,
    db: Session = Depends(get_db),
):
    """Chat par texte — génère une réponse et met à jour les préférences."""
    logger.info(f"💬 Chat texte — User: {request.student_id} | lang: {request.preferred_lang!r}")
    start_time = time.time()

    # Mise à jour préférences (UUID valide uniquement — évite les erreurs UUID)
    if is_valid_uuid(request.student_id):
        try:
            UserPreferenceService(db).update_preference(request.student_id, 'text')
        except Exception as e:
            logger.error(f"❌ Préférences: {e}")
    else:
        logger.debug(f"⚠️ student_id non-UUID ignoré: {request.student_id!r}")

    # Générer la réponse OpenAI
    ai_service = OpenAIService(db)
    response   = ai_service.generate_chat_response(
        message=request.message,
        student_id=request.student_id,
        detected_language=request.preferred_lang,   # hint langue pour GPT
    )

    response_text = response.get('response', '')
    elapsed       = time.time() - start_time
    logger.info(f"✅ Réponse texte en {elapsed:.2f}s: {response_text[:60]!r}")

    # Réponse vocale si préférence = voice (UUID uniquement)
    if is_valid_uuid(request.student_id):
        try:
            prefs = UserPreferenceService(db)
            if prefs.should_respond_with_voice(request.student_id, 'text'):
                audio = await tts.synthesize(
                    response_text,
                    request.preferred_lang or 'fr',
                )
                logger.info(f"🔊 Réponse vocale ({len(audio)} bytes)")
                return Response(
                    content=audio,
                    media_type="audio/mpeg",
                    headers={
                        "X-Response-Type": "voice",
                        "X-Text-Length":   str(len(response_text)),
                    },
                )
        except Exception as e:
            logger.error(f"❌ TTS: {e}")

    return JSONResponse(content={"type": "text", "data": response})


# ------------------------------------------------------------------ #
# ENDPOINT : CHAT VOCAL                                               #
# ------------------------------------------------------------------ #
@router.post("/voice")
async def chat_voice(
    file:            UploadFile = File(..., description="Message vocal (webm/wav/ogg/mp3)"),
    student_id:      Optional[str] = Query(None),
    preferred_lang:  Optional[str] = Query(None),   # 'fr' | 'en' | 'ar' | None | 'auto'
    response_format: Optional[str] = Query(None),   # 'json' pour forcer JSON
    response_mode:   Optional[str] = Query(None),   # 'text' | 'audio' | 'both'
    db:              Session = Depends(get_db),
):
    """
    Chat vocal complet :
      1. Transcription Whisper (avec ou sans langue forcée)
      2. Détection langue (verbose_json si auto)
      3. Génération réponse OpenAI dans la bonne langue
      4. Retour JSON ou audio selon préférences
    """
    request_id = f"voice_{int(time.time())}"
    start_time = time.time()

    logger.info("=" * 60)
    logger.info(f"🎤 [{request_id}] NOUVEAU MESSAGE VOCAL")
    logger.info(f"📁 [{request_id}] Fichier: {file.filename}")
    logger.info(f"📄 [{request_id}] Content-Type: {file.content_type}")
    logger.info(f"👤 [{request_id}] Student: {student_id}")
    logger.info(f"🌍 [{request_id}] Langue préférée: {preferred_lang!r}")
    logger.info("=" * 60)

    # Validation type fichier
    content_type = file.content_type or ''
    if not content_type.startswith('audio/'):
        logger.error(f"❌ [{request_id}] Type invalide: {content_type}")
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Fichier audio requis"},
        )

    try:
        # ---------------------------------------------------------- #
        # 1. Lecture de l'audio                                      #
        # ---------------------------------------------------------- #
        audio_bytes = await file.read()
        logger.info(f"📦 [{request_id}] {len(audio_bytes)} bytes reçus")

        if len(audio_bytes) < 100:
            return JSONResponse(content={
                "success": False,
                "error":   "Audio trop court — réenregistrez votre message",
            })

        # ---------------------------------------------------------- #
        # 2. Transcription Whisper                                   #
        #    - langue explicite → on la force                        #
        #    - auto ou absent  → verbose_json (récupère la langue)   #
        # ---------------------------------------------------------- #
        logger.info(f"🔄 [{request_id}] Transcription Whisper...")

        valid_langs  = {'fr', 'en', 'ar'}
        whisper_lang = preferred_lang if (preferred_lang in valid_langs) else None

        try:
            if whisper_lang:
                # Langue explicite → transcription directe
                transcription_text = await stt.transcribe(
                    audio_bytes,
                    language=whisper_lang,
                )
                detected_lang = whisper_lang
                transcription = {
                    "text":     transcription_text,
                    "language": detected_lang,
                    "source":   "openai-whisper",
                }
            else:
                # Auto → verbose_json pour récupérer la langue détectée
                transcription = await stt.transcribe_verbose(audio_bytes)
                detected_lang = transcription.get("language", "fr")

        except Exception as whisper_err:
            logger.error(f"❌ [{request_id}] Whisper: {whisper_err}")
            return JSONResponse(content={
                "success": False,
                "error":   f"Erreur transcription: {str(whisper_err)}",
            })

        transcribe_time  = time.time() - start_time
        transcribed_text = transcription.get("text", "").strip()

        logger.info(
            f"📝 [{request_id}] Transcription ({transcribe_time:.2f}s): "
            f"{transcribed_text[:80]!r} | langue={detected_lang!r}"
        )

        if not transcribed_text:
            return JSONResponse(content={
                "success":           False,
                "error":             "Transcription vide — parlez plus fort ou réessayez",
                "detected_language": detected_lang,
            })

        # ---------------------------------------------------------- #
        # 3. Mise à jour préférences (UUID valide uniquement)        #
        # ---------------------------------------------------------- #
        if is_valid_uuid(student_id):
            try:
                UserPreferenceService(db).update_preference(student_id, 'voice')
                logger.info(f"✅ [{request_id}] Préférences mises à jour")
            except Exception as e:
                logger.warning(f"⚠️ [{request_id}] Préférences: {e}")
        else:
            logger.debug(f"⚠️ [{request_id}] student_id non-UUID, préférences ignorées: {student_id!r}")

        # ---------------------------------------------------------- #
        # 4. Langue de réponse                                       #
        #    preferred_lang > detected_lang > None                   #
        # ---------------------------------------------------------- #
        response_lang = resolve_language(preferred_lang, detected_lang)
        logger.info(f"🌐 [{request_id}] Langue réponse: {response_lang!r}")

        # ---------------------------------------------------------- #
        # 5. Génération réponse OpenAI                               #
        #    detected_language → GPT répond en FR / EN / darija      #
        # ---------------------------------------------------------- #
        logger.info(f"🔄 [{request_id}] Génération réponse OpenAI...")
        ai_service  = OpenAIService(db)
        ai_response = ai_service.generate_chat_response(
            message=transcribed_text,
            student_id=student_id,
            detected_language=response_lang,   # ← clé de tout le système
        )

        response_text = ai_response.get('response', '')
        ai_time       = time.time() - start_time
        logger.info(f"✅ [{request_id}] Réponse OpenAI ({ai_time:.2f}s): {response_text[:60]!r}")

        # ---------------------------------------------------------- #
        # 6. Format de réponse : JSON ou audio                       #
        # ---------------------------------------------------------- #
        total_time = time.time() - start_time
        force_json = (response_format == 'json') or (response_mode == 'text')

        # Préférence vocale (UUID uniquement)
        wants_voice = False
        if not force_json and is_valid_uuid(student_id):
            try:
                wants_voice = UserPreferenceService(db).should_respond_with_voice(student_id, 'voice')
            except Exception as e:
                logger.warning(f"⚠️ [{request_id}] should_respond_with_voice: {e}")

        if wants_voice and not force_json:
            logger.info(f"🔄 [{request_id}] Génération TTS...")
            try:
                audio = await tts.synthesize(response_text, response_lang or 'fr')
                logger.info(f"🔊 [{request_id}] TTS ({len(audio)} bytes) en {total_time:.2f}s")
                logger.info("=" * 60)
                return Response(
                    content=audio,
                    media_type="audio/mpeg",
                    headers={
                        "X-Response-Type":   "voice",
                        "X-Request-ID":      request_id,
                        "X-Processing-Time": str(round(total_time, 2)),
                        "X-Transcribed":     transcribed_text[:200],
                        "X-Detected-Lang":   detected_lang or '',
                    },
                )
            except Exception as tts_err:
                logger.error(f"❌ [{request_id}] TTS: {tts_err} — fallback JSON")

        # Réponse JSON (défaut ou fallback)
        logger.info(f"✅ [{request_id}] COMPLET en {total_time:.2f}s — JSON")
        logger.info("=" * 60)

        return JSONResponse(content={
            "success":           True,
            "transcribed":       transcribed_text,
            "detected_language": detected_lang,
            "response_language": response_lang,
            "data":              ai_response,
            "processing_time":   round(total_time, 2),
        })

    except Exception as e:
        error_time = time.time() - start_time
        logger.error(f"❌ [{request_id}] Erreur à {error_time:.2f}s: {e}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={
                "success":         False,
                "error":           f"Erreur serveur: {str(e)}",
                "processing_time": round(error_time, 2),
            },
        )


# ------------------------------------------------------------------ #
# ENDPOINT : PRÉFÉRENCES                                              #
# ------------------------------------------------------------------ #
@router.get("/preferences/{student_id}")
async def get_preferences(
    student_id: str,
    db: Session = Depends(get_db),
):
    """Récupère les préférences d'un utilisateur."""
    try:
        # ID non-UUID (ex: "test-user-123") → retour silencieux sans erreur
        if not is_valid_uuid(student_id):
            logger.debug(f"⚠️ preferences: student_id non-UUID → défaut 'text': {student_id!r}")
            return JSONResponse(content={
                "student_id":     student_id,
                "preferred_mode": "text",
            })

        prefs          = UserPreferenceService(db)
        preferred_mode = prefs.get_preferred_mode(student_id)
        logger.info(f"📊 Préférences {student_id}: {preferred_mode}")
        return JSONResponse(content={
            "student_id":     student_id,
            "preferred_mode": preferred_mode,
        })

    except Exception as e:
        logger.error(f"❌ Erreur préférences: {e}")
        return JSONResponse(content={
            "student_id":     student_id,
            "preferred_mode": "text",
            "error":          str(e),
        })


# ------------------------------------------------------------------ #
# ENDPOINT : STATUT STT                                               #
# ------------------------------------------------------------------ #
@router.get("/stt-status")
async def stt_status():
    """Vérifie la connexion au service STT (Whisper OpenAI)."""
    try:
        status = await stt.test_connection()
        logger.info(f"📊 STT status: {status}")
        return JSONResponse(content=status)
    except Exception as e:
        logger.error(f"❌ Erreur test STT: {e}")
        return JSONResponse(content={"success": False, "error": str(e)})