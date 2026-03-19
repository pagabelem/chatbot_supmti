"""
Service OpenAI — Version corrigée
Corrections :
  - _detect_language() reconnaît le darija (arabe marocain)
  - System prompts darija améliorés (réponses naturelles en darija)
  - Suppression des répétitions "SUP MTI" dans les réponses
  - Détection langue appliquée aussi au texte transcrit depuis l'audio
"""
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
import uuid
import openai
import os
import re
from pathlib import Path

from app.database.models import Student, Program, Conversation, Message
from app.core.logging import logger
from app.services.multilingual_service import MultilingualService
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


class OpenAIService:
    """Service OpenAI — Mode Hybride — FR / EN / Darija"""

    def __init__(self, db: Session):
        self.db = db
        self.client = None
        self.use_demo = True
        self.school_data = self._load_school_data()
        # Utiliser MultilingualService pour la détection de langue
        self.multilingual = MultilingualService()

        if OPENAI_API_KEY:
            try:
                self.client = openai.OpenAI(
                    api_key=OPENAI_API_KEY,
                    timeout=30.0,
                    max_retries=2,
                )
                self.client.models.list()
                self.use_demo = False
                logger.info("✅ Service OpenAI initialisé")
            except Exception as e:
                logger.error(f"❌ Erreur init OpenAI: {e}")
                logger.warning("⚠️ Basculement vers mode démo")
        else:
            logger.warning("⚠️ Mode démo (pas de clé API)")

    # ------------------------------------------------------------------ #
    # CHARGEMENT DONNÉES ÉCOLE                                            #
    # ------------------------------------------------------------------ #
    def _load_school_data(self) -> Dict[str, Any]:
        """
        Charge les données depuis Data1.txt.
        Les données ci-dessous sont la source de vérité — ne pas inventer d'infos.
        """
        # ---------------------------------------------------------------- #
        # DONNÉES EXACTES issues de Data1.txt                             #
        # ---------------------------------------------------------------- #
        data = {
            "contacts": {
                "phone":   "+212 5 35 51 10 11",
                "email":   "contact@supmtimeknes.ac.ma",
                "website": "www.supmtimeknes.ac.ma",
                "address": "Centre-ville, Meknès",
                "hours":   "Lun–Ven 08:30–18:00 | Sam 08:30–12:00",
                "social": {
                    "facebook":  "https://www.facebook.com/ecolesupmtimeknes",
                    "instagram": "https://www.linkedin.com/company/ecolesupmti/",
                    "youtube":   "https://www.youtube.com/channel/UCzZnrI4YdZnRJgosOd71RDQ",
                },
            },
            "frais": {
                "scolarite_annuelle": 35000,
                "mensualites":        10,
                "mensualite_montant": 3500,
                "inscription":        3500,
                "total_annuel":       38500,
                "bourse_min_pct":     30,
                "bourse_max_pct":     100,
                "note": "La bourse s'applique uniquement sur les 35.000 DH de scolarité.",
            },
            "stats": {
                "laureats":       "+450",
                "nationalites":   "+10",
                "filieres":       6,
            },
            # 6 filières EXACTES — ne pas en inventer d'autres
            "programs": [
                {
                    "name":       "Management des Entreprises",
                    "level":      "BAC+3",
                    "dept":       "Management & Finance",
                    "admission":  "BAC (1ère année) ou BAC+2 gestion/économie",
                    "debouches":  ["Cadre bancaire", "Responsable commercial", "Analyste financier", "Assistant RH"],
                },
                {
                    "name":       "Finance, Audit et Contrôle de Gestion",
                    "level":      "BAC+5",
                    "dept":       "Management & Finance",
                    "admission":  "BAC+3 SUP MTI ou Licence équivalente (économie/gestion)",
                    "debouches":  ["Auditeur", "Contrôleur de gestion", "Expert-comptable", "Directeur financier"],
                },
                {
                    "name":       "Management et Relations Internationales (MSTIC)",
                    "level":      "BAC+5",
                    "dept":       "Management & Finance",
                    "admission":  "BAC+3 SUP MTI ou Licence équivalente",
                    "debouches":  ["Manager d'entreprise", "Responsable SI", "Responsable RH", "Responsable marketing"],
                },
                {
                    "name":       "Ingénierie Intelligente des Systèmes Informatiques (ISI)",
                    "level":      "BAC+3",
                    "dept":       "Ingénierie",
                    "admission":  "BAC scientifique (1ère année) ou BAC+2 informatique",
                    "debouches":  ["Développeur web", "Administrateur réseaux", "Analyste programmeur", "Webmaster"],
                },
                {
                    "name":       "Ingénierie Intelligente des Systèmes d'Information et Communications (IISIC)",
                    "level":      "BAC+5",
                    "dept":       "Ingénierie",
                    "admission":  "BAC+3 SUP MTI ISI ou Licence informatique",
                    "debouches":  ["Architecte réseaux", "Administrateur réseaux", "Responsable télécoms"],
                },
                {
                    "name":       "Ingénierie Intelligente des Systèmes, Réseaux et Télécommunications (IISRT)",
                    "level":      "BAC+5",
                    "dept":       "Ingénierie",
                    "admission":  "BAC+3 SUP MTI ISI ou Licence informatique",
                    "debouches":  ["Architecte systèmes réseaux", "Responsable infrastructures télécoms"],
                },
            ],
            "international": {
                "partenaires": [
                    "EFREI Paris (cycle préparatoire → ingénieur)",
                    "Université de Lorraine — Master MTI (double diplôme français)",
                    "ENSIIE Paris (poursuite d'études)",
                    "Télécom Sud Paris (poursuite d'études)",
                    "Groupe IGS Paris/Lyon/Toulouse — Bachelor & Master (double diplôme)",
                    "ISTEC Paris — Bachelor & Master Commerce (double diplôme)",
                    "Université d'Algarve — Portugal (poursuite d'études)",
                    "Université Moulay Ismaïl (UMI) Meknès (partenariat local)",
                ],
            },
            "certifications": ["Cisco (CCNA, CCNP)", "Microsoft Certified", "Oracle Certified"],
            "clubs": ["BDE", "Club Programmation", "Club Sportif", "Club Artistique",
                      "Club Gaming", "Club Solidarité", "Club Échanges Culturels"],
        }

        # Tenter aussi de lire Data1.txt si disponible (pour mises à jour futures)
        try:
            file_path = Path("Data1.txt")
            if file_path.exists():
                logger.info("✅ Data1.txt trouvé — données statiques utilisées (parsing désactivé)")
            else:
                logger.warning("⚠️ Data1.txt non trouvé — utilisation des données embarquées")
        except Exception as e:
            logger.warning(f"⚠️ Lecture Data1.txt: {e}")

        logger.info(f"✅ Données chargées: {len(data['programs'])} filières")
        return data

    # ------------------------------------------------------------------ #
    # POINT D'ENTRÉE PRINCIPAL                                            #
    # ------------------------------------------------------------------ #
    def generate_chat_response(
        self,
        message: str,
        student_id: Optional[str] = None,
        detected_language: Optional[str] = None,   # ← NOUVEAU paramètre
    ) -> Dict[str, Any]:
        """
        Génère une réponse.

        Args:
            message           : texte de l'utilisateur (peut venir de Whisper)
            student_id        : ID étudiant optionnel
            detected_language : langue déjà détectée par Whisper ('fr'|'en'|'ar'|None)
        """
        logger.info(f"💭 Message: {message[:60]!r} | lang_hint={detected_language!r}")

        student = self._get_student(student_id)
        conversation = self._save_user_message(message, student)

        if self.client and not self.use_demo:
            answer = self._try_openai(message, student, detected_language)
        else:
            answer = self._generate_natural_response(message, student, detected_language)

        if conversation:
            self._save_bot_message(answer, conversation)

        return {"response": answer, "student_id": student_id}

    # ------------------------------------------------------------------ #
    # OPENAI                                                              #
    # ------------------------------------------------------------------ #
    def _try_openai(
        self,
        message: str,
        student: Optional[Student],
        lang_hint: Optional[str] = None,
    ) -> str:
        try:
            # CORRECTION #2 : utiliser lang_hint si fourni (vient de Whisper)
            lang = lang_hint or self._detect_language(message)
            context = self._build_context(student)

            # ---------------------------------------------------------- #
            # CORRECTION #3 : system prompts sans répétition "SUP MTI"   #
            # On mentionne l'école UNE seule fois, brièvement.           #
            # ---------------------------------------------------------- #
            # ---------------------------------------------------------- #
            # DONNÉES OFFICIELLES À INJECTER DANS CHAQUE PROMPT         #
            # Source : Data1.txt — NE PAS inventer d'autres filières     #
            # ---------------------------------------------------------- #
            school_facts = (
                "FILIÈRES EXACTES (6 au total) : "
                "1) Management des Entreprises (BAC+3) — débouchés: cadre bancaire, commercial, RH. "
                "2) Finance Audit et Contrôle de Gestion (BAC+3) — débouchés: auditeur, expert-comptable. "
                "3) Management et Relations Internationales MSTIC (BAC+5) — débouchés: manager, responsable SI. "
                "4) Ingénierie Intelligente des Systèmes Informatiques ISI (BAC+3) — débouchés: dev web, admin réseaux. "
                "5) Ingénierie Intelligente des Systèmes d'Information et Communications IISIC (BAC+5). "
                "6) Ingénierie Intelligente des Systèmes Réseaux et Télécommunications IISRT (BAC+5). "
                "FRAIS : 35.000 DH/an (10 mensualités de 3.500) + 3.500 inscription = 38.500 DH total. "
                "BOURSES : 30% à 100% sur les frais de scolarité uniquement. "
                "CERTIFICATIONS : Cisco (CCNA/CCNP), Microsoft, Oracle. "
                "PARTENAIRES INTERNATIONAUX : EFREI Paris, Université de Lorraine (Master MTI double diplôme), "
                "ENSIIE Paris, Télécom Sud Paris, Groupe IGS, ISTEC Paris, Université d'Algarve. "
                "CONTACT : +212 5 35 51 10 11 | contact@supmtimeknes.ac.ma | www.supmtimeknes.ac.ma. "
                "RÈGLE ABSOLUE : Ne JAMAIS mentionner une filière 'Cybersécurité' ou 'IA' standalone — "
                "ces filières n'existent pas. L'IA est intégrée dans IISIC/IISRT/MSTIC."
            )

            system_prompts = {
                'fr': (
                    "Tu es un conseiller académique à SUP MTI Meknès. "
                    "Réponds UNIQUEMENT avec les informations officielles ci-dessous. "
                    "Sois chaleureux et conversationnel en français. "
                    f"{school_facts}"
                ),
                'en': (
                    "You are an academic advisor at SUP MTI Meknès. "
                    "Reply ONLY with the official information below. "
                    "Be warm and conversational in English. "
                    f"{school_facts}"
                ),
                'ar': (
                    "You are an academic advisor at SUP MTI Meknès. "
                    "ALWAYS reply in Moroccan Darija written with LATIN letters only, never Arabic script. "
                    "Use: wach, kifach, bzzaf, mzyan, chno, dyal, safi, kayn, bghit, n3awnak, bach, hna. "
                    "Example: 'Wach bghiti t3ref 3la les filières? Kayn 6 filières f SUP MTI...' "
                    "Reply ONLY with official info below. "
                    f"{school_facts}"
                ),
            }

            system_prompt = system_prompts.get(lang, system_prompts['fr'])
            user_prompt = message
            if context:
                user_prompt = f"Contexte étudiant: {context}\n\nMessage: {message}"

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=500,
                timeout=15,
            )

            answer = response.choices[0].message.content
            return answer.encode('utf-8', errors='ignore').decode('utf-8')

        except openai.RateLimitError as e:
            logger.error(f"❌ Quota OpenAI: {e}")
            return self._generate_natural_response(message, student, lang_hint)
        except openai.APIConnectionError as e:
            logger.error(f"❌ Connexion OpenAI: {e}")
            return self._generate_natural_response(message, student, lang_hint)
        except Exception as e:
            logger.error(f"❌ Erreur OpenAI: {e}")
            return self._generate_natural_response(message, student, lang_hint)

    # ------------------------------------------------------------------ #
    # MODE DÉMO (FALLBACK)                                                #
    # ------------------------------------------------------------------ #
    def _generate_natural_response(
        self,
        message: str,
        student: Optional[Student],
        lang_hint: Optional[str] = None,
    ) -> str:
        message_lower = message.lower()
        # CORRECTION #2 : utiliser lang_hint si fourni
        lang = lang_hint or self._detect_language(message)
        logger.info(f"💬 Mode démo — langue: {lang}")

        programs = self.db.query(Program).limit(10).all()
        program_names = [p.name for p in programs]

        # --- HISTOIRE ---
        if any(w in message_lower for w in ["histoire", "création", "fondation", "history", "created", "founded",
                                             "tassas", "fin", "wqtach", "imta"]):
            if lang == 'en':
                return (
                    "SUP MTI was founded in 2014 to meet the industrial sector's need "
                    "for specialists in information systems and telecoms. "
                    "Want to know more about our programs? 😊"
                )
            elif lang == 'ar':
                return (
                    "L'école tassasat f 2014 bach tjaweb l'7ajat dyal qta3 l'sina3i "
                    "f les spécialistes dyal les systèmes d'information. "
                    "Wach bghiti t3ref aktar 3la les programmes? 😊"
                )
            else:
                return (
                    "L'école a été fondée en 2014 pour répondre aux besoins du secteur "
                    "industriel en managers et spécialistes en systèmes d'information. "
                    "Tu veux en savoir plus sur un programme ? 😊"
                )

        # --- CONTACT ---
        elif any(w in message_lower for w in ["contact", "téléphone", "phone", "adresse", "address", "email",
                                               "telfon", "3nwan", "joini"]):
            if lang == 'en':
                return (
                    "📞 **Contact:**\n"
                    "Phone: +212 5 35 51 10 11\n"
                    "Email: contact@supmtimeknes.ac.ma\n"
                    "Hours: Mon–Fri 08:30–18:00 | Sat 08:30–12:00\n\n"
                    "Anything else? 😊"
                )
            elif lang == 'ar':
                return (
                    "📞 **Bach tjawbna:**\n"
                    "Telfon: +212 5 35 51 10 11\n"
                    "Email: contact@supmtimeknes.ac.ma\n"
                    "Mwa3id l'khedma: Ltnin–Jm3a 08:30–18:00 | Sbt 08:30–12:00\n\n"
                    "Wach kayn chi 7aja khra? 😊"
                )
            else:
                return (
                    "📞 **Contact :**\n"
                    "Tél : +212 5 35 51 10 11\n"
                    "Email : contact@supmtimeknes.ac.ma\n"
                    "Horaires : Lun–Ven 08:30–18:00 | Sam 08:30–12:00\n\n"
                    "Autre chose ? 😊"
                )

        # --- PROGRAMMES ---
        elif any(w in message_lower for w in ["programme", "formation", "filière", "filiere", "program", "course",
                                               "chno kayn", "filiyat", "takwin", "filières"]):
            # Les 6 filières EXACTES — source Data1.txt
            filieres = [
                ("Management des Entreprises", "BAC+3"),
                ("Finance, Audit et Contrôle de Gestion", "BAC+5"),
                ("Management et Relations Internationales (MSTIC)", "BAC+5"),
                ("Ingénierie Intelligente des Systèmes Informatiques (ISI)", "BAC+3"),
                ("Ingénierie Intelligente des Systèmes d'Information et Communications (IISIC)", "BAC+5"),
                ("Ingénierie Intelligente des Systèmes, Réseaux et Télécommunications (IISRT)", "BAC+5"),
            ]
            if lang == 'en':
                r = "📚 **6 programs at SUP MTI Meknès:**\n\n"
                for i, (n, lvl) in enumerate(filieres, 1):
                    r += f"{i}. {n} ({lvl})\n"
                r += "\nWhich one interests you? 😊"
            elif lang == 'ar':
                r = "📚 **Les 6 filières li kaynin f SUP MTI:**\n\n"
                for i, (n, lvl) in enumerate(filieres, 1):
                    r += f"{i}. {n} ({lvl})\n"
                r += "\nChno li kay7amssek? 😊"
            else:
                r = "📚 **Les 6 filières de SUP MTI Meknès :**\n\n"
                for i, (n, lvl) in enumerate(filieres, 1):
                    r += f"{i}. {n} ({lvl})\n"
                r += "\nLaquelle t'intéresse ? 😊"
            return r

        # --- IA / DATA / RÉSEAUX / TÉLÉCOMS ---
        elif any(w in message_lower for w in ["ia", "intelligence artificielle", "ai", "artificial",
                                               "machine learning", "data", "reseau", "réseau", "telecom",
                                               "zaka2", "informatique", "iisrt", "iisic", "isi"]):
            if lang == 'en':
                return (
                    "🤖 **Engineering programs** at SUP MTI cover AI, Data Science, Networks and Telecoms:\n\n"
                    "• **ISI (BAC+3)** — Software engineering, networks, web dev\n"
                    "• **IISIC (BAC+5)** — Smart info systems & communications, AI, IoT\n"
                    "• **IISRT (BAC+5)** — Smart networks & telecoms, AI, Data Science\n\n"
                    "Certifications included: Cisco (CCNA/CCNP), Microsoft, Oracle.\n"
                    "Want details on one of these? 😊"
                )
            elif lang == 'ar':
                return (
                    "🤖 **Les filières d'ingénierie** li kaynin f SUP MTI:\n\n"
                    "• **ISI (BAC+3)** — Dev web, réseaux, systèmes\n"
                    "• **IISIC (BAC+5)** — Systèmes d'information, IA, IoT\n"
                    "• **IISRT (BAC+5)** — Réseaux, télécoms, Data Science\n\n"
                    "Certifications: Cisco, Microsoft, Oracle.\n"
                    "Wach bghiti tعرف aktar 3la wa7da menhom? 😊"
                )
            else:
                return (
                    "🤖 **Filières ingénierie** de SUP MTI couvrant IA, Data et Réseaux :\n\n"
                    "• **ISI (BAC+3)** — Génie logiciel, réseaux, développement web\n"
                    "• **IISIC (BAC+5)** — Systèmes d'information intelligents, IA, IoT\n"
                    "• **IISRT (BAC+5)** — Réseaux & télécoms intelligents, Data Science\n\n"
                    "Certifications intégrées : Cisco (CCNA/CCNP), Microsoft, Oracle.\n"
                    "Tu veux plus de détails sur l'une d'elles ? 😊"
                )

        # --- MANAGEMENT / FINANCE ---
        elif any(w in message_lower for w in ["management", "finance", "audit", "gestion", "facg", "mstic",
                                               "comptabilité", "commercial", "marketing"]):
            if lang == 'en':
                return (
                    "💼 **Management programs** at SUP MTI:\n\n"
                    "• **Management des Entreprises (BAC+3)** — Business management, digital marketing, IT\n"
                    "• **Finance, Audit et Contrôle de Gestion (BAC+5)** — Auditing, financial control\n"
                    "• **MSTIC (BAC+5)** — Digital management, international relations, IS management\n\n"
                    "Want details on one? 😊"
                )
            elif lang == 'ar':
                return (
                    "💼 **Filières management** f SUP MTI:\n\n"
                    "• **Management des Entreprises (BAC+3)** — Gestion, marketing digital\n"
                    "• **Finance, Audit et Contrôle de Gestion (BAC+5)** — Audit, finance\n"
                    "• **MSTIC (BAC+5)** — Management digital, relations internationales\n\n"
                    "Wach bghiti t3ref aktar? 😊"
                )
            else:
                return (
                    "💼 **Filières Management** de SUP MTI :\n\n"
                    "• **Management des Entreprises (BAC+3)** — Gestion, marketing digital, informatique\n"
                    "• **Finance, Audit et Contrôle de Gestion (BAC+5)** — Audit, contrôle de gestion\n"
                    "• **MSTIC (BAC+5)** — Management digital, relations internationales\n\n"
                    "Tu veux plus de détails ? 😊"
                )

        # --- SALUTATIONS ---
        elif any(w in message_lower for w in ["bonjour", "salut", "hello", "hi", "hey",
                                               "salam", "labas", "wach labas", "ach khbar", "ahlan"]):
            if student and student.user:
                name = student.user.full_name.split()[0]
                if lang == 'en':
                    return f"Hey {name}! 👋 Good to see you. What can I help you with?"
                elif lang == 'ar':
                    return f"Salam {name}! 👋 Labas 3lik? Kifach nqdar n3awnak lyoum?"
                else:
                    return f"Salut {name} ! 👋 Comment je peux t'aider ?"
            else:
                if lang == 'en':
                    return "Hey! 👋 I'm your academic advisor. What would you like to know?"
                elif lang == 'ar':
                    return "Salam! 👋 Ana l'conseiller académique dyalk. Chno bghiti t3ref?"
                else:
                    return "Salut ! 👋 Je suis ton conseiller académique. Qu'est-ce que tu veux savoir ?"

        # --- DÉFAUT ---
        else:
            if lang == 'en':
                return (
                    "I can help you with:\n\n"
                    "📚 **6 Programs** — ISI (BAC+3), IISIC (BAC+5), IISRT (BAC+5), "
                    "Management des Entreprises (BAC+3), Finance Audit (BAC+5), MSTIC (BAC+5)\n"
                    "🎓 **Admission** — BAC scientifique/technique/économique or BAC+2/BAC+3 equivalent\n"
                    "💰 **Fees** — 35,000 MAD/year + 3,500 registration = 38,500 MAD total\n"
                    "🏆 **Scholarships** — 30% to 100% based on admission exam results\n"
                    "🌍 **International** — EFREI Paris, University of Lorraine, ENSIIE, IGS, ISTEC, Algarve\n"
                    "📜 **Certifications** — Cisco CCNA/CCNP, Microsoft, Oracle\n"
                    "📞 **Contact** — +212 5 35 51 10 11 | contact@supmtimeknes.ac.ma\n\n"
                    "What would you like to know? 😊"
                )
            elif lang == 'ar':
                return (
                    "Nqdar n3awnak f:\n\n"
                    "📚 **6 Filières** — ISI (BAC+3), IISIC (BAC+5), IISRT (BAC+5), "
                    "Management (BAC+3), Finance Audit (BAC+5), MSTIC (BAC+5)\n"
                    "🎓 **Admission** — BAC ou diplôme équivalent\n"
                    "💰 **Frais** — 35.000 DH/an + 3.500 inscription = 38.500 DH total\n"
                    "🏆 **Bourses** — 30% à 100% 3la résultats concours\n"
                    "🌍 **International** — EFREI Paris, Université de Lorraine, ENSIIE, IGS, ISTEC\n"
                    "📜 **Certifications** — Cisco, Microsoft, Oracle\n"
                    "📞 **Contact** — +212 5 35 51 10 11\n\n"
                    "Chno bghiti t3ref bzzaf? 😊"
                )
            else:
                return (
                    "Je peux t'aider avec :\n\n"
                    "📚 **6 Filières** — ISI (BAC+3), IISIC (BAC+5), IISRT (BAC+5), "
                    "Management des Entreprises (BAC+3), Finance Audit (BAC+5), MSTIC (BAC+5)\n"
                    "🎓 **Admission** — BAC scientifique/technique/économique ou équivalent\n"
                    "💰 **Frais** — 35.000 DH/an + 3.500 inscription = **38.500 DH total**\n"
                    "🏆 **Bourses** — 30% à 100% selon résultats au concours d'admission\n"
                    "🌍 **International** — EFREI Paris, Université de Lorraine, ENSIIE, IGS, ISTEC, Algarve\n"
                    "📜 **Certifications** — Cisco CCNA/CCNP, Microsoft, Oracle\n"
                    "📞 **Contact** — +212 5 35 51 10 11 | contact@supmtimeknes.ac.ma\n\n"
                    "Qu'est-ce qui t'intéresse ? 😊"
                )

    # ------------------------------------------------------------------ #
    # DÉTECTION DE LANGUE — CORRIGÉE                                     #
    # ------------------------------------------------------------------ #
    def _detect_language(self, text: str) -> str:
        """
        Détecte la langue via MultilingualService.
        Retourne 'fr' | 'en' | 'ar'.
        """
        if not text or not text.strip():
            return 'fr'

        analysis = self.multilingual.understand_message(text)
        primary = analysis.get('primary_language', 'french')
        confidence = analysis.get('confidence', 0)

        logger.debug(f"🌍 MultilingualService → {primary} ({confidence:.1f}%)")

        # Mapper les codes MultilingualService → codes API ('fr'|'en'|'ar')
        mapping = {
            'french':        'fr',
            'english':       'en',
            'darija_latin':  'ar',   # darija latin → on répond en darija
            'darija_arabic': 'ar',   # darija arabe → on répond en darija
            'unknown':       'fr',
        }
        return mapping.get(primary, 'fr')

    # ------------------------------------------------------------------ #
    # HELPERS DB                                                          #
    # ------------------------------------------------------------------ #
    def _get_student(self, student_id: Optional[str]) -> Optional[Student]:
        if not student_id:
            return None
        try:
            from uuid import UUID
            uid = UUID(student_id)
            return self.db.query(Student).filter(Student.id == uid).first()
        except Exception:
            logger.warning(f"⚠️ ID étudiant invalide: {student_id}")
            return None

    def _save_user_message(self, message: str, student: Optional[Student]) -> Optional[Conversation]:
        if not student:
            return None
        conversation = (
            self.db.query(Conversation)
            .filter(Conversation.student_id == student.id)
            .order_by(Conversation.started_at.desc())
            .first()
        )
        if not conversation:
            conversation = Conversation(id=uuid.uuid4(), student_id=student.id)
            self.db.add(conversation)
            self.db.flush()
        self.db.add(Message(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            content=message,
            sender="user",
        ))
        self.db.commit()
        return conversation

    def _save_bot_message(self, response: str, conversation: Conversation):
        self.db.add(Message(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            content=response,
            sender="ai",
        ))
        self.db.commit()

    def _build_context(self, student: Optional[Student]) -> str:
        if not student:
            return ""
        lines = []
        if student.user:
            lines.append(f"Étudiant: {student.user.full_name}")
        interests = []
        if hasattr(student, 'student_interests') and student.student_interests:
            for si in student.student_interests:
                if hasattr(si, 'interest') and si.interest:
                    interests.append(si.interest.name)
        lines.append(f"Centres d'intérêt: {', '.join(interests) if interests else 'Non renseignés'}")
        return "\n".join(lines)

    # Conservé pour compatibilité ascendante
    def _get_system_prompt(self) -> str:
        return (
            "Tu es un conseiller académique à SUP MTI Meknès. "
            "Réponds de façon naturelle en FR, EN ou darija selon la langue de l'étudiant."
        )

    def test_connection(self) -> Dict[str, Any]:
        if not self.client:
            return {"success": False, "error": "Client non initialisé"}
        try:
            models = self.client.models.list()
            return {
                "success": True,
                "models_count": len(models.data),
                "whisper_available": any("whisper" in m.id for m in models.data),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}