"""
Routes pour l'intégration Telegram.
"""
from fastapi import APIRouter, Request, HTTPException, Query
from app.services.telegram_service import TelegramBotService
from app.core.logging import logger
import telegram
from pydantic import BaseModel
from typing import Optional, List
import os
from dotenv import load_dotenv

# Charge les variables d'environnement
load_dotenv()

router = APIRouter(prefix="/telegram", tags=["telegram"])

class TestMessage(BaseModel):
    message: str
    user_id: str = "test_user"

class BroadcastRequest(BaseModel):
    chat_ids: List[str]
    message: str

# Récupère le token directement depuis .env
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Initialise le service Telegram si le token existe
bot_service = None
if TOKEN:
    try:
        bot_service = TelegramBotService(TOKEN)
        logger.info("✅ Service Telegram initialisé avec succès")
    except Exception as e:
        logger.error(f"❌ Erreur initialisation Telegram: {e}")
else:
    logger.warning("⚠️ TELEGRAM_BOT_TOKEN non défini, service Telegram en mode démo")

@router.post("/test")
async def test_telegram_message(msg: TestMessage):
    """
    Teste le bot Telegram en local sans webhook
    """
    if not bot_service:
        # Mode démo sans token
        logger.info(f"🧪 Test local (mode démo) - Message: {msg.message}")
        return {
            "success": True,
            "user_message": msg.message,
            "bot_response": f"[Mode démo] Réponse à: {msg.message}"
        }
    
    logger.info(f"🧪 Test local - Message: {msg.message}")
    response = await bot_service.handle_message_local(msg.message, msg.user_id)
    
    return {
        "success": True,
        "user_message": msg.message,
        "bot_response": response
    }

@router.post("/simulate")
async def simulate_conversation(messages: List[str]):
    """
    Simule une conversation complète (pour tests)
    """
    if not bot_service:
        return {
            "success": True,
            "conversation": [
                {"user": msg, "bot": f"[Mode démo] Réponse à: {msg}"} 
                for msg in messages
            ]
        }
    
    results = await bot_service.simulate_conversation(messages)
    return {
        "success": True,
        "conversation": results
    }

# Routes avancées uniquement si bot_service existe
if bot_service:
    @router.post("/webhook")
    async def telegram_webhook(request: Request):
        """Point d'entrée pour les messages Telegram"""
        try:
            data = await request.json()
            logger.info("📥 Webhook Telegram reçu")
            
            update = telegram.Update.de_json(data, bot_service.application.bot)
            await bot_service.application.process_update(update)
            return {"ok": True}
            
        except Exception as e:
            logger.error(f"❌ Erreur webhook: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/set-webhook")
    async def set_webhook(url: str = Query(..., description="URL publique du webhook")):
        """Configure le webhook Telegram"""
        try:
            await bot_service.application.bot.set_webhook(url)
            return {"message": f"✅ Webhook configuré sur {url}"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/webhook-info")
    async def get_webhook_info():
        """Vérifie la configuration du webhook"""
        info = await bot_service.application.bot.get_webhook_info()
        return {
            "url": info.url,
            "pending_update_count": info.pending_update_count
        }