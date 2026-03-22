"""
Service d'intégration Telegram pour le chatbot.
"""
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from app.services.openai_service import OpenAIService
from app.database.connection import SessionLocal
from app.core.logging import logger
import asyncio
from typing import Optional, List, Dict, Any

class TelegramBotService:
    """Service pour gérer le bot Telegram"""
    
    def __init__(self, token: str):
        self.token = token
        self.application = Application.builder().token(token).build()
        self._setup_handlers()
        logger.info("✅ Service Telegram initialisé")
    
    def _setup_handlers(self):
        """Configure les commandes du bot"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("programs", self.programs_command))
        self.application.add_handler(CommandHandler("contact", self.contact_command))
        self.application.add_handler(CommandHandler("test", self.test_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.application.add_handler(MessageHandler(filters.VOICE, self.handle_voice))
        logger.info("✅ Handlers Telegram configurés")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /start"""
        user = update.effective_user
        welcome_msg = (
            f"👋 Bonjour {user.first_name} !\n\n"
            "Je suis le conseiller virtuel de **SUP MTI Meknès**.\n\n"
            "**Je peux vous aider avec :**\n"
            "📚 **Programmes** : IA, Cybersécurité, Génie Logiciel, Management, Finance, Réseaux\n"
            "🎓 **Admission** : Conditions, concours, inscriptions\n"
            "💰 **Frais** : Scolarité, bourses, paiements\n"
            "🌍 **International** : Partenariats, doubles diplômes\n"
            "🎉 **Vie étudiante** : Clubs, événements, campus\n"
            "📞 **Contact** : Coordonnées, horaires, localisation\n\n"
            "**Commandes disponibles :**\n"
            "/help - Afficher l'aide\n"
            "/programs - Liste des programmes\n"
            "/contact - Coordonnées de l'école\n"
            "/test - Tester le mode démo\n\n"
            "Posez-moi toutes vos questions en français, anglais ou darija !"
        )
        await update.message.reply_text(welcome_msg, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /help"""
        help_msg = (
            "🤖 **Aide - Commandes disponibles**\n\n"
            "/start - Accueil et présentation\n"
            "/help - Afficher cette aide\n"
            "/programs - Liste des programmes\n"
            "/contact - Coordonnées de l'école\n"
            "/test - Tester le mode démo\n\n"
            "**Posez vos questions directement :**\n"
            "• En français : \"Quels sont les programmes ?\"\n"
            "• En anglais : \"What programs do you have?\"\n"
            "• En darija : \"Salam, chno kayn d programmes?\"\n\n"
            "Je parle les 3 langues !"
        )
        await update.message.reply_text(help_msg, parse_mode='Markdown')
    
    async def programs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /programs"""
        db = SessionLocal()
        try:
            from app.database.models import Program
            programs = db.query(Program).limit(10).all()
            
            if programs:
                msg = "📚 **Programmes disponibles à SUP MTI :**\n\n"
                for i, p in enumerate(programs, 1):
                    msg += f"{i}. **{p.name}**\n"
                msg += "\nSouhaitez-vous des détails sur un programme en particulier ?"
            else:
                msg = "📚 Les programmes seront bientôt disponibles."
            
            await update.message.reply_text(msg, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"❌ Erreur programmes: {e}")
            await update.message.reply_text("Désolé, une erreur est survenue lors de la récupération des programmes.")
        finally:
            db.close()
    
    async def contact_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /contact"""
        contact_msg = (
            "📞 **Contact SUP MTI Meknès :**\n\n"
            "📍 **Adresse :** Centre-ville, Meknès\n"
            "📱 **Téléphone :** +212 5 35 51 10 11\n"
            "📧 **Email :** contact@supmtimeknes.ac.ma\n"
            "🌐 **Site web :** www.supmtimeknes.ac.ma\n\n"
            "🕒 **Horaires :**\n"
            "• Lundi - Vendredi : 08:30 - 18:00\n"
            "• Samedi : 08:30 - 12:00"
        )
        await update.message.reply_text(contact_msg, parse_mode='Markdown')
    
    async def test_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /test - Mode démo"""
        await update.message.reply_text(
            "🧪 **Mode test activé**\n\n"
            "Envoyez-moi un message et je vous répondrai en mode démo !"
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère les messages texte"""
        user_message = update.message.text
        user_id = str(update.effective_user.id)
        user_name = update.effective_user.first_name
        
        logger.info(f"📱 Message Telegram de {user_name} ({user_id}): {user_message[:50]}...")
        
        # Indicateur de frappe
        await update.message.chat.send_action(action="typing")
        
        db = SessionLocal()
        try:
            # Réutilise ton service OpenAI existant
            ai_service = OpenAIService(db)
            # ✅ CORRECTION: Pas de await ici
            response_data = ai_service.generate_chat_response(user_message)
            
            # Extraire la réponse texte
            if isinstance(response_data, dict):
                response_text = response_data.get('response', str(response_data))
            else:
                response_text = str(response_data)
            
            # Telegram a une limite de 4096 caractères par message
            if len(response_text) > 4000:
                parts = [response_text[i:i+4000] for i in range(0, len(response_text), 4000)]
                for i, part in enumerate(parts, 1):
                    await update.message.reply_text(f"{part}\n\n({i}/{len(parts)})")
            else:
                await update.message.reply_text(response_text)
                
        except Exception as e:
            logger.error(f"❌ Erreur Telegram: {e}")
            await update.message.reply_text(
                "Désolé, une erreur technique est survenue. Veuillez réessayer plus tard.\n"
                f"Détail: {str(e)}"
            )
        finally:
            db.close()
    
    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère les messages vocaux"""
        await update.message.reply_text(
            "🎤 J'ai reçu votre message vocal ! "
            "La reconnaissance vocale sera bientôt disponible."
        )
    
    # === MÉTHODES POUR TESTS LOCAUX ===
    
    async def _process_ai_response(self, message: str) -> str:
        """Traite un message via l'IA et retourne la réponse texte"""
        db = SessionLocal()
        try:
            ai_service = OpenAIService(db)
            # ✅ CORRECTION: Pas de await ici
            response_data = ai_service.generate_chat_response(message)
            
            # Extraire la réponse texte
            if isinstance(response_data, dict):
                return response_data.get('response', str(response_data))
            return str(response_data)
            
        except Exception as e:
            logger.error(f"❌ Erreur AI: {e}")
            return f"Erreur AI: {str(e)}"
        finally:
            db.close()
    
    async def handle_message_local(self, message: str, user_id: str = "test_user") -> str:
        """
        Version locale pour tester sans webhook
        """
        logger.info(f"🧪 Test local - Message: {message}")
        return await self._process_ai_response(message)
    
    async def simulate_conversation(self, messages: List[str]) -> List[Dict[str, str]]:
        """
        Simule une conversation complète (pour tests)
        """
        responses = []
        for i, msg in enumerate(messages):
            logger.info(f"👤 Message {i+1}: {msg}")
            resp = await self.handle_message_local(msg)
            logger.info(f"🤖 Réponse {i+1}: {resp[:100]}...")
            responses.append({"user": msg, "bot": resp})
            await asyncio.sleep(1)
        return responses
    
    async def broadcast_message(self, chat_ids: List[str], message: str) -> List[Dict[str, Any]]:
        """
        Envoie un message à plusieurs utilisateurs (pour admin)
        """
        results = []
        for chat_id in chat_ids:
            try:
                await self.application.bot.send_message(chat_id=chat_id, text=message)
                results.append({"chat_id": chat_id, "success": True})
            except Exception as e:
                logger.error(f"❌ Erreur broadcast à {chat_id}: {e}")
                results.append({
                    "chat_id": chat_id, 
                    "success": False, 
                    "error": str(e)
                })
        return results
    
    async def get_bot_info(self) -> Dict[str, Any]:
        """Récupère les informations du bot"""
        try:
            bot_info = await self.application.bot.get_me()
            return {
                "id": bot_info.id,
                "username": bot_info.username,
                "first_name": bot_info.first_name,
                "is_bot": bot_info.is_bot
            }
        except Exception as e:
            logger.error(f"❌ Erreur récupération infos bot: {e}")
            return {"error": str(e)}