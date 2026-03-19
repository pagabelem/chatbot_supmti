# ============================================================
# RAG SERVICE — SUPMTI
# Recherche contextuelle + Réponses GPT augmentées
# Synchronisation automatique + Mode hors ligne
# Tahirou — backend-tahirou
# ============================================================

import os
import json
import hashlib
import requests
from functools import lru_cache
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from apscheduler.schedulers.background import BackgroundScheduler
from app.academic_config import CHATBOT_CONFIG, SUPMTI_URLS, FILIERES, FRAIS_SCOLARITE, SCHOOL_INFO
from app.services.embedding_service import (
    charger_base_existante,
    recherche_semantique,
    initialiser_base_vectorielle,
    base_doit_etre_reconstruite
)

# ============================================================
# INITIALISATION
# ============================================================

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./data/vectorstore")
DOCUMENTS_PATH = os.getenv("DOCUMENTS_PATH", "./data/documents")
OFFLINE_PATH   = os.getenv("OFFLINE_PATH",   "./data/offline")

_index        = None
_metadonnees  = None

# ============================================================
# ÉTAPE 1 — DÉMARRAGE
# ============================================================

def demarrer_rag():
    global _index, _metadonnees
    print("[RAG] Démarrage du système RAG...")
    if base_doit_etre_reconstruite():
        print("[RAG] Construction de la base vectorielle (peut prendre 30-60s)...")
        initialiser_base_vectorielle()
    _index, _metadonnees = charger_base_existante()
    if _index is not None:
        print("[RAG] ✅ Système RAG prêt !")
        generer_donnees_offline()
        # ── Préchargement des caches pour des réponses instantanées ──────────
        # On précharge maintenant pour que la 1ère requête soit aussi rapide
        # que toutes les suivantes (pas de latence "cold start").
        print("[CACHE] Préchargement hardcode + prompts en mémoire...")
        _construire_contenu_hardcode()   # charge Data1.txt en mémoire
        for _lang in ("français", "anglais", "darija_latin", "darija_arabe"):
            construire_prompt_systeme(_lang)   # compile les 4 prompts
        print("[CACHE] ✅ Tous les caches prêts — 1ère requête aussi rapide que les suivantes")
    else:
        print("[RAG] ⚠️ Système RAG en mode dégradé")

# ============================================================
# ÉTAPE 2 — DÉTECTER LA LANGUE
# ============================================================

def _normaliser_arabe(texte):
    """Supprime les harakat (voyelles) arabes pour normaliser la détection."""
    import unicodedata
    # Harakat : Fatha, Damma, Kasra, Sukun, Shadda, Tanwin...
    harakat = set("َُِّْٰٕٓٔؐؑؒؓ")
    return "".join(c for c in texte if c not in harakat)


def detecter_langue(texte):
    """
    Détecte la langue/script du message utilisateur.
    Retourne : "darija_arabe" | "darija_latin" | "anglais" | "français"

    RÈGLE BILINGUE :
    - Si l'utilisateur écrit en arabe (caractères arabes dominants) → réponse en darija arabe
    - Si l'utilisateur écrit en darija latine (chiffres 3/7/9, mots darija) → réponse en darija latine
    - Si l'utilisateur écrit en anglais → réponse en anglais
    - Sinon → français par défaut
    """
    texte_norm  = _normaliser_arabe(texte)   # sans harakat pour comparaison fiable
    texte_lower = texte_norm.lower()

    # ── Détection darija arabe ──────────────────────────────
    # Si la majorité des mots sont en arabe → darija_arabe
    caracteres_arabes = sum(1 for c in texte_norm if '\u0600' <= c <= '\u06FF')
    total_lettres     = sum(1 for c in texte_norm if c.isalpha())

    if total_lettres > 0 and (caracteres_arabes / total_lettres) > 0.5:
        return "darija_arabe"

    # Mots arabes isolés forts (même mélangés au latin)
    mots_arabes_forts = [
        "واش", "كيفاش", "بغيت", "كاين", "ماكاينش", "مزيان",
        "واخا", "ايه", "بزاف", "دابا", "ديال", "مشيت",
        "خايف", "ما عارفش", "محتار", "مش واثق", "فين", "شنو",
        "كيفاش", "أشنو", "علاش", "نتا", "نتي", "انا"
    ]
    if any(mot in texte for mot in mots_arabes_forts) and caracteres_arabes > 3:
        return "darija_arabe"

    # ── Détection darija latine ─────────────────────────────
    mots_darija_latin = [
        "wach", "wash", "wesh", "kifach", "bghit",
        "nta", "nti", "rani", "khoya", "khti",
        "3ndek", "3ndi", "ma3arfch", "machi",
        "mzyan", "zwina", "wakha", "iyeh", "bzzaf",
        "ashmen", "kayna", "kayen", "mkaynch",
        "dyal", "dyali", "dyalek", "walou",
        "3awenni", "safi khoya",
        "chnouma", "hnouma", "mnin", "fin", "bch7al",
        "7sab", "bach", "wla", "wlla", "bhal",
        "mazal", "daba", "dial", "f had", "had chi",
        "katkellef", "katkhdem", "kaydiru", "kaysewwel",
        "ndkhol", "katkhellef", "mdrass", "l-qra", "f-supmti"
    ]
    score_darija_latin = sum(1 for m in mots_darija_latin if m in texte_lower)
    if score_darija_latin >= 2:
        return "darija_latin"

    # ── Détection anglais ───────────────────────────────────
    # Mots-clés interrogatifs et communs anglais
    mots_anglais_forts = [
        "what", "how", "where", "when", "why", "which", "who",
        "can you", "could you", "please", "help me",
        "i want", "i need", "tell me", "show me",
        "is there", "are there", "do you", "does it",
        "give me", "explain", "describe"
    ]
    # Mots anglais simples — 1 seul suffit si la phrase est courte
    mots_anglais_simples = [
        "yes", "no", "hello", "hi", "thanks", "okay", "sure",
        "why", "what", "who", "how", "when", "where", "which",
        "continue", "next", "follow", "good", "great", "ok"
    ]

    score_fort = sum(1 for m in mots_anglais_forts if m in texte_lower)

    # 1 mot fort = anglais confirmé
    if score_fort >= 1:
        return "anglais"

    # Phrase courte avec 1 mot anglais simple = anglais
    # (ex: "why?", "yes", "hello", "next")
    if len(texte.split()) <= 4:
        score_simple = sum(1 for m in mots_anglais_simples if m in texte_lower)
        if score_simple >= 1:
            # Vérifier qu'il n'y a pas de mots français évidents
            mots_fr = ["je", "tu", "il", "nous", "vous", "les", "des", "est", "une", "pour"]
            has_fr = any(m in texte_lower.split() for m in mots_fr)
            if not has_fr:
                return "anglais"

    return "français"

# ============================================================
# ÉTAPE 3 — RÉSUMÉ DU PROFIL CONNU
# ============================================================

NIVEAUX_DECLARABLES = {
    "post_bac": "Terminale / Baccalauréat",
    "bac1":     "BAC+1",
    "bac2":     "BAC+2 (DUT/BTS/DEUG)",
    "bac3":     "BAC+3 (Licence)"
}


def construire_resume_profil(profil_etudiant):
    if not profil_etudiant:
        return ""

    infos    = profil_etudiant.get("informations_personnelles", {})
    parcours = profil_etudiant.get("parcours_academique", {})
    prefs    = profil_etudiant.get("preferences", {})

    prenom    = infos.get("prenom", "")
    type_bac  = parcours.get("type_bac", "")
    label_bac = parcours.get("label_bac", "")
    moyenne   = parcours.get("moyenne_generale", 0)
    mention   = parcours.get("mention", "")
    niveau    = parcours.get("niveau_actuel", "")
    diplome   = parcours.get("diplome_actuel", "")
    notes     = parcours.get("notes_matieres", {})
    interets  = prefs.get("centres_interet", [])
    ambition  = prefs.get("ambition_professionnelle", "")

    if not prenom and not type_bac and moyenne == 0:
        return ""

    lignes = ["PROFIL CONNU DE L'ETUDIANT :"]

    if prenom and prenom != "Étudiant":
        lignes.append(f"- Prénom        : {prenom}")
    if type_bac and type_bac != "AUTRE":
        lignes.append(f"- BAC           : {label_bac or type_bac}")
    if moyenne > 0:
        lignes.append(f"- Moyenne       : {moyenne}/20 ({mention})")
    if notes:
        lignes.append(f"- Notes         : {', '.join(f'{m}: {n}' for m, n in list(notes.items())[:5])}")
    if niveau and niveau in NIVEAUX_DECLARABLES:
        lignes.append(f"- Niveau        : {NIVEAUX_DECLARABLES[niveau]}")
    if diplome:
        lignes.append(f"- Diplôme       : {diplome}")
    if interets:
        lignes.append(f"- Intérêts      : {', '.join(interets)}")
    if ambition:
        lignes.append(f"- Ambition      : {ambition}")

    instructions = []

    if prenom and prenom != "Étudiant":
        instructions.append(f"Appelle cette personne par son prénom '{prenom}'.")

    if type_bac and type_bac != "AUTRE" and moyenne > 0:
        type_moy = parcours.get("type_moyenne","generale")
        label_moy = "moyenne générale" if type_moy == "generale" else f"moyenne en {type_moy}"
        instructions.append(
            f"BAC ({label_bac or type_bac}) et {label_moy} ({moyenne}/20) déjà connus. NE PAS les redemander."
        )

    if interets:
        instructions.append(f"Intérêts connus : {', '.join(interets)}. NE PAS les redemander.")

    if instructions:
        lignes.append("")
        lignes.append("INSTRUCTIONS :")
        lignes.extend(instructions)

    # Ajouter le FitScore si calculé
    fitscore_resume = profil_etudiant.get("fitscore_resume")
    if fitscore_resume and fitscore_resume.get("calcule"):
        meilleure_fs = fitscore_resume.get("meilleure","")
        top3         = fitscore_resume.get("top3",[])
        lignes.append(f"- FitScore calculé : filière recommandée = {meilleure_fs}")
        if top3:
            top3_str = ", ".join([f"{f} ({s}%)" for f,s in top3])
            lignes.append(f"- Classement FitScore : {top3_str}")
        lignes.append(
            f"Si l'étudiant demande son FitScore : donne les résultats ci-dessus "
            f"({meilleure_fs} recommandée). NE PAS dire que tu n'as pas accès à cette info."
        )

    return "\n".join(lignes)

# ============================================================
# ÉTAPE 4 — PROMPT SYSTÈME
# ============================================================

def _construire_bloc_frais_prompt():
    """DÉPRÉCIÉ — N'est plus appelé. Le prompt système ne contient plus de données.
    Conservé pour compatibilité éventuelle."""
    lignes = [
        "FRAIS DE SCOLARITÉ :",
        f"  Frais annuels    : {FRAIS_SCOLARITE['frais_annuels']} MAD/an",
        f"  Frais inscription: {FRAIS_SCOLARITE['frais_inscription']} MAD (unique)",
        f"  Total annuel     : {FRAIS_SCOLARITE['total_annuel']} MAD",
        f"  Mensualités      : {FRAIS_SCOLARITE['mensualites']} x {FRAIS_SCOLARITE['montant_mensuel']} MAD/mois",
        "",
        "BOURSES (sur résultats du concours d'admission) :",
        "  Note ≥ 18/20 → 100% de réduction (ne paye que 3 500 MAD d'inscription)",
        "  Note ≥ 16/20 → 70% de réduction  (14 000 MAD/an)",
        "  Note ≥ 14/20 → 50% de réduction  (21 000 MAD/an)",
        "  Note ≥ 12/20 → 30% de réduction  (28 000 MAD/an)",
        "  Note <  12/20 → Pas de bourse    (38 500 MAD/an)",
        "",
        "CONTACT :",
        f"  Téléphone : {SCHOOL_INFO['telephone']}",
        f"  Email     : {SCHOOL_INFO['email']}",
        f"  Horaires  : Lun-Ven {SCHOOL_INFO['horaires']['lundi_vendredi']} | Sam {SCHOOL_INFO['horaires']['samedi']}",
    ]
    return "\n".join(lignes)


def _construire_bloc_filieres_prompt():
    """DÉPRÉCIÉ — N'est plus appelé. L'index filières est dans le prompt directement.
    Conservé pour compatibilité éventuelle."""
    ordre = ["ISI", "IISRT", "IISIC", "ME", "FACG", "MSTIC"]
    lignes = ["LES 6 FILIÈRES DE SUPMTI (données garanties) :"]

    ecole_courante = None
    for fid in ordre:
        if fid not in FILIERES:
            continue
        f = FILIERES[fid]

        # Séparateur par école
        ecole = f.get("departement", "")
        if ecole != ecole_courante:
            ecole_courante = ecole
            if ecole == "Ingénierie":
                lignes.append("\n🎓 ÉCOLE D'INGÉNIERIE")
            elif ecole == "Management":
                lignes.append("\n🏢 ÉCOLE DE MANAGEMENT")

        # Nom + niveau + durée
        lignes.append(f"• {fid} — {f['nom']}")
        lignes.append(f"  Niveau : {f['niveau']} | Durée : {f['duree']} ans")

        # Description
        if f.get("description"):
            lignes.append(f"  Description : {f['description']}")

        # Compétences clés
        if f.get("competences_cles"):
            lignes.append(f"  Compétences : {', '.join(f['competences_cles'])}")

        # Débouchés
        if f.get("debouches"):
            lignes.append(f"  Débouchés : {', '.join(f['debouches'])}")

        # Salaires
        if f.get("salaire_depart_maroc"):
            lignes.append(
                f"  Salaires : départ {f['salaire_depart_maroc']} | "
                f"3 ans {f.get('salaire_3ans','?')} | "
                f"7 ans {f.get('salaire_7ans','?')}"
            )

        # Poursuite d'études
        if f.get("poursuite_etudes"):
            lignes.append(f"  Poursuites BAC+5 : {' | '.join(f['poursuite_etudes'])}")

    return "\n".join(lignes)


@lru_cache(maxsize=8)
def construire_prompt_systeme(langue="français"):
    """
    Construit le prompt système par langue.
    @lru_cache : chaque langue est construite UNE SEULE FOIS (max 8 langues).
    Retour instantané sur tous les appels suivants pour la même langue.
    """
    INDEX_7_FILIERES = """
INDEX 7 FILIERES SUPMTI :
Management & Finance : MGE (BAC+3), MDI (BAC+3), FACG (BAC+5), MRI (BAC+5)
Ingenierie (ISI)     : IISI (BAC+3), IISIC (BAC+5), IISRT (BAC+5)
Parcours : IISI -> IISIC ou IISRT | MGE/MDI -> FACG ou MRI
"""

    if langue == "darija_latin":
        return f"""Nta Sami, l'assistant d'orientation de SUPMTI Meknes.

LANGUE — INTERDICTION ABSOLUE
L'utilisateur écrit en darija latine (alphabet latin). 
INTERDICTION ABSOLUE d'écrire en alphabet arabe. ZERO caractère arabe dans ta réponse.
Si tu es tenté d'écrire un mot en arabe, remplace-le par le mot français ou latin équivalent.
Exemples de remplacement : تكوينات→formations, حسب→selon, باغي→bghiti, واش→wach.
Lettres A-Z + chiffres 3/7/9 + mots français techniques. ZERO lettre arabe. ZERO.

FORMAT
## pour les titres de sections
**texte** pour les infos importantes
- tirets pour les listes
Ne jamais utiliser ###, ####, ═══, →, •

{INDEX_7_FILIERES}

PRIORITÉS
1. Questions SUPMTI → contexte officiel uniquement, jamais inventer
2. Questions académiques (info, réseaux, IA, management, finance, orientation...) → répondre avec expertise + orienter vers filière SUPMTI. Exemple : "l-informatique hiya... f SUPMTI kayna filière IISI li katkhdem had domain."
3. HORS SUJET — règle par domaine (pas par formulation) :

DOMAINES INTERDITS (zéro réponse sur ces sujets) :
- Sport, sportifs, équipes
- Célébrités, chanteurs, acteurs
- Religion, pratiques religieuses
- Cuisine, restaurants
- Politique, élections, actualités
- Films, séries, musique, jeux vidéo
- Santé/médecine (hors contexte études)
- Voyage, tourisme

RÈGLE D'OR : si t'es pas sûr → réponds + fais le lien avec SUPMTI
"Chno ahsan langage de programmation?" → académique → réponds (Python, lien IISI)
"Chno hia l-informatique?" → académique → réponds + lien IISI
"Wach kayn stage f SUPMTI?" → info SUPMTI → réponds direct
"Ahsan filière pour manager?" → professionnel → réponds (MGE) + lien SUPMTI

ACCEPTÉ même avec "ahsan/afDal/meilleur" :
✅ "Chno ahsan langage?" → répondre + IISI
✅ "Chno ahsan domaine fal-informatique?" → répondre + IISI/IISIC
✅ "Wach SUPMTI mezyana wella la?" → répondre honnêtement
✅ "Chno hia l-gestion?" → répondre + MGE

REFUSÉ (domaine interdit) :
❌ "Chkoun howa ahsan laeib kura?" → sport
❌ "Chkoun Messi?" → célébrité
❌ "Chno hia salat l-fajr?" → religion

FORMULE DE REFUS : "Machi domaine dyali. [Alternative SUPMTI concrète]."

PERSONNALITÉ
Chaleureux, direct, comme un ami marocain sur WhatsApp.
Utilise le prénom. Tu t'appelles Sami."""

    elif langue == "darija_arabe":
        return f"""أنت سامي، مساعد التوجيه الأكاديمي لمدرسة SUPMTI مكناس.

اللغة — قاعدة مطلقة
المستخدم يكتب بالدارجة المغربية بالحروف العربية.
ردك يجب أن يكون بالدارجة المغربية بالحروف العربية حصريا.
فقط الأسماء التقنية (IISI, FACG, MGE...) والأرقام بالحروف اللاتينية.
ممنوع استخدام الحروف اللاتينية لكتابة الدارجة.

التنسيق
## للعناوين الرئيسية — ليس ### أو ####
**نص** للمعلومات المهمة — يجب أن يكون الفتح والإغلاق في نفس السطر مثل: **35 000 MAD**
- شرطات للقوائم (- فقط، ممنوع * أو • أو ► للقوائم أبدا)
لا تستخدم أبدا ###, ####, ═══, →, •, *
تأكد دائما أن كل ** مفتوح له ** مغلق في نفس السطر — لا تقطع الـ** على سطرين

{INDEX_7_FILIERES}

الأولويات
1. أسئلة SUPMTI ← من السياق الرسمي فقط، لا تخترع
2. الأسئلة الأكاديمية (تعليم، مسار، مهن، تكوين، إعلاميات، شبكات، تسيير، مالية، ذكاء اصطناعي...) ← أجب بخبرة + وجّه لفليار SUPMTI المناسب. مثال: "الإعلاميات هي... فـ SUPMTI، فليار IISI كاتغطي هاد الميدان."
3. خارج الموضوع — قاعدة حسب الميدان (مش حسب الصياغة) :

الميادين الممنوعة (لا تعطي أي معلومة عليها) :
- الرياضة، اللاعبين، الفرق
- المشاهير، الممثلين، المغنيين
- الدين والعبادات (الصلاة، الصوم، التجويد...)
- الطبخ والمطاعم
- السياسة، الانتخابات، الأخبار
- الترفيه: أفلام، مسلسلات، ألعاب فيديو، موسيقى
- السياحة والسفر

القاعدة الذهبية : إذا ماكنتش متأكد → جاوب + اربط بـ SUPMTI
مقبول حتى مع صيغة أحسن/أفضل :
✅ "Chno ahsan domaine fal-informatique?" → جاوب + IISI
✅ "Chno ahsan filière?" → جاوب + فليار SUPMTI
✅ "Sno kiddir wahd management?" → جاوب + MGE
✅ "Wach kayn stage f SUPMTI?" → جاوب مباشرة (معلومة SUPMTI)
مرفوض : "Chkoun ahsan laeib kura?" / "Chkoun Messi?" / "Chno hia salat l-fajr?"
أيضا : السلامات مقبولة دائما (labas, salam, صباح الخير...) — رد بحرارة
صيغة الرفض : "هذا مشي من دوميني. [بديل SUPMTI محدد]."

الشخصية
دافئ، مباشر، مثل صديق مغربي. استخدم الاسم. اسمك سامي."""

    elif langue == "anglais":
        return """You are Sami, the academic orientation assistant of SUPMTI Meknes.

LANGUAGE — ABSOLUTE RULE
The user writes in English. Your response MUST be strictly in English.

FORMATTING (mandatory)
## for section titles (not ### or ####)
**bold** for key info
- hyphens for lists
Never use ###, ####, ═══, →, •

INDEX 7 PROGRAMMES SUPMTI:
Management & Finance: MGE (BAC+3), MDI (BAC+3), FACG (BAC+5), MRI (BAC+5)
Engineering (ISI)   : IISI (BAC+3), IISIC (BAC+5), IISRT (BAC+5)

PRIORITIES
1. SUPMTI questions → official context only, never invent
2. Academic, educational and professional questions → You MUST answer:
   - Computer science, networking, cybersecurity, AI, data science, software development
   - Management, business administration, marketing, HR
   - Finance, accounting, audit, controlling
   - International business, international relations
   - Study methods, career guidance, exam prep, job market
   - Academic definitions ("what is computer science?", "what is management?"...)
   For these: answer with expertise + link to the relevant SUPMTI programme.
   Example: "Computer science is the study of... At SUPMTI, the IISI programme covers this field."
3. OFF-TOPIC — domain-based rule (not phrasing-based):

STRICTLY FORBIDDEN DOMAINS (never provide any information on these):
- Sports, athletes, teams, sports results
- Celebrities, actors, singers, influencers
- Religion, spirituality, religious practices
- Cooking, recipes, restaurants
- Politics, elections, news
- Entertainment: movies, TV shows, video games, music artists
- Health/medicine (unless as career context)
- Tourism, travel, hotels

GOLDEN RULE — when in doubt, ANSWER and link to SUPMTI:
"What's the best programming language?" → academic → answer + link to IISI
"What's the best career sector?" → professional → answer + link to SUPMTI programs
"Are there internships at SUPMTI?" → SUPMTI info → answer (P1)
"What is computer science / management / finance?" → academic → answer + link to program

QUESTIONS ACCEPTED even with "best/worst" phrasing:
✅ "Best language to learn programming?" → answer (Python) + link IISI
✅ "Best field in IT right now?" → answer (AI/cybersecurity) + link IISI/IISIC
✅ "Best program to become a manager?" → answer (MGE) + link SUPMTI
✅ "Easy or hard to study at SUPMTI?" → answer honestly
✅ "What is computer science?" → answer + link IISI

QUESTIONS REFUSED (forbidden domain):
❌ "Who is the best footballer?" → sport = refuse
❌ "Who is Messi?" → celebrity = refuse
❌ "What is tajweed?" → religion = refuse
❌ "Best restaurant in Meknes?" → tourism = refuse

REFUSAL FORMULA: "That's outside my area. [Specific SUPMTI alternative]."

CHARACTER
Warm, direct, professional. Use the person's first name. Your name is Sami."""

    else:
        return """Tu es Sami, l'assistant d'orientation académique de SUPMTI Meknès 🎓
Tu as la personnalité d'un conseiller pédagogique expérimenté : chaleureux, direct, ultra-compétent.

════════════════════════════════════════
MISSION ET PRIORITÉS
════════════════════════════════════════

PRIORITÉ 1 — Questions sur SUPMTI Meknès (absolu)
Réponds UNIQUEMENT à partir du contexte officiel fourni dans "CONTEXTE OFFICIEL SUPMTI".
Tu n'inventes JAMAIS ni n'extrapoles.
Si l'info est absente du contexte : "Je n'ai pas cette information précise. Contacte SUPMTI : +212 5 35 51 10 11 | contact@supmtimeknes.ac.ma"

PRIORITÉ 2 — Questions académiques, éducatives et professionnelles
Tu es un assistant académique expert. Tu DOIS répondre aux questions dans ces domaines :
- Informatique, développement logiciel, réseaux, cybersécurité, IA, data science, cloud
- Management, gestion d'entreprise, marketing, ressources humaines
- Finance, comptabilité, audit, contrôle de gestion
- Commerce international, relations internationales, export
- Orientation scolaire, méthodes de travail, préparation aux concours
- Débouchés professionnels, marché de l'emploi, compétences
- Définitions académiques dans ces domaines (ex: "c'est quoi l'informatique ?", "qu'est-ce que le management ?")
Pour ces questions : réponds avec expertise + fais le lien avec la filière SUPMTI la plus pertinente.
Exemple : "L'informatique, c'est... À SUPMTI, la filière IISI couvre exactement ce domaine."

PRIORITÉ 3 — HORS PÉRIMÈTRE (règle de domaine, pas de formulation)

DOMAINES STRICTEMENT INTERDITS (tu ne réponds sur AUCUN de ces sujets) :
- Sport, sportifs, équipes, résultats sportifs
- Célébrités, acteurs, chanteurs, influenceurs, personnalités publiques non académiques
- Religion, spiritualité, pratiques religieuses
- Cuisine, recettes, restaurants
- Politique, partis, élections, actualités
- Divertissement : films, séries, jeux vidéo, musique
- Santé, médecine, symptômes (sauf études de santé comme contexte)
- Voyages, tourisme, hôtels

RÈGLE D'OR — si tu as un doute, RÉPONDS et fais le lien avec SUPMTI :
Ex : "Quel est le meilleur langage de programmation ?" → c'est académique → réponds + lien IISI
Ex : "Quel est le meilleur secteur pour trouver un emploi ?" → c'est professionnel → réponds + filières

QUESTIONS ACCEPTÉES MALGRÉ LA FORME "meilleur/best/أحسن" :
✅ "Quel est le meilleur langage pour débuter ?" → répondre (Python, lien IISI)
✅ "Quel est le meilleur domaine en informatique ?" → répondre (IA/cybersécurité, lien IISI/IISIC)
✅ "Quel est le meilleur cursus pour devenir manager ?" → répondre (MGE, lien SUPMTI)
✅ "Est-ce que le stage est obligatoire à SUPMTI ?" → répondre (info SUPMTI = P1)
✅ "C'est quoi l'informatique / le management / la finance ?" → répondre + lien filière

QUESTIONS REFUSÉES (domaine interdit) :
❌ "Qui est le meilleur footballeur ?" → sport = refus
❌ "Qui est Messi ?" → célébrité = refus
❌ "C'est quoi le tajweed ?" → religion = refus
❌ "Meilleur restaurant à Meknès ?" → cuisine/tourisme = refus

FORMULE DE REFUS (courte, directe) :
"Ce n'est pas mon domaine. [Proposition alternative concrète liée à SUPMTI]."

════════════════════════════════════════
INDEX SUPMTI — 7 FILIÈRES
════════════════════════════════════════

Cherche les détails dans le contexte officiel. Cet index t'aide à savoir quoi chercher.

Département Management & Finance :
- MGE : Management de l'Entreprise (BAC+3, 3 ans)
- MDI : Management et Développement International (BAC+3, 3 ans)
- FACG : Finance, Audit et Contrôle de Gestion (BAC+5, 2 ans)
- MRI : Management et Relations Internationales (BAC+5, 2 ans)

Département Ingénierie (ISI) :
- IISI : Ingénierie Intelligente des Systèmes Informatiques (BAC+3, 3 ans)
- IISIC : Ingénierie Intelligente des Systèmes d'Information et Communication (BAC+5, 2 ans)
- IISRT : Ingénierie Intelligente des Systèmes Réseaux et Télécommunications (BAC+5, 2 ans)

Parcours : bachelier → IISI, MGE ou MDI. Les BAC+5 sont des suites après le BAC+3.

════════════════════════════════════════
FORMAT DE RÉPONSE — RÈGLES STRICTES
════════════════════════════════════════

Utilise TOUJOURS ce format pour structurer tes réponses :

## Titre de section principale
Texte d'introduction ou paragraphe explicatif.
**information clé**, **chiffre important**, **nom de filière**
- élément de liste
- autre élément

RÈGLES :
- ## pour CHAQUE titre de section (obligatoire dès qu'il y a plusieurs parties)
- **gras** pour les chiffres, noms de filières, informations importantes (ouverture ET fermeture sur la même ligne obligatoires)
- Tirets - pour les listes (jamais de •, jamais de ►)
- JAMAIS de : →, ═══, ####, ──── dans le texte visible
- Maximum 2 emojis par réponse, seulement dans les titres ## si pertinent
- Montants : 35 000 MAD (toujours avec espace et MAD)
- Ligne vide entre chaque section ## pour la lisibilité

EXEMPLE DE BONNE RÉPONSE (frais) :
## 💰 Frais de scolarité
Les frais s'élèvent à **35 000 MAD par an**, payables en **10 mensualités de 3 500 MAD/mois**.
Auxquels s'ajoutent **3 500 MAD** de frais d'inscription (une seule fois, non remboursables).
**Total annuel complet : 38 500 MAD**

## Bourses d'excellence
Les bourses réduisent les **35 000 MAD** de scolarité selon ta note au concours :
- Note **≥ 18/20** : bourse 100% — tu payes seulement l'inscription (**3 500 MAD**)
- Note **≥ 16/20** : bourse 70% — **14 000 MAD/an**
- Note **≥ 14/20** : bourse 50% — **21 000 MAD/an**
- Note **≥ 12/20** : bourse 30% — **28 000 MAD/an**
- Note **< 12/20** : pas de bourse — **38 500 MAD/an**

════════════════════════════════════════
CALIBRATION DES RÉPONSES
════════════════════════════════════════

Question courte (salut, ça va, c'est quoi X) :
- 2-4 lignes, une seule section, pas de liste

Question standard (frais, contact, bourse, admission) :
- 1-3 sections ## bien structurées, réponse complète mais concise

Question détaillée (présente-moi X, programme complet) :
- Réponse exhaustive avec toutes les sections nécessaires

Question d'orientation personnelle (j'ai BAC D, j'aime l'info) :
- Analyse du profil + recommandation personnalisée + étapes concrètes

════════════════════════════════════════
PERSONNALITÉ ET COMPORTEMENT
════════════════════════════════════════
- Chaleureux, direct, professionnel — comme un ami conseiller pédagogique très compétent
- Utilise toujours le prénom quand tu le connais
- Ne redemande JAMAIS une information déjà donnée dans la conversation
- Ne suppose JAMAIS le niveau d'études avant que la personne le dise
- Salutations seules (bonjour, ça va) : réponds chaleureusement SANS lister les filières
- Si la personne hésite ou veut un témoignage : "Tu peux utiliser Peer Match dans le menu pour parler à un étudiant actuel"
- Tu t'appelles Sami 😊

════════════════════════════════════════
UTILISATION DE L'HISTORIQUE — RÈGLE ABSOLUE
════════════════════════════════════════
L'historique de la conversation t'est fourni. Tu DOIS l'utiliser.

- "Suivant" ou "suite" ou "continue" → regarde le dernier message pour savoir ce qui précédait et continue.
- "Au niveau où nous étions" → relis l'historique et reprends exactement là où on s'est arrêté.
- Ne jamais demander à l'utilisateur de répéter ce qui est déjà dans l'historique.
- Si quelqu'un dit "étape 2" ou "filière suivante", regarde quelle était l'étape 1 dans l'historique.

EXEMPLE CORRECT :
L'historique montre que tu présentais MGE.
L'utilisateur dit "Suivant".
→ Tu passes directement à MDI sans demander de clarification."""


# ============================================================
# ÉTAPE 5 — RÉPONSE RAG PRINCIPALE
# ============================================================

def _top_k_pour_question(question):
    """
    top_k FAISS — conservé modéré car Data1.txt complet est injecté en hardcode.
    FAISS sert à identifier les passages les plus pertinents pour affiner la réponse.
    """
    q = question.lower()
    mots_larges = [
        "filiere", "filieres", "filière", "filières",
        "toutes", "tous", "liste", "complet", "complète",
        "presentation", "présentation", "supmti", "ecole", "école",
        "programme", "formation", "parcours", "semestre",
        "debouche", "débouché", "admission", "condition",
        "qui sommes", "vision", "mission", "valeur", "valeurs",
        "equipe", "enseignant", "partenariat", "certification",
        "bourse", "frais", "scolarite", "scolarité", "contact",
        "bac+3", "bac+5", "niveau", "departement", "département",
        # Infos institutionnelles
        "fondateur", "fondé", "fondation", "créé", "créateur",
        "année", "date", "historique", "histoire", "origine",
        "slogan", "devise", "accréditation", "agrément",
        # Domaines académiques (pour lier à une filière)
        "informatique", "réseaux", "télécommunication", "telecom",
        "management", "finance", "audit", "international",
        "intelligence artificielle", "data", "cloud", "cybersécurité",
        "gestion", "comptabilité", "marketing", "commerce",
        "definition", "définition", "c'est quoi", "qu'est-ce",
        "expliquer", "expliquez", "expliquer moi"
    ]
    if any(m in q for m in mots_larges):
        return 10   # Réduit : Data1.txt complet est déjà dans le contexte garanti
    return 5        # Questions précises : le hardcode suffit, FAISS confirme



def _tokens_pour_question(question):
    """
    max_tokens dynamique.
    Calibré pour le Data1.txt officiel (69 000 chars).
    Un programme complet de filière = 6 semestres + compétences + débouchés + admission
    = environ 3000-5000 tokens de réponse complète.
    """
    q = question.lower()

    # Questions ultra-courtes : salutations, remerciements
    # Salutations pures → courtes
    # Salutations pures françaises → 400 tokens (réponse courte)
    mots_salutations_fr = {"salut", "bonjour", "merci", "d'accord", "ça va", "ca va",
                           "super", "parfait", "bonsoir", "au revoir", "oui", "non",
                           "ok", "okay", "bsr"}
    q_clean = q.strip().rstrip("?!. ").lower()
    if q_clean in mots_salutations_fr:
        return 400
    # Très court (≤ 3 chars) → 400
    if len(q.strip()) <= 3:
        return 400

    # Questions demandant une réponse très longue et exhaustive
    mots_exhaustifs = [
        "programme complet", "tous les semestres", "semestre 1", "semestre 2",
        "semestre 3", "semestre 4", "semestre 5", "semestre 6",
        "presentation complete", "présentation complète", "tout sur",
        "détaille", "detaille", "explique en détail", "explique-moi tout",
        "toutes les filieres", "toutes les filières", "les 7 filieres",
        "etape par etape", "étape par étape", "filiere par filiere",
        "compétences requises", "conditions d'admission",
        "débouchés professionnels", "organisation du programme",
        "points forts", "certifications", "partenariat",
        "masters internationaux", "vie etudiante",
        "programme de formation", "programme de la formation",
        "comparaison", "compare", "présente-moi", "presente-moi",
        "donne-moi tous", "donnes-moi tout", "suivant", "suite", "continue",
    ]
    if any(m in q for m in mots_exhaustifs):
        return 8000   # Assez pour 7 filières complètes ou 1 filière exhaustive

    # Questions standard (filière, frais, bourse, admission résumée)
    mots_standards = [
        # Français
        "filiere", "filière", "programme", "semestre", "admission",
        "bourse", "frais", "scolarite", "scolarité", "présentation", "presentation",
        "comment", "quelles sont", "quels sont", "debouches", "débouchés",
        "competences", "compétences", "condition", "passerelle", "quelle est",
        "c'est quoi", "kesquoi", "kifsah", "responsable", "équipe", "professeur",
        "encadrement", "jury", "directeur", "coordonnateur",
        # Anglais
        "supervisor", "supervisors", "teacher", "professor", "staff", "team",
        "tutor", "coordinator", "director", "fees", "cost", "price",
        "scholarship", "program", "curriculum", "major", "track", "course",
        "requirement", "degree", "certificate", "application", "apply",
        "career", "job", "salary", "graduate", "admission", "enroll",
        # Darija latin
        "filiere", "chou3ab", "qraya", "taklef", "bourse", "concours",
        "admission", "programme", "semestre", "diplome", "bac", "stage",
        "shuman", "shno", "ashmen", "kifach", "kif", "3lach", "wach",
        # Darija arabe
        "تخصص", "فلييرة", "قراية", "بورصة", "كونكور", "برنامج", "سمستر",
    ]
    if any(m in q for m in mots_standards):
        return 3000   # Assez pour une réponse complète (liste membres, frais, filière)

    return 1200  # réponse standard


def generer_reponse_rag(question, historique=None, profil_etudiant=None):
    global _index, _metadonnees

    if not verifier_connexion():
        return reponse_hors_ligne(question)

    if _index is None:
        _index, _metadonnees = charger_base_existante()

    if _index is None:
        return {
            "reponse": "Je suis désolé, ma base de connaissances n'est pas disponible.",
            "mode": "erreur", "sources": []
        }

    langue  = detecter_langue(question)
    top_k   = _top_k_pour_question(question)
    chunks_pertinents = recherche_semantique(question, _index, _metadonnees, top_k=top_k)
    print(f"[RAG] top_k={top_k} | chunks={len(chunks_pertinents)} | question: {question[:60]}")

    # Contexte RAG depuis FAISS
    contexte_faiss = "\n\n---\n\n".join([
        f"Source: {c['source']}\n{c['contenu']}" for c in chunks_pertinents
    ])

    # Données garanties depuis academic_config (filières, frais, contact)
    # Toujours injectées — indépendamment du FAISS
    contexte_garanti = _construire_contenu_hardcode()

    # Contexte final = données garanties + chunks FAISS (sans doublon)
    contexte = f"{contexte_garanti}\n\n===CONTEXTE RAG===\n{contexte_faiss}" if contexte_faiss else contexte_garanti

    resume_profil = construire_resume_profil(profil_etudiant)

    messages = [
        {"role": "system", "content": construire_prompt_systeme(langue)},
        {"role": "system", "content": f"CONTEXTE OFFICIEL SUPMTI :\n{contexte}"}
    ]

    if resume_profil:
        messages.append({"role": "system", "content": resume_profil})

    if historique:
        # Limiter l'historique : garder les 8 derniers messages
        # ET tronquer les messages trop longs (réponses de filières complètes)
        hist_filtre = historique[-8:]
        for echange in hist_filtre:
            contenu = echange.get("content", "")
            # Si un message dépasse 3000 tokens (~12000 chars), résumer
            if len(contenu) > 12000:
                contenu = contenu[:4000] + "\n[...réponse longue tronquée pour l'historique...]"
            messages.append({"role": echange["role"], "content": contenu})

    messages.append({"role": "user", "content": question})

    try:
        r = client.chat.completions.create(
            model=CHATBOT_CONFIG["modele_gpt"],
            messages=messages,
            temperature=CHATBOT_CONFIG["temperature_gpt"],
            max_completion_tokens=_tokens_pour_question(question)
        )
        return {
            "reponse":         r.choices[0].message.content,
            "mode":            "rag",
            "langue":          langue,
            "sources":         [c["source"] for c in chunks_pertinents],
            "chunks_utilises": len(chunks_pertinents)
        }
    except Exception as e:
        print(f"[ERREUR GPT] {e}")
        return {
            "reponse": "Je rencontre une difficulté technique. Veuillez réessayer.",
            "mode": "erreur", "sources": []
        }


def generer_reponse_rag_stream(question, historique=None, profil_etudiant=None):
    """
    Version streaming de generer_reponse_rag.
    Retourne un générateur de tokens pour SSE (Server-Sent Events).
    """
    global _index, _metadonnees

    if not verifier_connexion():
        r = reponse_hors_ligne(question)
        yield r["reponse"], None
        return

    if _index is None:
        _index, _metadonnees = charger_base_existante()

    if _index is None:
        yield "Je suis désolé, ma base de connaissances n'est pas disponible.", None
        return

    langue  = detecter_langue(question)
    top_k   = _top_k_pour_question(question)
    chunks_pertinents = recherche_semantique(question, _index, _metadonnees, top_k=top_k)

    # Données garanties + chunks FAISS
    contexte_faiss   = "\n\n---\n\n".join([
        f"Source: {c['source']}\n{c['contenu']}" for c in chunks_pertinents
    ])
    contexte_garanti = _construire_contenu_hardcode()
    contexte = f"{contexte_garanti}\n\n===CONTEXTE RAG===\n{contexte_faiss}" if contexte_faiss else contexte_garanti

    resume_profil = construire_resume_profil(profil_etudiant)

    messages = [
        {"role": "system", "content": construire_prompt_systeme(langue)},
        {"role": "system", "content": f"CONTEXTE OFFICIEL SUPMTI :\n{contexte}"}
    ]
    if resume_profil:
        messages.append({"role": "system", "content": resume_profil})
    if historique:
        hist_filtre = historique[-8:]
        for echange in hist_filtre:
            contenu = echange.get("content", "")
            if len(contenu) > 12000:
                contenu = contenu[:4000] + "\n[...réponse longue tronquée pour l'historique...]"
            messages.append({"role": echange["role"], "content": contenu})
    messages.append({"role": "user", "content": question})

    try:
        stream = client.chat.completions.create(
            model=CHATBOT_CONFIG["modele_gpt"],
            messages=messages,
            temperature=CHATBOT_CONFIG["temperature_gpt"],
            max_completion_tokens=_tokens_pour_question(question),
            stream=True
        )
        full_response = ""
        for chunk in stream:
            if chunk.choices[0].delta.content:
                token = chunk.choices[0].delta.content
                full_response += token
                yield token, None  # (token, None) = pas encore terminé

        yield None, full_response  # (None, full_response) = terminé

    except Exception as e:
        print(f"[ERREUR GPT STREAM] {e}")
        yield "Je rencontre une difficulté technique. Veuillez réessayer.", None

# ============================================================
# ÉTAPE 6 — MODE HORS LIGNE
# ============================================================

def verifier_connexion():
    try:
        requests.get("https://www.google.com", timeout=3)
        return True
    except Exception:
        return False


def generer_donnees_offline():
    os.makedirs(OFFLINE_PATH, exist_ok=True)

    # Ordre fixe des filières : IISI → MGE → MDI → IISIC → IISRT → FACG → MRI
    ORDRE_FILIERES = ["IISI", "MGE", "MDI", "IISIC", "IISRT", "FACG", "MRI"]

    filieres_ordonnees = {}
    for fid in ORDRE_FILIERES:
        if fid in FILIERES:
            f = FILIERES[fid]
            filieres_ordonnees[fid] = {
                "nom": f["nom"], "niveau": f["niveau"],
                "duree": f["duree"], "description": f["description"],
                "debouches": f["debouches"]
            }
    # Ajouter les filières éventuellement absentes de l'ordre fixe
    for fid, f in FILIERES.items():
        if fid not in filieres_ordonnees:
            filieres_ordonnees[fid] = {
                "nom": f["nom"], "niveau": f["niveau"],
                "duree": f["duree"], "description": f["description"],
                "debouches": f["debouches"]
            }

    donnees_offline = {
        "derniere_mise_a_jour": datetime.now().isoformat(),
        "ecole": {
            "nom":       SCHOOL_INFO["nom"],
            "telephone": SCHOOL_INFO["telephone"],
            "email":     SCHOOL_INFO["email"],
            "horaires":  SCHOOL_INFO["horaires"]
        },
        "frais": FRAIS_SCOLARITE,
        "filieres": filieres_ordonnees,
        "faq": [
            {
                "question": "frais scolarite",
                "reponse": (
                    f"Les frais sont de {FRAIS_SCOLARITE['frais_annuels']} DH/an "
                    f"payables en {FRAIS_SCOLARITE['mensualites']} mensualités "
                    f"de {FRAIS_SCOLARITE['montant_mensuel']} DH, plus "
                    f"{FRAIS_SCOLARITE['frais_inscription']} DH d'inscription. "
                    f"Total annuel : {FRAIS_SCOLARITE['total_annuel']} DH."
                )
            },
            {
                "question": "filieres formations",
                "reponse": (
                    f"SUPMTI Meknès propose {len(FILIERES)} filières : "
                    f"Ingénierie (IISI → IISIC, IISRT) et Management (MGE/MDI → FACG, MRI)."
                )
            },
            {
                "question": "contact telephone email",
                "reponse": (
                    f"Téléphone : {SCHOOL_INFO['telephone']} | "
                    f"Email : {SCHOOL_INFO['email']} | "
                    f"Horaires : Lun-Ven 08h30-18h00, Sam 08h30-12h00"
                )
            },
            {
                "question": "admission bac",
                "reponse": (
                    "L'admission se fait sur dossier et entretien. "
                    "Bac scientifique pour l'ingénierie, "
                    "tous bacs pour le management."
                )
            }
        ]
    }

    chemin = os.path.join(OFFLINE_PATH, "donnees_essentielles.json")
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(donnees_offline, f, ensure_ascii=False, indent=2)
    print("[OFFLINE] ✅ Données hors ligne sauvegardées")


def reponse_hors_ligne(question):
    chemin = os.path.join(OFFLINE_PATH, "donnees_essentielles.json")
    if not os.path.exists(chemin):
        return {
            "reponse": "⚠️ Mode hors ligne actif. Veuillez vous connecter à internet.",
            "mode": "hors_ligne_erreur"
        }

    with open(chemin, "r", encoding="utf-8") as f:
        donnees = json.load(f)

    question_lower = question.lower().strip()

    # Messages sociaux — répondre simplement
    mots_sociaux = [
        "merci", "thank", "ok", "okay", "safi", "wakha",
        "super", "parfait", "d'accord", "bien", "bonjour",
        "salut", "bonsoir", "bonne", "au revoir", "bye"
    ]
    if any(m in question_lower for m in mots_sociaux):
        return {
            "reponse": (
                "⚠️ Mode hors ligne actif.\n\n"
                "Je suis limité en ce moment, mais je reste disponible "
                "pour tes questions sur SUPMTI 😊\n"
                "📞 +212 5 35 51 10 11"
            ),
            "mode": "hors_ligne"
        }

    # FAQ — chercher dans les mots clés
    for faq in donnees["faq"]:
        if any(m in question_lower for m in faq["question"].split()):
            return {
                "reponse": f"⚠️ Mode hors ligne actif.\n\n{faq['reponse']}",
                "mode": "hors_ligne"
            }

    # Question inconnue — réponse claire sans surcharge d'info
    return {
        "reponse": (
            "⚠️ Mode hors ligne actif.\n\n"
            "Je n'ai pas cette information en mode hors ligne.\n\n"
            "📞 Vérifiez votre connexion internet ou contactez SUPMTI : "
            f"{donnees['ecole']['telephone']}\n"
            "Reconnectez-vous à internet pour des informations complètes."
        ),
        "mode": "hors_ligne"
    }


# ============================================================
# ÉTAPE 7 — SYNCHRONISATION AUTOMATIQUE (WEBSCRAPING)
# ============================================================

def calculer_hash_contenu(contenu):
    return hashlib.md5(contenu.encode("utf-8")).hexdigest()


def _extraire_texte_page(soup, url):
    """
    Extrait le texte utile d'une page HTML.

    Stratégie :
    - Supprimer script / style / nav / header / meta / link
    - GARDER <footer> car il contient téléphone, email, adresse
    - Si le contenu principal est trop court (page JS dynamique) → retourner ""
    """
    # Supprimer seulement les balises vraiment inutiles
    # NOTE : on ne supprime PAS footer ni header — ils contiennent
    # le téléphone (+212 5 35 51 10 11), l'email et l'adresse
    for tag in soup(["script", "style", "nav", "meta", "link",
                     "noscript", "iframe", "button", "form"]):
        tag.decompose()

    texte = soup.get_text(separator="\n", strip=True)
    lignes = [l.strip() for l in texte.splitlines() if l.strip() and len(l.strip()) > 2]
    texte_propre = "\n".join(lignes)

    # Pages rendues en JavaScript dynamique → contenu inutilisable
    # Seuil : 400 chars = page vide côté JS (BDE: 588, clubs: 851 → légèrement au-dessus)
    # On baisse à 300 pour ne pas exclure les pages légères mais valides
    if len(texte_propre) < 300:
        print(f"[SYNC] ⚠️ {url} : {len(texte_propre)} chars — probablement rendu JS, ignoré")
        return ""

    return texte_propre


_HARDCODE_CACHE = None   # Cache mémoire — chargé une seule fois au démarrage

def _construire_contenu_hardcode():
    """
    Génère un bloc de texte avec les informations critiques de SUPMTI
    OPTIMISATION : résultat mis en cache mémoire après le premier appel.
    Aucune lecture disque ni reconstruction de string sur les appels suivants.
    tirées de academic_config.py.
    Ce bloc est TOUJOURS ajouté au contenu scrapé pour garantir que
    les frais, le téléphone et les filières sont dans la base RAG,
    même si le site web ne les affiche pas directement.
    """
    global _HARDCODE_CACHE
    if _HARDCODE_CACHE is not None:
        return _HARDCODE_CACHE   # ← retour immédiat (0ms) après le 1er appel

    lignes = [
        "=== SOURCE: academic_config_supmti ===",
        f"École : {SCHOOL_INFO['nom']} — {SCHOOL_INFO['nom_complet']}",
        f"Slogan : {SCHOOL_INFO['slogan']}",
        f"Fondée en : {SCHOOL_INFO.get('fondation', 2014)} (année de création : 2014)",
        "Fondateurs : M. KRIOUILE Mohamed et M. KRIOUILE Abdelaziz",
        f"Adresse : {SCHOOL_INFO['adresse']}",
        f"Téléphone : {SCHOOL_INFO['telephone']}",
        f"Email : {SCHOOL_INFO['email']}",
        f"Site web : {SCHOOL_INFO['site_web']}",
        f"Horaires : Lundi-Vendredi {SCHOOL_INFO['horaires']['lundi_vendredi']}, "
        f"Samedi {SCHOOL_INFO['horaires']['samedi']}",
        "",
        "=== FRAIS DE SCOLARITÉ ===",
        f"Frais annuels : {FRAIS_SCOLARITE['frais_annuels']} MAD/an",
        f"Frais d'inscription : {FRAIS_SCOLARITE['frais_inscription']} MAD (une seule fois)",
        f"Total annuel (inscription incluse) : {FRAIS_SCOLARITE['total_annuel']} MAD",
        f"Mensualités : {FRAIS_SCOLARITE['mensualites']} paiements "
        f"de {FRAIS_SCOLARITE['montant_mensuel']} MAD/mois",
        "",
        "=== BOURSES D'EXCELLENCE ===",
        "Les bourses sont attribuées selon les résultats du concours d'admission :",
        "- Note ≥ 18/20 → Bourse 100% (ne paye que 3 500 MAD d'inscription)",
        "- Note ≥ 16/20 → Bourse 70% (14 000 MAD/an)",
        "- Note ≥ 14/20 → Bourse 50% (21 000 MAD/an)",
        "- Note ≥ 12/20 → Bourse 30% (28 000 MAD/an)",
        "- Note < 12/20 → Pas de bourse (38 500 MAD/an)",
        "",
        "=== FILIÈRES SUPMTI ===",
    ]

    for fid, f in FILIERES.items():
        lignes += [
            f"Filière {fid} — {f['nom']}",
            f"  Niveau : {f['niveau']} | Durée : {f['duree']} ans",
            f"  Département : {f['departement']}",
            f"  Description : {f['description']}",
            f"  Compétences : {', '.join(f.get('competences_cles', []))}",
            f"  Débouchés : {', '.join(f.get('debouches', []))}",
            ""
        ]

    lignes += [
        "=== STRUCTURE DES ÉTUDES (7 FILIÈRES) ===",
        "Département Ingénierie (ISI) :",
        "  IISI (BAC+3, 3 ans) → spécialisation IISIC ou IISRT (BAC+5, 2 ans supplémentaires)",
        "Département Management et Finance :",
        "  MGE (BAC+3, 3 ans) → spécialisation FACG ou MRI (BAC+5, 2 ans supplémentaires)",
        "  MDI (BAC+3, 3 ans) → spécialisation MRI ou FACG (BAC+5, 2 ans supplémentaires)",
        "",
        "=== ADMISSION ===",
        "Admission en 1ère année : après le BAC, sur dossier + entretien.",
        "Admission en 3ème année (BAC+2) : DUT, BTS, DEUG, TS.",
        "Admission en 4ème année (BAC+3) : Licence, BAC+3 SUPMTI ou équivalent.",
        "Toutes nationalités acceptées. Étudiants internationaux bienvenus.",
    ]

    # Injecter les programmes complets par semestre depuis le fichier Data1.txt
    try:
        import os
        doc_path = os.path.join(
            os.getenv("DOCUMENTS_PATH", "./data/documents"), "Data1.txt"
        )
        if os.path.exists(doc_path):
            with open(doc_path, "r", encoding="utf-8") as f:
                data_raw = f.read()
            lignes.append("")
            lignes.append("=== PROGRAMMES COMPLETS PAR SEMESTRE (SOURCE: Data1.txt) ===")
            lignes.append(data_raw)
    except Exception as e:
        print(f"[HARDCODE] Impossible de charger Data1.txt: {e}")

    _HARDCODE_CACHE = "\n".join(lignes)
    print(f"[CACHE] Hardcode chargé en mémoire ({len(_HARDCODE_CACHE):,} chars) — lectures disque futures = 0ms")
    return _HARDCODE_CACHE


def scraper_site_supmti():
    """
    Scrape toutes les URLs SUPMTI définies dans academic_config.py.
    Retourne le contenu textuel total agrégé.

    Améliorations v2 :
    - Conserve le footer HTML (contient téléphone et email)
    - Ignore les pages < 300 chars (rendu JS dynamique)
    - Injecte toujours un bloc hardcodé avec frais/contact/filières
      pour garantir que ces données critiques sont dans la base RAG
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection":      "keep-alive",
    }

    urls_ok     = 0
    urls_erreur = 0
    urls_js     = 0

    # Toujours commencer par le bloc de données garanties
    contenu_total = _construire_contenu_hardcode()
    print(f"[SYNC] ✅ Bloc données hardcodé injecté ({len(contenu_total)} chars)")

    for url in SUPMTI_URLS:
        try:
            r = requests.get(url, headers=headers, timeout=15)
            r.raise_for_status()
            soup = BeautifulSoup(r.content, "html.parser")

            texte_propre = _extraire_texte_page(soup, url)

            if texte_propre:
                contenu_total += f"\n\n=== SOURCE: {url} ===\n{texte_propre}"
                urls_ok += 1
                print(f"[SYNC] ✅ {url} ({len(texte_propre)} chars)")
            else:
                urls_js += 1

        except requests.exceptions.Timeout:
            print(f"[SYNC] ⏱️ Timeout : {url}")
            urls_erreur += 1
        except requests.exceptions.HTTPError as e:
            print(f"[SYNC] ❌ HTTP {e.response.status_code} : {url}")
            urls_erreur += 1
        except requests.exceptions.ConnectionError:
            print(f"[SYNC] 🔌 Connexion impossible : {url}")
            urls_erreur += 1
        except Exception as e:
            print(f"[SYNC] ⚠️ Erreur inattendue {url} : {e}")
            urls_erreur += 1

    print(
        f"[SYNC] Résumé : {urls_ok} OK / {urls_js} pages JS ignorées / "
        f"{urls_erreur} erreurs / {len(SUPMTI_URLS)} total"
    )
    return contenu_total


def synchroniser_base_rag():
    """
    Synchronisation complète du site SUPMTI.

    ⚠️  SCRAPING SUSPENDU par défaut (irrégularités détectées sur le site).
    Pour réactiver : mettre SCRAPING_ACTIF=true dans le fichier .env
    ou appeler cette fonction manuellement depuis un shell :
        python -c "from app.services.rag_service import synchroniser_base_rag; synchroniser_base_rag()"
    """
    global _index, _metadonnees

    # ── Vérification activation scraping ──────────────────────
    scraping_actif = os.getenv("SCRAPING_ACTIF", "false").lower() == "true"
    if not scraping_actif:
        print("[SYNC] ⏸️  Scraping SUSPENDU (SCRAPING_ACTIF=false dans .env)")
        print("[SYNC]    Pour activer : ajouter SCRAPING_ACTIF=true dans .env et redémarrer.")
        return

    print(f"\n[SYNC] ══════ Synchronisation RAG — {datetime.now().strftime('%Y-%m-%d %H:%M')} ══════")

    if not verifier_connexion():
        print("[SYNC] ⚠️ Pas de connexion internet — synchronisation annulée")
        return

    chemin_hash     = os.path.join(VECTOR_DB_PATH, "site_hash.txt")
    nouveau_contenu = scraper_site_supmti()

    if not nouveau_contenu or len(nouveau_contenu.strip()) < 100:
        print("[SYNC] ⚠️ Contenu insuffisant récupéré — synchronisation annulée")
        return

    nouveau_hash = calculer_hash_contenu(nouveau_contenu)
    ancien_hash  = ""
    if os.path.exists(chemin_hash):
        try:
            with open(chemin_hash, "r") as f:
                ancien_hash = f.read().strip()
        except Exception:
            ancien_hash = ""

    if nouveau_hash == ancien_hash:
        print("[SYNC] ✅ Aucun changement détecté — base RAG à jour")
        return

    print("[SYNC] 🔄 Changement détecté — mise à jour de la base RAG...")

    os.makedirs(DOCUMENTS_PATH, exist_ok=True)
    chemin_site = os.path.join(DOCUMENTS_PATH, "site_supmti.txt")
    try:
        with open(chemin_site, "w", encoding="utf-8") as f:
            f.write(nouveau_contenu)
        print(f"[SYNC] 📄 Contenu sauvegardé ({len(nouveau_contenu)} caractères)")
    except Exception as e:
        print(f"[SYNC] ❌ Erreur sauvegarde contenu : {e}")
        return

    try:
        initialiser_base_vectorielle()
        _index, _metadonnees = charger_base_existante()
        print(f"[SYNC] 🧠 Base FAISS reconstruite — {_index.ntotal if _index else 0} vecteurs")
    except Exception as e:
        print(f"[SYNC] ❌ Erreur reconstruction FAISS : {e}")
        return

    try:
        os.makedirs(VECTOR_DB_PATH, exist_ok=True)
        with open(chemin_hash, "w") as f:
            f.write(nouveau_hash)
    except Exception as e:
        print(f"[SYNC] ⚠️ Erreur sauvegarde hash : {e}")

    generer_donnees_offline()
    # Invalider le cache hardcode pour forcer rechargement avec le nouveau contenu
    global _HARDCODE_CACHE
    _HARDCODE_CACHE = None
    _construire_contenu_hardcode()   # recharger immédiatement en mémoire
    construire_prompt_systeme.cache_clear()  # invalider cache prompts (langue peut changer)
    print("[SYNC] ✅ Synchronisation terminée + caches invalidés !")


def demarrer_scheduler():
    """
    Démarre le scheduler APScheduler.

    ⚠️  Si SCRAPING_ACTIF=false (défaut), le scheduler tourne mais
    synchroniser_base_rag() s'arrête immédiatement au contrôle.
    Pour activer le scraping : SCRAPING_ACTIF=true dans .env
    """
    scheduler = BackgroundScheduler(
        timezone="Africa/Casablanca",
        job_defaults={"misfire_grace_time": 3600}
    )
    scheduler.add_job(
        synchroniser_base_rag,
        "cron",
        hour=3, minute=0,
        id="sync_rag_quotidien",
        replace_existing=True
    )
    scheduler.start()
    scraping_actif = os.getenv("SCRAPING_ACTIF", "false").lower() == "true"
    if scraping_actif:
        print("[SCHEDULER] ✅ Scraping activé — sync automatique à 3h00 (Casablanca)")
    else:
        print("[SCHEDULER] ⏸️  Scheduler démarré — scraping SUSPENDU (SCRAPING_ACTIF=false)")
        print("[SCHEDULER]    Pour activer le scraping : SCRAPING_ACTIF=true dans .env")
    return scheduler