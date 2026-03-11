"""
Service unifié de sélection de langue
"""
from typing import Optional, Dict
from app.services.multilingual_service import MultilingualService

class LanguageSelector:
    """Gère la sélection de langue (auto ou manuelle)"""
    
    def __init__(self):
        self.multilingual = MultilingualService()
        self.supported_languages = {
            'fr': {
                'name': 'Français',
                'flag': '🇫🇷',
                'tts_code': 'fr',
                'stt_code': 'fr'
            },
            'en': {
                'name': 'English',
                'flag': '🇬🇧',
                'tts_code': 'en',
                'stt_code': 'en'
            },
            'ar': {
                'name': 'العربية',
                'flag': '🇲🇦',
                'tts_code': 'ar',
                'stt_code': 'ar'
            }
        }
    
    def get_language_info(self, lang_code: str) -> Dict:
        """Retourne les infos d'une langue"""
        return self.supported_languages.get(lang_code, self.supported_languages['fr'])
    
    def determine_response_language(self, 
                                   detected_lang: str, 
                                   preferred_lang: Optional[str] = None,
                                   user_history: Optional[list] = None) -> str:
        """
        Détermine la langue de réponse basée sur:
        - Langue détectée automatiquement
        - Langue préférée de l'utilisateur
        - Historique des conversations
        """
        if preferred_lang and preferred_lang in self.supported_languages:
            return preferred_lang
        
        if detected_lang and detected_lang in self.supported_languages:
            return detected_lang
        
        # Par défaut: français
        return 'fr'
    
    def get_available_languages(self) -> Dict[str, str]:
        """Retourne la liste des langues disponibles"""
        return {
            code: info['name'] 
            for code, info in self.supported_languages.items()
        }