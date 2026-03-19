"""
Point d'entrée principal de l'application FastAPI.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi.staticfiles import StaticFiles
import os
from app.api.routes import ocr
from app.api.routes import chat_adaptive

from app.api.routes import chat, profile, orientation, info,compare,report,chat_stream,telegram
from app.database.connection import engine, Base
from app.core.config import settings
from app.core.logging import logger
from app.api.routes import test_stt
from app.api.routes import language

# === Création des tables ===
logger.info("🗄️ Création des tables dans la base de données...")
Base.metadata.create_all(bind=engine)
logger.info("✅ Tables créées avec succès")

# === Initialisation FastAPI ===
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "SUP MTI Meknès",
        "email": "contact@supmtimeknes.ac.ma",
    }
)

# === CORS Configuration ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Inclusion des routes ===
app.include_router(chat.router)
app.include_router(profile.router)
app.include_router(orientation.router)
app.include_router(info.router)
app.include_router(compare.router)
app.include_router(report.router)
app.include_router(chat_stream.router)
app.include_router(ocr.router)
app.include_router(telegram.router) 
app.include_router(chat_adaptive.router) 
app.include_router(test_stt.router)
app.include_router(language.router)


# === Routes de base ===
@app.get("/", tags=["root"])
def read_root():
    """Route racine - Informations sur l'API"""
    return {
        "message": "Bienvenue sur l'API du chatbot SUP'MTI",
        "version": settings.API_VERSION,
        "documentation": "/docs"
    }

@app.get("/health", tags=["health"])
def health_check():
    """Vérification de l'état de l'API"""
    return {
        "status": "healthy",
        "database": "connected",
        "version": settings.API_VERSION
    }

logger.info(f"🚀 Application démarrée - Version {settings.API_VERSION}")


static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logger.info(f"📁 Dossier static monté: {static_dir}")
else:
    logger.warning(f"⚠️ Dossier static non trouvé: {static_dir}")