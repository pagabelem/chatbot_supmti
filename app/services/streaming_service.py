"""
Service de streaming pour les réponses du chat.
Version améliorée avec mode démo enrichi, streaming optimisé et support multilingue.
"""
import asyncio
import openai
from typing import AsyncGenerator, Optional, Dict, List
from sqlalchemy.orm import Session
import uuid
import re
import random

from app.core.config import settings
from app.core.logging import logger
from app.database.models import Student, Program, Conversation, Message, Interest, StudentInterest
from app.api.routes.compare import get_career_by_keywords
from app.services.multilingual_service import MultilingualService

class StreamingService:
    """Service pour gérer le streaming des réponses"""
    
    def __init__(self, db: Session):
        self.db = db
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        self.multilingual = MultilingualService()
        
        # === BASE DE CONNAISSANCES AMÉLIORÉE POUR LE MODE DÉMO ===
        self.knowledge_base = {
            "greetings": {
                "patterns": ["bonjour", "salut", "hello", "hi", "coucou", "bonsoir", "cc", "salam", "marhba", "ahlan"],
                "responses": {
                    "french": "Bonjour ! 👋 Comment puis-je vous aider avec votre orientation ?",
                    "english": "Hello! 👋 How can I help you with your orientation?",
                    "darija_latin": "Salam! 👋 Kifach n3awnkom f tawjih dialkom?",
                    "darija_arabic": "سلام! 👋 كيفاش نعونكم ف التوجيه ديالكم؟"
                }
            },
            "programs": {
                "patterns": ["programme", "formation", "filière", "cours", "matière", "étudier", "takhasos", "تخصص"],
                "responses": {
                    "french": "📚 **Programmes disponibles à SUP MTI :**\n\n**Cycle Ingénieur / Bachelor (3 ans) :**\n• 🧠 **Intelligence Artificielle et Data Science**\n• 🛡️ **Cybersécurité et Confiance Numérique**\n• 💻 **Génie Logiciel et Cloud Computing**\n• 🌐 **Réseaux et Télécommunications**\n\n**Cycle Master (5 ans) :**\n• 📈 **Management des Systèmes d'Information**\n• 💰 **Finance, Audit et Contrôle de Gestion**\n\nSouhaitez-vous des détails sur un programme en particulier ?",
                    "english": "📚 **Available programs at SUP MTI:**\n\n**Engineering / Bachelor Cycle (3 years):**\n• 🧠 **Artificial Intelligence and Data Science**\n• 🛡️ **Cybersecurity and Digital Trust**\n• 💻 **Software Engineering and Cloud Computing**\n• 🌐 **Networks and Telecommunications**\n\n**Master Cycle (5 years):**\n• 📈 **Information Systems Management**\n• 💰 **Finance, Audit and Management Control**\n\nWould you like details on a specific program?",
                    "darija_latin": "📚 **Takhasosat motaha f SUP MTI:**\n\n**Cycle Ingénieur / Bachelor (3 snin):**\n• 🧠 **Intelligence Artificielle et Data Science**\n• 🛡️ **Cybersécurité et Confiance Numérique**\n• 💻 **Génie Logiciel et Cloud Computing**\n• 🌐 **Réseaux et Télécommunications**\n\n**Cycle Master (5 snin):**\n• 📈 **Management des Systèmes d'Information**\n• 💰 **Finance, Audit et Contrôle de Gestion**\n\nBghiti t9ra 3la wa7d takhasos b dorof?",
                    "darija_arabic": "📚 **التخصصات المتاحة في SUP MTI:**\n\n**دورة الهندسة / باكالوريوس (3 سنوات):**\n• 🧠 **الذكاء الاصطناعي وعلوم البيانات**\n• 🛡️ **الأمن السيبراني والثقة الرقمية**\n• 💻 **هندسة البرمجيات والحوسبة السحابية**\n• 🌐 **الشبكات والاتصالات**\n\n**دورة الماستر (5 سنوات):**\n• 📈 **تدبير أنظمة المعلومات**\n• 💰 **المالية والتدقيق وتدبير المخاطر**\n\nبغيتي تقرى على تخصص معين؟"
                }
            },
            "ai_program": {
                "patterns": ["ia", "intelligence artificielle", "artificielle", "machine learning", "deep learning", "data science", "data", "dka", "ذكاء"],
                "responses": {
                    "french": "🧠 **Programme Intelligence Artificielle et Data Science**\n\n**Description :** Formation avancée en IA, Machine Learning, Deep Learning et Big Data.\n\n**Durée :** 3 ans (Bachelor)\n**Prérequis :** BAC Scientifique avec bon niveau en maths\n**Certifications :** TensorFlow, AWS AI, Microsoft Azure AI\n\n**Débouchés :**\n• Data Scientist\n• Ingénieur IA\n• ML Engineer\n• Data Analyst\n• Chercheur en IA\n\n**Matières principales :**\n• Machine Learning\n• Deep Learning\n• NLP (Traitement du langage)\n• Computer Vision\n• Python, TensorFlow, PyTorch",
                    "english": "🧠 **Artificial Intelligence and Data Science Program**\n\n**Description:** Advanced training in AI, Machine Learning, Deep Learning and Big Data.\n\n**Duration:** 3 years (Bachelor)\n**Prerequisites:** Scientific Baccalaureate with good math level\n**Certifications:** TensorFlow, AWS AI, Microsoft Azure AI\n\n**Career opportunities:**\n• Data Scientist\n• AI Engineer\n• ML Engineer\n• Data Analyst\n• AI Researcher\n\n**Main subjects:**\n• Machine Learning\n• Deep Learning\n• NLP\n• Computer Vision\n• Python, TensorFlow, PyTorch",
                    "darija_latin": "🧠 **Programme Intelligence Artificielle et Data Science**\n\n**Description:** Takwin moutaqadim f l'IA, Machine Learning, Deep Learning o Big Data.\n\n**Mouadda:** 3 snin (Bachelor)\n**Chourout:** BAC 3ilmi m3a mustawa jayid f l'maths\n**Chahadat:** TensorFlow, AWS AI, Microsoft Azure AI\n\n**Farass choghl:**\n• Mohandis données\n• Mohandis IA\n• ML Engineer\n• Data Analyst\n• Bahith f l'IA",
                    "darija_arabic": "🧠 **برنامج الذكاء الاصطناعي وعلوم البيانات**\n\n**الوصف:** تكوين متقدم في الذكاء الاصطناعي والتعلم الآلي والتعلم العميق والبيانات الضخمة.\n\n**المدة:** 3 سنوات (باكالوريوس)\n**شروط القبول:** باك علمي بمستوى جيد في الرياضيات\n**الشهادات:** TensorFlow, AWS AI, Microsoft Azure AI\n\n**فرص العمل:**\n• مهندس بيانات\n• مهندس ذكاء اصطناعي\n• مهندس تعلم آلي\n• محلل بيانات\n• باحث في الذكاء الاصطناعي"
                }
            },
            "cyber_program": {
                "patterns": ["cyber", "sécurité", "securite", "hacking", "pentest", "cryptographie", "forensic", "amn", "أمن"],
                "responses": {
                    "french": "🛡️ **Programme Cybersécurité et Confiance Numérique**\n\n**Description :** Formation complète en sécurité des systèmes, ethical hacking, cryptographie et gouvernance.\n\n**Durée :** 3 ans (Bachelor)\n**Prérequis :** BAC Scientifique ou Technique\n**Certifications :** CEH, Cisco CCNA Security, CompTIA Security+\n\n**Débouchés :**\n• Analyste Cyber (SOC)\n• Pentester (Ethical Hacker)\n• RSSI (Responsable Sécurité)\n• Consultant en sécurité\n• Forensic Analyst\n\n**Matières principales :**\n• Cryptographie\n• Ethical Hacking\n• Sécurité réseau\n• Forensique\n• SOC (Security Operations Center)",
                    "english": "🛡️ **Cybersecurity and Digital Trust Program**\n\n**Description:** Comprehensive training in systems security, ethical hacking, cryptography and governance.\n\n**Duration:** 3 years (Bachelor)\n**Prerequisites:** Scientific or Technical Baccalaureate\n**Certifications:** CEH, Cisco CCNA Security, CompTIA Security+\n\n**Career opportunities:**\n• Cyber Analyst (SOC)\n• Pentester (Ethical Hacker)\n• CISO\n• Security Consultant\n• Forensic Analyst",
                    "darija_latin": "🛡️ **Programme Cybersécurité et Confiance Numérique**\n\n**Description:** Takwin chamil f amn l'anodima, ethical hacking, cryptographie o gouvernance.\n\n**Mouadda:** 3 snin (Bachelor)\n**Chourout:** BAC 3ilmi ou taqni\n**Chahadat:** CEH, Cisco CCNA Security, CompTIA Security+\n\n**Farass choghl:**\n• Analyste Cyber (SOC)\n• Pentester\n• Responsable Sécurité\n• Consultant sécurité",
                    "darija_arabic": "🛡️ **برنامج الأمن السيبراني والثقة الرقمية**\n\n**الوصف:** تكوين شامل في أمن الأنظمة والاختراق الأخلاقي والتشفير.\n\n**المدة:** 3 سنوات (باكالوريوس)\n**شروط القبول:** باك علمي أو تقني\n**الشهادات:** CEH, Cisco CCNA Security, CompTIA Security+\n\n**فرص العمل:**\n• محلل أمن سيبراني\n• مختبر اختراق\n• مسؤول أمن المعلومات\n• مستشار أمني"
                }
            },
            "software_program": {
                "patterns": ["logiciel", "software", "développement", "programmation", "code", "dev", "full stack", "mobile", "برمجة"],
                "responses": {
                    "french": "💻 **Programme Génie Logiciel et Cloud Computing**\n\n**Description :** Développement d'applications modernes, architectures cloud, DevOps et conteneurisation.\n\n**Durée :** 3 ans (Bachelor)\n**Prérequis :** BAC Scientifique ou Technique\n**Certifications :** AWS, Azure, Docker, Kubernetes\n\n**Débouchés :**\n• Développeur Full Stack\n• Architecte logiciel\n• DevOps Engineer\n• Tech Lead\n• Ingénieur Cloud\n\n**Matières principales :**\n• Algorithmique avancée\n• Bases de données\n• Développement Web/Mobile\n• Architecture logicielle\n• Docker, Kubernetes, AWS/Azure",
                    "english": "💻 **Software Engineering and Cloud Computing Program**\n\n**Description:** Modern application development, cloud architectures, DevOps and containerization.\n\n**Duration:** 3 years (Bachelor)\n**Prerequisites:** Scientific or Technical Baccalaureate\n**Certifications:** AWS, Azure, Docker, Kubernetes\n\n**Career opportunities:**\n• Full Stack Developer\n• Software Architect\n• DevOps Engineer\n• Tech Lead\n• Cloud Engineer",
                    "darija_latin": "💻 **Programme Génie Logiciel et Cloud Computing**\n\n**Description:** Tatwir les applications modernes, architectures cloud, DevOps o conteneurisation.\n\n**Mouadda:** 3 snin (Bachelor)\n**Chourout:** BAC 3ilmi ou taqni\n**Chahadat:** AWS, Azure, Docker, Kubernetes\n\n**Farass choghl:**\n• Développeur Full Stack\n• Architecte logiciel\n• DevOps Engineer\n• Ingénieur Cloud",
                    "darija_arabic": "💻 **برنامج هندسة البرمجيات والحوسبة السحابية**\n\n**الوصف:** تطوير التطبيقات الحديثة والهندسة السحابية و DevOps.\n\n**المدة:** 3 سنوات (باكالوريوس)\n**شروط القبول:** باك علمي أو تقني\n**الشهادات:** AWS, Azure, Docker, Kubernetes\n\n**فرص العمل:**\n• مطور تطبيقات\n• مهندس برمجيات\n• مهندس DevOps\n• مهندس سحابي"
                }
            },
            "admission": {
                "patterns": ["admission", "inscription", "comment s'inscrire", "dossier", "concours", "تسجيل", "قبول"],
                "responses": {
                    "french": "📝 **Procédure d'admission à SUP MTI :**\n\n**1. Pré-requis :**\n• Baccalauréat (toutes séries)\n• Dossier scolaire\n\n**2. Étapes :**\n• Dépôt du dossier en ligne\n• Étude du dossier\n• Entretien de motivation\n• Résultats sous 48h\n\n**3. Dates importantes :**\n• Pré-inscription : Mars - Juillet\n• Concours : Juillet\n• Rentrée : Septembre\n\n**4. Frais :**\n• Frais d'inscription : 3 500 DH\n• Scolarité : 35 000 DH/an (payable en 10 mensualités)\n\n📞 Contact : +212 5 35 51 10 11",
                    "english": "📝 **Admission procedure at SUP MTI:**\n\n**1. Prerequisites:**\n• Baccalaureate (all series)\n• Academic record\n\n**2. Steps:**\n• Online application\n• File review\n• Motivation interview\n• Results within 48h\n\n**3. Important dates:**\n• Pre-registration: March - July\n• Competition: July\n• Start of academic year: September\n\n**4. Fees:**\n• Registration fees: 3,500 MAD\n• Tuition: 35,000 MAD/year (payable in 10 installments)",
                    "darija_latin": "📝 **Procédure d'admission à SUP MTI:**\n\n**1. Chourout:**\n• Bac (jamii3 ch3ab)\n• Dossier scolaire\n\n**2. Khoutawat:**\n• Depôt du dossier en ligne\n• Étude du dossier\n• Entretien de motivation\n• Résultats dans 48h\n\n**3. Tarikh mhimma:**\n• Pré-inscription: Mars - Juillet\n• Concours: Juillet\n• Rentrée: Septembre\n\n**4. Frais:**\n• Inscription: 3 500 DH\n• Année: 35 000 DH/an (10 mensualités)\n\n📞 Contact: +212 5 35 51 10 11",
                    "darija_arabic": "📝 **إجراءات القبول في SUP MTI:**\n\n**1. الشروط:**\n• الباكالوريا (جميع الشعب)\n• الملف الدراسي\n\n**2. الخطوات:**\n• تقديم الملف عبر الإنترنت\n• دراسة الملف\n• مقابلة شخصية\n• النتائج في غضون 48 ساعة\n\n**3. التواريخ المهمة:**\n• التسجيل المبدئي: مارس - يوليوز\n• المباراة: يوليوز\n• الدخول المدرسي: شتنبر\n\n**4. المصاريف:**\n• التسجيل: 3 500 درهم\n• السنة الدراسية: 35 000 درهم/سنة"
                }
            },
            "fees": {
                "patterns": ["frais", "prix", "coût", "tarif", "bourse", "paiement", "mensualité", "فلوس", "ثمن"],
                "responses": {
                    "french": "💰 **Frais de scolarité SUP MTI :**\n\n• **Frais d'inscription :** 3 500 DH (une seule fois)\n• **Scolarité annuelle :** 35 000 DH\n• **Paiement :** 10 mensualités de 3 500 DH\n\n**Bourses d'excellence :**\n• Bourses de 30% à 100% selon les résultats au concours\n• Attribution basée sur le mérite académique\n\n**Exemple avec bourse 40% :**\n• Scolarité après bourse : 21 000 DH\n• Total annuel : 24 500 DH (scolarité + inscription)\n\n📞 Contact pour plus d'informations : +212 5 35 51 10 11",
                    "english": "💰 **SUP MTI Tuition Fees:**\n\n• **Registration fees:** 3,500 MAD (one time)\n• **Annual tuition:** 35,000 MAD\n• **Payment:** 10 installments of 3,500 MAD\n\n**Excellence scholarships:**\n• Scholarships from 30% to 100% based on competition results\n• Awarded based on academic merit\n\n**Example with 40% scholarship:**\n• Tuition after scholarship: 21,000 MAD\n• Total annual: 24,500 MAD (tuition + registration)",
                    "darija_latin": "💰 **Frais de scolarité SUP MTI:**\n\n• **Frais d'inscription:** 3 500 DH (marra whda)\n• **Année:** 35 000 DH\n• **Paiement:** 10 mois f 3 500 DH\n\n**Bourses d'excellence:**\n• Bourses mn 30% 7ta 100% 7ssab les résultats f concours\n• 3la 7sab l'mérite académique\n\n**Mtal 3la bourse 40%:**\n• Année après bourse: 21 000 DH\n• Total annuel: 24 500 DH (scolarité + inscription)\n\n📞 Contact: +212 5 35 51 10 11",
                    "darija_arabic": "💰 **مصاريف الدراسة في SUP MTI:**\n\n• **مصاريف التسجيل:** 3 500 درهم (مرة واحدة)\n• **السنة الدراسية:** 35 000 درهم\n• **الدفع:** 10 أقساط بقيمة 3 500 درهم\n\n**المنح الدراسية:**\n• منح من 30% إلى 100% حسب نتائج المباراة\n• على أساس الاستحقاق الأكاديمي\n\n**مثال على منحة 40%:**\n• السنة بعد المنحة: 21 000 درهم\n• المجموع السنوي: 24 500 درهم"
                }
            },
            "contact": {
                "patterns": ["contact", "adresse", "téléphone", "email", "joindre", "localisation", "اتصال"],
                "responses": {
                    "french": "📞 **Contact SUP MTI Meknès :**\n\n**Adresse :**\nSUP MTI Meknès\nCentre-ville, Meknès\n\n**Téléphone :**\n☎️ +212 5 35 51 10 11\n\n**Email :**\n📧 contact@supmtimeknes.ac.ma\n\n**Horaires :**\n• Lundi - Vendredi : 08:30 - 18:00\n• Samedi : 08:30 - 12:00\n\n**Site web :**\n🌐 www.supmtimeknes.ac.ma",
                    "english": "📞 **Contact SUP MTI Meknès:**\n\n**Address:**\nSUP MTI Meknès\nDowntown, Meknes\n\n**Phone:**\n☎️ +212 5 35 51 10 11\n\n**Email:**\n📧 contact@supmtimeknes.ac.ma\n\n**Hours:**\n• Monday - Friday: 08:30 - 18:00\n• Saturday: 08:30 - 12:00\n\n**Website:**\n🌐 www.supmtimeknes.ac.ma",
                    "darija_latin": "📞 **Contact SUP MTI Meknès:**\n\n**Adresse:**\nSUP MTI Meknès\nCentre-ville, Meknès\n\n**Téléphone:**\n☎️ +212 5 35 51 10 11\n\n**Email:**\n📧 contact@supmtimeknes.ac.ma\n\n**Horaires:**\n• Lundi - Vendredi: 08:30 - 18:00\n• Samedi: 08:30 - 12:00",
                    "darija_arabic": "📞 **اتصل ب SUP MTI مكناس:**\n\n**العنوان:**\nSUP MTI مكناس\nوسط المدينة، مكناس\n\n**الهاتف:**\n☎️ +212 5 35 51 10 11\n\n**البريد الإلكتروني:**\n📧 contact@supmtimeknes.ac.ma\n\n**ساعات العمل:**\n• الإثنين - الجمعة: 08:30 - 18:00\n• السبت: 08:30 - 12:00"
                }
            },
            "default": {
                "responses": {
                    "french": "Je peux vous renseigner sur :\n\n📚 **Programmes :** IA, Cybersécurité, Génie Logiciel, Management, Finance, Réseaux\n🎓 **Admission :** Conditions, concours, inscriptions\n💰 **Frais :** Scolarité, bourses, paiements\n🌍 **International :** Partenariats, doubles diplômes\n🎉 **Vie étudiante :** Clubs, événements, campus\n📞 **Contact :** Coordonnées, horaires, localisation\n\nQue souhaitez-vous savoir ?",
                    "english": "I can help you with:\n\n📚 **Programs:** AI, Cybersecurity, Software Engineering, Management, Finance, Networks\n🎓 **Admission:** Requirements, competition, registration\n💰 **Fees:** Tuition, scholarships, payments\n🌍 **International:** Partnerships, double degrees\n🎉 **Student life:** Clubs, events, campus\n📞 **Contact:** Address, phone, hours\n\nWhat would you like to know?",
                    "darija_latin": "N9der n3awnkom f:\n\n📚 **Programmes:** IA, Cybersécurité, Génie Logiciel, Management, Finance, Réseaux\n🎓 **Admission:** Conditions, concours, inscriptions\n💰 **Frais:** Scolarité, bourses, paiements\n🌍 **International:** Partenariats, doubles diplômes\n🎉 **Vie étudiante:** Clubs, événements, campus\n📞 **Contact:** Coordonnées, horaires, localisation\n\nChno bghiti t3ref?",
                    "darija_arabic": "نقدر نعاونك ف:\n\n📚 **البرامج:** الذكاء الاصطناعي، الأمن السيبراني، هندسة البرمجيات، التدبير، المالية، الشبكات\n🎓 **التسجيل:** الشروط، المباراة، التسجيل\n💰 **المصاريف:** السنة، البورصات، الدفع\n🌍 **الدولي:** الشراكات، الشهادات المزدوجة\n🎉 **الحياة الطلابية:** الأندية، الأنشطة، الحرم الجامعي\n📞 **الاتصال:** العنوان، الهاتف، ساعات العمل\n\nشنو بغيتي تعرف؟"
                }
            }
        }
    
    async def stream_response(
        self,
        message: str,
        student_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Génère une réponse en streaming optimisée avec support multilingue.
        """
        logger.info(f"💬 Streaming pour: {message[:50]}...")
        
        # === 1. Analyser le message avec le service multilingue ===
        analysis = self.multilingual.understand_message(message)
        logger.info(f"🌍 Analyse linguistique - Langue: {analysis['primary_language']}, Intention: {analysis['intent']}, Confiance: {analysis['confidence']:.1f}%")
        
        # === 2. Récupérer l'étudiant ===
        student = await self._get_student(student_id)
        
        # === 3. Sauvegarder le message utilisateur ===
        conversation = await self._save_user_message(message, student)
        
        # === 4. Générer la réponse en streaming ===
        if self.client:
            async for chunk in self._stream_openai_optimized(message, student, analysis):
                yield chunk
        else:
            async for chunk in self._stream_demo_multilingual(message, student, analysis):
                yield chunk
    
    async def _stream_demo_multilingual(
        self, 
        message: str, 
        student: Optional[Student], 
        analysis: Dict
    ) -> AsyncGenerator[str, None]:
        """Streaming optimisé avec compréhension multilingue"""
        
        # Déterminer la langue principale
        primary_lang = analysis['primary_language']
        intent = analysis['intent']
        
        logger.info(f"🗣️ Génération réponse en: {primary_lang} pour intention: {intent}")
        
        # Sélectionner le template de réponse approprié
        response = self._get_response_by_intent(intent, primary_lang, student)
        
        # Streamer la réponse
        chunks = self._smart_split(response)
        full_response = ""
        
        for chunk in chunks:
            full_response += chunk
            yield chunk
            # Délai adaptatif
            if chunk.endswith(('.', '!', '?', ':\n')):
                await asyncio.sleep(0.08)
            elif chunk.endswith(','):
                await asyncio.sleep(0.05)
            else:
                await asyncio.sleep(0.02)
        
        # Sauvegarder la réponse
        if student:
            conversation = await self._get_conversation(student)
            if conversation:
                await self._save_bot_message(full_response, conversation)
    
    def _get_response_by_intent(self, intent: str, lang: str, student: Optional[Student]) -> str:
        """Retourne la réponse appropriée selon l'intention et la langue"""
        
        # Mapper les langues détectées vers les clés de la base
        lang_map = {
            'french': 'french',
            'english': 'english',
            'darija_latin': 'darija_latin',
            'darija_arabic': 'darija_arabic',
            'unknown': 'french'
        }
        target_lang = lang_map.get(lang, 'french')
        
        logger.info(f"🎯 Langue cible: {target_lang} (détectée: {lang})")
        
        # Chercher dans la base de connaissances
        if intent in self.knowledge_base:
            if 'responses' in self.knowledge_base[intent]:
                if target_lang in self.knowledge_base[intent]['responses']:
                    response = self.knowledge_base[intent]['responses'][target_lang]
                else:
                    # Fallback au français
                    response = self.knowledge_base[intent]['responses'].get('french', 
                               self.knowledge_base['default']['responses']['french'])
                    logger.info(f"⚠️ Langue {target_lang} non disponible, fallback français")
            else:
                response = self.knowledge_base['default']['responses'][target_lang]
        else:
            response = self.knowledge_base['default']['responses'][target_lang]
        
        # Personnalisation avec le nom de l'étudiant
        if student and hasattr(student, 'user') and student.user:
            name = student.user.full_name.split()[0]
            response = response.replace("{name}", name)
        
        return response
    
    async def _get_student(self, student_id: Optional[str]) -> Optional[Student]:
        """Récupère l'étudiant par son ID"""
        if not student_id:
            return None
        
        try:
            from uuid import UUID
            student_uuid = UUID(student_id.strip())
            student = self.db.query(Student).filter(Student.id == student_uuid).first()
            
            # Charger les intérêts
            if student:
                interests = self.db.query(Interest).join(
                    StudentInterest
                ).filter(
                    StudentInterest.student_id == student.id
                ).all()
                student.interests_list = [i.name for i in interests]
            
            return student
        except Exception as e:
            logger.warning(f"⚠️ ID étudiant invalide: {student_id}")
            return None
    
    async def _save_user_message(self, message: str, student: Optional[Student]) -> Optional[Conversation]:
        """Sauvegarde le message de l'utilisateur"""
        if not student:
            return None
        
        conversation = self.db.query(Conversation).filter(
            Conversation.student_id == student.id
        ).order_by(Conversation.started_at.desc()).first()
        
        if not conversation:
            conversation = Conversation(
                id=uuid.uuid4(),
                student_id=student.id
            )
            self.db.add(conversation)
            self.db.flush()
        
        user_message = Message(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            content=message,
            sender="user"
        )
        self.db.add(user_message)
        self.db.commit()
        
        return conversation
    
    async def _save_bot_message(self, response: str, conversation: Conversation):
        """Sauvegarde la réponse du bot"""
        bot_message = Message(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            content=response,
            sender="ai"
        )
        self.db.add(bot_message)
        self.db.commit()
    
    async def _stream_openai_optimized(
        self, 
        message: str, 
        student: Optional[Student],
        analysis: Dict
    ) -> AsyncGenerator[str, None]:
        """Streaming optimisé avec OpenAI"""
        try:
            context = self._build_context(student)
            prompt = self._build_prompt(message, context)
            
            stream = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self._get_system_prompt(analysis['primary_language'])},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500,
                stream=True,
                presence_penalty=0.6,
                frequency_penalty=0.3
            )
            
            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield content
                    delay = 0.01 if len(content) > 1 else 0.02
                    await asyncio.sleep(delay)
            
            if student:
                conversation = await self._get_conversation(student)
                if conversation:
                    await self._save_bot_message(full_response, conversation)
            
        except Exception as e:
            logger.error(f"❌ Erreur OpenAI streaming: {str(e)}")
            async for chunk in self._stream_demo_multilingual(message, student, analysis):
                yield chunk
    
    def _get_system_prompt(self, lang: str = 'french') -> str:
        """Prompt système pour OpenAI adapté à la langue"""
        prompts = {
            'french': """Tu es un conseiller académique virtuel de SUP MTI Meknès.
            Réponds en français, sois amical et professionnel.
            Aide les étudiants à choisir leur orientation.
            Donne des informations précises sur les programmes, l'admission, les frais, etc.
            """,
            'english': """You are a virtual academic advisor at SUP MTI Meknès.
            Answer in English, be friendly and professional.
            Help students choose their orientation.
            Give accurate information about programs, admission, fees, etc.
            """,
            'darija_latin': """nta mostachar akadimi f SUP MTI Meknès.
            Jawb b ed-darija, koun lattef o mohtaref.
            Awen t-tollab f tawjih hom.
            A3tihom ma3lomat sa7i7a 3la les programmes, l'inscription, les frais, etc.
            """,
            'darija_arabic': """أنت مستشار أكاديمي في SUP MTI مكناس.
            جاوب بالدارجة، كن لطيف و محترف.
            عاون الطلاب ف توجيههم.
            أعطيهم معلومات صحيحة على البرامج، التسجيل، المصاريف، إلخ.
            """
        }
        return prompts.get(lang, prompts['french'])
    
    def _build_context(self, student: Optional[Student]) -> str:
        """Construit le contexte à partir du profil"""
        if not student:
            return ""
        
        context = []
        if student.user:
            context.append(f"Étudiant: {student.user.full_name}")
        
        if hasattr(student, 'interests_list') and student.interests_list:
            context.append(f"Centres d'intérêt: {', '.join(student.interests_list)}")
        
        return "\n".join(context)
    
    def _build_prompt(self, message: str, context: str) -> str:
        """Construit le prompt complet"""
        if context:
            return f"Contexte:\n{context}\n\nQuestion: {message}"
        return message
    
    def _smart_split(self, text: str) -> List[str]:
        """Découpe intelligemment le texte pour un streaming naturel"""
        chunks = []
        sentences = re.split(r'([.!?:\n])', text)
        i = 0
        while i < len(sentences):
            if i + 1 < len(sentences) and sentences[i+1] in ['.', '!', '?', ':', '\n']:
                chunks.append(sentences[i] + sentences[i+1])
                i += 2
            else:
                if len(sentences[i]) > 50:
                    parts = re.split(r'([,;])', sentences[i])
                    for j in range(0, len(parts), 2):
                        if j + 1 < len(parts):
                            chunks.append(parts[j] + parts[j+1])
                        else:
                            chunks.append(parts[j])
                else:
                    chunks.append(sentences[i])
                i += 1
        
        return [c for c in chunks if c and c.strip()]
    
    async def _get_conversation(self, student: Student) -> Optional[Conversation]:
        """Récupère la dernière conversation"""
        return self.db.query(Conversation).filter(
            Conversation.student_id == student.id
        ).order_by(Conversation.started_at.desc()).first()
    
    def _detect_intent(self, message: str, student: Optional[Student]) -> str:
        """Détecte l'intention du message (méthode de compatibilité)"""
        analysis = self.multilingual.understand_message(message)
        return analysis['intent']