"""
Routes API pour le sélecteur de langue de l'interface.
Le développeur frontend appelle ces endpoints pour changer la langue de toute l'interface.
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from app.services.language_selector import LanguageSelector
from app.core.logging import logger

router = APIRouter(prefix="/language", tags=["langue interface"])

selector = LanguageSelector()


class SetLanguageRequest(BaseModel):
    user_id:  str
    language: str   # 'fr' | 'en' | 'ar'


@router.get("/available")
async def get_available_languages():
    """
    Liste toutes les langues disponibles avec leurs métadonnées.

    Exemple de réponse :
    {
      "fr": {"code": "fr", "name": "Français", "flag": "🇫🇷", "direction": "ltr"},
      "en": {"code": "en", "name": "English",  "flag": "🇬🇧", "direction": "ltr"},
      "ar": {"code": "ar", "name": "Darija",   "flag": "🇲🇦", "direction": "ltr"}
    }
    """
    return JSONResponse(content=selector.get_available_languages())


@router.get("/ui/{lang}")
async def get_ui_strings(lang: str):
    """
    Retourne toutes les chaînes de l'interface dans la langue demandée.
    Le frontend applique ces chaînes à chaque élément de l'interface.

    Exemple d'utilisation JS :
      const res  = await fetch('/language/ui/ar');
      const strings = await res.json();
      document.getElementById('sendBtn').textContent = strings.btn_send;
      document.getElementById('input').placeholder   = strings.input_placeholder;
    """
    if lang not in ('fr', 'en', 'ar'):
        lang = 'fr'
    strings = selector.get_ui_strings(lang)
    return JSONResponse(content=strings)


@router.get("/ui")
async def get_all_ui_strings():
    """
    Retourne les chaînes des 3 langues d'un coup.
    Utile si le frontend veut tout charger au démarrage.
    """
    return JSONResponse(content={
        lang: selector.get_ui_strings(lang)
        for lang in ('fr', 'en', 'ar')
    })