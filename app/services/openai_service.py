# openai_service.py
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class OpenAIService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY non trouvée dans .env")
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("MODEL_NAME", "gpt-5.2")

    def get_chat_response(self, message: str, historique: list = None) -> str:
        
        messages = [
            {
                "role": "system",
                "content": (
                    "Tu es Sami, l'assistant intelligent d'orientation académique "
                    "de SUPMTI Meknès. Tu aides les étudiants avec empathie et "
                    "précision en te basant sur les filières de l'école."
                )
            }
        ]

        # Ajoute l'historique si disponible (max 10 échanges)
        if historique:
            messages.extend(historique[-10:])

        messages.append({"role": "user", "content": message})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Erreur OpenAI : {str(e)}"

openai_service = OpenAIService()