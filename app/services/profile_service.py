# ============================================================
# PROFILE SERVICE — SUPMTI
# Analyse de Profil Étudiant (4.4)
# Test Psychométrique Adaptatif (4.5)
# Peer Match AI (4.13)
# Tahirou — backend-tahirou
# ============================================================

import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from app.academic_config import (
    TYPES_BAC,
    COMPATIBILITE_BAC_FILIERE,
    FILIERES,
    CONDITIONS_ADMISSION,
    INTERETS_FILIERE,
    PROFIL_PSYCHO_FILIERE,
    SIGNAUX_HESITATION,
    CHATBOT_CONFIG
)

# ============================================================
# INITIALISATION
# ============================================================

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ============================================================
# PARTIE 1 — ANALYSE DE PROFIL ÉTUDIANT (4.4)
# ============================================================

MAPPING_INTERETS = {
    "finance": ["finance", "gestion", "comptabilité"],
    "audit": ["audit", "finance", "contrôle de gestion"],
    "comptabilité": ["comptabilité", "finance", "gestion"],
    "gestion": ["gestion", "management", "finance"],
    "management": ["management", "gestion", "entreprise"],
    "banque": ["finance", "banque", "économie"],
    "économie": ["économie", "finance", "gestion"],
    "marketing": ["marketing", "commerce", "management"],
    "commerce": ["commerce", "marketing", "management"],
    "entreprise": ["management", "gestion", "entreprise"],
    "informatique": ["informatique", "programmation", "développement"],
    "programmation": ["programmation", "informatique", "développement"],
    "développement": ["développement", "programmation", "informatique"],
    "dev": ["développement", "programmation", "informatique"],
    "web": ["développement web", "programmation", "informatique"],
    "mobile": ["développement mobile", "programmation", "informatique"],
    "réseau": ["réseaux", "infrastructure", "télécommunications"],
    "reseaux": ["réseaux", "infrastructure", "télécommunications"],
    "télécommunications": ["télécommunications", "réseaux", "infrastructure"],
    "telecom": ["télécommunications", "réseaux", "infrastructure"],
    "cybersécurité": ["cybersécurité", "réseaux", "sécurité informatique"],
    "securite": ["cybersécurité", "réseaux", "sécurité informatique"],
    "intelligence artificielle": ["intelligence artificielle", "IA", "data science"],
    "ia": ["intelligence artificielle", "IA", "machine learning"],
    "data": ["data science", "intelligence artificielle", "machine learning"],
    "data science": ["data science", "intelligence artificielle", "machine learning"],
    "machine learning": ["machine learning", "intelligence artificielle", "data science"],
}


def detecter_interets_depuis_message(texte):
    texte_lower = texte.lower()
    interets_detectes = []
    for mot_cle, interets in MAPPING_INTERETS.items():
        if mot_cle in texte_lower:
            for interet in interets:
                if interet not in interets_detectes:
                    interets_detectes.append(interet)
    return interets_detectes


def construire_profil_etudiant(donnees_brutes):
    prenom   = donnees_brutes.get("prenom", "Étudiant")
    pays     = donnees_brutes.get("pays", "Maroc")
    ville    = donnees_brutes.get("ville", "")
    type_bac = donnees_brutes.get("type_bac", "AUTRE").upper()
    moyenne  = float(donnees_brutes.get("moyenne_generale", 0))
    notes    = donnees_brutes.get("notes_matieres", {})

    # ── FIX BUG 2 ──────────────────────────────────────────
    # Valeur par défaut vide → on ne suppose JAMAIS "post_bac"
    # avant que l'interlocuteur l'ait déclaré explicitement.
    niveau   = donnees_brutes.get("niveau_actuel", "")
    # ────────────────────────────────────────────────────────

    diplome  = donnees_brutes.get("diplome_actuel", None)
    interets = donnees_brutes.get("centres_interet", [])
    ambition = donnees_brutes.get("ambition_professionnelle", "")
    preference = donnees_brutes.get("preference_apprentissage", "mixte")
    langue   = donnees_brutes.get("langue_preferee", "français")

    infos_bac     = TYPES_BAC.get(type_bac, TYPES_BAC["AUTRE"])
    mention       = calculer_mention(moyenne)
    compatibilites = COMPATIBILITE_BAC_FILIERE.get(type_bac, {})
    interets_scores = calculer_scores_interets(interets, ambition)

    profil = {
        "informations_personnelles": {
            "prenom": prenom,
            "pays": pays,
            "ville": ville,
            "langue_preferee": langue
        },
        "parcours_academique": {
            "type_bac": type_bac,
            "label_bac": infos_bac.get("label", type_bac),
            "pays_bac": infos_bac.get("pays", pays),
            "moyenne_generale": moyenne,
            "mention": mention,
            "notes_matieres": notes,
            "niveau_actuel": niveau,   # ← "" par défaut
            "diplome_actuel": diplome
        },
        "forces_academiques": {
            "force_maths": infos_bac.get("force_maths", 3),
            "force_physique": infos_bac.get("force_physique", 3),
            "force_info": infos_bac.get("force_info", 2),
            "force_economie": infos_bac.get("force_economie", 2),
            "force_gestion": infos_bac.get("force_gestion", 2),
            "force_langues": infos_bac.get("force_langues", 3)
        },
        "preferences": {
            "centres_interet": interets,
            "ambition_professionnelle": ambition,
            "preference_apprentissage": preference,
            "scores_interets_filieres": interets_scores
        },
        "compatibilite_filieres": compatibilites,
        "profil_psychometrique": None,
        "statut_profil": "incomplet" if not interets else "complet"
    }

    print(f"[PROFIL] ✅ Profil construit pour {prenom} — BAC {type_bac} — Moyenne {moyenne}")
    return profil


def calculer_mention(moyenne):
    if moyenne >= 16: return "très_bien"
    elif moyenne >= 14: return "bien"
    elif moyenne >= 12: return "assez_bien"
    elif moyenne >= 10: return "passable"
    else: return "insuffisant"


def calculer_scores_interets(interets, ambition):
    scores = {}
    texte_complet = " ".join(interets).lower() + " " + ambition.lower()
    for filiere_id, mots_cles in INTERETS_FILIERE.items():
        scores[filiere_id] = sum(
            1 for mot in mots_cles if mot.lower() in texte_complet
        )
    return scores


def extraire_infos_conversation(message, profil_actuel):
    interets_detectes = detecter_interets_depuis_message(message)

    prompt = f'''Analyse ce message et extrais les informations académiques déclarées.

Message : "{message}"
Profil actuel : {json.dumps(profil_actuel, ensure_ascii=False)}

Réponds en JSON avec SEULEMENT les champs trouvés (null pour tout le reste) :
{{
    "type_bac": "SMA/SMB/SP/SVT/STE/STM/STGC/SEG/SGC/LSH/S/SM/D/E/C/L/A/BAC_GENERAL_FR/AUTRE ou null",
    "moyenne_generale": "nombre 0-20 ou null",
    "notes_matieres": {{"matière": note}} ou null,
    "centres_interet": ["liste"] ou null,
    "ambition_professionnelle": "texte ou null",
    "ville": "texte ou null",
    "pays": "texte ou null",
    "prenom": "texte ou null",
    "niveau_actuel": "post_bac/bac1/bac2/bac3 ou null",
    "diplome_actuel": "texte ou null"
}}

RÈGLES STRICTES :
- Mets null pour tout ce qui n'est PAS mentionné explicitement
- "niveau_actuel" = "post_bac" UNIQUEMENT si la personne dit clairement
  être en Terminale, avoir le Bac ou venir juste de l'avoir.
  Si elle dit juste son prénom ou ses intérêts → null
- "centres_interet" → remplis si la personne mentionne informatique,
  finance, réseaux, IA, data, management, etc.
- Bac D ivoirien → "S" | Bac SMA marocain → "SMA"'''

    try:
        reponse = client.chat.completions.create(
            model="gpt-5.2",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_completion_tokens=500
        )
        texte = reponse.choices[0].message.content
        texte = texte.replace("```json", "").replace("```", "").strip()
        infos = json.loads(texte)

        if interets_detectes:
            interets_gpt = infos.get("centres_interet") or []
            infos["centres_interet"] = list(set(interets_gpt + interets_detectes))

        return mettre_a_jour_profil(profil_actuel, infos)

    except Exception as e:
        print(f"[PROFIL] Erreur extraction : {e}")
        if interets_detectes:
            return mettre_a_jour_profil(
                profil_actuel, {"centres_interet": interets_detectes}
            )
        return profil_actuel


def mettre_a_jour_profil(profil, nouvelles_infos):
    if not profil:
        profil = construire_profil_etudiant({})

    for cle, valeur in nouvelles_infos.items():
        if valeur is None:
            continue

        if cle == "type_bac":
            profil["parcours_academique"]["type_bac"] = valeur
            infos_bac = TYPES_BAC.get(valeur, TYPES_BAC["AUTRE"])
            profil["parcours_academique"]["label_bac"] = infos_bac.get("label", valeur)
            profil["compatibilite_filieres"] = COMPATIBILITE_BAC_FILIERE.get(valeur, {})
            profil["forces_academiques"] = {
                "force_maths":    infos_bac.get("force_maths", 3),
                "force_physique": infos_bac.get("force_physique", 3),
                "force_info":     infos_bac.get("force_info", 2),
                "force_economie": infos_bac.get("force_economie", 2),
                "force_gestion":  infos_bac.get("force_gestion", 2),
                "force_langues":  infos_bac.get("force_langues", 3)
            }

        elif cle == "moyenne_generale":
            profil["parcours_academique"]["moyenne_generale"] = float(valeur)
            profil["parcours_academique"]["mention"] = calculer_mention(float(valeur))

        elif cle == "notes_matieres" and isinstance(valeur, dict):
            profil["parcours_academique"].setdefault("notes_matieres", {}).update(valeur)

        elif cle == "centres_interet" and isinstance(valeur, list) and valeur:
            existants = profil["preferences"].get("centres_interet", [])
            nouveaux = list(set(existants + valeur))
            profil["preferences"]["centres_interet"] = nouveaux
            ambition = profil["preferences"].get("ambition_professionnelle", "")
            profil["preferences"]["scores_interets_filieres"] = \
                calculer_scores_interets(nouveaux, ambition)

        elif cle == "ambition_professionnelle" and valeur:
            profil["preferences"]["ambition_professionnelle"] = valeur
            interets_ambition = detecter_interets_depuis_message(valeur)
            if interets_ambition:
                existants = profil["preferences"].get("centres_interet", [])
                profil["preferences"]["centres_interet"] = \
                    list(set(existants + interets_ambition))
            interets = profil["preferences"].get("centres_interet", [])
            profil["preferences"]["scores_interets_filieres"] = \
                calculer_scores_interets(interets, valeur)

        elif cle == "ville"    and valeur: profil["informations_personnelles"]["ville"] = valeur
        elif cle == "pays"     and valeur: profil["informations_personnelles"]["pays"]  = valeur
        elif cle == "prenom"   and valeur: profil["informations_personnelles"]["prenom"] = valeur
        elif cle == "diplome_actuel" and valeur:
            profil["parcours_academique"]["diplome_actuel"] = valeur

        elif cle == "niveau_actuel" and valeur:
            # ── FIX BUG 2 : n'écrase que si la valeur vient du message ──
            profil["parcours_academique"]["niveau_actuel"] = valeur

    # Statut profil
    interets = profil["preferences"].get("centres_interet", [])
    moyenne  = profil["parcours_academique"].get("moyenne_generale", 0)
    type_bac = profil["parcours_academique"].get("type_bac", "AUTRE")

    if interets and moyenne > 0 and type_bac != "AUTRE":
        profil["statut_profil"] = "complet"
    elif type_bac != "AUTRE" or moyenne > 0:
        profil["statut_profil"] = "partiel"
    else:
        profil["statut_profil"] = "incomplet"

    return profil


# ============================================================
# PARTIE 2 — TEST PSYCHOMÉTRIQUE ADAPTATIF (4.5)
# ============================================================

DIMENSIONS_PSYCHO = {
    "logique":        "Raisonnement logique et analytique",
    "creativite":     "Créativité et innovation",
    "leadership":     "Leadership et prise de décision",
    "gestion_stress": "Gestion du stress et résilience",
    "travail_equipe": "Travail en équipe",
    "style_cognitif": "Style cognitif (analytique vs intuitif)"
}

PLAN_QUESTIONS = [
    "logique", "creativite", "leadership",
    "gestion_stress", "travail_equipe", "style_cognitif",
    "logique", "creativite", "leadership",
    "gestion_stress", "travail_equipe", "style_cognitif",
    "logique", "creativite", "leadership",
    "gestion_stress", "travail_equipe", "style_cognitif",
]

QUESTIONS_INITIALES = {
    "logique":        "Si tu dois résoudre un problème complexe, quelle est ta première réaction ?",
    "creativite":     "Quand tu travailles sur un projet, tu préfères suivre un plan établi ou explorer des nouvelles idées ?",
    "leadership":     "Dans un travail de groupe, quel rôle prends-tu naturellement ?",
    "gestion_stress": "Comment tu te comportes quand tu as plusieurs deadlines en même temps ?",
    "travail_equipe": "Tu préfères travailler seul ou en équipe ? Pourquoi ?",
    "style_cognitif": "Pour prendre une décision importante, tu te bases sur les faits ou sur ton intuition ?"
}


def demarrer_test_psychometrique(profil_etudiant):
    TOTAL_QUESTIONS = 10  # ← ajouter cette ligne en haut

    prenom = profil_etudiant.get("informations_personnelles", {}).get("prenom", "")

    etat_test = {
        "en_cours": True,
        "question_actuelle": 1,
        "total_questions": TOTAL_QUESTIONS,
        "dimension_actuelle": PLAN_QUESTIONS[0],
        "plan_questions": PLAN_QUESTIONS[:TOTAL_QUESTIONS],
        "questions_posees": [],
        "reponses": [],
        "scores_somme": {dim: 0 for dim in DIMENSIONS_PSYCHO},
        "scores_compteur": {dim: 0 for dim in DIMENSIONS_PSYCHO},
        "complete": False
    }

    premiere_question = QUESTIONS_INITIALES["logique"]

    message_intro = f"""
🧠 **Test de personnalité académique**

{'Parfait ' + prenom + ' !' if prenom else 'Parfait !'}

Pour mieux comprendre ton profil, je vais te poser **{TOTAL_QUESTIONS} questions rapides**.

👉 Il n'y a **pas de bonnes ou mauvaises réponses**.  
Sois simplement honnête 😊

━━━━━━━━━━━━━━━━━━

**Question 1/{TOTAL_QUESTIONS} — {DIMENSIONS_PSYCHO['logique']}**

{premiere_question}
"""

    etat_test["questions_posees"].append({
        "numero": 1,
        "dimension": "logique",
        "question": premiere_question
    })

    return message_intro.strip(), etat_test


def generer_question_suivante(reponse_precedente, etat_test, profil_etudiant):

    if etat_test["complete"]:
        return None, etat_test

    numero_actuel = etat_test["question_actuelle"]
    dimension_actuelle = etat_test["dimension_actuelle"]

    etat_test["reponses"].append({
        "numero": numero_actuel,
        "dimension": dimension_actuelle,
        "reponse": reponse_precedente
    })

    etat_test = analyser_reponse_psycho(
        reponse_precedente,
        dimension_actuelle,
        etat_test
    )

    if numero_actuel >= etat_test["total_questions"]:
        etat_test["complete"] = True
        etat_test["en_cours"] = False
        return None, etat_test

    prochaine_dimension = etat_test["plan_questions"][numero_actuel]

    etat_test["dimension_actuelle"] = prochaine_dimension
    etat_test["question_actuelle"] = numero_actuel + 1

    prompt = f"""
Tu es psychologue académique.

Génère UNE question courte pour évaluer :
{DIMENSIONS_PSYCHO[prochaine_dimension]}

Réponse précédente :
"{reponse_precedente}"

Question simple, ouverte, max 1 phrase.
"""

    question = None

    try:

        r = client.chat.completions.create(
            model="gpt-5.2",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_completion_tokens=100
        )

        question = r.choices[0].message.content.strip()

    except Exception as e:

        print("[PSYCHO ERROR]", e)

    # fallback si GPT retourne vide
    if not question or len(question) < 5:

        fallback_questions = {
            "logique": "Comment vérifies-tu que ta solution à un problème est correcte ?",
            "creativite": "Quand tu bloques sur un projet, que fais-tu pour trouver une nouvelle idée ?",
            "leadership": "Comment réagis-tu quand ton groupe n'arrive pas à se décider ?",
            "gestion_stress": "Comment gères-tu plusieurs examens la même semaine ?",
            "travail_equipe": "Qu'est-ce qui est le plus important pour bien travailler en équipe ?",
            "style_cognitif": "Préfères-tu analyser beaucoup d'informations ou suivre ton intuition ?"
        }

        question = fallback_questions.get(
            prochaine_dimension,
            "Peux-tu décrire comment tu abordes cette situation ?"
        )

    etat_test["questions_posees"].append({
        "numero": etat_test["question_actuelle"],
        "dimension": prochaine_dimension,
        "question": question
    })

    message = f"""
━━━━━━━━━━━━━━━━━━

**Question {etat_test['question_actuelle']}/{etat_test['total_questions']} — {DIMENSIONS_PSYCHO[prochaine_dimension]}**

{question}
"""

    return message.strip(), etat_test


def analyser_reponse_psycho(reponse, dimension, etat_test):
    prompt = f"""Psychologue académique. Évalue cette réponse sur la dimension
"{DIMENSIONS_PSYCHO[dimension]}" : "{reponse}"

Score 1-10 :
- 8-10 : Très positif, clair, mature
- 6-7  : Bonne capacité démontrée
- 4-5  : Moyen, partiel ou hésitant
- 2-3  : Faible, vague
- 1    : Hors sujet / pas de réponse

La plupart des étudiants normaux obtiennent 5-8. Ne sois pas trop sévère.
Réponds UNIQUEMENT avec un entier entre 1 et 10."""

    try:
        r = client.chat.completions.create(
            model="gpt-5.2",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_completion_tokens=10
        )
        txt = ''.join(c for c in r.choices[0].message.content.strip() if c.isdigit() or c == '.')
        score = max(1.0, min(10.0, float(txt) if txt else 5.0))
    except:
        score = 5.0

    etat_test["scores_somme"][dimension]    = etat_test["scores_somme"].get(dimension, 0) + score
    etat_test["scores_compteur"][dimension] = etat_test["scores_compteur"].get(dimension, 0) + 1
    return etat_test


def calculer_profil_psychometrique_final(etat_test):
    scores_normalises = {}
    for dim in DIMENSIONS_PSYCHO:
        somme    = etat_test["scores_somme"].get(dim, 0)
        compteur = etat_test["scores_compteur"].get(dim, 0)
        moyenne_dim = (somme / compteur) if compteur > 0 else 5.0
        scores_normalises[dim] = max(20, round((moyenne_dim / 10) * 100))

    points_forts  = sorted(scores_normalises.items(), key=lambda x: x[1], reverse=True)[:3]
    points_faibles = sorted(scores_normalises.items(), key=lambda x: x[1])[:2]

    compatibilite_psycho = {}
    for filiere_id, profil_filiere in PROFIL_PSYCHO_FILIERE.items():
        score_total = poids_total = 0
        for dimension, poids in profil_filiere.items():
            if dimension in scores_normalises:
                score_total += scores_normalises[dimension] * poids
                poids_total += 100 * poids
        if poids_total > 0:
            compatibilite_psycho[filiere_id] = round((score_total / poids_total) * 100)

    return {
        "scores": scores_normalises,
        "points_forts":  [d for d, _ in points_forts],
        "points_faibles": [d for d, _ in points_faibles],
        "compatibilite_filieres": compatibilite_psycho,
        "complete": True
    }


def generer_rapport_psychometrique(profil_psycho, prenom=""):
    scores = profil_psycho["scores"]
    points_forts = profil_psycho["points_forts"]
    noms = {
        "logique": "🧠 Logique", "creativite": "💡 Créativité",
        "leadership": "👑 Leadership", "gestion_stress": "💪 Gestion du stress",
        "travail_equipe": "🤝 Travail en équipe", "style_cognitif": "🔍 Style analytique"
    }
    rapport = f"✅ **Test psychométrique terminé !**\n"
    rapport += f"{'Voici ton profil ' + prenom + ' :' if prenom else 'Voici ton profil :'}\n\n"
    for dim, score in scores.items():
        barre = "█" * (score // 10) + "░" * (10 - score // 10)
        rapport += f"{noms.get(dim, dim)} : {barre} {score}%\n"
    rapport += "\n🌟 **Tes points forts :**\n"
    for dim in points_forts:
        rapport += f"• {noms.get(dim, dim)}\n"
    rapport += "\n📊 Ces résultats vont maintenant affiner ton orientation personnalisée !"
    return rapport


# ============================================================
# PARTIE 3 — PEER MATCH AI (4.13)
# ============================================================

def detecter_hesitation(historique_conversation):
    if len(historique_conversation) < CHATBOT_CONFIG["min_echanges_peer_match"]:
        return False, None

    derniers_messages = [
        msg["content"] for msg in historique_conversation[-10:]
        if msg.get("role") == "user"
    ][-5:]
    texte_recent = " ".join(derniers_messages).lower()
    signaux_detectes = [s for s in SIGNAUX_HESITATION if s.lower() in texte_recent]

    if not signaux_detectes:
        return False, None

    filiere_concernee = identifier_filiere_hesitation(derniers_messages, historique_conversation)
    return True, filiere_concernee


def identifier_filiere_hesitation(derniers_messages, historique_complet):
    texte = " ".join(derniers_messages + [
        msg["content"] for msg in historique_complet[-20:] if msg.get("role") == "user"
    ]).lower()

    mots_cles = {
        "ISI":   ["isi", "informatique", "systèmes informatiques", "développement", "programmation"],
        "IISRT": ["iisrt", "réseaux", "télécommunications", "télécom", "réseau"],
        "IISIC": ["iisic", "intelligence artificielle", "ia", "data science", "machine learning"],
        "ME":    ["management", "entreprise", "marketing", "commerce", "gestion"],
        "FACG":  ["facg", "finance", "audit", "comptabilité", "contrôle de gestion"],
        "MSTIC": ["mstic", "systèmes d'information", "digital", "management digital"]
    }
    scores = {fid: sum(1 for m in mots if m in texte) for fid, mots in mots_cles.items()}
    return max(scores, key=scores.get) if max(scores.values()) > 0 else None


def trouver_ambassadeur(program_id, ambassadeurs_db):
    if not ambassadeurs_db:
        return None
    actifs = [a for a in ambassadeurs_db
              if a.get("program_id") == program_id and a.get("is_active", False)]
    if not actifs:
        return None
    import random
    return random.choice(actifs)


def generer_message_peer_match(ambassadeur, filiere_id, prenom_etudiant=""):
    filiere_nom = FILIERES.get(filiere_id, {}).get("nom", filiere_id)
    contact = f"WhatsApp : {ambassadeur['whatsapp']}" if ambassadeur.get('whatsapp') \
        else f"Email : {ambassadeur.get('email', 'non disponible')}"

    prompt = f"""Tu es Sami, conseiller de SUPMTI Meknès.
Un étudiant{' ' + prenom_etudiant if prenom_etudiant else ''} hésite sur "{filiere_nom}".
Génère un message chaleureux (3-4 lignes) pour lui présenter l'ambassadeur
{ambassadeur.get('nom')} ({ambassadeur.get('niveau','2ème année')}).
Contact : {contact}. Style naturel, encourageant. Langue : français."""

    try:
        r = client.chat.completions.create(
            model="gpt-5.2",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_completion_tokens=300
        )
        return r.choices[0].message.content.strip()
    except:
        return (f"Je comprends ton hésitation 😊\n\n"
                f"Voici **{ambassadeur.get('nom')}**, étudiant(e) en "
                f"**{ambassadeur.get('niveau','2ème année')}** en **{filiere_nom}**.\n"
                f"📱 {contact}")


def verifier_declenchement_peer_match(historique_conversation, fitscore_calcule,
                                      peer_match_deja_declenche):
    nb = len([m for m in historique_conversation if m.get("role") == "user"])
    if nb < CHATBOT_CONFIG["min_echanges_peer_match"]: return False, None
    if not fitscore_calcule:           return False, None
    if peer_match_deja_declenche:      return False, None
    hesitation, filiere = detecter_hesitation(historique_conversation)
    return (True, filiere) if hesitation else (False, None)