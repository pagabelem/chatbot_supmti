"""
Routes pour le chat avec le conseiller virtuel.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional

from app.database.connection import get_db
from app.services.openai_service import OpenAIService
from app.core.logging import logger

router = APIRouter(prefix="/chat", tags=["chat"])

# === Schémas Pydantic ===
class ChatRequest(BaseModel):
    """Schéma pour les requêtes de chat"""
    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Message de l'utilisateur"
    )
    student_id: Optional[str] = Field(
        None,
        description="ID de l'étudiant (UUID) pour personnaliser la réponse"
    )

class ChatResponse(BaseModel):
    """Schéma pour les réponses du chat"""
    response: str
    student_id: Optional[str] = None

# === Routes ===
@router.post(
    "",
    response_model=ChatResponse,
    summary="Envoyer un message",
    description="Envoie un message au chatbot et reçoit une réponse personnalisée"
)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Envoie un message au chatbot et reçoit une réponse.
    
    - **message**: Le texte de la question (obligatoire)
    - **student_id**: ID de l'étudiant (optionnel, pour personnaliser)
    
    Le chatbot utilise:
    - Le profil de l'étudiant si student_id est fourni
    - L'API OpenAI pour générer des réponses naturelles
    """
    logger.info(f"💬 POST /chat - Message: {request.message[:50]}...")
    
    try:
        service = OpenAIService(db)
        result = service.generate_chat_response(
            message=request.message,
            student_id=request.student_id
        )
        
        logger.info("✅ Réponse générée avec succès")
        return ChatResponse(
            response=result["response"],
            student_id=result.get("student_id")
        )
        
    except Exception as e:
        logger.error(f"❌ Erreur chat: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Désolé, une erreur technique est survenue. Veuillez réessayer."
        )