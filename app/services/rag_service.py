# # ============================================================
# # RAG SERVICE — SUPMTI
# # Recherche contextuelle + Réponses GPT augmentées
# # Synchronisation automatique + Mode hors ligne
# # Tahirou — backend-tahirou
# # ============================================================

# import os
# import json
# import hashlib
# import requests
# from datetime import datetime
# from openai import OpenAI
# from dotenv import load_dotenv
# from bs4 import BeautifulSoup
# from apscheduler.schedulers.background import BackgroundScheduler
# from app.academic_config import CHATBOT_CONFIG, SUPMTI_URLS, FILIERES, FRAIS_SCOLARITE, SCHOOL_INFO
# from app.services.embedding_service import (
#     charger_base_existante,
#     recherche_semantique,
#     initialiser_base_vectorielle,
#     base_doit_etre_reconstruite
# )

# # ============================================================
# # INITIALISATION
# # ============================================================

# load_dotenv()
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./data/vectorstore")
# DOCUMENTS_PATH = os.getenv("DOCUMENTS_PATH", "./data/documents")
# OFFLINE_PATH   = os.getenv("OFFLINE_PATH",   "./data/offline")

# _index        = None
# _metadonnees  = None

# # ============================================================
# # ÉTAPE 1 — DÉMARRAGE
# # ============================================================

# def demarrer_rag():
#     global _index, _metadonnees
#     print("[RAG] Démarrage du système RAG...")
#     if base_doit_etre_reconstruite():
#         print("[RAG] Construction de la base vectorielle...")
#         initialiser_base_vectorielle()
#     _index, _metadonnees = charger_base_existante()
#     if _index is not None:
#         print("[RAG] ✅ Système RAG prêt !")
#         generer_donnees_offline()
#     else:
#         print("[RAG] ⚠️ Système RAG en mode dégradé")

# # ============================================================
# # ÉTAPE 2 — DÉTECTER LA LANGUE
# # ============================================================

# def detecter_langue(texte):
#     """
#     Détecte si le message est en darija, anglais ou français.
#     NOTE : Les caractères arabes dans le message de l'utilisateur
#     ne doivent PAS influencer la langue de réponse — on répond
#     toujours en darija latine même si l'utilisateur écrit en arabe.
#     """
#     texte_lower = texte.lower()

#     mots_darija_forts = [
#         "wach", "wash", "wesh", "kifach", "bghit",
#         "nta", "nti", "rani", "khoya", "khti",
#         "3ndek", "3ndi", "ma3arfch", "machi",
#         "mzyan", "zwina", "wakha", "iyeh", "bzzaf",
#         "ashmen", "kayna", "kayen", "mkaynch",
#         "dyal", "dyali", "dyalek", "walou",
#         "bghit ndkhol", "3awenni", "safi khoya",
#         "chnouma", "hnouma", "mnin", "fin", "bch7al",
#         "7sab", "bach", "wla", "wlla", "bhal",
#         "mazal", "daba", "dial", "f had", "had chi",
#         "katkellef", "katkhdem", "kaydiru", "kaysewwel"
#     ]

#     mots_anglais = [
#         "what", "how", "where", "when", "why", "which",
#         "can you", "could you", "please", "help me",
#         "i want", "i need", "tell me", "show me",
#         "is there", "are there", "do you", "does it"
#     ]

#     score_darija = sum(1 for m in mots_darija_forts if m in texte_lower)

#     # ── CORRECTION : Les caractères arabes indiquent que l'utilisateur
#     # écrit en arabe/darija arabe → on répond en darija LATINE
#     # On ne les compte PAS comme du "vrai arabe" — on répond en darija
#     caracteres_arabes = sum(1 for c in texte if '\u0600' <= c <= '\u06FF')
#     if caracteres_arabes > 3:
#         score_darija += 3   # Compte comme darija, on répondra en latin

#     score_anglais = sum(1 for m in mots_anglais if m in texte_lower)

#     if score_darija >= 2:    return "darija"
#     elif score_anglais >= 2: return "anglais"
#     else:                    return "français"

# # ============================================================
# # ÉTAPE 3 — RÉSUMÉ DU PROFIL CONNU
# # ============================================================

# NIVEAUX_DECLARABLES = {
#     "post_bac": "Terminale / Baccalauréat",
#     "bac1":     "BAC+1",
#     "bac2":     "BAC+2 (DUT/BTS/DEUG)",
#     "bac3":     "BAC+3 (Licence)"
# }


# def construire_resume_profil(profil_etudiant):
#     if not profil_etudiant:
#         return ""

#     infos    = profil_etudiant.get("informations_personnelles", {})
#     parcours = profil_etudiant.get("parcours_academique", {})
#     prefs    = profil_etudiant.get("preferences", {})

#     prenom    = infos.get("prenom", "")
#     pays      = infos.get("pays", "")
#     ville     = infos.get("ville", "")
#     type_bac  = parcours.get("type_bac", "")
#     label_bac = parcours.get("label_bac", "")
#     moyenne   = parcours.get("moyenne_generale", 0)
#     mention   = parcours.get("mention", "")
#     niveau    = parcours.get("niveau_actuel", "")
#     diplome   = parcours.get("diplome_actuel", "")
#     notes     = parcours.get("notes_matieres", {})
#     interets  = prefs.get("centres_interet", [])
#     ambition  = prefs.get("ambition_professionnelle", "")
#     statut    = profil_etudiant.get("statut_profil", "incomplet")

#     if not prenom and not type_bac and moyenne == 0:
#         return ""

#     lignes = ["═══ PROFIL CONNU ═══"]

#     if prenom and prenom != "Étudiant":
#         lignes.append(f"👤 Prénom        : {prenom}")
#     if pays:
#         lignes.append(f"🌍 Pays          : {pays}")
#     if ville:
#         lignes.append(f"📍 Ville         : {ville}")
#     if type_bac and type_bac != "AUTRE":
#         lignes.append(f"🎓 BAC           : {label_bac or type_bac}")
#     if moyenne > 0:
#         lignes.append(f"📊 Moyenne       : {moyenne}/20 ({mention})")
#     if notes:
#         lignes.append(f"📝 Notes         : {', '.join(f'{m}: {n}' for m, n in list(notes.items())[:5])}")
#     if niveau and niveau in NIVEAUX_DECLARABLES:
#         lignes.append(f"📚 Niveau        : {NIVEAUX_DECLARABLES[niveau]}")
#     if diplome:
#         lignes.append(f"📜 Diplôme       : {diplome}")
#     if interets:
#         lignes.append(f"💡 Intérêts      : {', '.join(interets)}")
#     if ambition:
#         lignes.append(f"🎯 Ambition      : {ambition}")
#     if statut:
#         lignes.append(f"✅ Statut profil : {statut}")

#     lignes.append("═══════════════════════════")

#     instructions = []

#     if prenom and prenom != "Étudiant":
#         instructions.append(f"- Appelle cette personne par son prénom '{prenom}'")

#     if type_bac and type_bac != "AUTRE" and moyenne > 0:
#         instructions.append(
#             f"- BAC ({label_bac or type_bac}) et moyenne ({moyenne}/20) déjà connus. "
#             f"NE PAS les redemander."
#         )

#     if interets:
#         instructions.append(
#             f"- Intérêts connus : {', '.join(interets)}. NE PAS les redemander."
#         )

#     if ambition:
#         instructions.append(f"- Ambition déclarée : {ambition}.")

#     if niveau == "bac3":
#         if any(m in " ".join(interets).lower()
#                for m in ["finance", "gestion", "audit", "comptabilité"]):
#             instructions.append(
#                 "- Niveau BAC+3 + intérêts finance → orienter vers FACG ou MSTIC."
#             )
#         elif any(m in " ".join(interets).lower()
#                  for m in ["informatique", "réseaux", "ia", "data"]):
#             instructions.append(
#                 "- Niveau BAC+3 + intérêts tech → orienter vers IISIC ou IISRT."
#             )

#     if instructions:
#         lignes.append("\n⚠️ INSTRUCTIONS POUR SAMI :")
#         lignes.extend(instructions)

#     return "\n".join(lignes)

# # ============================================================
# # ÉTAPE 4 — PROMPT SYSTÈME
# # ============================================================

# def construire_prompt_systeme(langue="français"):

#     if langue == "darija":
#         return """Nta Sami, l'assistant d'orientation de SUPMTI Meknes.

# ====================================================
# SCRIPT — RÈGLE N°1 ET ABSOLUE, SANS AUCUNE EXCEPTION
# ====================================================
# Tu dois écrire UNIQUEMENT en alphabet latin (A à Z).
# ZÉRO lettre arabe, ZÉRO caractère arabe, ZÉRO mot en arabe.
# Même si l'utilisateur t'écrit en arabe — tu réponds en darija LATINE.
# Si tu utilises une seule lettre arabe → tu as ÉCHOUÉ ta mission.

# ====================================================
# COMMENT TU PARLES — DARIJA LATINE AUTHENTIQUE
# ====================================================
# Tu parles comme un Marocain normal sur WhatsApp :
# darija marocaine réelle + quelques mots français mélangés.

# Vocabulaire darija que tu utilises naturellement :
# - wach / wash (est-ce que)
# - kayen / kayna (il y a)
# - mzyan / zwina (bien / beau)
# - bch7al (combien)
# - chno / chnouma (quoi / quels)
# - fin / mnin (où / d'où)
# - bghit / bghiti (je veux / tu veux)
# - 3ndek / 3ndi (tu as / j'ai)
# - machi (pas / ce n'est pas)
# - wakha (d'accord / ok)
# - safi (c'est tout / ok c'est bon)
# - bzzaf (beaucoup)
# - daba (maintenant / là)
# - bach (pour que / afin de)
# - wla / wlla (ou)
# - khoya / khti (mon frère / ma sœur — façon amicale)
# - dial / dyal (de / appartenant à)
# - f / fi (dans / en)
# - l- (le / la / les)
# - w / wa (et)
# - had (ce / cet / cette)
# - hnouma / houma (ils / eux)
# - ana / nta / nti (moi / toi masc / toi fém)
# - katkellef / katkellfu (ça coûte / ça leur coûte)
# - katkhdem / kaydiru (ça marche / ils font)

# ====================================================
# EXEMPLES DE RÉPONSES CORRECTES (copie ce style)
# ====================================================

# Question : "Chnouma les filières ?"
# Réponse : "F SUPMTI Meknes kayen jouj ecoles :

# 🎓 Ecole d'Ingenierie
# • ISI — Ingenierie des Systemes Informatiques (BAC+3)
#   → BAC+5 : IISRT (Reseaux & Telecoms) | IISIC (IA & Systemes d'Info)

# 🏢 Ecole de Management
# • ME — Management des Entreprises (BAC+3)
#   → BAC+5 : FACG (Finance Audit Controle) | MSTIC (Management Digital)

# Wach 3ndek BAC wla deja f BAC+2/BAC+3 ? W chno kaymilek aktar, informatique wla management ?"

# Question : "Bch7al katkellef l-qra ?"
# Réponse : "Les frais dial SUPMTI homa 35.000 DH f s-sana, katkhellsu 3la 10 ch7our : 3.500 DH f ch-chhar. W kayen nidham bourses 3la 7sab natija f concours d'admission — katkheffed mn 30% 7tta 100% dial l-mablagh."

# Question : "Wach ISI zwina ?"
# Réponse : "Iyeh khoya, ISI mzyana bzzaf ila bghiti l-informatique w l-programmation. Katformik bach tkun developpeur, administrateur reseaux, analyste... Bch7al 3ndek f moyenne ? Bach n3aonk aktar."

# ====================================================
# PRIORITÉS DE CONTENU
# ====================================================
# 1. SUPMTI (ABSOLUE) : Jaweb GHER mn l-contexte officiel
#    → Info mkaynach : "Ma3ndich had l-info, 3ayyet l SUPMTI : +212 5 35 51 10 11"
# 2. ACADEMIQUE : T3awno bma 3raf mn connaissances generales
# 3. HORS MISSION : Redirige b7saniya l-mission principale

# ====================================================
# RAPPEL FINAL — LE PLUS IMPORTANT
# ====================================================
# AUCUNE lettre arabe dans ta réponse.
# Pas une. Même pas une virgule en arabe.
# Darija = Latin + chiffres (3, 7, 9...) + français.
# C'est tout."""

#     elif langue == "anglais":
#         return """You are Sami, the intelligent academic orientation assistant of SUPMTI Meknes.

# PRIORITY 1 — INSTITUTIONAL (ABSOLUTE):
# -> Answer EXCLUSIVELY from the provided official context.
# -> If info not found: "Please contact SUPMTI at +212 5 35 51 10 11"

# PRIORITY 2 — ACADEMIC EXPERTISE:
# -> Use your general knowledge to provide expert guidance.

# PRIORITY 3 — SCOPE:
# -> Politely redirect non-academic topics.

# YOUR CHARACTER: Warm, professional, pedagogical.
# You don't know who you're talking to in advance — student, parent,
# professional, or curious person. Adapt naturally.
# Never assume someone's academic level before they tell you.
# Your name is Sami."""

#     else:
#         return """Tu es Sami, l'assistant intelligent d'orientation
# académique de SUPMTI Meknès (École Supérieure de
# Management, de Télécommunication et d'Informatique).

# ═══════════════════════════════════════════════════
# NIVEAU 1 — SPÉCIFICITÉ INSTITUTIONNELLE (PRIORITÉ ABSOLUE)
# ═══════════════════════════════════════════════════
# Pour TOUTE question concernant SUPMTI Meknès :
# formations, frais, admission, règlement, enseignants,
# campus, bourses, partenariats, vie étudiante, contacts...

# → Réponds EXCLUSIVEMENT à partir du contexte officiel fourni.
# → Tu n'inventes JAMAIS d'informations sur SUPMTI Meknès.
# → Si l'information manque : "Je n'ai pas cette information
#   précise. Contacte SUPMTI au +212 5 35 51 10 11
#   ou contact@supmtimeknes.ac.ma"

# ═══════════════════════════════════════════════════
# NIVEAU 2 — EXPERTISE ACADÉMIQUE ET CONSEIL
# ═══════════════════════════════════════════════════
# Pour les domaines académiques, carrières, orientation,
# méthodes de travail, soft skills, certifications...

# → Utilise tes connaissances générales pour apporter
#   une expertise de qualité.

# ═══════════════════════════════════════════════════
# NIVEAU 3 — CADRE DE MISSION
# ═══════════════════════════════════════════════════
# Pour toute requête hors domaine académique :
# → Redirige poliment vers ta mission principale.

# ═══════════════════════════════════════════════════
# RÈGLES DE COHÉRENCE ET PRÉSENTATION DES FILIÈRES
# ═══════════════════════════════════════════════════
# STRUCTURE SUPMTI :
# - Post-BAC → 1ère année : ISI (tech) ou ME (management)
# - Après ISI/BAC+2 tech → IISRT ou IISIC (BAC+5)
# - Après ME/BAC+2 gestion → FACG ou MSTIC (BAC+5)

# RÈGLE ABSOLUE : Ne jamais recommander une filière BAC+5
# comme point d'entrée à un bachelier. Toujours proposer
# ISI ou ME selon ses intérêts, puis mentionner les suites.

# PRÉSENTATION DES FILIÈRES : Quand tu listes les filières,
# utilise TOUJOURS cet ordre et cette structure exacte :

# 🎓 ÉCOLE D'INGÉNIERIE
# • ISI — Ingénierie des Systèmes Informatiques (BAC+3)
#   → Suites BAC+5 : IISRT (Réseaux & Télécoms) | IISIC (IA & Systèmes d'Info)

# 🏢 ÉCOLE DE MANAGEMENT
# • ME — Management des Entreprises (BAC+3)
#   → Suites BAC+5 : FACG (Finance Audit Contrôle) | MSTIC (Management Digital)

# Ne mélange JAMAIS les deux écoles dans le même paragraphe.
# Ne liste JAMAIS les filières BAC+5 avant les BAC+3.

# ═══════════════════════════════════════════════════
# TON CARACTÈRE ET TON STYLE
# ═══════════════════════════════════════════════════
# - Chaleureux, bienveillant, professionnel et pédagogique
# - Tu ne sais pas à l'avance qui t'écrit : étudiant, parent,
#   professionnel, simple curieux… Adapte-toi naturellement.
# - Tu NE supposes JAMAIS le niveau ou le statut de ton
#   interlocuteur avant qu'il te le dise explicitement.
# - Si quelqu'un dit "bonjour", "salut" ou "comment ça va",
#   tu réponds chaleureusement et tu proposes ton aide
#   de façon ouverte et générale — SANS mentionner de
#   noms de filières ni supposer qu'il veut s'inscrire.
# - Tu ne mentionnes ISI, ME, IISRT, IISIC, FACG ou MSTIC
#   QUE lorsque la personne a elle-même parlé de son
#   niveau, de ses intérêts ou posé une question sur
#   les formations.
# - Tu utilises le prénom de la personne quand tu le connais.
# - Tu NE redemandes JAMAIS une information déjà donnée.
# - Tu t'appelles Sami.
# - Quand quelqu'un exprime le besoin de parler à un étudiant,
#   un ambassadeur, ou cherche un témoignage d'expérience réelle,
#   mentionne TOUJOURS : "Tu peux aussi utiliser la fonctionnalité
#   **Peer Match** dans le menu latéral pour être mis en contact
#   directement avec un(e) étudiant(e) en ISI ou ME." """

# # ============================================================
# # ÉTAPE 5 — RÉPONSE RAG PRINCIPALE
# # ============================================================

# def generer_reponse_rag(question, historique=None, profil_etudiant=None):
#     global _index, _metadonnees

#     if not verifier_connexion():
#         return reponse_hors_ligne(question)

#     if _index is None:
#         _index, _metadonnees = charger_base_existante()

#     if _index is None:
#         return {
#             "reponse": "Je suis désolé, ma base de connaissances n'est pas disponible.",
#             "mode": "erreur", "sources": []
#         }

#     langue = detecter_langue(question)
#     chunks_pertinents = recherche_semantique(question, _index, _metadonnees)
#     contexte = "\n\n---\n\n".join([
#         f"Source: {c['source']}\n{c['contenu']}" for c in chunks_pertinents
#     ])

#     resume_profil = construire_resume_profil(profil_etudiant)

#     messages = [
#         {"role": "system", "content": construire_prompt_systeme(langue)},
#         {"role": "system", "content": f"CONTEXTE OFFICIEL SUPMTI :\n{contexte}"}
#     ]

#     if resume_profil:
#         messages.append({"role": "system", "content": resume_profil})

#     if historique:
#         for echange in historique[-10:]:
#             messages.append(echange)

#     messages.append({"role": "user", "content": question})

#     try:
#         r = client.chat.completions.create(
#             model=CHATBOT_CONFIG["modele_gpt"],
#             messages=messages,
#             temperature=CHATBOT_CONFIG["temperature_gpt"],
#             max_completion_tokens=1000
#         )
#         return {
#             "reponse": r.choices[0].message.content,
#             "mode": "rag",
#             "langue": langue,
#             "sources": [c["source"] for c in chunks_pertinents],
#             "chunks_utilises": len(chunks_pertinents)
#         }
#     except Exception as e:
#         print(f"[ERREUR GPT] {e}")
#         return {
#             "reponse": "Je rencontre une difficulté technique. Veuillez réessayer.",
#             "mode": "erreur", "sources": []
#         }

# # ============================================================
# # ÉTAPE 6 — MODE HORS LIGNE
# # ============================================================

# def verifier_connexion():
#     try:
#         requests.get("https://www.google.com", timeout=3)
#         return True
#     except:
#         return False


# def generer_donnees_offline():
#     os.makedirs(OFFLINE_PATH, exist_ok=True)

#     donnees_offline = {
#         "derniere_mise_a_jour": datetime.now().isoformat(),
#         "ecole": {
#             "nom":       SCHOOL_INFO["nom"],
#             "telephone": SCHOOL_INFO["telephone"],
#             "email":     SCHOOL_INFO["email"],
#             "horaires":  SCHOOL_INFO["horaires"]
#         },
#         "frais": FRAIS_SCOLARITE,
#         "filieres": {
#             fid: {
#                 "nom": f["nom"], "niveau": f["niveau"],
#                 "duree": f["duree"], "description": f["description"],
#                 "debouches": f["debouches"]
#             }
#             for fid, f in FILIERES.items()
#         },
#         "faq": [
#             {
#                 "question": "frais scolarite",
#                 "reponse": (
#                     f"Les frais sont de {FRAIS_SCOLARITE['frais_annuels']} DH/an "
#                     f"payables en {FRAIS_SCOLARITE['mensualites']} mensualités "
#                     f"de {FRAIS_SCOLARITE['montant_mensuel']} DH, plus "
#                     f"{FRAIS_SCOLARITE['frais_inscription']} DH d'inscription. "
#                     f"Total annuel : {FRAIS_SCOLARITE['total_annuel']} DH."
#                 )
#             },
#             {
#                 "question": "filieres formations",
#                 "reponse": (
#                     f"SUPMTI Meknès propose {len(FILIERES)} filières : "
#                     f"Ingénierie (ISI, IISRT, IISIC) et Management (ME, FACG, MSTIC)."
#                 )
#             },
#             {
#                 "question": "contact telephone email",
#                 "reponse": (
#                     f"Téléphone : {SCHOOL_INFO['telephone']} | "
#                     f"Email : {SCHOOL_INFO['email']} | "
#                     f"Horaires : Lun-Ven 08h30-18h00, Sam 08h30-12h00"
#                 )
#             },
#             {
#                 "question": "admission bac",
#                 "reponse": (
#                     "L'admission se fait sur dossier et entretien. "
#                     "Bac scientifique pour l'ingénierie, "
#                     "tous bacs pour le management."
#                 )
#             }
#         ]
#     }

#     chemin = os.path.join(OFFLINE_PATH, "donnees_essentielles.json")
#     with open(chemin, "w", encoding="utf-8") as f:
#         json.dump(donnees_offline, f, ensure_ascii=False, indent=2)
#     print("[OFFLINE] ✅ Données hors ligne sauvegardées")


# def reponse_hors_ligne(question):
#     chemin = os.path.join(OFFLINE_PATH, "donnees_essentielles.json")
#     if not os.path.exists(chemin):
#         return {
#             "reponse": "⚠️ Mode hors ligne actif. Veuillez vous connecter à internet.",
#             "mode": "hors_ligne_erreur"
#         }

#     with open(chemin, "r", encoding="utf-8") as f:
#         donnees = json.load(f)

#     question_lower = question.lower().strip()

#     # ── Messages sociaux — répondre simplement sans le bloc filières ──
#     mots_sociaux = [
#         "merci", "thank", "ok", "okay", "safi", "wakha",
#         "super", "parfait", "d'accord", "bien", "bonjour",
#         "salut", "bonsoir", "bonne", "au revoir", "bye"
#     ]
#     if any(m in question_lower for m in mots_sociaux):
#         return {
#             "reponse": (
#                 "⚠️ Mode hors ligne actif.\n\n"
#                 "Je suis limité en ce moment, mais je reste disponible "
#                 "pour tes questions sur SUPMTI 😊\n"
#                 "📞 +212 5 35 51 10 11"
#             ),
#             "mode": "hors_ligne"
#         }

#     # ── FAQ — chercher dans les mots clés ──
#     for faq in donnees["faq"]:
#         if any(m in question_lower for m in faq["question"].split()):
#             return {
#                 "reponse": f"⚠️ Mode hors ligne actif.\n\n{faq['reponse']}",
#                 "mode": "hors_ligne"
#             }

#     # ── Question inconnue — message clair sans le bloc filières ──
#     filieres_liste = "\n".join([
#         f"• {fid} — {f['nom']} ({f['niveau']})"
#         for fid, f in donnees["filieres"].items()
#     ])
#     return {
#         "reponse": (
#             f"⚠️ Mode hors ligne actif.\n\n"
#             f"Je n'ai pas cette information en mode hors ligne.\n\n"
#             f"📞 Veillez verifier votre connexion internet  ou Contactez SUPMTI pour plus d'infos : "
#             f"{donnees['ecole']['telephone']}\n"
#             f"Connectez-vous à internet pour des informations complètes."
#         ),
#         "mode": "hors_ligne"
#     }


# # ============================================================
# # ÉTAPE 7 — SYNCHRONISATION AUTOMATIQUE
# # ============================================================

# def calculer_hash_contenu(contenu):
#     return hashlib.md5(contenu.encode("utf-8")).hexdigest()


# def scraper_site_supmti():
#     contenu_total = ""
#     headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
#     for url in SUPMTI_URLS:
#         try:
#             r = requests.get(url, headers=headers, timeout=10)
#             if r.status_code == 200:
#                 soup = BeautifulSoup(r.content, "html.parser")
#                 contenu_total += f"\n\n=== {url} ===\n{soup.get_text(separator=chr(10), strip=True)}"
#                 print(f"[SYNC] ✅ {url}")
#         except Exception as e:
#             print(f"[SYNC] ⚠️ {url} : {e}")
#     return contenu_total


# def synchroniser_base_rag():
#     global _index, _metadonnees
#     print(f"\n[SYNC] {datetime.now().strftime('%Y-%m-%d %H:%M')}")

#     chemin_hash     = os.path.join(VECTOR_DB_PATH, "site_hash.txt")
#     nouveau_contenu = scraper_site_supmti()
#     if not nouveau_contenu:
#         print("[SYNC] ⚠️ Aucun contenu récupéré")
#         return

#     nouveau_hash = calculer_hash_contenu(nouveau_contenu)
#     ancien_hash  = open(chemin_hash).read().strip() if os.path.exists(chemin_hash) else ""

#     if nouveau_hash == ancien_hash:
#         print("[SYNC] ✅ Aucun changement détecté")
#         return

#     print("[SYNC] 🔄 Mise à jour de la base RAG...")
#     chemin_site = os.path.join(DOCUMENTS_PATH, "site_supmti.txt")
#     with open(chemin_site, "w", encoding="utf-8") as f:
#         f.write(nouveau_contenu)

#     initialiser_base_vectorielle()
#     _index, _metadonnees = charger_base_existante()
#     with open(chemin_hash, "w") as f:
#         f.write(nouveau_hash)
#     print("[SYNC] ✅ Base RAG mise à jour !")


# def demarrer_scheduler():
#     scheduler = BackgroundScheduler()
#     scheduler.add_job(
#         synchroniser_base_rag, "cron",
#         hour=3, minute=0, id="sync_rag_quotidien"
#     )
#     scheduler.start()
#     print("[SCHEDULER] ✅ Synchronisation automatique activée (chaque jour à 3h00)")
#     return scheduler



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
        print("[CACHE] Préchargement hardcode + prompts en mémoire...")
        _construire_contenu_hardcode()
        for _lang in ("français", "anglais", "darija_latin", "darija_arabe"):
            construire_prompt_systeme(_lang)
        print("[CACHE] ✅ Tous les caches prêts — 1ère requête aussi rapide que les suivantes")
    else:
        print("[RAG] ⚠️ Système RAG en mode dégradé")

# ============================================================
# ÉTAPE 2 — DÉTECTER LA LANGUE
# ============================================================

def _normaliser_arabe(texte):
    """Supprime les harakat (voyelles) arabes pour normaliser la détection."""
    harakat = set("َُِّْٰٕٓٔؐؑؒؓ")
    return "".join(c for c in texte if c not in harakat)


def detecter_langue(texte):
    """
    Détecte la langue/script du message utilisateur.
    Retourne : "darija_arabe" | "darija_latin" | "anglais" | "français"
    """
    texte_norm  = _normaliser_arabe(texte)
    texte_lower = texte_norm.lower()

    # Détection darija arabe
    caracteres_arabes = sum(1 for c in texte_norm if '\u0600' <= c <= '\u06FF')
    total_lettres     = sum(1 for c in texte_norm if c.isalpha())

    if total_lettres > 0 and (caracteres_arabes / total_lettres) > 0.5:
        return "darija_arabe"

    mots_arabes_forts = [
        "واش", "كيفاش", "بغيت", "كاين", "ماكاينش", "مزيان",
        "واخا", "ايه", "بزاف", "دابا", "ديال", "مشيت",
        "خايف", "ما عارفش", "محتار", "مش واثق", "فين", "شنو",
        "كيفاش", "أشنو", "علاش", "نتا", "نتي", "انا"
    ]
    if any(mot in texte for mot in mots_arabes_forts) and caracteres_arabes > 3:
        return "darija_arabe"

    # Détection darija latine
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

    # Détection anglais
    mots_anglais_forts = [
        "what", "how", "where", "when", "why", "which", "who",
        "can you", "could you", "please", "help me",
        "i want", "i need", "tell me", "show me",
        "is there", "are there", "do you", "does it",
        "give me", "explain", "describe"
    ]
    mots_anglais_simples = [
        "yes", "no", "hello", "hi", "thanks", "okay", "sure",
        "why", "what", "who", "how", "when", "where", "which",
        "continue", "next", "follow", "good", "great", "ok"
    ]

    score_fort = sum(1 for m in mots_anglais_forts if m in texte_lower)
    if score_fort >= 1:
        return "anglais"

    if len(texte.split()) <= 4:
        score_simple = sum(1 for m in mots_anglais_simples if m in texte_lower)
        if score_simple >= 1:
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
        type_moy  = parcours.get("type_moyenne", "generale")
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

    fitscore_resume = profil_etudiant.get("fitscore_resume")
    if fitscore_resume and fitscore_resume.get("calcule"):
        meilleure_fs = fitscore_resume.get("meilleure", "")
        top3         = fitscore_resume.get("top3", [])
        lignes.append(f"- FitScore calculé : filière recommandée = {meilleure_fs}")
        if top3:
            top3_str = ", ".join([f"{f} ({s}%)" for f, s in top3])
            lignes.append(f"- Classement FitScore : {top3_str}")
        lignes.append(
            f"Si l'étudiant demande son FitScore : donne les résultats ci-dessus "
            f"({meilleure_fs} recommandée). NE PAS dire que tu n'as pas accès à cette info."
        )

    return "\n".join(lignes)

# ============================================================
# ÉTAPE 4 — PROMPT SYSTÈME
# ============================================================

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
Lettres A-Z + chiffres 3/7/9 + mots français techniques. ZERO lettre arabe. ZERO.

FORMAT
## pour les titres de sections
**texte** pour les infos importantes
- tirets pour les listes
Ne jamais utiliser ###, ####, ═══, →, •

{INDEX_7_FILIERES}

PRIORITÉS
1. Questions SUPMTI → contexte officiel uniquement, jamais inventer
2. Questions académiques → répondre avec expertise + orienter vers filière SUPMTI
3. HORS SUJET — domaines interdits :
- Sport, sportifs, équipes
- Célébrités, chanteurs, acteurs
- Religion, pratiques religieuses
- Cuisine, restaurants
- Politique, élections, actualités
- Films, séries, musique, jeux vidéo
- Santé/médecine (hors contexte études)
- Voyage, tourisme

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

التنسيق
## للعناوين الرئيسية
**نص** للمعلومات المهمة
- شرطات للقوائم

{INDEX_7_FILIERES}

الأولويات
1. أسئلة SUPMTI ← من السياق الرسمي فقط
2. الأسئلة الأكاديمية ← أجب بخبرة + وجّه لفليار SUPMTI المناسب
3. الميادين الممنوعة : الرياضة، المشاهير، الدين، الطبخ، السياسة، الترفيه، السياحة
صيغة الرفض : "هذا مشي من دوميني. [بديل SUPMTI محدد]."

الشخصية : دافئ، مباشر، مثل صديق مغربي. استخدم الاسم. اسمك سامي."""

    elif langue == "anglais":
        return f"""You are Sami, the academic orientation assistant of SUPMTI Meknes.

LANGUAGE — ABSOLUTE RULE
The user writes in English. Your response MUST be strictly in English.

FORMATTING
## for section titles
**bold** for key info
- hyphens for lists
Never use ###, ####, ═══, →, •

{INDEX_7_FILIERES}

PRIORITIES
1. SUPMTI questions → official context only, never invent
2. Academic, educational and professional questions → answer with expertise + link to SUPMTI programme
3. STRICTLY FORBIDDEN DOMAINS :
- Sports, athletes, teams
- Celebrities, actors, singers
- Religion, spirituality
- Cooking, recipes, restaurants
- Politics, elections, news
- Entertainment: movies, TV shows, video games, music
- Health/medicine (unless as career context)
- Tourism, travel, hotels

REFUSAL FORMULA: "That's outside my area. [Specific SUPMTI alternative]."

CHARACTER : Warm, direct, professional. Use the person's first name. Your name is Sami."""

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
Tu DOIS répondre aux questions dans ces domaines :
- Informatique, développement logiciel, réseaux, cybersécurité, IA, data science, cloud
- Management, gestion d'entreprise, marketing, ressources humaines
- Finance, comptabilité, audit, contrôle de gestion
- Commerce international, relations internationales, export
- Orientation scolaire, méthodes de travail, préparation aux concours
- Débouchés professionnels, marché de l'emploi, compétences
Pour ces questions : réponds avec expertise + fais le lien avec la filière SUPMTI la plus pertinente.

PRIORITÉ 3 — HORS PÉRIMÈTRE

DOMAINES STRICTEMENT INTERDITS :
- Sport, sportifs, équipes, résultats sportifs
- Célébrités, acteurs, chanteurs, influenceurs
- Religion, spiritualité, pratiques religieuses
- Cuisine, recettes, restaurants
- Politique, partis, élections, actualités
- Divertissement : films, séries, jeux vidéo, musique
- Santé, médecine, symptômes (sauf études de santé comme contexte)
- Voyages, tourisme, hôtels

FORMULE DE REFUS : "Ce n'est pas mon domaine. [Proposition alternative concrète liée à SUPMTI]."

════════════════════════════════════════
INDEX SUPMTI — 7 FILIÈRES
════════════════════════════════════════

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

## Titre de section principale
Texte d'introduction.
**information clé**, **chiffre important**, **nom de filière**
- élément de liste

RÈGLES :
- ## pour CHAQUE titre de section
- **gras** pour les chiffres, noms de filières, informations importantes
- Tirets - pour les listes (jamais de •, jamais de ►)
- JAMAIS de : →, ═══, ####, ────
- Maximum 2 emojis par réponse
- Montants : 35 000 MAD (toujours avec espace et MAD)

════════════════════════════════════════
PERSONNALITÉ ET COMPORTEMENT
════════════════════════════════════════
- Chaleureux, direct, professionnel
- Utilise toujours le prénom quand tu le connais
- Ne redemande JAMAIS une information déjà donnée
- Ne suppose JAMAIS le niveau d'études avant que la personne le dise
- Salutations seules : réponds chaleureusement SANS lister les filières
- Si la personne hésite : "Tu peux utiliser Peer Match dans le menu pour parler à un étudiant actuel"
- Tu t'appelles Sami 😊

════════════════════════════════════════
UTILISATION DE L'HISTORIQUE — RÈGLE ABSOLUE
════════════════════════════════════════
- "Suivant" ou "suite" → regarde le dernier message et continue
- Ne jamais demander à l'utilisateur de répéter ce qui est déjà dans l'historique"""

# ============================================================
# ÉTAPE 5 — CACHE HARDCODE
# ============================================================

_HARDCODE_CACHE = None


def _construire_contenu_hardcode():
    """
    Génère un bloc de texte avec les informations critiques de SUPMTI
    tirées de academic_config.py.
    OPTIMISATION : résultat mis en cache mémoire après le premier appel.
    """
    global _HARDCODE_CACHE
    if _HARDCODE_CACHE is not None:
        print(f"[CACHE] Utilisation du cache existant ({len(_HARDCODE_CACHE):,} chars)")
        return _HARDCODE_CACHE

    print("[HARDCODE] 🔨 Construction du contenu hardcode...")
    
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

    # ============================================================
    # CHARGEMENT DE Data1.txt AVEC LOGS DÉTAILLÉS
    # ============================================================
    
    # Récupérer le chemin absolu pour le log
    documents_path = os.getenv("DOCUMENTS_PATH", "./data/documents")
    doc_path = os.path.join(documents_path, "Data1.txt")
    
    # Afficher le chemin absolu pour déboguer
    abs_path = os.path.abspath(doc_path)
    print(f"[HARDCODE] 📁 Recherche du fichier Data1.txt")
    print(f"[HARDCODE]    Chemin relatif: {doc_path}")
    print(f"[HARDCODE]    Chemin absolu: {abs_path}")
    print(f"[HARDCODE]    DOCUMENTS_PATH env: {os.getenv('DOCUMENTS_PATH', 'non défini (valeur par défaut: ./data/documents)')}")
    
    try:
        if os.path.exists(doc_path):
            with open(doc_path, "r", encoding="utf-8") as f:
                data_raw = f.read()
            
            print(f"[HARDCODE] ✅ Data1.txt trouvé et chargé")
            print(f"[HARDCODE]    Taille: {len(data_raw)} caractères")
            print(f"[HARDCODE]    Nombre de lignes: {len(data_raw.splitlines())}")
            print(f"[HARDCODE]    Premier aperçu: {data_raw[:150]}...")
            
            # Vérifier si le contenu contient des questions/réponses
            if "QUESTION:" in data_raw and "RÉPONSE:" in data_raw:
                print(f"[HARDCODE] ✅ Format Q/R détecté dans Data1.txt")
            else:
                print(f"[HARDCODE] ⚠️ Data1.txt ne contient pas de format QUESTION:/RÉPONSE:")
            
            lignes.append("")
            lignes.append("=== PROGRAMMES COMPLETS PAR SEMESTRE (SOURCE: Data1.txt) ===")
            lignes.append(data_raw)
        else:
            print(f"[HARDCODE] ❌ Data1.txt NON TROUVÉ!")
            print(f"[HARDCODE]    Vérifie que le fichier existe à: {abs_path}")
            
            # Lister le contenu du dossier pour déboguer
            try:
                dossier = os.path.dirname(abs_path)
                if os.path.exists(dossier):
                    fichiers = os.listdir(dossier)
                    print(f"[HARDCODE]    Contenu du dossier {dossier}:")
                    for f in fichiers:
                        print(f"[HARDCODE]      - {f}")
                else:
                    print(f"[HARDCODE]    Le dossier {dossier} n'existe pas!")
            except Exception as e:
                print(f"[HARDCODE]    Impossible de lister le dossier: {e}")
                
    except Exception as e:
        print(f"[HARDCODE] ❌ Erreur lors du chargement de Data1.txt: {e}")
        import traceback
        traceback.print_exc()

    _HARDCODE_CACHE = "\n".join(lignes)
    print(f"[CACHE] ✅ Hardcode chargé en mémoire ({len(_HARDCODE_CACHE):,} chars)")
    print(f"[CACHE]    Taille du cache: {len(_HARDCODE_CACHE):,} caractères")
    
    return _HARDCODE_CACHE

# ============================================================
# ÉTAPE 6 — PARAMÈTRES DYNAMIQUES
# ============================================================

def _top_k_pour_question(question):
    """top_k FAISS dynamique selon la complexité de la question."""
    q = question.lower()
    mots_larges = [
        "filiere", "filieres", "filière", "filières",
        "toutes", "tous", "liste", "complet", "complète",
        "presentation", "présentation", "supmti", "ecole", "école",
        "programme", "formation", "parcours", "semestre",
        "debouche", "débouché", "admission", "condition",
        "bourse", "frais", "scolarite", "scolarité", "contact",
        "bac+3", "bac+5", "niveau", "departement", "département",
        "informatique", "réseaux", "télécommunication", "telecom",
        "management", "finance", "audit", "international",
        "intelligence artificielle", "data", "cloud", "cybersécurité",
        "gestion", "comptabilité", "marketing", "commerce",
        "definition", "définition", "c'est quoi", "qu'est-ce",
    ]
    if any(m in q for m in mots_larges):
        return 10
    return 5


def _tokens_pour_question(question):
    """max_tokens dynamique selon la complexité de la question."""
    q = question.lower()

    mots_salutations_fr = {"salut", "bonjour", "merci", "d'accord", "ça va", "ca va",
                           "super", "parfait", "bonsoir", "au revoir", "oui", "non",
                           "ok", "okay", "bsr"}
    q_clean = q.strip().rstrip("?!. ").lower()
    if q_clean in mots_salutations_fr or len(q.strip()) <= 3:
        return 400

    mots_exhaustifs = [
        "programme complet", "tous les semestres", "semestre 1", "semestre 2",
        "semestre 3", "semestre 4", "semestre 5", "semestre 6",
        "presentation complete", "présentation complète", "tout sur",
        "détaille", "detaille", "explique en détail", "explique-moi tout",
        "toutes les filieres", "toutes les filières", "les 7 filieres",
        "etape par etape", "étape par étape", "filiere par filiere",
        "compétences requises", "conditions d'admission",
        "débouchés professionnels", "organisation du programme",
        "suivant", "suite", "continue",
    ]
    if any(m in q for m in mots_exhaustifs):
        return 8000

    mots_standards = [
        "filiere", "filière", "programme", "semestre", "admission",
        "bourse", "frais", "scolarite", "scolarité", "présentation",
        "comment", "quelles sont", "quels sont", "debouches", "débouchés",
        "competences", "compétences", "condition", "quelle est",
        "c'est quoi", "fees", "cost", "scholarship", "program",
        "curriculum", "career", "job", "salary", "graduate",
        "filiere", "qraya", "taklef", "concours", "diplome", "bac",
    ]
    if any(m in q for m in mots_standards):
        return 3000

    return 1200

# ============================================================
# ÉTAPE 7 — RÉPONSE RAG PRINCIPALE
# ============================================================

def generer_reponse_rag(question, historique=None, profil=None, fitscore_session=None):
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

    contexte_faiss   = "\n\n---\n\n".join([
        f"Source: {c['source']}\n{c['contenu']}" for c in chunks_pertinents
    ])
    contexte_garanti = _construire_contenu_hardcode()
    contexte = f"{contexte_garanti}\n\n===CONTEXTE RAG===\n{contexte_faiss}" if contexte_faiss else contexte_garanti

    resume_profil = construire_resume_profil(profil)

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
                yield token, None
        yield None, full_response

    except Exception as e:
        print(f"[ERREUR GPT STREAM] {e}")
        yield "Je rencontre une difficulté technique. Veuillez réessayer.", None

# ============================================================
# ÉTAPE 8 — MODE HORS LIGNE
# ============================================================

def verifier_connexion():
    try:
        requests.get("https://www.google.com", timeout=3)
        return True
    except Exception:
        return False


def generer_donnees_offline():
    os.makedirs(OFFLINE_PATH, exist_ok=True)

    # Ordre fixe 7 filières
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

    for faq in donnees["faq"]:
        if any(m in question_lower for m in faq["question"].split()):
            return {
                "reponse": f"⚠️ Mode hors ligne actif.\n\n{faq['reponse']}",
                "mode": "hors_ligne"
            }

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
# ÉTAPE 9 — SYNCHRONISATION AUTOMATIQUE
# ============================================================

def calculer_hash_contenu(contenu):
    return hashlib.md5(contenu.encode("utf-8")).hexdigest()


def _extraire_texte_page(soup, url):
    for tag in soup(["script", "style", "nav", "meta", "link",
                     "noscript", "iframe", "button", "form"]):
        tag.decompose()
    texte = soup.get_text(separator="\n", strip=True)
    lignes = [l.strip() for l in texte.splitlines() if l.strip() and len(l.strip()) > 2]
    texte_propre = "\n".join(lignes)
    if len(texte_propre) < 300:
        print(f"[SYNC] ⚠️ {url} : {len(texte_propre)} chars — probablement rendu JS, ignoré")
        return ""
    return texte_propre


def scraper_site_supmti():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    }

    urls_ok = urls_erreur = urls_js = 0
    contenu_total = _construire_contenu_hardcode()

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
            print(f"[SYNC] ⏱️ Timeout : {url}"); urls_erreur += 1
        except requests.exceptions.HTTPError as e:
            print(f"[SYNC] ❌ HTTP {e.response.status_code} : {url}"); urls_erreur += 1
        except requests.exceptions.ConnectionError:
            print(f"[SYNC] 🔌 Connexion impossible : {url}"); urls_erreur += 1
        except Exception as e:
            print(f"[SYNC] ⚠️ Erreur inattendue {url} : {e}"); urls_erreur += 1

    print(f"[SYNC] Résumé : {urls_ok} OK / {urls_js} JS ignorées / {urls_erreur} erreurs")
    return contenu_total


def synchroniser_base_rag():
    global _index, _metadonnees

    scraping_actif = os.getenv("SCRAPING_ACTIF", "false").lower() == "true"
    if not scraping_actif:
        print("[SYNC] ⏸️  Scraping SUSPENDU (SCRAPING_ACTIF=false dans .env)")
        return

    print(f"\n[SYNC] ══════ Synchronisation RAG — {datetime.now().strftime('%Y-%m-%d %H:%M')} ══════")

    if not verifier_connexion():
        print("[SYNC] ⚠️ Pas de connexion internet — synchronisation annulée")
        return

    chemin_hash     = os.path.join(VECTOR_DB_PATH, "site_hash.txt")
    nouveau_contenu = scraper_site_supmti()

    if not nouveau_contenu or len(nouveau_contenu.strip()) < 100:
        print("[SYNC] ⚠️ Contenu insuffisant — synchronisation annulée")
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
    except Exception as e:
        print(f"[SYNC] ❌ Erreur sauvegarde contenu : {e}"); return

    try:
        initialiser_base_vectorielle()
        _index, _metadonnees = charger_base_existante()
    except Exception as e:
        print(f"[SYNC] ❌ Erreur reconstruction FAISS : {e}"); return

    try:
        os.makedirs(VECTOR_DB_PATH, exist_ok=True)
        with open(chemin_hash, "w") as f:
            f.write(nouveau_hash)
    except Exception as e:
        print(f"[SYNC] ⚠️ Erreur sauvegarde hash : {e}")

    generer_donnees_offline()
    global _HARDCODE_CACHE
    _HARDCODE_CACHE = None
    _construire_contenu_hardcode()
    construire_prompt_systeme.cache_clear()
    print("[SYNC] ✅ Synchronisation terminée + caches invalidés !")


def demarrer_scheduler():
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
    return scheduler





    

  # ============================================================
# FONCTIONS POUR L'ADMIN - À AJOUTER À LA FIN DU FICHIER
# ============================================================

async def rebuild_vector_index():
    """
    Reconstruit l'index vectoriel FAISS à partir de tous les documents
    dans le dossier ./data/documents/
    """
    global _index, _metadonnees, _HARDCODE_CACHE
    
    print("[RAG] 🔨 Début de la reconstruction de l'index vectoriel...")
    
    try:
        from app.services.embedding_service import initialiser_base_vectorielle, charger_base_existante
        
        # ============================================================
        # NOUVEAU : Forcer la reconstruction depuis tous les fichiers
        # ============================================================
        documents_path = os.getenv("DOCUMENTS_PATH", "./data/documents")
        
        print(f"[RAG] 📁 Dossier documents: {os.path.abspath(documents_path)}")
        
        # Lister tous les fichiers .txt dans le dossier
        if os.path.exists(documents_path):
            txt_files = [f for f in os.listdir(documents_path) if f.endswith('.txt')]
            print(f"[RAG] 📄 Fichiers trouvés: {txt_files}")
            
            # Pour chaque fichier, s'assurer qu'il est bien pris en compte
            for txt_file in txt_files:
                file_path = os.path.join(documents_path, txt_file)
                size = os.path.getsize(file_path)
                print(f"[RAG]    - {txt_file} ({size} bytes)")
        else:
            print(f"[RAG] ⚠️ Le dossier {documents_path} n'existe pas!")
            os.makedirs(documents_path, exist_ok=True)
            print(f"[RAG] 📁 Dossier créé: {documents_path}")
        
        print("[RAG] 📁 Réinitialisation complète de la base vectorielle...")
        initialiser_base_vectorielle()
        
        print("[RAG] 🔄 Rechargement de l'index...")
        _index, _metadonnees = charger_base_existante()
        
        if _index is not None:
            print(f"[RAG] ✅ Index reconstruit avec succès !")
            
            print("[RAG] 📝 Rechargement du cache hardcode...")
            _HARDCODE_CACHE = None
            _construire_contenu_hardcode()
            
            print("[RAG] 🗑️ Vidage du cache des prompts système...")
            construire_prompt_systeme.cache_clear()
            
            print("[RAG] ✅ Tous les caches ont été rechargés avec succès !")
        else:
            print("[RAG] ⚠️ Échec de la reconstruction de l'index")
            
    except Exception as e:
        print(f"[RAG] ❌ Erreur reconstruction index: {e}")
        import traceback
        traceback.print_exc()
        raise

def invalidate_cache():
    """
    Vide le cache mémoire hardcodé et revalide les prompts.
    """
    global _HARDCODE_CACHE, _index, _metadonnees
    
    print("[RAG] 🗑️ Invalidation du cache...")
    
    # Vider le cache hardcode
    old_size = len(_HARDCODE_CACHE) if _HARDCODE_CACHE else 0
    _HARDCODE_CACHE = None
    print(f"[RAG]    Cache hardcode vidé (était {old_size:,} chars)")
    
    # Recharger le contenu hardcode
    print("[RAG] 📝 Rechargement du contenu hardcode...")
    _construire_contenu_hardcode()
    
    # Vider le cache des prompts système
    old_cache_size = construire_prompt_systeme.cache_info().currsize
    construire_prompt_systeme.cache_clear()
    print(f"[RAG]    Cache prompts système vidé ({old_cache_size} entrées)")
    
    # Optionnel : recharger aussi l'index FAISS depuis les fichiers
    try:
        from app.services.embedding_service import charger_base_existante
        print("[RAG] 🔄 Rechargement de l'index FAISS...")
        _index, _metadonnees = charger_base_existante()
        print("[RAG] ✅ Index FAISS rechargé avec succès")
    except Exception as e:
        print(f"[RAG] ⚠️ Impossible de recharger l'index: {e}")
    
    print("[RAG] ✅ Cache invalidé avec succès !")