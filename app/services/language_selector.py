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
    
    
from typing import Optional, Dict, Any
from app.services.multilingual_service import MultilingualService
from app.core.logging import logger


class LanguageSelector:
    """
    Gestionnaire de langue de l'interface utilisateur.
    Fournit les traductions complètes pour FR / EN / Darija latin.
    """

    SUPPORTED_LANGUAGES = {
        'fr': {
            'name':      'Français',
            'flag':      '🇫🇷',
            'direction': 'ltr',
            'tts_code':  'fr',
            'stt_code':  'fr',
        },
        'en': {
            'name':      'English',
            'flag':      '🇬🇧',
            'direction': 'ltr',
            'tts_code':  'en',
            'stt_code':  'en',
        },
        'ar': {
            'name':      'Darija',
            'flag':      '🇲🇦',
            'direction': 'ltr',   # darija latin → gauche à droite
            'tts_code':  'ar',
            'stt_code':  'ar',
        },
    }

    # ------------------------------------------------------------------ #
    # TRADUCTIONS COMPLÈTES DE L'INTERFACE                                #
    # Toutes les chaînes utilisées dans chat_adaptive.html               #
    # Le développeur frontend n'a qu'à appeler get_ui_strings(lang)      #
    # ------------------------------------------------------------------ #
    UI_STRINGS = {
        'fr': {
            # Titre et entête
            'app_title':          '🤖 Chat Adaptatif SUP MTI',
            'pref_loading':       'Chargement...',
            'pref_voice':         '🎤 Vocal',
            'pref_text':          '✍️ Texte',
            'pref_label':         'Mode préféré :',
            'pref_default':       'Mode préféré : Texte (par défaut)',

            # Sélecteur de langue
            'lang_auto':          '🌐 Auto-détection',
            'lang_fr':            '🇫🇷 Français',
            'lang_en':            '🇬🇧 English',
            'lang_ar':            '🇲🇦 Darija',
            'lang_selector_label':'Langue :',

            # Boutons
            'btn_send':           'Envoyer',
            'btn_record':         '🎤 Parler',
            'btn_record_stop':    '⏹ Arrêter',
            'btn_test_stt':       '🔍 Test STT',
            'btn_settings':       '⚙️ Config',
            'btn_save':           'Sauvegarder',
            'btn_play':           '🔊 Réécouter',

            # Champ de saisie
            'input_placeholder':  'Tapez votre message ou parlez...',

            # Messages dans le chat
            'msg_you':            '👤 Vous',
            'msg_assistant':      '🤖 Assistant',
            'msg_transcript':     '🗣 Transcription',
            'msg_voice_user':     '🎤 Votre message vocal',
            'msg_voice_bot':      '🔊 Réponse audio',
            'msg_recording':      '🎤 Enregistrement...',
            'msg_speak_now':      '🎤 Parlez maintenant...',
            'msg_processing':     '⏳ Traitement...',
            'msg_error':          '❌ Erreur',
            'msg_timeout':        '⏱️ Délai dépassé',
            'msg_server_error':   '❌ Serveur inaccessible',

            # Unités
            'unit_seconds':       's',

            # Statut STT
            'stt_ok':             '✅ STT OK',
            'stt_error':          '❌ STT Error',

            # Panneau config
            'settings_title':     '⚙️ Configuration',
            'settings_mode':      'Mode réponse :',
            'settings_timeout':   'Timeout (s) :',
            'settings_debug':     'Debug :',
            'settings_json':      'Forcer JSON :',
            'mode_auto':          'Auto',
            'mode_text':          'Texte uniquement',
            'mode_audio':         'Audio uniquement',
            'mode_both':          'Texte + Audio',

            # Debug
            'debug_show':         '🐛 Afficher debug',
            'debug_hide':         '🐛 Masquer debug',
        },

        'en': {
            # Titre et entête
            'app_title':          '🤖 Adaptive Chat SUP MTI',
            'pref_loading':       'Loading...',
            'pref_voice':         '🎤 Voice',
            'pref_text':          '✍️ Text',
            'pref_label':         'Preferred mode:',
            'pref_default':       'Preferred mode: Text (default)',

            # Sélecteur de langue
            'lang_auto':          '🌐 Auto-detect',
            'lang_fr':            '🇫🇷 Français',
            'lang_en':            '🇬🇧 English',
            'lang_ar':            '🇲🇦 Darija',
            'lang_selector_label':'Language:',

            # Boutons
            'btn_send':           'Send',
            'btn_record':         '🎤 Speak',
            'btn_record_stop':    '⏹ Stop',
            'btn_test_stt':       '🔍 Test STT',
            'btn_settings':       '⚙️ Settings',
            'btn_save':           'Save',
            'btn_play':           '🔊 Play',

            # Champ de saisie
            'input_placeholder':  'Type your message or speak...',

            # Messages dans le chat
            'msg_you':            '👤 You',
            'msg_assistant':      '🤖 Assistant',
            'msg_transcript':     '🗣 Transcription',
            'msg_voice_user':     '🎤 Your voice message',
            'msg_voice_bot':      '🔊 Audio response',
            'msg_recording':      '🎤 Recording...',
            'msg_speak_now':      '🎤 Speak now...',
            'msg_processing':     '⏳ Processing...',
            'msg_error':          '❌ Error',
            'msg_timeout':        '⏱️ Timeout',
            'msg_server_error':   '❌ Server unreachable',

            # Unités
            'unit_seconds':       's',

            # Statut STT
            'stt_ok':             '✅ STT OK',
            'stt_error':          '❌ STT Error',

            # Panneau config
            'settings_title':     '⚙️ Settings',
            'settings_mode':      'Response mode:',
            'settings_timeout':   'Timeout (s):',
            'settings_debug':     'Debug:',
            'settings_json':      'Force JSON:',
            'mode_auto':          'Auto',
            'mode_text':          'Text only',
            'mode_audio':         'Audio only',
            'mode_both':          'Text + Audio',

            # Debug
            'debug_show':         '🐛 Show debug',
            'debug_hide':         '🐛 Hide debug',
        },

        'ar': {
            # Titre et entête — darija latin
            'app_title':          '🤖 Chat dyal SUP MTI',
            'pref_loading':       'Kan y7mel...',
            'pref_voice':         '🎤 Swit',
            'pref_text':          '✍️ Ktaba',
            'pref_label':         'L mode dyal:',
            'pref_default':       'L mode dyal: Ktaba (par défaut)',

            # Sélecteur de langue
            'lang_auto':          '🌐 Auto-détection',
            'lang_fr':            '🇫🇷 Français',
            'lang_en':            '🇬🇧 English',
            'lang_ar':            '🇲🇦 Darija',
            'lang_selector_label':'Lgha:',

            # Boutons
            'btn_send':           'Sift',
            'btn_record':         '🎤 Hder',
            'btn_record_stop':    '⏹ Wqef',
            'btn_test_stt':       '🔍 Test STT',
            'btn_settings':       '⚙️ L3dat',
            'btn_save':           'S7eb',
            'btn_play':           '🔊 Sme3',

            # Champ de saisie
            'input_placeholder':  'Kteb risaltek wlla hder...',

            # Messages dans le chat
            'msg_you':            '👤 Nta',
            'msg_assistant':      '🤖 L mssa3ed',
            'msg_transcript':     '🗣 Transcription',
            'msg_voice_user':     '🎤 Risaltek b swit',
            'msg_voice_bot':      '🔊 Jawab b swit',
            'msg_recording':      '🎤 Kan y9id...',
            'msg_speak_now':      '🎤 Hder daba...',
            'msg_processing':     '⏳ Kan y3mel...',
            'msg_error':          '❌ Mochkil',
            'msg_timeout':        '⏱️ W9t sali',
            'msg_server_error':   '❌ Server ma kaynch',

            # Unités
            'unit_seconds':       'th',

            # Statut STT
            'stt_ok':             '✅ STT mzyan',
            'stt_error':          '❌ Mochkil f STT',

            # Panneau config
            'settings_title':     '⚙️ L3dat',
            'settings_mode':      'Mode dyal jawab:',
            'settings_timeout':   'Timeout (th):',
            'settings_debug':     'Debug:',
            'settings_json':      'Força JSON:',
            'mode_auto':          'Auto',
            'mode_text':          'Ktaba ghi',
            'mode_audio':         'Swit ghi',
            'mode_both':          'Ktaba + Swit',

            # Debug
            'debug_show':         '🐛 Wri debug',
            'debug_hide':         '🐛 Khbi debug',
        },
    }

    def __init__(self):
        self.multilingual = MultilingualService()

    # ------------------------------------------------------------------ #
    # MÉTHODES PRINCIPALES                                                #
    # ------------------------------------------------------------------ #

    def get_available_languages(self) -> Dict[str, Any]:
        """
        Retourne la liste des langues disponibles avec leurs métadonnées.
        Appelé par GET /language/available
        """
        return {
            code: {
                'code':      code,
                'name':      info['name'],
                'flag':      info['flag'],
                'direction': info['direction'],
            }
            for code, info in self.SUPPORTED_LANGUAGES.items()
        }

    def get_ui_strings(self, lang: str) -> Dict[str, str]:
        """
        Retourne toutes les chaînes de l'interface dans la langue demandée.
        Appelé par GET /language/ui/{lang}

        Le frontend remplace chaque élément HTML avec la chaîne correspondante.
        Ex: document.getElementById('sendBtn').textContent = strings['btn_send']
        """
        if lang not in self.UI_STRINGS:
            logger.warning(f"⚠️ Langue {lang!r} non supportée → fallback 'fr'")
            lang = 'fr'

        strings = self.UI_STRINGS[lang].copy()
        # Ajouter les métadonnées de langue
        strings['_lang']      = lang
        strings['_direction'] = self.SUPPORTED_LANGUAGES[lang]['direction']
        strings['_name']      = self.SUPPORTED_LANGUAGES[lang]['name']
        strings['_flag']      = self.SUPPORTED_LANGUAGES[lang]['flag']

        logger.info(f"🌍 UI strings demandées pour: {lang}")
        return strings

    def determine_response_language(
        self,
        detected_lang:  Optional[str] = None,
        preferred_lang: Optional[str] = None,
    ) -> str:
        """
        Détermine la langue de réponse.
        Priorité : preferred_lang > detected_lang > 'fr'
        """
        valid = set(self.SUPPORTED_LANGUAGES.keys())

        if preferred_lang and preferred_lang in valid:
            return preferred_lang
        if detected_lang and detected_lang in valid:
            return detected_lang
        return 'fr'

    def detect_language_from_text(self, text: str) -> str:
        """
        Détecte la langue d'un texte via MultilingualService.
        Retourne 'fr' | 'en' | 'ar'.
        """
        return self.multilingual.detect_lang_code(text)

    def get_language_info(self, lang_code: str) -> Dict[str, str]:
        """Retourne les métadonnées d'une langue."""
        return self.SUPPORTED_LANGUAGES.get(lang_code, self.SUPPORTED_LANGUAGES['fr'])