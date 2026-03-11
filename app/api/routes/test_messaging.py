# test_messaging.py
import requests
import json
from datetime import datetime

class MessagingTest:
    def __init__(self):
        self.api_url = "http://127.0.0.1:8000"
    
    def test_telegram_webhook(self, message):
        """Simule un message Telegram"""
        print(f"📱 Simulation message Telegram: {message}")
        
        # Simuler le payload Telegram
        telegram_update = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "from": {
                    "id": 12345678,
                    "first_name": "Test",
                    "username": "test_user"
                },
                "chat": {
                    "id": 12345678,
                    "type": "private"
                },
                "date": int(datetime.now().timestamp()),
                "text": message
            }
        }
        
        # Envoyer à notre API (à implémenter plus tard)
        print(f"📤 Payload: {json.dumps(telegram_update, indent=2)}")
        
        # Simuler une réponse du bot
        response = {
            "text": f"Réponse à: {message}",
            "chat_id": 12345678
        }
        
        print(f"📥 Réponse du bot: {response['text']}")
        return response
    
    def test_whatsapp_webhook(self, message):
        """Simule un message WhatsApp"""
        print(f"💬 Simulation message WhatsApp: {message}")
        
        # Simuler le payload WhatsApp
        whatsapp_update = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "212600000000",
                            "phone_number_id": "123456789"
                        },
                        "contacts": [{
                            "profile": {"name": "Test User"},
                            "wa_id": "212612345678"
                        }],
                        "messages": [{
                            "from": "212612345678",
                            "id": "wamid.123456789",
                            "timestamp": str(int(datetime.now().timestamp())),
                            "text": {"body": message},
                            "type": "text"
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }
        
        print(f"📤 Payload: {json.dumps(whatsapp_update, indent=2)}")
        
        # Simuler une réponse
        response = {
            "text": f"Réponse WhatsApp à: {message}",
            "to": "212612345678"
        }
        
        print(f"📥 Réponse du bot: {response['text']}")
        return response

if __name__ == "__main__":
    tester = MessagingTest()
    
    print("=" * 50)
    tester.test_telegram_webhook("Bonjour, quels sont les programmes?")
    print("=" * 50)
    tester.test_whatsapp_webhook("Salam, chno kayn d programmes?")
    print("=" * 50)