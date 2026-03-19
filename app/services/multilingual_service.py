"""
Service avancé de compréhension multilingue.
Gère le darija (écrit en arabe ou en lettres latines), le français et l'anglais,
même avec des erreurs ou du mélange de langues.
"""
import re
from typing import Dict, List, Tuple, Any, Optional
import unicodedata
from app.core.logging import logger


class MultilingualService:
    """Service de compréhension multilingue avancé"""

    def __init__(self):
        # === DICTIONNAIRE DARIJA (écriture arabe) ===
        self.darija_arabic = {
            "السلام": "greeting", "سلام": "greeting", "مرحبا": "greeting", "أهلا": "greeting",
            "شنو": "what", "واش": "what/if", "كيف": "how", "فين": "where", "ملي": "when",
            "علاش": "why", "شحال": "how_much", "واخا": "okay",
            "تخصص": "program", "تخصصات": "programs", "فيلير": "program", "فيليرات": "programs",
            "مدرسة": "school", "جامعة": "university",
            "ذكاء": "ai", "اصطناعي": "ai", "بيانات": "data", "سيبر": "cyber", "أمن": "security",
            "شبكات": "networks", "برمجة": "programming", "تطوير": "development",
            "تسجيل": "registration", "قبول": "admission", "شروط": "conditions", "معدل": "average",
            "باك": "bac", "ديپلوم": "diploma",
            "ثمن": "price", "فلوس": "money", "درهم": "dirham", "بزاف": "a_lot", "غالي": "expensive",
            "رخيص": "cheap", "مجاني": "free", "بورصة": "scholarship",
            "هاد": "this", "دابا": "now", "بغيت": "want", "عندي": "i_have",
            "ممكن": "possible", "واخا": "okay",
        }

        # === DICTIONNAIRE DARIJA LATIN (alphabet français) ===
        # Enrichi avec tous les mots utilisés dans openai_service
        self.darija_latin = {
            # Salutations
            "salam": "greeting", "slm": "greeting", "ahlan": "greeting", "marhba": "greeting",
            "labas": "greeting", "wach labas": "greeting", "ach khbar": "greeting",
            # Questions
            "chno": "what", "chnou": "what", "ash": "what", "wach": "what/if", "kif": "how",
            "kifach": "how", "kifash": "how", "fin": "where", "fayn": "where",
            "mli": "when", "imta": "when", "3lach": "why", "3la": "on",
            "9deh": "how_much", "ch7al": "how_much", "waha": "okay",
            # Programmes / École
            "takhasos": "program", "tkhasos": "program", "filiere": "program",
            "filières": "programs", "filiyat": "programs",
            "mdrasa": "school", "lycée": "school", "fac": "university",
            "takwin": "training",
            # IA et Tech
            "dka2": "ai", "dkaa": "ai", "dka": "ai", "ia": "ai",
            "data": "data", "cyber": "cyber", "amn": "security",
            "reseaux": "networks", "code": "programming", "dev": "development",
            "machine learning": "ai", "deep learning": "ai",
            # Admission
            "tssjl": "registration", "9bol": "admission", "chort": "condition",
            "m3dal": "average", "note": "average", "bac": "bac", "diplome": "diploma",
            # Frais / Argent
            "taman": "price", "flous": "money", "derhem": "dirham",
            "bzzaf": "a_lot", "bzaf": "a_lot", "ghali": "expensive",
            "rkhis": "cheap", "majani": "free", "bourse": "scholarship",
            # Verbes / Particules courantes darija
            "had": "this", "hada": "this", "hadchi": "this_thing",
            "daba": "now", "bgheet": "want", "bghit": "want",
            "3ndi": "i_have", "3andi": "i_have", "mumkin": "possible",
            "kayn": "there_is", "kayna": "there_is", "mkayn": "there_is_not",
            "nqdar": "i_can", "nkdar": "i_can", "bhal": "like",
            "hna": "here", "ntoma": "you_pl", "nta": "you",
            "ana": "i", "ghir": "just", "safi": "enough/ok",
            "mzyan": "good", "zwina": "beautiful", "mochkil": "problem",
            "3awni": "help_me", "n3awnak": "i_help_you",
            "ssewel": "ask", "nssewel": "i_ask",
            "3la": "about/on", "dyal": "of/belonging_to", "dial": "of",
            "bach": "so_that", "f": "in", "m3a": "with",
            "7ta": "until/even", "bla": "without",
        }

        # === MOTS VIDES ===
        self.stop_words = {
            'fr': ['le', 'la', 'les', 'de', 'du', 'des', 'un', 'une', 'et', 'ou', 'mais',
                   'donc', 'car', 'ni', 'ce', 'cet', 'cette', 'ces', 'mon', 'ton', 'son',
                   'mes', 'tes', 'ses', 'notre', 'votre', 'leur', 'nos', 'vos', 'leurs',
                   'je', 'tu', 'il', 'elle', 'on', 'nous', 'vous', 'ils', 'elles',
                   'me', 'te', 'se', 'lui', 'ceci', 'cela', 'voici', 'voilà',
                   'chez', 'avec', 'sans', 'sous', 'sur', 'dans'],
            'en': ['the', 'a', 'an', 'and', 'or', 'but', 'if', 'then', 'else', 'when',
                   'at', 'from', 'by', 'on', 'off', 'for', 'in', 'out', 'over', 'under',
                   'to', 'into', 'with', 'as', 'than', 'also', 'very', 'just', 'so',
                   'too', 'not', 'can', 'will', 'may'],
            'ar': ['في', 'من', 'إلى', 'عن', 'على', 'مع', 'هذا', 'هذه', 'ذلك', 'تلك',
                   'كان', 'كانت', 'لم', 'لن', 'سوف', 'قد', 'هل', 'أو', 'ثم',
                   'حتى', 'عند', 'بين', 'خلال', 'أيضا'],
        }

        # === MOTS FRÉQUENTS PAR LANGUE ===
        self.common_words = {
            'french': ['est', 'sont', 'dans', 'pour', 'avec', 'sans', 'chez', 'comment',
                      'pourquoi', 'quand', 'où', 'combien', 'quel', 'quelle', 'quels', 'quelles'],
            'english': ['is', 'are', 'in', 'for', 'with', 'without', 'how', 'why', 'when',
                       'where', 'how much', 'what', 'which'],
            'darija_latin': ['f', 'd', 'had', 'hada', 'hadchi', 'bhal', '3la', '7ta', 'bla',
                            'm3a', 'kifash', '3lach', 'fayn', 'mli', 'ch7al', 'ach', 'chno',
                            'wach', 'bghit', 'kayn', 'daba', 'safi', 'mzyan'],
        }

    # ------------------------------------------------------------------ #
    # MÉTHODE PRATIQUE — utilisée par openai_service                      #
    # ------------------------------------------------------------------ #
    def detect_lang_code(self, text: str) -> str:
        """
        Raccourci qui retourne directement 'fr' | 'en' | 'ar'.
        À utiliser depuis openai_service._detect_language().
        """
        analysis = self.understand_message(text)
        primary  = analysis.get('primary_language', 'french')
        mapping  = {
            'french':        'fr',
            'english':       'en',
            'darija_latin':  'ar',
            'darija_arabic': 'ar',
            'unknown':       'fr',
        }
        return mapping.get(primary, 'fr')

    # ------------------------------------------------------------------ #
    # NORMALISATION                                                        #
    # ------------------------------------------------------------------ #
    def normalize_text(self, text: str) -> str:
        """Normalise le texte (enlève accents, met en minuscules)"""
        if not text:
            return ""
        text = unicodedata.normalize('NFKD', text)
        text = text.encode('ASCII', 'ignore').decode('utf-8')
        text = text.lower()
        arabic_digits = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
        text = text.translate(arabic_digits)
        return text

    def detect_writing_system(self, text: str) -> str:
        """Détecte si le texte est en caractères arabes ou latins"""
        arabic_chars = re.findall(r'[\u0600-\u06FF]', text)
        if len(arabic_chars) > len(text) * 0.3:
            return 'arabic'
        return 'latin'

    def extract_keywords(self, text: str) -> List[str]:
        """Extrait les mots-clés importants du texte"""
        text = re.sub(r'[^\w\s]', ' ', text)
        words = text.split()
        return [w for w in words if len(w) > 2]

    # ------------------------------------------------------------------ #
    # DÉTECTION COMPOSITION LINGUISTIQUE                                  #
    # ------------------------------------------------------------------ #
    def detect_language_composition(self, text: str) -> Dict[str, float]:
        """
        Détecte la composition linguistique du texte.
        Retourne un dictionnaire avec les scores estimés.
        """
        words = text.split()
        total = len(words) or 1

        scores = {
            'darija_arabic': 0,
            'darija_latin':  0,
            'french':        0,
            'english':       0,
            'unknown':       0,
        }

        for word in words:
            word_lower = word.lower()

            # Caractères arabes
            if any('\u0600' <= c <= '\u06FF' for c in word):
                if word in self.darija_arabic:
                    scores['darija_arabic'] += 3
                else:
                    scores['darija_arabic'] += 1

            # Darija latin (mots exacts)
            elif word_lower in self.darija_latin:
                scores['darija_latin'] += 3

            # Mots courants darija (liste commune)
            elif word_lower in self.common_words['darija_latin']:
                scores['darija_latin'] += 2

            # Mots français
            elif (word_lower in self.stop_words['fr']
                  or word_lower in self.common_words['french']
                  or word_lower.endswith(('tion', 'ment', 'eur', 'aire', 'ique'))):
                scores['french'] += 2

            # Mots anglais
            elif (word_lower in self.stop_words['en']
                  or word_lower in self.common_words['english']
                  or word_lower.endswith(('ing', 'ed', 'ly', 'ness', 'tion'))):
                scores['english'] += 2

            else:
                scores['unknown'] += 1

        return {k: (v / total) * 100 for k, v in scores.items()}

    # ------------------------------------------------------------------ #
    # COMPRÉHENSION PRINCIPALE                                            #
    # ------------------------------------------------------------------ #
    def understand_message(self, message: str) -> Dict[str, Any]:
        """
        Analyse le message et retourne:
        - primary_language : 'french' | 'english' | 'darija_latin' | 'darija_arabic'
        - intent           : catégorie de la question
        - keywords         : mots-clés extraits
        - confidence       : score de confiance (0–100)
        """
        result = {
            'original':       message,
            'normalized':     self.normalize_text(message),
            'writing_system': self.detect_writing_system(message),
            'composition':    self.detect_language_composition(message),
            'primary_language': 'unknown',
            'intent':         'unknown',
            'keywords':       [],
            'confidence':     0.0,
        }

        comp = result['composition']

        # Règle rapide : présence de caractères arabes
        if re.search(r'[\u0600-\u06FF]', message):
            result['primary_language'] = 'darija_arabic'
            result['confidence']       = 80
        else:
            candidates = {k: v for k, v in comp.items() if v > 5 and k != 'unknown'}
            if candidates:
                top = max(candidates.items(), key=lambda x: x[1])
                result['primary_language'] = top[0]
                result['confidence']       = top[1]
            else:
                # Heuristiques de secours
                msg_lower = message.lower()
                if any(w in msg_lower for w in self.common_words['darija_latin']):
                    result['primary_language'] = 'darija_latin'
                    result['confidence']       = 50
                elif any(w in msg_lower for w in self.common_words['english']):
                    result['primary_language'] = 'english'
                    result['confidence']       = 40
                elif any(w in msg_lower for w in self.common_words['french']):
                    result['primary_language'] = 'french'
                    result['confidence']       = 40
                else:
                    result['primary_language'] = 'french'
                    result['confidence']       = 30

        result['intent']   = self._detect_intent_from_keywords(message, result['primary_language'])
        result['keywords'] = self.extract_keywords(message)

        logger.info(
            f"🌍 Détection — {result['primary_language']} "
            f"(confiance: {result['confidence']:.0f}%) | intent: {result['intent']}"
        )

        return result

    # ------------------------------------------------------------------ #
    # DÉTECTION D'INTENTION                                               #
    # ------------------------------------------------------------------ #
    def _detect_intent_from_keywords(self, message: str, language: str) -> str:
        """Détecte l'intention à partir des mots-clés (multilingue)"""
        msg = message.lower()

        intent_keywords = {
            'greeting': [
                'bonjour', 'salut', 'salam', 'hello', 'hi', 'marhba', 'ahlan',
                'مرحبا', 'سلام', 'أهلا', 'labas', 'wach labas', 'ach khbar',
            ],
            'programs': [
                'programme', 'filière', 'formation', 'takhasos', 'program', 'course',
                'تخصص', 'برنامج', 'فيلير', 'filiere', 'filières', 'filiyat', 'takwin',
                'chno kayn', 'les filières', 'quelles filières',
            ],
            # IA, Data, Réseaux → filières IISIC / IISRT / ISI (vraies filières Data1.txt)
            'engineering': [
                'ia', 'intelligence artificielle', 'ai', 'artificial intelligence',
                'data', 'machine learning', 'deep learning', 'data science',
                'réseau', 'reseau', 'telecom', 'télécommunication', 'iot',
                'informatique', 'iisrt', 'iisic', 'isi', 'ingénierie',
                'ذكاء', 'dka', 'réseaux', 'systèmes',
            ],
            # Management → filières Management / FACG / MSTIC (vraies filières Data1.txt)
            'management': [
                'management', 'finance', 'audit', 'gestion', 'facg', 'mstic',
                'comptabilité', 'commercial', 'marketing', 'entreprise',
                'contrôle de gestion', 'relations internationales',
            ],
            'admission': [
                'admission', 'inscription', 'concours', 'dossier', 'inscrire',
                'تسجيل', 'قبول', 'tssjl', '9bol', 'comment s\'inscrire',
                'conditions', 'bac', 'prérequis',
            ],
            'fees': [
                'frais', 'prix', 'coût', 'bourse', 'paiement', 'tarif', 'mensualité',
                'فلوس', 'ثمن', 'flous', 'taman', 'bzzaf', 'ghali', 'dirham', 'dh',
            ],
            'contact': [
                'contact', 'téléphone', 'adresse', 'email', 'localisation', 'site',
                'اتصال', 'عنوان', 'هاتف', 'telfon', '3nwan', 'joini',
            ],
            'international': [
                'international', 'partenaire', 'efrei', 'lorraine', 'double diplôme',
                'étranger', 'france', 'mobilité', 'ensiie', 'igs', 'istec',
            ],
            'certifications': [
                'certification', 'cisco', 'microsoft', 'oracle', 'ccna', 'ccnp',
                'certifié', 'certif',
            ],
            'career': [
                'débouché', 'métier', 'travail', 'emploi', 'carrière', 'job',
                'وظيفة', 'شغل', 'khdma', 'après', 'insertion',
            ],
            'farewell': [
                'au revoir', 'bye', 'سلام', 'slm', 'مع السلامة', 'bslama',
            ],
        }

        for intent, keywords in intent_keywords.items():
            if any(kw in msg for kw in keywords):
                return intent

        return 'general'

    # ------------------------------------------------------------------ #
    # UTILITAIRES                                                         #
    # ------------------------------------------------------------------ #
    def get_language_name(self, lang_code: str) -> str:
        names = {
            'french':        'Français',
            'english':       'English',
            'darija_latin':  'Darija (Latin)',
            'darija_arabic': 'الدارجة',
            'unknown':       'Inconnu',
        }
        return names.get(lang_code, lang_code)