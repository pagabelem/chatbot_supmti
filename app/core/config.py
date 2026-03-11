"""
Configuration centrale de l'application.
"""
import os
from dotenv import load_dotenv
from typing import Optional

# Charger les variables d'environnement
load_dotenv()

class Settings:
    """Configuration de l'application"""
    
    # === Base de données ===
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:postgres123@localhost:5432/postgres"
    )
    
    # === OpenAI ===
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", "")
    
    # === API ===
    API_TITLE: str = "Chatbot SUP'MTI"
    API_VERSION: str = "0.2.0"
    API_DESCRIPTION: str = "API du chatbot d'orientation académique"
    
    # === Sécurité ===
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # === Rate Limiting ===
    RATE_LIMIT_PER_MINUTE: int = 10
    
    # === Upload ===
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS: list = [".pdf", ".jpg", ".jpeg", ".png"]

# Créer une instance unique des settings
settings = Settings()

# Exporter settings pour pouvoir l'importer ailleurs
__all__ = ["settings"]