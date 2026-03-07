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
        print("[RAG] Construction de la base vectorielle...")
        initialiser_base_vectorielle()
    _index, _metadonnees = charger_base_existante()
    if _index is not None:
        print("[RAG] ✅ Système RAG prêt !")
        generer_donnees_offline()
    else:
        print("[RAG] ⚠️ Système RAG en mode dégradé")

# ============================================================
# ÉTAPE 2 — DÉTECTER LA LANGUE
# ============================================================

def detecter_langue(texte):
    """
    Détecte si le message est en darija, anglais ou français.
    NOTE : Les caractères arabes dans le message de l'utilisateur
    ne doivent PAS influencer la langue de réponse — on répond
    toujours en darija latine même si l'utilisateur écrit en arabe.
    """
    texte_lower = texte.lower()

    mots_darija_forts = [
        "wach", "wash", "wesh", "kifach", "bghit",
        "nta", "nti", "rani", "khoya", "khti",
        "3ndek", "3ndi", "ma3arfch", "machi",
        "mzyan", "zwina", "wakha", "iyeh", "bzzaf",
        "ashmen", "kayna", "kayen", "mkaynch",
        "dyal", "dyali", "dyalek", "walou",
        "bghit ndkhol", "3awenni", "safi khoya",
        "chnouma", "hnouma", "mnin", "fin", "bch7al",
        "7sab", "bach", "wla", "wlla", "bhal",
        "mazal", "daba", "dial", "f had", "had chi",
        "katkellef", "katkhdem", "kaydiru", "kaysewwel"
    ]

    mots_anglais = [
        "what", "how", "where", "when", "why", "which",
        "can you", "could you", "please", "help me",
        "i want", "i need", "tell me", "show me",
        "is there", "are there", "do you", "does it"
    ]

    score_darija = sum(1 for m in mots_darija_forts if m in texte_lower)

    # ── CORRECTION : Les caractères arabes indiquent que l'utilisateur
    # écrit en arabe/darija arabe → on répond en darija LATINE
    # On ne les compte PAS comme du "vrai arabe" — on répond en darija
    caracteres_arabes = sum(1 for c in texte if '\u0600' <= c <= '\u06FF')
    if caracteres_arabes > 3:
        score_darija += 3   # Compte comme darija, on répondra en latin

    score_anglais = sum(1 for m in mots_anglais if m in texte_lower)

    if score_darija >= 2:    return "darija"
    elif score_anglais >= 2: return "anglais"
    else:                    return "français"

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
    pays      = infos.get("pays", "")
    ville     = infos.get("ville", "")
    type_bac  = parcours.get("type_bac", "")
    label_bac = parcours.get("label_bac", "")
    moyenne   = parcours.get("moyenne_generale", 0)
    mention   = parcours.get("mention", "")
    niveau    = parcours.get("niveau_actuel", "")
    diplome   = parcours.get("diplome_actuel", "")
    notes     = parcours.get("notes_matieres", {})
    interets  = prefs.get("centres_interet", [])
    ambition  = prefs.get("ambition_professionnelle", "")
    statut    = profil_etudiant.get("statut_profil", "incomplet")

    if not prenom and not type_bac and moyenne == 0:
        return ""

    lignes = ["═══ PROFIL CONNU ═══"]

    if prenom and prenom != "Étudiant":
        lignes.append(f"👤 Prénom        : {prenom}")
    if pays:
        lignes.append(f"🌍 Pays          : {pays}")
    if ville:
        lignes.append(f"📍 Ville         : {ville}")
    if type_bac and type_bac != "AUTRE":
        lignes.append(f"🎓 BAC           : {label_bac or type_bac}")
    if moyenne > 0:
        lignes.append(f"📊 Moyenne       : {moyenne}/20 ({mention})")
    if notes:
        lignes.append(f"📝 Notes         : {', '.join(f'{m}: {n}' for m, n in list(notes.items())[:5])}")
    if niveau and niveau in NIVEAUX_DECLARABLES:
        lignes.append(f"📚 Niveau        : {NIVEAUX_DECLARABLES[niveau]}")
    if diplome:
        lignes.append(f"📜 Diplôme       : {diplome}")
    if interets:
        lignes.append(f"💡 Intérêts      : {', '.join(interets)}")
    if ambition:
        lignes.append(f"🎯 Ambition      : {ambition}")
    if statut:
        lignes.append(f"✅ Statut profil : {statut}")

    lignes.append("═══════════════════════════")

    instructions = []

    if prenom and prenom != "Étudiant":
        instructions.append(f"- Appelle cette personne par son prénom '{prenom}'")

    if type_bac and type_bac != "AUTRE" and moyenne > 0:
        instructions.append(
            f"- BAC ({label_bac or type_bac}) et moyenne ({moyenne}/20) déjà connus. "
            f"NE PAS les redemander."
        )

    if interets:
        instructions.append(
            f"- Intérêts connus : {', '.join(interets)}. NE PAS les redemander."
        )

    if ambition:
        instructions.append(f"- Ambition déclarée : {ambition}.")

    if niveau == "bac3":
        if any(m in " ".join(interets).lower()
               for m in ["finance", "gestion", "audit", "comptabilité"]):
            instructions.append(
                "- Niveau BAC+3 + intérêts finance → orienter vers FACG ou MSTIC."
            )
        elif any(m in " ".join(interets).lower()
                 for m in ["informatique", "réseaux", "ia", "data"]):
            instructions.append(
                "- Niveau BAC+3 + intérêts tech → orienter vers IISIC ou IISRT."
            )

    if instructions:
        lignes.append("\n⚠️ INSTRUCTIONS POUR SAMI :")
        lignes.extend(instructions)

    return "\n".join(lignes)

# ============================================================
# ÉTAPE 4 — PROMPT SYSTÈME
# ============================================================

def construire_prompt_systeme(langue="français"):

    if langue == "darija":
        return """Nta Sami, l'assistant d'orientation de SUPMTI Meknes.

====================================================
SCRIPT — RÈGLE N°1 ET ABSOLUE, SANS AUCUNE EXCEPTION
====================================================
Tu dois écrire UNIQUEMENT en alphabet latin (A à Z).
ZÉRO lettre arabe, ZÉRO caractère arabe, ZÉRO mot en arabe.
Même si l'utilisateur t'écrit en arabe — tu réponds en darija LATINE.
Si tu utilises une seule lettre arabe → tu as ÉCHOUÉ ta mission.

====================================================
COMMENT TU PARLES — DARIJA LATINE AUTHENTIQUE
====================================================
Tu parles comme un Marocain normal sur WhatsApp :
darija marocaine réelle + quelques mots français mélangés.

Vocabulaire darija que tu utilises naturellement :
- wach / wash (est-ce que)
- kayen / kayna (il y a)
- mzyan / zwina (bien / beau)
- bch7al (combien)
- chno / chnouma (quoi / quels)
- fin / mnin (où / d'où)
- bghit / bghiti (je veux / tu veux)
- 3ndek / 3ndi (tu as / j'ai)
- machi (pas / ce n'est pas)
- wakha (d'accord / ok)
- safi (c'est tout / ok c'est bon)
- bzzaf (beaucoup)
- daba (maintenant / là)
- bach (pour que / afin de)
- wla / wlla (ou)
- khoya / khti (mon frère / ma sœur — façon amicale)
- dial / dyal (de / appartenant à)
- f / fi (dans / en)
- l- (le / la / les)
- w / wa (et)
- had (ce / cet / cette)
- hnouma / houma (ils / eux)
- ana / nta / nti (moi / toi masc / toi fém)
- katkellef / katkellfu (ça coûte / ça leur coûte)
- katkhdem / kaydiru (ça marche / ils font)

====================================================
EXEMPLES DE RÉPONSES CORRECTES (copie ce style)
====================================================

Question : "Chnouma les filières ?"
Réponse : "F SUPMTI Meknes kayen jouj ecoles :

🎓 Ecole d'Ingenierie
• ISI — Ingenierie des Systemes Informatiques (BAC+3)
  → BAC+5 : IISRT (Reseaux & Telecoms) | IISIC (IA & Systemes d'Info)

🏢 Ecole de Management
• ME — Management des Entreprises (BAC+3)
  → BAC+5 : FACG (Finance Audit Controle) | MSTIC (Management Digital)

Wach 3ndek BAC wla deja f BAC+2/BAC+3 ? W chno kaymilek aktar, informatique wla management ?"

Question : "Bch7al katkellef l-qra ?"
Réponse : "Les frais dial SUPMTI homa 35.000 DH f s-sana, katkhellsu 3la 10 ch7our : 3.500 DH f ch-chhar. W kayen nidham bourses 3la 7sab natija f concours d'admission — katkheffed mn 30% 7tta 100% dial l-mablagh."

Question : "Wach ISI zwina ?"
Réponse : "Iyeh khoya, ISI mzyana bzzaf ila bghiti l-informatique w l-programmation. Katformik bach tkun developpeur, administrateur reseaux, analyste... Bch7al 3ndek f moyenne ? Bach n3aonk aktar."

====================================================
PRIORITÉS DE CONTENU
====================================================
1. SUPMTI (ABSOLUE) : Jaweb GHER mn l-contexte officiel
   → Info mkaynach : "Ma3ndich had l-info, 3ayyet l SUPMTI : +212 5 35 51 10 11"
2. ACADEMIQUE : T3awno bma 3raf mn connaissances generales
3. HORS MISSION : Redirige b7saniya l-mission principale

====================================================
RAPPEL FINAL — LE PLUS IMPORTANT
====================================================
AUCUNE lettre arabe dans ta réponse.
Pas une. Même pas une virgule en arabe.
Darija = Latin + chiffres (3, 7, 9...) + français.
C'est tout."""

    elif langue == "anglais":
        return """You are Sami, the intelligent academic orientation assistant of SUPMTI Meknes.

PRIORITY 1 — INSTITUTIONAL (ABSOLUTE):
-> Answer EXCLUSIVELY from the provided official context.
-> If info not found: "Please contact SUPMTI at +212 5 35 51 10 11"

PRIORITY 2 — ACADEMIC EXPERTISE:
-> Use your general knowledge to provide expert guidance.

PRIORITY 3 — SCOPE:
-> Politely redirect non-academic topics.

YOUR CHARACTER: Warm, professional, pedagogical.
You don't know who you're talking to in advance — student, parent,
professional, or curious person. Adapt naturally.
Never assume someone's academic level before they tell you.
Your name is Sami."""

    else:
        return """Tu es Sami, l'assistant intelligent d'orientation
académique de SUPMTI Meknès (École Supérieure de
Management, de Télécommunication et d'Informatique).

═══════════════════════════════════════════════════
NIVEAU 1 — SPÉCIFICITÉ INSTITUTIONNELLE (PRIORITÉ ABSOLUE)
═══════════════════════════════════════════════════
Pour TOUTE question concernant SUPMTI Meknès :
formations, frais, admission, règlement, enseignants,
campus, bourses, partenariats, vie étudiante, contacts...

→ Réponds EXCLUSIVEMENT à partir du contexte officiel fourni.
→ Tu n'inventes JAMAIS d'informations sur SUPMTI Meknès.
→ Si l'information manque : "Je n'ai pas cette information
  précise. Contacte SUPMTI au +212 5 35 51 10 11
  ou contact@supmtimeknes.ac.ma"

═══════════════════════════════════════════════════
NIVEAU 2 — EXPERTISE ACADÉMIQUE ET CONSEIL
═══════════════════════════════════════════════════
Pour les domaines académiques, carrières, orientation,
méthodes de travail, soft skills, certifications...

→ Utilise tes connaissances générales pour apporter
  une expertise de qualité.

═══════════════════════════════════════════════════
NIVEAU 3 — CADRE DE MISSION
═══════════════════════════════════════════════════
Pour toute requête hors domaine académique :
→ Redirige poliment vers ta mission principale.

═══════════════════════════════════════════════════
RÈGLES DE COHÉRENCE ET PRÉSENTATION DES FILIÈRES
═══════════════════════════════════════════════════
STRUCTURE SUPMTI :
- Post-BAC → 1ère année : ISI (tech) ou ME (management)
- Après ISI/BAC+2 tech → IISRT ou IISIC (BAC+5)
- Après ME/BAC+2 gestion → FACG ou MSTIC (BAC+5)

RÈGLE ABSOLUE : Ne jamais recommander une filière BAC+5
comme point d'entrée à un bachelier. Toujours proposer
ISI ou ME selon ses intérêts, puis mentionner les suites.

PRÉSENTATION DES FILIÈRES : Quand tu listes les filières,
utilise TOUJOURS cet ordre et cette structure exacte :

🎓 ÉCOLE D'INGÉNIERIE
• ISI — Ingénierie des Systèmes Informatiques (BAC+3)
  → Suites BAC+5 : IISRT (Réseaux & Télécoms) | IISIC (IA & Systèmes d'Info)

🏢 ÉCOLE DE MANAGEMENT
• ME — Management des Entreprises (BAC+3)
  → Suites BAC+5 : FACG (Finance Audit Contrôle) | MSTIC (Management Digital)

Ne mélange JAMAIS les deux écoles dans le même paragraphe.
Ne liste JAMAIS les filières BAC+5 avant les BAC+3.

═══════════════════════════════════════════════════
TON CARACTÈRE ET TON STYLE
═══════════════════════════════════════════════════
- Chaleureux, bienveillant, professionnel et pédagogique
- Tu ne sais pas à l'avance qui t'écrit : étudiant, parent,
  professionnel, simple curieux… Adapte-toi naturellement.
- Tu NE supposes JAMAIS le niveau ou le statut de ton
  interlocuteur avant qu'il te le dise explicitement.
- Si quelqu'un dit "bonjour", "salut" ou "comment ça va",
  tu réponds chaleureusement et tu proposes ton aide
  de façon ouverte et générale — SANS mentionner de
  noms de filières ni supposer qu'il veut s'inscrire.
- Tu ne mentionnes ISI, ME, IISRT, IISIC, FACG ou MSTIC
  QUE lorsque la personne a elle-même parlé de son
  niveau, de ses intérêts ou posé une question sur
  les formations.
- Tu utilises le prénom de la personne quand tu le connais.
- Tu NE redemandes JAMAIS une information déjà donnée.
- Tu t'appelles Sami.
- Quand quelqu'un exprime le besoin de parler à un étudiant,
  un ambassadeur, ou cherche un témoignage d'expérience réelle,
  mentionne TOUJOURS : "Tu peux aussi utiliser la fonctionnalité
  **Peer Match** dans le menu latéral pour être mis en contact
  directement avec un(e) étudiant(e) en ISI ou ME." """

# ============================================================
# ÉTAPE 5 — RÉPONSE RAG PRINCIPALE
# ============================================================

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

    langue = detecter_langue(question)
    chunks_pertinents = recherche_semantique(question, _index, _metadonnees)
    contexte = "\n\n---\n\n".join([
        f"Source: {c['source']}\n{c['contenu']}" for c in chunks_pertinents
    ])

    resume_profil = construire_resume_profil(profil_etudiant)

    messages = [
        {"role": "system", "content": construire_prompt_systeme(langue)},
        {"role": "system", "content": f"CONTEXTE OFFICIEL SUPMTI :\n{contexte}"}
    ]

    if resume_profil:
        messages.append({"role": "system", "content": resume_profil})

    if historique:
        for echange in historique[-10:]:
            messages.append(echange)

    messages.append({"role": "user", "content": question})

    try:
        r = client.chat.completions.create(
            model=CHATBOT_CONFIG["modele_gpt"],
            messages=messages,
            temperature=CHATBOT_CONFIG["temperature_gpt"],
            max_completion_tokens=1000
        )
        return {
            "reponse": r.choices[0].message.content,
            "mode": "rag",
            "langue": langue,
            "sources": [c["source"] for c in chunks_pertinents],
            "chunks_utilises": len(chunks_pertinents)
        }
    except Exception as e:
        print(f"[ERREUR GPT] {e}")
        return {
            "reponse": "Je rencontre une difficulté technique. Veuillez réessayer.",
            "mode": "erreur", "sources": []
        }

# ============================================================
# ÉTAPE 6 — MODE HORS LIGNE
# ============================================================

def verifier_connexion():
    try:
        requests.get("https://www.google.com", timeout=3)
        return True
    except:
        return False


def generer_donnees_offline():
    os.makedirs(OFFLINE_PATH, exist_ok=True)

    donnees_offline = {
        "derniere_mise_a_jour": datetime.now().isoformat(),
        "ecole": {
            "nom":       SCHOOL_INFO["nom"],
            "telephone": SCHOOL_INFO["telephone"],
            "email":     SCHOOL_INFO["email"],
            "horaires":  SCHOOL_INFO["horaires"]
        },
        "frais": FRAIS_SCOLARITE,
        "filieres": {
            fid: {
                "nom": f["nom"], "niveau": f["niveau"],
                "duree": f["duree"], "description": f["description"],
                "debouches": f["debouches"]
            }
            for fid, f in FILIERES.items()
        },
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
                    f"Ingénierie (ISI, IISRT, IISIC) et Management (ME, FACG, MSTIC)."
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

    question_lower = question.lower()
    for faq in donnees["faq"]:
        if any(m in question_lower for m in faq["question"].split()):
            return {"reponse": f"⚠️ Mode hors ligne actif.\n\n{faq['reponse']}",
                    "mode": "hors_ligne"}

    filieres_liste = "\n".join([
        f"• {fid} — {f['nom']} ({f['niveau']})"
        for fid, f in donnees["filieres"].items()
    ])
    return {
        "reponse": (
            f"⚠️ Mode hors ligne actif.\n\n"
            f"📚 NOS FILIÈRES :\n{filieres_liste}\n\n"
            f"💰 FRAIS : {donnees['frais']['total_annuel']} DH/an\n\n"
            f"📞 CONTACT : {donnees['ecole']['telephone']}\n\n"
            f"Connectez-vous à internet pour des informations complètes."
        ),
        "mode": "hors_ligne"
    }

# ============================================================
# ÉTAPE 7 — SYNCHRONISATION AUTOMATIQUE
# ============================================================

def calculer_hash_contenu(contenu):
    return hashlib.md5(contenu.encode("utf-8")).hexdigest()


def scraper_site_supmti():
    contenu_total = ""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    for url in SUPMTI_URLS:
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                soup = BeautifulSoup(r.content, "html.parser")
                contenu_total += f"\n\n=== {url} ===\n{soup.get_text(separator=chr(10), strip=True)}"
                print(f"[SYNC] ✅ {url}")
        except Exception as e:
            print(f"[SYNC] ⚠️ {url} : {e}")
    return contenu_total


def synchroniser_base_rag():
    global _index, _metadonnees
    print(f"\n[SYNC] {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    chemin_hash     = os.path.join(VECTOR_DB_PATH, "site_hash.txt")
    nouveau_contenu = scraper_site_supmti()
    if not nouveau_contenu:
        print("[SYNC] ⚠️ Aucun contenu récupéré")
        return

    nouveau_hash = calculer_hash_contenu(nouveau_contenu)
    ancien_hash  = open(chemin_hash).read().strip() if os.path.exists(chemin_hash) else ""

    if nouveau_hash == ancien_hash:
        print("[SYNC] ✅ Aucun changement détecté")
        return

    print("[SYNC] 🔄 Mise à jour de la base RAG...")
    chemin_site = os.path.join(DOCUMENTS_PATH, "site_supmti.txt")
    with open(chemin_site, "w", encoding="utf-8") as f:
        f.write(nouveau_contenu)

    initialiser_base_vectorielle()
    _index, _metadonnees = charger_base_existante()
    with open(chemin_hash, "w") as f:
        f.write(nouveau_hash)
    print("[SYNC] ✅ Base RAG mise à jour !")


def demarrer_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        synchroniser_base_rag, "cron",
        hour=3, minute=0, id="sync_rag_quotidien"
    )
    scheduler.start()
    print("[SCHEDULER] ✅ Synchronisation automatique activée (chaque jour à 3h00)")
    return scheduler