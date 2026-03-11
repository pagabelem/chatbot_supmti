"""
Service d'intégration avec OpenAI pour le chatbot.
Version hybride : API payante + réponses naturelles multilingues
"""
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
import uuid
import openai
import os
import json
import re
from pathlib import Path

from app.database.models import Student, Program, Conversation, Message
from app.core.logging import logger
from dotenv import load_dotenv


load_dotenv()
# Lire la clé API directement depuis l'environnement
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

class OpenAIService:
    """Service pour l'interaction avec l'API OpenAI - Mode Hybride"""
    
    def __init__(self, db: Session):
        self.db = db
        self.client = None
        self.use_demo = True
        
        # Charger les données de l'école pour le mode démo
        self.school_data = self._load_school_data()
        
        if OPENAI_API_KEY:
            try:
                self.client = openai.OpenAI(
                    api_key=OPENAI_API_KEY,
                    timeout=30.0,
                    max_retries=2
                )
                # Test rapide de connexion
                self.client.models.list()
                self.use_demo = False
                logger.info("✅ Service OpenAI initialisé avec clé API")
            except Exception as e:
                logger.error(f"❌ Erreur initialisation OpenAI: {e}")
                logger.warning("⚠️ Basculement vers mode démo naturel")
        else:
            logger.warning("⚠️ Service OpenAI en mode démo naturel (pas de clé API)")
    
    def _load_school_data(self) -> Dict[str, Any]:
        """Charge les données de l'école depuis Data1.txt"""
        data = {
            "programs": [],
            "faculty": [],
            "contacts": {},
            "stats": {},
            "international": []
        }
        
        try:
            file_path = Path("Data1.txt")
            if not file_path.exists():
                logger.warning("⚠️ Fichier Data1.txt non trouvé")
                return data
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extraire les programmes
            program_pattern = r'◦\s*([A-Z][^•\n]+?)\s*\(BAC \+?(\d+)\)'
            programs = re.findall(program_pattern, content)
            data["programs"] = [{"name": p[0], "duration": p[1]} for p in programs]
            
            # Extraire les contacts
            phone = re.search(r'Contact\s*:\s*([+\d\s]+)', content)
            if phone:
                data["contacts"]["phone"] = phone.group(1).strip()
            
            email = re.search(r'Email\s*:\s*([^\s]+)', content)
            if email:
                data["contacts"]["email"] = email.group(1).strip()
            
            # Extraire les statistiques
            stats = re.findall(r'\+?(\d+)\s*([^\n]+)', content)
            data["stats"] = {stat[1].strip(): stat[0] for stat in stats if len(stat) > 1}
            
            logger.info(f"✅ Données chargées: {len(data['programs'])} programmes")
            
        except Exception as e:
            logger.error(f"❌ Erreur chargement données: {e}")
        
        return data
    
    def generate_chat_response(self, message: str, student_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Génère une réponse contextuelle basée sur le profil.
        Mode hybride: utilise OpenAI si disponible, sinon réponses naturelles.
        """
        logger.info(f"💭 Génération réponse pour: {message[:50]}...")
        
        # 1. Récupérer l'étudiant
        student = self._get_student(student_id)
        
        # 2. Sauvegarder le message utilisateur
        conversation = self._save_user_message(message, student)
        
        # 3. Essayer d'utiliser OpenAI si disponible
        if self.client and not self.use_demo:
            logger.info("🤖 Utilisation de l'API OpenAI")
            answer = self._try_openai(message, student)
        else:
            logger.info("💬 Utilisation du mode démo naturel")
            answer = self._generate_natural_response(message, student)
        
        # 4. Sauvegarder la réponse
        if conversation:
            self._save_bot_message(answer, conversation)
        
        logger.info("✅ Réponse générée avec succès")
        
        return {
            "response": answer,
            "student_id": student_id
        }
    
    def _get_student(self, student_id: Optional[str]) -> Optional[Student]:
        """Récupère l'étudiant par son ID"""
        if not student_id:
            return None
        
        try:
            from uuid import UUID
            student_uuid = UUID(student_id)
            student = self.db.query(Student).filter(Student.id == student_uuid).first()
            if student:
                logger.debug(f"👤 Étudiant trouvé: {student.id}")
            return student
        except Exception as e:
            logger.warning(f"⚠️ ID étudiant invalide: {student_id}")
            return None
    
    def _save_user_message(self, message: str, student: Optional[Student]) -> Optional[Conversation]:
        """Sauvegarde le message de l'utilisateur"""
        if not student:
            return None
        
        # Récupérer ou créer une conversation
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
            logger.debug(f"💬 Nouvelle conversation: {conversation.id}")
        
        # Sauvegarder le message
        user_message = Message(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            content=message,
            sender="user"
        )
        self.db.add(user_message)
        self.db.commit()
        logger.debug("📝 Message utilisateur sauvegardé")
        
        return conversation
    
    def _save_bot_message(self, response: str, conversation: Conversation):
        """Sauvegarde la réponse du bot"""
        bot_message = Message(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            content=response,
            sender="ai"
        )
        self.db.add(bot_message)
        self.db.commit()
        logger.debug("🤖 Réponse bot sauvegardée")
    
    def _try_openai(self, message: str, student: Optional[Student]) -> str:
        """Utilise OpenAI avec des prompts naturels"""
        try:
            # Détecter la langue
            lang = self._detect_language(message)
            context = self._build_context(student)
            
            # Prompts système adaptés à chaque langue
            system_prompts = {
                'en': """You are a friendly academic advisor at SUP MTI Meknès, a higher education institution in Morocco.
                
                Guidelines:
                - Respond in natural, conversational English (like you're chatting with a student)
                - Be warm, enthusiastic, and encouraging
                - Use casual language, sometimes with "hey", "cool", "awesome" etc.
                - Keep it professional but friendly
                - If the student doesn't have a profile, gently ask them to create one
                - Give personalized advice based on their interests
                - Use official school information in your responses
                
                Goal: Help students choose their academic orientation at SUP MTI.""",
                
                'ar': """أنت مستشار أكاديمي ودي في SUP MTI مكناس، مؤسسة تعليم عالي في المغرب.
                
                الإرشادات:
                - جاوب بالدارجة المغربية الطبيعية (زي ما كتهدر مع صديق)
                - كون دافئ ومتحمس ومشجع
                - استخدم كلمات وعبارات دارجة مثل "واش"، "شنو"، "كيفاش"، "بزاف"
                - حافظ على الاحترافية ولكن كن وديًا
                - إذا ما عندش الطالب بروفيل، اطلب منه بلطف يخلق واحد
                - أعط نصائح مخصصة على حسب اهتماماتهم
                - استخدم المعلومات الرسمية للمدرسة في ردودك
                
                الهدف: ساعد الطلاب على اختيار توجيههم الأكاديمي في SUP MTI.""",
                
                'fr': """Tu es un conseiller académique amical à SUP MTI Meknès, une école supérieure au Maroc.
                
                Consignes:
                - Réponds en français naturel et conversationnel
                - Sois chaleureux, enthousiaste et encourageant
                - Utilise un langage naturel, parfois familier mais toujours respectueux
                - Reste professionnel tout en étant accessible
                - Si l'étudiant n'a pas de profil, invite-le gentiment à en créer un
                - Donne des conseils personnalisés basés sur ses centres d'intérêt
                - Utilise les informations officielles de l'école dans tes réponses
                
                Objectif: Aider les étudiants à choisir leur orientation académique à SUP MTI."""
            }
            
            system_prompt = system_prompts.get(lang, system_prompts['fr'])
            
            # Construire le message utilisateur
            user_prompt = message
            if context:
                user_prompt = f"Student context: {context}\n\nQuestion: {message}"
            
            # Appeler OpenAI
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.8,  # Plus créatif pour des réponses naturelles
                max_tokens=500,
                timeout=15
            )
            
            answer = response.choices[0].message.content
            # S'assurer que la réponse est bien en UTF-8
            answer = answer.encode('utf-8', errors='ignore').decode('utf-8')
            return answer
            
        except openai.RateLimitError as e:
            logger.error(f"❌ Quota OpenAI dépassé: {e}")
            return self._generate_natural_response(message, student)
            
        except openai.APIConnectionError as e:
            logger.error(f"❌ Erreur de connexion OpenAI: {e}")
            return self._generate_natural_response(message, student)
            
        except Exception as e:
            logger.error(f"❌ Erreur OpenAI: {str(e)}")
            logger.info("🔄 Fallback vers mode démo naturel")
            return self._generate_natural_response(message, student)
    
    def _generate_natural_response(self, message: str, student: Optional[Student]) -> str:
        """
        Génère des réponses naturelles pré-enregistrées (fallback)
        """
        message_lower = message.lower()
        
        # Détecter la langue
        lang = self._detect_language(message)
        logger.info(f"🌍 Mode démo naturel - Langue: {lang}")
        
        # Récupérer les programmes de la base
        programs = self.db.query(Program).limit(10).all()
        program_names = [p.name for p in programs]
        
        # Catégorisation des questions
        if any(word in message_lower for word in ["histoire", "création", "fondation", "history", "created", "founded"]):
            if lang == 'en':
                return """Hey! SUP MTI Meknès was founded back in 2014 by M. KRIOUILE Mohamed (he used to be CEO of Lafarge Plaster Morocco) and M. KRIOUILE Abdelaziz (who teaches at ENSIAS Rabat and heads the SUP MTI Morocco Group).

The school was created because the industrial sector really needed managers and specialists in information systems and telecommunications. Pretty cool, right? 😊

Is there anything specific you'd like to know about our programs?"""
            elif lang == 'ar':
                return """مرحبا! تأسست SUP MTI مكناس في 2014 على يد السيد كريويل محمد (كان الرئيس التنفيذي لشركة لافارج بلاط المغرب) والسيد كريويل عبد العزيز (أستاذ في ENSIAS الرباط ورئيس مجموعة SUP MTI المغرب).

المدرسة تأسسات باش تلبي حاجيات القطاع الصناعي من المديرين والمتخصصين في نظم المعلومات والاتصالات. واش عندك سؤال محدد على البرامج؟"""
            else:
                return """SUP MTI Meknès a été fondée en 2014 par M. KRIOUILE Mohamed (Ex PDG Lafarge plâtre Maroc) et M. KRIOUILE Abdelaziz (Enseignant à l'ENSIAS de Rabat et Président du Groupe SUP MTI Maroc).

L'école a été créée pour répondre aux besoins du secteur industriel en managers et spécialistes en systèmes d'informations et télécommunications. Tu veux en savoir plus sur un programme en particulier ?"""

        elif any(word in message_lower for word in ["contact", "téléphone", "phone", "adresse", "address", "email"]):
            if lang == 'en':
                return """📞 Wanna get in touch with SUP MTI Meknès? Here you go:

Phone: +212 5 35 51 10 11 (give 'em a call!)
Email: contact@supmtimeknes.ac.ma (drop a message)
Address: Right in the city center of Meknes

Hours we're open:
Monday - Friday: 08:30 to 18:00
Saturday: 08:30 to 12:00

Also find us on:
Facebook: /ecolesupmtimeknes
LinkedIn: /company/ecolesupmti
YouTube: /channel/UCzZnrI4YdZnRJgosOd71RDQ

Anything else you'd like to know? 😊"""
            elif lang == 'ar':
                return """📞 بغيتي تتواصل مع SUP MTI مكناس؟ هاد المعلومات:

الهاتف: +212 5 35 51 10 11
الإيميل: contact@supmtimeknes.ac.ma
العنوان: وسط المدينة، مكناس

ساعات العمل:
الإثنين - الجمعة: 08:30 حتّى 18:00
السبت: 08:30 حتّى 12:00

وتلقانا على:
Facebook: /ecolesupmtimeknes
LinkedIn: /company/ecolesupmti
YouTube: /channel/UCzZnrI4YdZnRJgosOd71RDQ

واش بغيتي حاجة أخرى؟"""
            else:
                return """📞 Contact SUP MTI Meknès :

Téléphone : +212 5 35 51 10 11
Email : contact@supmtimeknes.ac.ma
Adresse : Centre-ville, Meknès

Horaires :
Lundi - Vendredi : 08:30 à 18:00
Samedi : 08:30 à 12:00

Réseaux sociaux :
Facebook : /ecolesupmtimeknes
LinkedIn : /company/ecolesupmti
YouTube : /channel/UCzZnrI4YdZnRJgosOd71RDQ

Autre chose que tu veux savoir ?"""

        elif any(word in message_lower for word in ["programme", "formation", "filière", "program", "course"]):
            if program_names:
                if lang == 'en':
                    response = "📚 **Programs we offer at SUP MTI:**\n\n"
                    for i, name in enumerate(program_names, 1):
                        response += f"{i}. **{name}**\n"
                    response += "\nWhich one sounds interesting to you? I can tell you more about it! 😊"
                elif lang == 'ar':
                    response = "📚 **البرامج لي كاينة ف SUP MTI:**\n\n"
                    for i, name in enumerate(program_names, 1):
                        response += f"{i}. **{name}**\n"
                    response += "\nشنو اللي يحمسك من بينهم؟ نقدر نعطيك تفاصيل أكثر! 😊"
                else:
                    response = "📚 **Programmes disponibles à SUP MTI :**\n\n"
                    for i, name in enumerate(program_names, 1):
                        response += f"{i}. **{name}**\n"
                    response += "\nLequel t'intéresse ? Je peux te donner plus de détails ! 😊"
                return response

        elif any(word in message_lower for word in ["ia", "intelligence artificielle", "ai", "artificial intelligence"]):
            if lang == 'en':
                return """🤖 **AI & Data Science Program** - this one's really cool!

It's an advanced program covering AI, Machine Learning, Deep Learning, and Big Data.

**Duration:** 3 years (Bachelor)
**What you need:** Scientific Baccalaureate with good math skills
**Certifications:** TensorFlow, AWS AI, Microsoft Azure AI

**Career opportunities:** Data Scientist, AI Engineer, ML Engineer, Data Analyst

Sounds like something you'd be into? Want more details? 😊"""
            elif lang == 'ar':
                return """🤖 **برنامج الذكاء الاصطناعي وعلوم البيانات** - هاد واحد بزاف!

تكوين متقدم ف الذكاء الاصطناعي و Machine Learning و Deep Learning و Big Data.

**المدة:** 3 سنوات (بكالوريوس)
**شروط القبول:** باك علمي بمستوى جيد ف الرياضيات
**الشهادات:** TensorFlow, AWS AI, Microsoft Azure AI

**فرص العمل:** عالم بيانات، مهندس ذكاء اصطناعي، مهندس تعلم آلي، محلل بيانات

كيجذبك هاد المجال؟ تحب تفاصيل أكثر؟ 😊"""
            else:
                return """🤖 **Programme Intelligence Artificielle et Data Science** - celui-ci est vraiment cool !

Formation avancée en IA, Machine Learning, Deep Learning et Big Data.

**Durée:** 3 ans (Bachelor)
**Prérequis:** BAC Scientifique avec bon niveau en maths
**Certifications:** TensorFlow, AWS AI, Microsoft Azure AI

**Débouchés:** Data Scientist, Ingénieur IA, ML Engineer, Analyste Data

Ça te tente ? Tu veux plus de détails ? 😊"""

        elif any(word in message_lower for word in ["cyber", "sécurité", "security"]):
            if lang == 'en':
                return """🛡️ **Cybersecurity & Digital Trust Program** - perfect if you're into ethical hacking!

Comprehensive training in systems security, ethical hacking, cryptography, and governance.

**Duration:** 3 years (Bachelor)
**What you need:** Scientific or Technical Baccalaureate
**Certifications:** CEH, Cisco CCNA Security, CompTIA Security+

**Career opportunities:** Cyber Analyst, Pentester, CISO, Security Consultant

Interested in becoming a cybersecurity expert? 😊"""
            elif lang == 'ar':
                return """🛡️ **برنامج الأمن السيبراني والثقة الرقمية** - هاد الشي مزيان بزاف إلا كنت مهتم بالاختراق الأخلاقي!

تكوين شامل ف أمن الأنظمة والاختراق الأخلاقي والتشفير والحوكمة.

**المدة:** 3 سنوات (بكالوريوس)
**شروط القبول:** باك علمي أو تقني
**الشهادات:** CEH, Cisco CCNA Security, CompTIA Security+

**فرص العمل:** محلل سيبراني، مختبر اختراق، مسؤول أمن المعلومات، مستشار أمني

واش كتهتم بالأمن السيبراني؟ 😊"""
            else:
                return """🛡️ **Programme Cybersécurité et Confiance Numérique** - parfait si tu aimes le hacking éthique !

Formation complète en sécurité des systèmes, ethical hacking, cryptographie et gouvernance.

**Durée:** 3 ans (Bachelor)
**Prérequis:** BAC Scientifique ou Technique
**Certifications:** CEH, Cisco CCNA Security, CompTIA Security+

**Débouchés:** Analyste Cyber, Pentester, RSSI, Consultant en sécurité

Intéressé par la cybersécurité ? 😊"""

        # === SALUTATIONS ===
        elif any(word in message_lower for word in ["bonjour", "salut", "hello", "hi", "مرحبا"]):
            if student and student.user:
                name = student.user.full_name.split()[0]
                if lang == 'en':
                    return f"Hey {name}! 👋 Good to see you again. What can I help you with today?"
                elif lang == 'ar':
                    return f"مرحبا {name}! 👋 تشرفت بيك مرة أخرى. كيفاش نقدر نعاونك النهاردة؟"
                else:
                    return f"Salut {name} ! 👋 Ravi de te revoir. Comment je peux t'aider aujourd'hui ?"
            else:
                if lang == 'en':
                    return "Hey there! 👋 I'm your virtual academic advisor at SUP MTI. What would you like to know about our programs?"
                elif lang == 'ar':
                    return "مرحبا! 👋 أنا المستشار الأكاديمي ديال SUP MTI. شنو بغيتي تعرف على البرامج ديالنا؟"
                else:
                    return "Salut ! 👋 Je suis ton conseiller académique virtuel à SUP MTI. Qu'est-ce que tu veux savoir sur nos programmes ?"

        # === RÉPONSE PAR DÉFAUT ===
        else:
            if lang == 'en':
                return """I can help you with:

📚 **Our programs** - AI, Cybersecurity, Software Engineering, Management, Finance, Networks
🎓 **Admission stuff** - BAC requirements, License, Masters degrees
💰 **Fees & scholarships** - 35,000 MAD/year, scholarships up to 100% (pretty sweet deal!)
🌍 **International** - Cool partnerships with EFREI Paris and University of Lorraine
📞 **Contact** - +212 5 35 51 10 11

What would you like to know more about? 😊"""
            elif lang == 'ar':
                return """نقدر نعاونك ف:

📚 **البرامج ديالنا** - الذكاء الاصطناعي، الأمن السيبراني، هندسة البرمجيات، الإدارة، المالية، الشبكات
🎓 **شروط التسجيل** - البكالوريا، الإجازة، الماستر
💰 **المصاريف و المنح** - 35,000 درهم/سنة، منح حتى 100%
🌍 **الدولي** - شراكات مع EFREI Paris و جامعة لورين
📞 **الاتصال** - +212 5 35 51 10 11

شنو بغيتي تعرف بالضبط؟ 😊"""
            else:
                return """Je peux t'aider avec :

📚 **Nos programmes** - IA, Cybersécurité, Génie Logiciel, Management, Finance, Réseaux
🎓 **Conditions d'admission** - BAC, Licence, Masters
💰 **Frais et bourses** - 35 000 DH/an, bourses jusqu'à 100%
🌍 **International** - Partenariats avec EFREI Paris, Université de Lorraine
📞 **Contact** - +212 5 35 51 10 11

Qu'est-ce qui t'intéresse ? 😊"""

    def _get_system_prompt(self) -> str:
        """Retourne le prompt système pour OpenAI (conservé pour compatibilité)"""
        return self._get_hybrid_system_prompt()
    
    def _build_context(self, student: Optional[Student]) -> str:
        """Construit le contexte à partir du profil étudiant"""
        if not student:
            return ""
        
        context_lines = []
        
        # Informations de base
        if student.user:
            context_lines.append(f"Étudiant: {student.user.full_name}")
        
        # Centres d'intérêt
        interests = []
        if hasattr(student, 'student_interests') and student.student_interests:
            for si in student.student_interests:
                if hasattr(si, 'interest') and si.interest:
                    interests.append(si.interest.name)
        
        if interests:
            context_lines.append(f"Centres d'intérêt: {', '.join(interests)}")
        else:
            context_lines.append("Centres d'intérêt: Non renseignés")
        
        return "\n".join(context_lines)
    
    def _build_prompt(self, message: str, context: str) -> str:
        """Construit le prompt complet pour OpenAI"""
        if context:
            return f"Contexte de l'étudiant:\n{context}\n\nQuestion: {message}"
        return message
    
    def _detect_language(self, text: str) -> str:
        """Détection améliorée de la langue"""
        text_lower = text.lower()
        
        # Mots-clés anglais étendus
        english_keywords = [
            'hello', 'hi', 'hey', 'what', 'who', 'where', 'when', 'why', 'how',
            'program', 'course', 'university', 'college', 'school', 'education',
            'admission', 'apply', 'application', 'fee', 'tuition', 'scholarship',
            'ai', 'artificial intelligence', 'cybersecurity', 'security',
            'software', 'engineering', 'management', 'finance', 'network',
            'president', 'director', 'professor', 'teacher', 'class', 'student',
            'can you', 'please', 'thank', 'help', 'question', 'information',
            'the', 'is', 'are', 'in', 'at', 'for', 'to', 'with', 'about'
        ]
        
        # Mots-clés français
        french_keywords = [
            'bonjour', 'salut', 'coucou', 'programme', 'formation', 'filière',
            'université', 'école', 'admission', 'inscription', 'frais', 'bourse',
            'ia', 'intelligence artificielle', 'cybersécurité', 'sécurité',
            'logiciel', 'génie', 'management', 'gestion', 'finance', 'réseau',
            'président', 'directeur', 'professeur', 'enseignant', 'étudiant',
            'pouvez', 's\'il vous plaît', 'merci', 'aide', 'question', 'information',
            'le', 'la', 'les', 'un', 'une', 'des', 'est', 'sont', 'dans', 'pour'
        ]
        
        # Vérifier caractères arabes
        arabic_chars = re.search(r'[\u0600-\u06FF]', text)
        if arabic_chars:
            return 'ar'
        
        # Compter les occurrences avec pondération
        english_count = 0
        french_count = 0
        
        # Compter les mots-clés anglais
        for word in english_keywords:
            if word in text_lower:
                # Les mots courts ont moins de poids
                if len(word) <= 3:
                    english_count += 0.5
                else:
                    english_count += 1
        
        # Compter les mots-clés français
        for word in french_keywords:
            if word in text_lower:
                if len(word) <= 3:
                    french_count += 0.5
                else:
                    french_count += 1
        
        # Bonus pour la ponctuation anglaise
        if '?' in text and '?' in text:
            english_count += 0.5
        
        logger.debug(f"🌍 Détection langue - Anglais: {english_count}, Français: {french_count}")
        
        if english_count > french_count:
            return 'en'
        elif french_count > english_count:
            return 'fr'
        
        # En cas d'égalité, regarder le premier mot
        if text_lower.split():
            first_word = text_lower.split()[0]
            if first_word in ['hello', 'hi', 'hey', 'what', 'how', 'why', 'when', 'where']:
                return 'en'
            elif first_word in ['bonjour', 'salut']:
                return 'fr'
        
        return 'fr'  # Par défaut
    
    def test_connection(self) -> Dict[str, Any]:
        """Teste la connexion à l'API OpenAI"""
        if not self.client:
            return {"success": False, "error": "Client non initialisé"}
        
        try:
            models = self.client.models.list()
            return {
                "success": True,
                "models_count": len(models.data),
                "whisper_available": any("whisper" in m.id for m in models.data)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}