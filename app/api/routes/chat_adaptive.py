"""
Route de chat adaptative (texte/vocal selon préférences)
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
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
import json
import time
import traceback

router = APIRouter(prefix="/chat-adaptive", tags=["chat adaptatif"])

# Initialisation des services
stt = STTService()
tts = TTSService()

class TextChatRequest(BaseModel):
    message: str
    student_id: Optional[str] = None
    preferred_lang: Optional[str] = None

class VoiceChatResponse(BaseModel):
    success: bool
    transcribed: Optional[str] = None
    detected_language: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@router.post("/text")
async def chat_text(
    request: TextChatRequest,
    db: Session = Depends(get_db)
):
    """
    Chat par texte - met à jour les préférences
    """
    logger.info(f"💬 Chat texte - User: {request.student_id}")
    start_time = time.time()
    
    # Mettre à jour les préférences
    if request.student_id:
        try:
            prefs = UserPreferenceService(db)
            prefs.update_preference(request.student_id, 'text')
        except Exception as e:
            logger.error(f"❌ Erreur mise à jour préférences: {e}")
    
    # Générer réponse
    ai_service = OpenAIService(db)
    response = ai_service.generate_chat_response(
        message=request.message,
        student_id=request.student_id
    )
    
    response_text = response.get('response', '')
    elapsed = time.time() - start_time
    logger.info(f"✅ Réponse texte générée en {elapsed:.2f}s: {response_text[:50]}...")
    
    # Déterminer si réponse vocale
    if request.student_id:
        try:
            prefs = UserPreferenceService(db)
            if prefs.should_respond_with_voice(request.student_id, 'text'):
                # Générer audio
                audio = await tts.synthesize(
                    response_text,
                    request.preferred_lang or 'fr'
                )
                
                logger.info(f"🔊 Réponse vocale générée ({len(audio)} bytes)")
                return Response(
                    content=audio,
                    media_type="audio/mpeg",
                    headers={
                        "X-Response-Type": "voice",
                        "X-Text-Length": str(len(response_text))
                    }
                )
        except Exception as e:
            logger.error(f"❌ Erreur génération audio: {e}")
    
    # Réponse texte normale
    return JSONResponse(
        content={
            "type": "text",
            "data": response
        }
    )

@router.post("/voice")
async def chat_voice(
    file: UploadFile = File(..., description="Message vocal"),
    student_id: Optional[str] = None,
    preferred_lang: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Chat par vocal - Retourne transcription + réponse
    """
    request_id = f"voice_{int(time.time())}"
    logger.info("=" * 60)
    logger.info(f"🎤 [{request_id}] NOUVEAU MESSAGE VOCAL REÇU")
    logger.info(f"📁 [{request_id}] Fichier: {file.filename}")
    logger.info(f"📄 [{request_id}] Content-Type: {file.content_type}")
    logger.info(f"👤 [{request_id}] Student: {student_id}")
    logger.info(f"🌍 [{request_id}] Langue préférée: {preferred_lang}")
    logger.info("=" * 60)
    
    start_time = time.time()
    
    if not file.content_type.startswith('audio/'):
        logger.error(f"❌ [{request_id}] Type de fichier invalide: {file.content_type}")
        return JSONResponse(
            content={"error": "Fichier audio requis"},
            status_code=400
        )
    
    try:
        # 1. Lire l'audio
        audio_bytes = await file.read()
        logger.info(f"📦 [{request_id}] Taille audio reçue: {len(audio_bytes)} bytes")
        
        if len(audio_bytes) < 100:
            logger.warning(f"⚠️ [{request_id}] Fichier audio trop petit")
            return JSONResponse(
                content={
                    "success": False,
                    "error": "Fichier audio trop petit"
                }
            )
        
        # 2. Transcrire avec Whisper
        logger.info(f"🔄 [{request_id}] Début transcription Whisper...")
        transcription = await stt.transcribe_with_detection(audio_bytes)
        
        transcribe_time = time.time() - start_time
        logger.info(f"📝 [{request_id}] Transcription ({transcribe_time:.2f}s): {transcription.get('text', '')[:100]}...")
        
        # Vérifier si la transcription a réussi
        if transcription.get("source") == "error":
            logger.error(f"❌ [{request_id}] Erreur transcription: {transcription.get('text')}")
            return JSONResponse(
                content={
                    "success": False,
                    "error": transcription.get("text", "Erreur de transcription"),
                    "detected_language": transcription.get("language")
                }
            )
        
        # 3. Mettre à jour les préférences
        if student_id:
            try:
                prefs = UserPreferenceService(db)
                prefs.update_preference(student_id, 'voice')
                logger.info(f"✅ [{request_id}] Préférences mises à jour")
            except Exception as e:
                logger.error(f"❌ [{request_id}] Erreur mise à jour préférences: {e}")
        
        # 4. Générer réponse avec le texte transcrit
        logger.info(f"🔄 [{request_id}] Génération réponse OpenAI...")
        ai_service = OpenAIService(db)
        response = ai_service.generate_chat_response(
            message=transcription["text"],
            student_id=student_id
        )
        
        response_text = response.get('response', '')
        ai_time = time.time() - start_time
        logger.info(f"✅ [{request_id}] Réponse OpenAI ({ai_time:.2f}s): {response_text[:50]}...")
        
        # 5. Déterminer le format de réponse
        if student_id:
            try:
                prefs = UserPreferenceService(db)
                if prefs.should_respond_with_voice(student_id, 'voice'):
                    # Réponse vocale
                    logger.info(f"🔄 [{request_id}] Génération réponse vocale...")
                    audio = await tts.synthesize(
                        response_text,
                        preferred_lang or transcription.get('language', 'fr') or 'fr'
                    )
                    
                    tts_time = time.time() - start_time
                    logger.info(f"🔊 [{request_id}] Réponse vocale générée en {tts_time:.2f}s ({len(audio)} bytes)")
                    
                    total_time = time.time() - start_time
                    logger.info(f"✅ [{request_id}] TRAITEMENT COMPLET en {total_time:.2f}s")
                    logger.info("=" * 60)
                    
                    return Response(
                        content=audio,
                        media_type="audio/mpeg",
                        headers={
                            "X-Response-Type": "voice",
                            "X-Request-ID": request_id,
                            "X-Processing-Time": str(round(total_time, 2))
                        }
                    )
            except Exception as e:
                logger.error(f"❌ [{request_id}] Erreur génération audio: {e}")
        
        # Réponse texte
        total_time = time.time() - start_time
        logger.info(f"✅ [{request_id}] TRAITEMENT COMPLET en {total_time:.2f}s (réponse texte)")
        logger.info("=" * 60)
        
        return JSONResponse(
            content={
                "success": True,
                "transcribed": transcription["text"],
                "detected_language": transcription.get("language", "fr"),
                "data": response,
                "processing_time": round(total_time, 2)
            }
        )
        
    except Exception as e:
        error_time = time.time() - start_time
        logger.error(f"❌ [{request_id}] Erreur à {error_time:.2f}s: {str(e)}")
        logger.error(traceback.format_exc())
        
        return JSONResponse(
            content={
                "success": False,
                "error": f"Erreur serveur: {str(e)}",
                "processing_time": round(error_time, 2)
            }
        )

@router.get("/preferences/{student_id}")
async def get_preferences(
    student_id: str,
    db: Session = Depends(get_db)
):
    """
    Récupère les préférences d'un utilisateur
    """
    try:
        prefs = UserPreferenceService(db)
        preferred_mode = prefs.get_preferred_mode(student_id)
        logger.info(f"📊 Préférences pour {student_id}: {preferred_mode}")
        
        return JSONResponse(
            content={
                "student_id": student_id,
                "preferred_mode": preferred_mode
            }
        )
    except Exception as e:
        logger.error(f"❌ Erreur récupération préférences: {e}")
        return JSONResponse(
            content={
                "student_id": student_id,
                "preferred_mode": "text",
                "error": str(e)
            }
        )

@router.get("/stt-status")
async def stt_status():
    """
    Vérifie le statut du service STT
    """
    try:
        status = await stt.test_connection()
        logger.info(f"📊 Statut STT: {status}")
        return JSONResponse(content=status)
    except Exception as e:
        logger.error(f"❌ Erreur test STT: {e}")
        return JSONResponse(
            content={
                "success": False,
                "error": str(e)
            }
        )