"""
Route pour le chat avec streaming.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import json

from app.database.connection import get_db
from app.services.streaming_service import StreamingService
from app.core.logging import logger

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatStreamRequest(BaseModel):
    message: str
    student_id: Optional[str] = None

@router.post("/stream")
async def chat_stream(
    request: ChatStreamRequest,
    db: Session = Depends(get_db)
):
    """
    Chat en streaming avec effet "typing".
    """
    logger.info(f"💬 POST /chat/stream - Message: {request.message[:50]}...")
    
    service = StreamingService(db)
    
    async def generate():
        full_response = ""
        async for chunk in service.stream_response(
            message=request.message,
            student_id=request.student_id
        ):
            full_response += chunk
            # Format Server-Sent Events
            yield f"data: {json.dumps({'chunk': chunk, 'full': full_response})}\n\n"
        
        # Signal de fin
        yield f"data: {json.dumps({'done': True})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Désactive le buffering pour nginx
        }
    )

@router.post("/stream/simple")
async def chat_stream_simple(
    request: ChatStreamRequest,
    db: Session = Depends(get_db)
):
    """
    Version simplifiée - retourne directement le texte en streaming.
    """
    logger.info(f"💬 POST /chat/stream/simple - Message: {request.message[:50]}...")
    
    service = StreamingService(db)
    
    async def generate():
        async for chunk in service.stream_response(
            message=request.message,
            student_id=request.student_id
        ):
            yield chunk
    
    return StreamingResponse(
        generate(),
        media_type="text/plain"
    )