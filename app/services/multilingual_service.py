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
            # Salutations
            "السلام": "greeting", "سلام": "greeting", "مرحبا": "greeting", "أهلا": "greeting",
            # Questions courantes
            "شنو": "what", "واش": "what/if", "كيف": "how", "فين": "where", "ملي": "when",
            "علاش": "why", "شحال": "how_much", "واخا": "okay",
            # Programmes
            "تخصص": "program", "تخصصات": "programs", "فيلير": "program", "فيليرات": "programs",
            "مدرسة": "school", "جامعة": "university",
            # IA et Tech
            "ذكاء": "ai", "اصطناعي": "ai", "بيانات": "data", "سيبر": "cyber", "أمن": "security",
            "شبكات": "networks", "برمجة": "programming", "تطوير": "development",
            # Admission
            "تسجيل": "registration", "قبول": "admission", "شروط": "conditions", "معدل": "average",
            "باك": "bac", "ديپلوم": "diploma",
            # Frais
            "ثمن": "price", "فلوس": "money", "درهم": "dirham", "بزاف": "a_lot", "غالي": "expensive",
            "رخيص": "cheap", "مجاني": "free", "بورصة": "scholarship",
            # Divers
            "هاد": "this", "دaba": "now", "دابا": "now", "بغيت": "want", "عندي": "i_have",
            "ممكن": "possible", "واخا": "okay", "سلام": "bye"
        }
        
        # === DICTIONNAIRE DARIJA LATIN (alphabet français) ===
        self.darija_latin = {
            # Salutations
            "salam": "greeting", "slm": "greeting", "ahlan": "greeting", "marhba": "greeting",
            # Questions courantes
            "chno": "what", "chnou": "what", "ash": "what", "wach": "what/if", "kif": "how",
            "kifach": "how", "fin": "where", "fayn": "where", "mli": "when", "imta": "when",
            "3lach": "why", "3la": "why", "9deh": "how_much", "ch7al": "how_much", "waha": "okay",
            # Programmes
            "takhasos": "program", "tkhasos": "program", "filiere": "program", "filières": "programs",
            "mdrasa": "school", "lycée": "school", "fac": "university",
            # IA et Tech
            "dka2": "ai", "dkaa": "ai", "dka": "ai", "intelligence": "ai", "ia": "ai",
            "données": "data", "data": "data", "cyber": "cyber", "amn": "security", "sécurité": "security",
            "réseaux": "networks", "reseaux": "networks", "programmation": "programming",
            "codage": "programming", "code": "programming", "dev": "development",
            # Admission
            "tssjl": "registration", "9bol": "admission", "chort": "condition", "m3dal": "average",
            "note": "average", "bac": "bac", "diplome": "diploma",
            # Frais
            "taman": "price", "flous": "money", "derhem": "dirham", "bzzaf": "a_lot", "ghali": "expensive",
            "rkhis": "cheap", "majani": "free", "bourse": "scholarship",
            # Divers
            "had": "this", "hada": "this", "daba": "now", "daba": "now", "bgheet": "want", "bghit": "want",
            "3ndi": "i_have", "mumkin": "possible", "waha": "okay", "slm": "bye"
        }
        
        # === MOTS VIDES (stop words) pour le nettoyage ===
        self.stop_words = {
            'fr': ['le', 'la', 'les', 'de', 'du', 'des', 'un', 'une', 'et', 'ou', 'mais', 'donc',
                   'car', 'ni', 'ce', 'cet', 'cette', 'ces', 'mon', 'ton', 'son', 'mes', 'tes', 'ses',
                   'notre', 'votre', 'leur', 'nos', 'vos', 'leurs', 'je', 'tu', 'il', 'elle', 'on',
                   'nous', 'vous', 'ils', 'elles', 'me', 'te', 'se', 'lui', 'leur', 'ceci', 'cela',
                   'voici', 'voilà', 'il y a', 'chez', 'avec', 'sans', 'sous', 'sur', 'dans'],
            
            'en': ['the', 'a', 'an', 'and', 'or', 'but', 'if', 'then', 'else', 'when', 'at', 'from',
                   'by', 'on', 'off', 'for', 'in', 'out', 'over', 'under', 'to', 'into', 'with',
                   'as', 'than', 'also', 'very', 'just', 'so', 'too', 'not', 'can', 'will', 'may'],
            
            'ar': ['في', 'من', 'إلى', 'عن', 'على', 'مع', 'هذا', 'هذه', 'ذلك', 'تلك', 'كان', 'كانت',
                   'لم', 'لن', 'سوف', 'قد', 'هل', 'أو', 'ثم', 'حتى', 'عند', 'بين', 'خلال', 'أيضا']
        }
        
        # === MOTS FRÉQUENTS PAR LANGUE POUR AMÉLIORER LA DÉTECTION ===
        self.common_words = {
            'french': ['est', 'sont', 'dans', 'pour', 'avec', 'sans', 'chez', 'comment', 'pourquoi',
                      'quand', 'où', 'combien', 'quel', 'quelle', 'quels', 'quelles'],
            
            'english': ['is', 'are', 'in', 'for', 'with', 'without', 'how', 'why', 'when', 'where',
                       'how much', 'what', 'which'],
            
            'darija_latin': ['f', 'd', 'had', 'hada', 'hadchi', 'bhal', '3la', '7ta', 'bla', 'm3a',
                            'kifash', '3lach', 'fayn', 'mli', 'ch7al', 'ach', 'chno']
        }
        
    def normalize_text(self, text: str) -> str:
        """Normalise le texte (enlève accents, met en minuscules)"""
        if not text:
            return ""
        
        # Normaliser les caractères Unicode
        text = unicodedata.normalize('NFKD', text)
        text = text.encode('ASCII', 'ignore').decode('utf-8')
        
        # Mettre en minuscules
        text = text.lower()
        
        # Remplacer les chiffres arabes par des latins
        arabic_digits = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
        text = text.translate(arabic_digits)
        
        return text
    
    def detect_writing_system(self, text: str) -> str:
        """Détecte si le texte est en caractères arabes ou latins"""
        # Compter les caractères arabes
        arabic_chars = re.findall(r'[\u0600-\u06FF]', text)
        
        if len(arabic_chars) > len(text) * 0.3:  # Plus de 30% de caractères arabes
            return 'arabic'
        else:
            return 'latin'
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extrait les mots-clés importants du texte"""
        # Nettoyer le texte
        text = re.sub(r'[^\w\s]', ' ', text)
        words = text.split()
        
        # Enlever les mots trop courts
        keywords = [w for w in words if len(w) > 2]
        
        return keywords
    
    def detect_language_composition(self, text: str) -> Dict[str, float]:
        """
        Détecte la composition linguistique du texte.
        Retourne un dictionnaire avec les pourcentages estimés.
        """
        words = text.split()
        total = len(words) or 1
        
        scores = {
            'darija_arabic': 0,
            'darija_latin': 0,
            'french': 0,
            'english': 0,
            'unknown': 0
        }
        
        for word in words:
            word_lower = word.lower()
            
            # Vérifier si le mot est en darija (arabe)
            if any(char >= '\u0600' and char <= '\u06FF' for char in word):
                if word in self.darija_arabic:
                    scores['darija_arabic'] += 3  # Poids plus élevé pour les mots connus
                else:
                    scores['darija_arabic'] += 1  # Caractère arabe mais mot inconnu
                    
            # Vérifier si le mot est en darija (latin)
            elif word_lower in self.darija_latin:
                scores['darija_latin'] += 3
                
            # Mots français courants
            elif word_lower in self.stop_words['fr'] or word_lower.endswith(('tion', 'ment', 'eur', 'aire')):
                scores['french'] += 2
                
            # Mots anglais courants
            elif word_lower in self.stop_words['en'] or word_lower.endswith(('ing', 'ed', 'ly', 'tion')):
                scores['english'] += 2
                
            # Mots communs spécifiques
            elif word_lower in self.common_words['french']:
                scores['french'] += 2
            elif word_lower in self.common_words['english']:
                scores['english'] += 2
            elif word_lower in self.common_words['darija_latin']:
                scores['darija_latin'] += 2
                
            else:
                scores['unknown'] += 1
        
        # Convertir en pourcentages
        return {k: (v / total) * 100 for k, v in scores.items()}
    
    def understand_message(self, message: str) -> Dict[str, Any]:
        """
        Fonction principale de compréhension.
        Analyse le message et retourne:
        - La langue principale détectée
        - Les intentions
        - Les mots-clés extraits
        - Une version normalisée
        """
        result = {
            'original': message,
            'normalized': self.normalize_text(message),
            'writing_system': self.detect_writing_system(message),
            'composition': self.detect_language_composition(message),
            'primary_language': 'unknown',
            'intent': 'unknown',
            'keywords': [],
            'confidence': 0.0
        }
        
        # Déterminer la langue principale
        comp = result['composition']
        
        # Filtrer les langues avec un score significatif
        candidates = {k: v for k, v in comp.items() if v > 10 and k != 'unknown'}
        
        if candidates:
            # Prendre la langue avec le score le plus élevé
            max_lang = max(candidates.items(), key=lambda x: x[1])
            result['primary_language'] = max_lang[0]
            result['confidence'] = max_lang[1]
        else:
            # Si aucun candidat clair, utiliser des heuristiques
            if any(char >= '\u0600' and char <= '\u06FF' for char in message):
                result['primary_language'] = 'darija_arabic'
                result['confidence'] = 50
            elif any(word in message.lower() for word in self.common_words['french']):
                result['primary_language'] = 'french'
                result['confidence'] = 40
            elif any(word in message.lower() for word in self.common_words['english']):
                result['primary_language'] = 'english'
                result['confidence'] = 40
            else:
                result['primary_language'] = 'french'  # Langue par défaut
                result['confidence'] = 30
        
        # Extraire l'intention
        result['intent'] = self._detect_intent_from_keywords(message, result['primary_language'])
        
        # Extraire les mots-clés
        result['keywords'] = self.extract_keywords(message)
        
        # Log pour debug
        logger.info(f"🌍 Détection langue: {result['primary_language']} (confiance: {result['confidence']:.1f}%)")
        
        return result
    
    def _detect_intent_from_keywords(self, message: str, language: str) -> str:
        """Détecte l'intention à partir des mots-clés"""
        message_lower = message.lower()
        
        # Mots-clés d'intention par catégorie (multilingues)
        intent_keywords = {
            'greeting': ['bonjour', 'salut', 'salam', 'hello', 'hi', 'marhba', 'ahlan', 
                        'مرحبا', 'سلام', 'أهلا'],
            
            'programs': ['programme', 'filière', 'formation', 'takhasos', 'program', 'course',
                        'تخصص', 'برنامج', 'فيلير'],
            
            'ai': ['ia', 'intelligence', 'artificielle', 'data', 'machine learning', 'deep learning',
                  'ذكاء', 'dka', 'data science'],
            
            'cyber': ['cyber', 'sécurité', 'securite', 'hacking', 'pentest', 'cryptographie',
                     'أمن', 'amn', 'سيبر'],
            
            'admission': ['admission', 'inscription', 'concours', 'comment s\'inscrire', 'dossier',
                         'تسجيل', 'قبول', 'tssjl', '9bol'],
            
            'fees': ['frais', 'prix', 'coût', 'bourse', 'paiement', 'mensualité', 'tarif',
                    'فلوس', 'ثمن', 'flous', 'taman'],
            
            'contact': ['contact', 'téléphone', 'telephone', 'adresse', 'email', 'localisation',
                       'اتصال', 'عنوان', 'هاتف'],
            
            'career': ['débouché', 'métier', 'travail', 'emploi', 'carrière', 'job',
                      'وظيفة', 'شغل', 'khdma'],
            
            'farewell': ['au revoir', 'bye', 'سلام', 'slm', 'مع السلامة']
        }
        
        # Vérifier chaque intention
        for intent, keywords in intent_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                return intent
        
        return 'general'
    
    def get_language_name(self, lang_code: str) -> str:
        """Retourne le nom complet de la langue"""
        names = {
            'french': 'Français',
            'english': 'English',
            'darija_latin': 'Darija (Latin)',
            'darija_arabic': 'الدارجة',
            'unknown': 'Inconnu'
        }
        return names.get(lang_code, lang_code)
