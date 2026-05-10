# # ============================================================
# # COACH SERVICE — SUPMTI
# # Coach Académique Continu (4.22)
# # Tahirou — backend-tahirou
# # ============================================================

# import os
# import json
# from datetime import datetime
# from openai import OpenAI
# from dotenv import load_dotenv
# from app.academic_config import FILIERES, CHATBOT_CONFIG
# from app.services.fit_score_service import calculer_fitscore_complet

# # ============================================================
# # INITIALISATION
# # ============================================================

# load_dotenv()
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# # ============================================================
# # PARTIE 1 — SUIVI DE L'ÉVOLUTION DU PROFIL
# # ============================================================

# def initialiser_suivi_coach(profil_etudiant):
#     """
#     Initialise le suivi coach pour un étudiant.
#     Crée un snapshot du profil initial pour comparaison future.
#     """
#     prenom = profil_etudiant.get(
#         "informations_personnelles", {}
#     ).get("prenom", "")

#     suivi = {
#         "prenom": prenom,
#         "date_debut": datetime.now().isoformat(),
#         "snapshots": [
#             {
#                 "date": datetime.now().isoformat(),
#                 "type": "initial",
#                 "profil": profil_etudiant.copy(),
#                 "fitscore": None
#             }
#         ],
#         "objectifs": [],
#         "recommandations_historique": [],
#         "nb_sessions": 1,
#         "progression": {}
#     }

#     print(f"[COACH] ✅ Suivi initialisé pour {prenom}")
#     return suivi


# def ajouter_snapshot(suivi_coach, profil_actuel, fitscore_actuel=None):
#     """
#     Ajoute un nouveau snapshot du profil pour suivre l'évolution.
#     Appelé à chaque nouvelle session ou mise à jour significative.
#     """
#     nouveau_snapshot = {
#         "date": datetime.now().isoformat(),
#         "type": "mise_a_jour",
#         "profil": profil_actuel.copy(),
#         "fitscore": fitscore_actuel
#     }

#     suivi_coach["snapshots"].append(nouveau_snapshot)
#     suivi_coach["nb_sessions"] += 1

#     print(f"[COACH] 📸 Snapshot ajouté — Session {suivi_coach['nb_sessions']}")
#     return suivi_coach


# # ============================================================
# # PARTIE 2 — COMPARAISON PROFIL INITIAL VS ACTUEL
# # ============================================================

# def analyser_evolution_profil(suivi_coach):
#     """
#     Compare le profil initial avec le profil actuel.
#     Identifie les changements et la progression.
#     """
#     snapshots = suivi_coach.get("snapshots", [])

#     if len(snapshots) < 2:
#         return {
#             "evolution_detectee": False,
#             "message": "Pas assez de données pour analyser l'évolution."
#         }

#     profil_initial = snapshots[0]["profil"]
#     profil_actuel = snapshots[-1]["profil"]

#     fitscore_initial = snapshots[0].get("fitscore")
#     fitscore_actuel = snapshots[-1].get("fitscore")

#     changements = []
#     ameliorations = []
#     points_attention = []

#     # ── Comparer les moyennes ──
#     moyenne_initiale = profil_initial.get(
#         "parcours_academique", {}
#     ).get("moyenne_generale", 0)
#     moyenne_actuelle = profil_actuel.get(
#         "parcours_academique", {}
#     ).get("moyenne_generale", 0)

#     if moyenne_actuelle > moyenne_initiale:
#         diff = round(moyenne_actuelle - moyenne_initiale, 2)
#         ameliorations.append(
#             f"Moyenne améliorée de +{diff} points ({moyenne_initiale} → {moyenne_actuelle})"
#         )
#         changements.append("moyenne")
#     elif moyenne_actuelle < moyenne_initiale:
#         diff = round(moyenne_initiale - moyenne_actuelle, 2)
#         points_attention.append(
#             f"Moyenne en baisse de -{diff} points ({moyenne_initiale} → {moyenne_actuelle})"
#         )
#         changements.append("moyenne")

#     # ── Comparer les centres d'intérêt ──
#     interets_initiaux = set(
#         profil_initial.get("preferences", {}).get("centres_interet", [])
#     )
#     interets_actuels = set(
#         profil_actuel.get("preferences", {}).get("centres_interet", [])
#     )

#     nouveaux_interets = interets_actuels - interets_initiaux
#     if nouveaux_interets:
#         ameliorations.append(
#             f"Nouveaux centres d'intérêt identifiés : {', '.join(nouveaux_interets)}"
#         )
#         changements.append("interets")

#     # ── Comparer les FitScores ──
#     if fitscore_initial and fitscore_actuel:
#         top_initial = fitscore_initial["classement"][0] if fitscore_initial.get("classement") else None
#         top_actuel = fitscore_actuel["classement"][0] if fitscore_actuel.get("classement") else None

#         if top_initial and top_actuel:
#             if top_actuel["score_total"] > top_initial["score_total"]:
#                 diff = top_actuel["score_total"] - top_initial["score_total"]
#                 ameliorations.append(
#                     f"FitScore amélioré de +{diff}% pour {top_actuel['filiere_nom']}"
#                 )
#             if top_initial["filiere_id"] != top_actuel["filiere_id"]:
#                 changements.append("orientation")
#                 points_attention.append(
#                     f"Changement d'orientation : {top_initial['filiere_nom']} → {top_actuel['filiere_nom']}"
#                 )

#     return {
#         "evolution_detectee": len(changements) > 0,
#         "changements": changements,
#         "ameliorations": ameliorations,
#         "points_attention": points_attention,
#         "nb_sessions": suivi_coach["nb_sessions"],
#         "duree_suivi": calculer_duree_suivi(suivi_coach)
#     }


# def calculer_duree_suivi(suivi_coach):
#     """
#     Calcule la durée totale du suivi en jours
#     """
#     try:
#         date_debut = datetime.fromisoformat(suivi_coach["date_debut"])
#         maintenant = datetime.now()
#         duree = (maintenant - date_debut).days
#         return duree
#     except:
#         return 0


# # ============================================================
# # PARTIE 3 — RÉÉVALUATION FITSCORE
# # ============================================================

# def reevaluer_fitscore(suivi_coach, profil_actuel, profil_psychometrique=None):
#     """
#     Recalcule le FitScore avec le profil mis à jour.
#     Compare avec le FitScore précédent.
#     """
#     print("[COACH] 🔄 Réévaluation du FitScore...")

#     # Calculer le nouveau FitScore
#     nouveau_fitscore = calculer_fitscore_complet(
#         profil_actuel, profil_psychometrique
#     )

#     # Récupérer l'ancien FitScore
#     snapshots = suivi_coach.get("snapshots", [])
#     ancien_fitscore = None
#     for snapshot in reversed(snapshots[:-1]):
#         if snapshot.get("fitscore"):
#             ancien_fitscore = snapshot["fitscore"]
#             break

#     # Comparer les FitScores
#     comparaison = None
#     if ancien_fitscore:
#         comparaison = comparer_fitscores(ancien_fitscore, nouveau_fitscore)

#     return {
#         "nouveau_fitscore": nouveau_fitscore,
#         "ancien_fitscore": ancien_fitscore,
#         "comparaison": comparaison
#     }


# def comparer_fitscores(ancien, nouveau):
#     """
#     Compare deux FitScores et retourne les différences
#     """
#     differences = []

#     ancien_classement = {
#         item["filiere_id"]: item["score_total"]
#         for item in ancien.get("classement", [])
#     }
#     nouveau_classement = {
#         item["filiere_id"]: item["score_total"]
#         for item in nouveau.get("classement", [])
#     }

#     for filiere_id, nouveau_score in nouveau_classement.items():
#         ancien_score = ancien_classement.get(filiere_id, 0)
#         diff = nouveau_score - ancien_score

#         if diff != 0:
#             differences.append({
#                 "filiere_id": filiere_id,
#                 "filiere_nom": FILIERES.get(filiere_id, {}).get("nom", filiere_id),
#                 "ancien_score": ancien_score,
#                 "nouveau_score": nouveau_score,
#                 "difference": diff,
#                 "tendance": "↑" if diff > 0 else "↓"
#             })

#     # Vérifier si la meilleure filière a changé
#     ancienne_top = ancien.get("meilleure_filiere")
#     nouvelle_top = nouveau.get("meilleure_filiere")
#     changement_orientation = ancienne_top != nouvelle_top

#     return {
#         "differences": differences,
#         "changement_orientation": changement_orientation,
#         "ancienne_top": ancienne_top,
#         "nouvelle_top": nouvelle_top
#     }


# # ============================================================
# # PARTIE 4 — CONSEILS PERSONNALISÉS GPT
# # ============================================================

# def generer_conseils_coach(
#     profil_etudiant,
#     fitscore_actuel,
#     evolution=None,
#     objectifs=None
# ):
#     """
#     Génère des conseils personnalisés et actionnables
#     basés sur le profil et l'évolution de l'étudiant.
#     """
#     prenom = profil_etudiant.get(
#         "informations_personnelles", {}
#     ).get("prenom", "")
#     moyenne = profil_etudiant.get(
#         "parcours_academique", {}
#     ).get("moyenne_generale", 0)
#     type_bac = profil_etudiant.get(
#         "parcours_academique", {}
#     ).get("type_bac", "")

#     meilleure_filiere = None
#     score_top = 0
#     if fitscore_actuel and fitscore_actuel.get("classement"):
#         top = fitscore_actuel["classement"][0]
#         meilleure_filiere = top["filiere_nom"]
#         score_top = top["score_total"]

#     # Construire le contexte d'évolution
#     contexte_evolution = ""
#     if evolution and evolution.get("evolution_detectee"):
#         if evolution.get("ameliorations"):
#             contexte_evolution += "Points positifs récents :\n"
#             for a in evolution["ameliorations"]:
#                 contexte_evolution += f"- {a}\n"
#         if evolution.get("points_attention"):
#             contexte_evolution += "Points d'attention :\n"
#             for p in evolution["points_attention"]:
#                 contexte_evolution += f"- {p}\n"

#     prompt = f"""Tu es Sami, coach académique personnel de SUPMTI Meknès.
# Tu suis l'étudiant{' ' + prenom if prenom else ''} depuis plusieurs sessions.

# PROFIL ACTUEL :
# - BAC : {type_bac}
# - Moyenne : {moyenne}/20
# - Meilleure filière recommandée : {meilleure_filiere} ({score_top}%)

# {contexte_evolution}

# OBJECTIFS DÉCLARÉS : {', '.join(objectifs) if objectifs else 'Non définis'}

# Génère un message de coaching personnalisé qui inclut :

# 1. 🎯 **Situation actuelle** (1-2 phrases bienveillantes)
# 2. 💪 **3 actions concrètes** à faire cette semaine pour progresser
# 3. 📚 **1 ressource spécifique** à consulter (cours, certification, projet)
# 4. 🌟 **Message de motivation** personnalisé

# RÈGLES :
# - Utilise le prénom {prenom if prenom else "de l'étudiant"}
# - Sois concret, pas vague
# - Actions réalistes et mesurables
# - Ton chaleureux et encourageant
# - Max 200 mots"""

#     try:
#         reponse_gpt = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0.7,
#             max_completion_tokens=400
#         )

#         conseils = reponse_gpt.choices[0].message.content.strip()
#         print(f"[COACH] ✅ Conseils générés pour {prenom}")
#         return conseils

#     except Exception as e:
#         print(f"[COACH] Erreur conseils : {e}")
#         return generer_conseils_fallback(prenom, meilleure_filiere, moyenne)


# def generer_conseils_fallback(prenom, filiere, moyenne):
#     """Conseils de base si GPT échoue"""
#     return f"""🎯 **Situation actuelle**
# {'Bonjour ' + prenom + ' !' if prenom else 'Bonjour !'} Tu es sur la bonne voie vers {filiere if filiere else 'ton orientation'}.

# 💪 **3 actions pour cette semaine :**
# 1. Révise tes matières clés et vise une moyenne au-dessus de {round(moyenne + 0.5, 1)}/20
# 2. Explore les ressources en ligne liées à ta filière cible
# 3. Prépare une liste de questions pour ton entretien d'admission

# 📚 **Ressource recommandée :**
# Visite le site de SUPMTI Meknès pour en savoir plus sur ta filière.

# 🌟 **Motivation :**
# Chaque effort aujourd'hui construit ton succès de demain. Continue ! 💪"""


# # ============================================================
# # PARTIE 5 — TABLEAU DE BORD PROGRESSION
# # ============================================================

# def generer_tableau_de_bord(suivi_coach, fitscore_actuel):
#     """
#     Génère les données du tableau de bord de progression
#     pour affichage par Basile (frontend).
#     Format JSON optimisé pour les graphiques.
#     """
#     snapshots = suivi_coach.get("snapshots", [])

#     # Données pour graphique d'évolution des moyennes
#     evolution_moyenne = []
#     for i, snapshot in enumerate(snapshots):
#         moyenne = snapshot["profil"].get(
#             "parcours_academique", {}
#         ).get("moyenne_generale", 0)
#         evolution_moyenne.append({
#             "session": i + 1,
#             "date": snapshot["date"][:10],
#             "moyenne": moyenne
#         })

#     # Données pour graphique FitScore par filière
#     fitscore_data = []
#     if fitscore_actuel and fitscore_actuel.get("classement"):
#         for item in fitscore_actuel["classement"]:
#             fitscore_data.append({
#                 "filiere": item["filiere_id"],
#                 "filiere_nom": item["filiere_nom"],
#                 "score": item["score_total"],
#                 "eligible": item["eligible"]
#             })

#     # Statistiques générales
#     profil_actuel = snapshots[-1]["profil"] if snapshots else {}
#     stats = {
#         "nb_sessions": suivi_coach.get("nb_sessions", 1),
#         "duree_suivi_jours": calculer_duree_suivi(suivi_coach),
#         "profil_complet": profil_actuel.get("statut_profil") == "complet",
#         "test_psycho_complete": profil_actuel.get("profil_psychometrique") is not None,
#         "meilleure_filiere": fitscore_actuel.get(
#             "meilleure_filiere"
#         ) if fitscore_actuel else None
#     }

#     return {
#         "stats": stats,
#         "evolution_moyenne": evolution_moyenne,
#         "fitscore_filieres": fitscore_data,
#         "derniere_mise_a_jour": datetime.now().isoformat()
#     }


# # ============================================================
# # PARTIE 6 — DÉFINIR ET SUIVRE LES OBJECTIFS
# # ============================================================

# def definir_objectifs(suivi_coach, objectifs):
#     """
#     Enregistre les objectifs académiques de l'étudiant.
#     objectifs = liste de strings
#     """
#     suivi_coach["objectifs"] = objectifs
#     print(f"[COACH] 🎯 {len(objectifs)} objectif(s) défini(s)")
#     return suivi_coach


# def evaluer_objectifs(suivi_coach, profil_actuel):
#     """
#     Évalue la progression vers les objectifs définis.
#     """
#     objectifs = suivi_coach.get("objectifs", [])
#     if not objectifs:
#         return {"message": "Aucun objectif défini."}

#     prompt = f"""Évalue la progression de cet étudiant vers ses objectifs.

# Profil actuel :
# - Moyenne : {profil_actuel.get('parcours_academique', {}).get('moyenne_generale', 0)}/20
# - Statut profil : {profil_actuel.get('statut_profil', 'incomplet')}

# Objectifs définis :
# {chr(10).join(['- ' + obj for obj in objectifs])}

# Pour chaque objectif, donne :
# 1. Une évaluation courte (atteint / en cours / à travailler)
# 2. Un conseil spécifique

# Format JSON :
# [{{"objectif": "...", "statut": "...", "conseil": "..."}}]"""

#     try:
#         reponse = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0.5,
#             max_completion_tokens=300
#         )

#         texte = reponse.choices[0].message.content.strip()
#         texte = texte.replace("```json", "").replace("```", "").strip()
#         return json.loads(texte)

#     except Exception as e:
#         print(f"[COACH] Erreur évaluation objectifs : {e}")
#         return [
#             {"objectif": obj, "statut": "en cours", "conseil": "Continue tes efforts !"}
#             for obj in objectifs
#         ]


# # ============================================================
# # PARTIE 7 — RAPPORT COACH COMPLET
# # ============================================================

# def generer_rapport_coach(suivi_coach, profil_actuel, fitscore_actuel):
#     """
#     Génère un rapport complet de coaching pour l'étudiant.
#     """
#     prenom = suivi_coach.get("prenom", "")
#     evolution = analyser_evolution_profil(suivi_coach)
#     tableau_bord = generer_tableau_de_bord(suivi_coach, fitscore_actuel)
#     conseils = generer_conseils_coach(
#         profil_actuel, fitscore_actuel, evolution
#     )

#     # Meilleure filière actuelle
#     meilleure = None
#     if fitscore_actuel and fitscore_actuel.get("classement"):
#         meilleure = fitscore_actuel["classement"][0]

#     rapport = f"""📊 **Rapport de Suivi Coach**
# {'Pour ' + prenom if prenom else ''}
# Date : {datetime.now().strftime('%d/%m/%Y')}
# Sessions : {suivi_coach.get('nb_sessions', 1)} | Suivi depuis : {tableau_bord['stats']['duree_suivi_jours']} jour(s)

# """

#     if meilleure:
#         rapport += f"""🎯 **Orientation Recommandée**
# {meilleure['filiere_nom']} ({meilleure['filiere_niveau']})
# Score de compatibilité : {meilleure['score_total']}%
# Éligibilité : {'✅ Oui' if meilleure['eligible'] else '⚠️ Conditions à vérifier'}

# """

#     if evolution.get("ameliorations"):
#         rapport += "✅ **Progrès récents :**\n"
#         for a in evolution["ameliorations"]:
#             rapport += f"• {a}\n"
#         rapport += "\n"

#     if evolution.get("points_attention"):
#         rapport += "⚠️ **Points d'attention :**\n"
#         for p in evolution["points_attention"]:
#             rapport += f"• {p}\n"
#         rapport += "\n"

#     rapport += f"---\n{conseils}"

#     return rapport



# ============================================================
# COACH SERVICE — SUPMTI
# Coach Académique Continu (4.22)
# Tahirou — backend-tahirou
# ============================================================

import os
import json
import copy
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from app.academic_config import FILIERES, CHATBOT_CONFIG
from app.services.fit_score_service import calculer_fitscore_complet

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ============================================================
# PARTIE 1 — SUIVI DE L'ÉVOLUTION DU PROFIL
# ============================================================

def initialiser_suivi_coach(profil_etudiant):
    """
    Initialise le suivi coach pour un étudiant.
    FIX : deepcopy pour éviter la corruption de l'historique.
    """
    prenom = profil_etudiant.get("informations_personnelles", {}).get("prenom", "")

    suivi = {
        "prenom":                     prenom,
        "date_debut":                 datetime.now().isoformat(),
        "snapshots": [
            {
                "date":   datetime.now().isoformat(),
                "type":   "initial",
                "profil": copy.deepcopy(profil_etudiant),
                "fitscore": None
            }
        ],
        "objectifs":                  [],
        "recommandations_historique": [],
        "nb_sessions":                1,
        "progression":                {}
    }

    print(f"[COACH] ✅ Suivi initialisé pour {prenom}")
    return suivi


def ajouter_snapshot(suivi_coach, profil_actuel, fitscore_actuel=None):
    """
    Ajoute un nouveau snapshot du profil.
    FIX : deepcopy pour éviter que les modifications futures corrompent l'historique.
    """
    nouveau_snapshot = {
        "date":     datetime.now().isoformat(),
        "type":     "mise_a_jour",
        "profil":   copy.deepcopy(profil_actuel),
        "fitscore": fitscore_actuel
    }

    suivi_coach["snapshots"].append(nouveau_snapshot)
    suivi_coach["nb_sessions"] += 1

    print(f"[COACH] 📸 Snapshot ajouté — Session {suivi_coach['nb_sessions']}")
    return suivi_coach

# ============================================================
# PARTIE 2 — COMPARAISON PROFIL INITIAL VS ACTUEL
# ============================================================

def analyser_evolution_profil(suivi_coach):
    snapshots = suivi_coach.get("snapshots", [])

    if len(snapshots) < 2:
        return {
            "evolution_detectee": False,
            "message": "Pas assez de données pour analyser l'évolution."
        }

    profil_initial   = snapshots[0]["profil"]
    profil_actuel    = snapshots[-1]["profil"]
    fitscore_initial = snapshots[0].get("fitscore")
    fitscore_actuel  = snapshots[-1].get("fitscore")

    changements      = []
    ameliorations    = []
    points_attention = []

    moyenne_initiale = profil_initial.get("parcours_academique", {}).get("moyenne_generale", 0)
    moyenne_actuelle = profil_actuel.get("parcours_academique", {}).get("moyenne_generale", 0)

    if moyenne_actuelle > moyenne_initiale:
        diff = round(moyenne_actuelle - moyenne_initiale, 2)
        ameliorations.append(
            f"Moyenne améliorée de +{diff} points ({moyenne_initiale} → {moyenne_actuelle})"
        )
        changements.append("moyenne")
    elif moyenne_actuelle < moyenne_initiale:
        diff = round(moyenne_initiale - moyenne_actuelle, 2)
        points_attention.append(
            f"Moyenne en baisse de -{diff} points ({moyenne_initiale} → {moyenne_actuelle})"
        )
        changements.append("moyenne")

    interets_initiaux = set(profil_initial.get("preferences", {}).get("centres_interet", []))
    interets_actuels  = set(profil_actuel.get("preferences", {}).get("centres_interet", []))
    nouveaux_interets = interets_actuels - interets_initiaux

    if nouveaux_interets:
        ameliorations.append(
            f"Nouveaux centres d'intérêt identifiés : {', '.join(nouveaux_interets)}"
        )
        changements.append("interets")

    if fitscore_initial and fitscore_actuel:
        top_initial = (fitscore_initial["classement"][0]
                       if fitscore_initial.get("classement") else None)
        top_actuel  = (fitscore_actuel["classement"][0]
                       if fitscore_actuel.get("classement") else None)

        if top_initial and top_actuel:
            if top_actuel["score_total"] > top_initial["score_total"]:
                diff = top_actuel["score_total"] - top_initial["score_total"]
                ameliorations.append(
                    f"FitScore amélioré de +{diff}% pour {top_actuel['filiere_nom']}"
                )
            if top_initial["filiere_id"] != top_actuel["filiere_id"]:
                changements.append("orientation")
                points_attention.append(
                    f"Changement d'orientation : {top_initial['filiere_nom']} "
                    f"→ {top_actuel['filiere_nom']}"
                )

    return {
        "evolution_detectee": len(changements) > 0,
        "changements":        changements,
        "ameliorations":      ameliorations,
        "points_attention":   points_attention,
        "nb_sessions":        suivi_coach["nb_sessions"],
        "duree_suivi":        calculer_duree_suivi(suivi_coach)
    }


def calculer_duree_suivi(suivi_coach):
    """
    Calcule la durée totale du suivi en jours.
    FIX : gestion robuste du format ISO avec ou sans timezone offset.
    """
    try:
        date_str = suivi_coach["date_debut"]
        date_str = date_str.split("+")[0].split("Z")[0].strip()
        date_debut = datetime.fromisoformat(date_str)
        return (datetime.now() - date_debut).days
    except Exception:
        return 0

# ============================================================
# PARTIE 3 — RÉÉVALUATION FITSCORE
# ============================================================

def reevaluer_fitscore(suivi_coach, profil_actuel, profil_psychometrique=None):
    print("[COACH] 🔄 Réévaluation du FitScore...")

    nouveau_fitscore = calculer_fitscore_complet(profil_actuel, profil_psychometrique)

    snapshots       = suivi_coach.get("snapshots", [])
    ancien_fitscore = None
    for snapshot in reversed(snapshots[:-1]):
        if snapshot.get("fitscore"):
            ancien_fitscore = snapshot["fitscore"]
            break

    comparaison = None
    if ancien_fitscore:
        comparaison = comparer_fitscores(ancien_fitscore, nouveau_fitscore)

    return {
        "nouveau_fitscore": nouveau_fitscore,
        "ancien_fitscore":  ancien_fitscore,
        "comparaison":      comparaison
    }


def comparer_fitscores(ancien, nouveau):
    ancien_classement = {
        item["filiere_id"]: item["score_total"]
        for item in ancien.get("classement", [])
    }
    nouveau_classement = {
        item["filiere_id"]: item["score_total"]
        for item in nouveau.get("classement", [])
    }

    differences = []
    for filiere_id, nouveau_score in nouveau_classement.items():
        ancien_score = ancien_classement.get(filiere_id, 0)
        diff         = nouveau_score - ancien_score
        if diff != 0:
            differences.append({
                "filiere_id":   filiere_id,
                "filiere_nom":  FILIERES.get(filiere_id, {}).get("nom", filiere_id),
                "ancien_score": ancien_score,
                "nouveau_score": nouveau_score,
                "difference":   diff,
                "tendance":     "↑" if diff > 0 else "↓"
            })

    ancienne_top           = ancien.get("meilleure_filiere")
    nouvelle_top           = nouveau.get("meilleure_filiere")
    changement_orientation = ancienne_top != nouvelle_top

    return {
        "differences":           differences,
        "changement_orientation": changement_orientation,
        "ancienne_top":          ancienne_top,
        "nouvelle_top":          nouvelle_top
    }

# ============================================================
# PARTIE 4 — CONSEILS PERSONNALISÉS GPT
# ============================================================

def generer_conseils_coach(
    profil_etudiant,
    fitscore_actuel,
    evolution=None,
    objectifs=None
):
    prenom   = profil_etudiant.get("informations_personnelles", {}).get("prenom", "")
    moyenne  = profil_etudiant.get("parcours_academique", {}).get("moyenne_generale", 0)
    type_bac = profil_etudiant.get("parcours_academique", {}).get("type_bac", "")

    meilleure_filiere = None
    score_top         = 0
    if fitscore_actuel and fitscore_actuel.get("classement"):
        top               = fitscore_actuel["classement"][0]
        meilleure_filiere = top["filiere_nom"]
        score_top         = top["score_total"]

    contexte_evolution = ""
    if evolution and evolution.get("evolution_detectee"):
        if evolution.get("ameliorations"):
            contexte_evolution += "Points positifs récents :\n"
            for a in evolution["ameliorations"]:
                contexte_evolution += f"- {a}\n"
        if evolution.get("points_attention"):
            contexte_evolution += "Points d'attention :\n"
            for p in evolution["points_attention"]:
                contexte_evolution += f"- {p}\n"

    ligne_objectifs = (
        f"OBJECTIFS DÉCLARÉS : {', '.join(objectifs)}"
        if objectifs else ""
    )

    prompt = f"""Tu es Sami, coach académique personnel de SUPMTI Meknès.
Tu suis l'étudiant{' ' + prenom if prenom else ''} depuis plusieurs sessions.

PROFIL ACTUEL :
- BAC : {type_bac}
- Moyenne : {moyenne}/20
- Meilleure filière recommandée : {meilleure_filiere} ({score_top}%)

{contexte_evolution}
{ligne_objectifs}

Génère un message de coaching personnalisé :

## Situation actuelle
1-2 phrases bienveillantes sur le profil.

## 3 actions concrètes
- Action 1 (mesurable cette semaine)
- Action 2 (mesurable cette semaine)
- Action 3 (mesurable cette semaine)

## Ressource recommandée
1 ressource spécifique (cours, certification, projet).

## Motivation
1-2 phrases encourageantes personnalisées.

FORMAT OBLIGATOIRE :
- ## pour les titres
- **texte** pour les éléments importants
- - tirets pour les actions
- Jamais de : •, ►, ════
Max 200 mots."""

    try:
        r = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=400
        )
        conseils = r.choices[0].message.content.strip()
        print(f"[COACH] ✅ Conseils générés pour {prenom}")
        return conseils

    except Exception as e:
        print(f"[COACH] Erreur conseils : {e}")
        return generer_conseils_fallback(prenom, meilleure_filiere, moyenne)


def generer_conseils_fallback(prenom, filiere, moyenne):
    nom = (prenom + " !") if prenom else "!"
    filiere_str = filiere if filiere else "ton orientation"
    return (
        f"## Situation actuelle\n"
        f"Bonjour {nom} Tu es sur la bonne voie vers **{filiere_str}**.\n\n"
        f"## 3 actions pour cette semaine\n"
        f"- Révise tes matières clés et vise **{round(moyenne + 0.5, 1)}/20** minimum\n"
        f"- Explore des ressources en ligne liées à ta filière cible\n"
        f"- Prépare une liste de questions pour ton entretien d'admission\n\n"
        f"## Ressource recommandée\n"
        f"Consulte le site officiel de SUPMTI Meknès pour les détails de ta filière.\n\n"
        f"Chaque effort aujourd'hui construit ton succès de demain. Continue !"
    )

# ============================================================
# PARTIE 5 — TABLEAU DE BORD PROGRESSION
# ============================================================

def generer_tableau_de_bord(suivi_coach, fitscore_actuel):
    snapshots = suivi_coach.get("snapshots", [])

    evolution_moyenne = []
    for i, snapshot in enumerate(snapshots):
        moyenne = snapshot["profil"].get(
            "parcours_academique", {}
        ).get("moyenne_generale", 0)
        evolution_moyenne.append({
            "session": i + 1,
            "date":    snapshot["date"][:10],
            "moyenne": moyenne
        })

    fitscore_data = []
    if fitscore_actuel and fitscore_actuel.get("classement"):
        for item in fitscore_actuel["classement"]:
            fitscore_data.append({
                "filiere":     item["filiere_id"],
                "filiere_nom": item["filiere_nom"],
                "score":       item["score_total"],
                "eligible":    item["eligible"]
            })

    profil_actuel = snapshots[-1]["profil"] if snapshots else {}
    stats = {
        "nb_sessions":         suivi_coach.get("nb_sessions", 1),
        "duree_suivi_jours":   calculer_duree_suivi(suivi_coach),
        "profil_complet":      profil_actuel.get("statut_profil") == "complet",
        "test_psycho_complete": profil_actuel.get("profil_psychometrique") is not None,
        "meilleure_filiere":   (
            fitscore_actuel.get("meilleure_filiere") if fitscore_actuel else None
        )
    }

    return {
        "stats":                stats,
        "evolution_moyenne":    evolution_moyenne,
        "fitscore_filieres":    fitscore_data,
        "derniere_mise_a_jour": datetime.now().isoformat()
    }

# ============================================================
# PARTIE 6 — OBJECTIFS
# ============================================================

def definir_objectifs(suivi_coach, objectifs):
    suivi_coach["objectifs"] = objectifs
    print(f"[COACH] 🎯 {len(objectifs)} objectif(s) défini(s)")
    return suivi_coach


def evaluer_objectifs(suivi_coach, profil_actuel):
    objectifs = suivi_coach.get("objectifs", [])
    if not objectifs:
        return {"message": "Aucun objectif défini."}

    prompt = f"""Évalue la progression de cet étudiant vers ses objectifs.

Profil actuel :
- Moyenne : {profil_actuel.get('parcours_academique', {}).get('moyenne_generale', 0)}/20
- Statut profil : {profil_actuel.get('statut_profil', 'incomplet')}

Objectifs définis :
{chr(10).join(['- ' + obj for obj in objectifs])}

Retourne UNIQUEMENT un tableau JSON valide sans backticks ni preamble :
[{{"objectif": "...", "statut": "...", "conseil": "..."}}]"""

    try:
        r = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=300
        )
        texte = r.choices[0].message.content.strip()
        texte = texte.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(texte)
        except json.JSONDecodeError as je:
            print(f"[COACH] JSON malformé dans evaluer_objectifs : {je} | Texte : {texte[:200]}")
            raise

    except Exception as e:
        print(f"[COACH] Erreur évaluation objectifs : {e}")
        return [
            {"objectif": obj, "statut": "en cours", "conseil": "Continue tes efforts !"}
            for obj in objectifs
        ]

# ============================================================
# PARTIE 7 — RAPPORT COACH COMPLET
# ============================================================

def generer_rapport_coach(suivi_coach, profil_actuel, fitscore_actuel):
    prenom = suivi_coach.get("prenom", "")

    snapshots = suivi_coach.get("snapshots", [])
    if not snapshots:
        return "Aucune donnée de suivi disponible. Lance une première session."

    evolution    = analyser_evolution_profil(suivi_coach)
    tableau_bord = generer_tableau_de_bord(suivi_coach, fitscore_actuel)
    conseils     = generer_conseils_coach(profil_actuel, fitscore_actuel, evolution)

    meilleure = None
    if fitscore_actuel and fitscore_actuel.get("classement"):
        meilleure = fitscore_actuel["classement"][0]

    rapport  = "## Rapport de Suivi Coach\n"
    if prenom:
        rapport += f"Pour {prenom}\n"
    rapport += (
        f"Date : {datetime.now().strftime('%d/%m/%Y')} | "
        f"Sessions : {suivi_coach.get('nb_sessions', 1)} | "
        f"Suivi depuis : {tableau_bord['stats']['duree_suivi_jours']} jour(s)\n\n"
    )

    if meilleure:
        rapport += (
            f"## Orientation recommandée\n"
            f"**{meilleure['filiere_nom']}** ({meilleure.get('filiere_niveau', '')})\n"
            f"- Score de compatibilité : **{meilleure.get('score_total', meilleure.get('score', '?'))}%**\n"
            f"- Éligibilité : {'Oui' if meilleure['eligible'] else 'Conditions à vérifier'}\n\n"
        )

    if evolution.get("ameliorations"):
        rapport += "## Progrès récents\n"
        for a in evolution["ameliorations"]:
            rapport += f"- {a}\n"
        rapport += "\n"

    if evolution.get("points_attention"):
        rapport += "## Points d'attention\n"
        for p in evolution["points_attention"]:
            rapport += f"- {p}\n"
        rapport += "\n"

    rapport += f"## Conseils personnalisés\n{conseils}"
    return rapport