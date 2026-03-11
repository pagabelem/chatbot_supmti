"""
Route pour tester le service STT
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.stt_service import STTService
from app.core.logging import logger

router = APIRouter(prefix="/test-stt", tags=["test"])

@router.post("/transcribe")
async def test_transcription(
    file: UploadFile = File(..., description="Fichier audio à tester")
):
    """
    Teste la transcription vocale
    """
    logger.info(f"🧪 Test STT - Fichier: {file.filename}")
    
    if not file.content_type.startswith('audio/'):
        raise HTTPException(400, "Le fichier doit être un fichier audio")
    
    stt = STTService()
    audio_bytes = await file.read()
    
    result = await stt.transcribe_with_detection(audio_bytes)
    return result

@router.get("/status")
async def test_status():
    """
    Vérifie le statut du service STT
    """
    stt = STTService()
    return await stt.test_connection()