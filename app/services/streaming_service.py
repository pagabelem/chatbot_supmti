        
# app/services/streaming_service.py
import asyncio
from typing import AsyncGenerator, Optional
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.services.rag_service import generer_reponse_rag
from app.services.chat_session_service import chat_session_service


class StreamingService:
    def __init__(self, db: Session):
        self.db = db

    async def stream_response(
        self,
        message: str,
        student_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Streaming basé sur la même source de vérité que le chat normal:
        rag_service + academic_config.
        """
        logger.info(f"💬 Streaming RAG pour: {message[:60]}")

        # 1) Récupérer l'historique/profil si disponible
        historique = []
        profil_etudiant = None

        try:
            if session_id:
                sess = chat_session_service.get_or_create(session_id)
                historique = sess.get("historique", []) or []
                profil_etudiant = sess.get("profil")
        except Exception as e:
            logger.warning(f"[STREAM] Impossible de charger la session: {e}")

        # 2) Appeler exactement le même moteur que le chat normal
        resultat = generer_reponse_rag(
            question=message,
            historique=historique,
            profil=profil_etudiant,
        )

        texte = (
            resultat.get("reponse")
            or resultat.get("message")
            or "Je n'ai pas pu générer une réponse."
        )

        # 3) Streamer le texte proprement
        for chunk in self._smart_split(texte):
            yield chunk
            if chunk.endswith((".", "!", "?", ":\n")):
                await asyncio.sleep(0.06)
            elif chunk.endswith(","):
                await asyncio.sleep(0.035)
            else:
                await asyncio.sleep(0.015)

    def _smart_split(self, text: str, max_chunk: int = 20):
        """
        Découpe lisible pour effet typing.
        """
        words = text.split()
        current = ""

        for word in words:
            candidate = f"{current} {word}".strip()
            if len(candidate) <= max_chunk:
                current = candidate
            else:
                if current:
                    yield current + " "
                current = word

        if current:
            yield current