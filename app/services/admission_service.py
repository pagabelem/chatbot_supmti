# ============================================================
# ADMISSION SERVICE — SUPMTI
# Admission Predictor (4.11)
# Tahirou — backend-tahirou
# ============================================================

import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from app.academic_config import (
    FILIERES,
    HISTORIQUE_ADMISSION,
    CONDITIONS_ADMISSION,
    BOURSES,
    SEUILS_MENTION
)
from app.services.fit_score_service import verifier_eligibilite

# ============================================================
# INITIALISATION
# ============================================================

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ============================================================
# PARTIE 1 — CALCUL DE PROBABILITÉ D'ADMISSION
# ============================================================

def calculer_probabilite_admission(profil_etudiant, filiere_id, fitscore=None):
    """
    Calcule la probabilité d'admission d'un étudiant
    dans une filière spécifique.

    Retourne un résultat détaillé avec :
    - Probabilité en %
    - Catégorie (Très bonnes chances / Bonnes / Moyennes / Faibles)
    - Points forts et points faibles
    - Conseils pour améliorer les chances
    """
    print(f"[ADMISSION] Calcul probabilité pour filière {filiere_id}...")

    parcours = profil_etudiant.get("parcours_academique", {})
    moyenne = float(parcours.get("moyenne_generale", 0))
    type_bac = parcours.get("type_bac", "AUTRE")
    mention = parcours.get("mention", "passable")

    # ── Vérifier l'éligibilité d'abord ──
    eligible, raison = verifier_eligibilite(profil_etudiant, filiere_id)

    if not eligible:
        return {
            "filiere_id": filiere_id,
            "filiere_nom": FILIERES.get(filiere_id, {}).get("nom", filiere_id),
            "probabilite": 0,
            "categorie": "Non éligible",
            "eligible": False,
            "raison_ineligibilite": raison,
            "points_forts": [],
            "points_faibles": [raison],
            "conseils": generer_conseils_admission(
                profil_etudiant, filiere_id, 0, eligible=False
            ),
            "bourse_estimee": None
        }

    # ── Récupérer les données historiques ──
    historique = HISTORIQUE_ADMISSION.get(filiere_id, {})
    moyenne_admis = historique.get("moyenne_admis", 12.5)
    fitscore_moyen = historique.get("fitscore_moyen", 65)
    taux_base = historique.get("taux_admission", 0.70)

    # ── Calcul des scores composants ──

    # Score 1 : Moyenne vs historique (30%)
    score_moyenne = calculer_score_moyenne_admission(
        moyenne, moyenne_admis
    )

    # Score 2 : FitScore (40%)
    score_fitscore = calculer_score_fitscore_admission(
        fitscore, fitscore_moyen
    )

    # Score 3 : Profil psychométrique (20%)
    score_psycho = calculer_score_psycho_admission(profil_etudiant)

    # Score 4 : Motivation simulée (10%)
    score_motivation = calculer_score_motivation(profil_etudiant, filiere_id)

    # ── Calcul probabilité finale ──
    probabilite = (
        score_moyenne * 0.25 +
        score_fitscore * 0.45 +
        score_psycho * 0.20 +
        score_motivation * 0.10
    )

    # Ajuster selon le taux d'admission historique
    probabilite = probabilite * taux_base * 1.3
    # Bonus de cohérence : si FitScore élevé pour cette filière, booster la probabilité
    if fitscore and fitscore >= fitscore_moyen:
        probabilite = probabilite * 1.05

    probabilite = min(95, max(5, round(probabilite)))
    # ── Catégoriser le résultat ──
    categorie = categoriser_probabilite(probabilite)

    # ── Identifier les points forts et faibles ──
    points_forts, points_faibles = identifier_points(
        profil_etudiant, filiere_id, moyenne,
        moyenne_admis, fitscore, fitscore_moyen
    )

    # ── Estimer la bourse potentielle ──
    bourse = estimer_bourse(moyenne)

    # ── Générer les conseils ──
    conseils = generer_conseils_admission(
        profil_etudiant, filiere_id, probabilite, eligible=True
    )

    resultat = {
        "filiere_id": filiere_id,
        "filiere_nom": FILIERES.get(filiere_id, {}).get("nom", filiere_id),
        "filiere_niveau": FILIERES.get(filiere_id, {}).get("niveau", ""),
        "probabilite": probabilite,
        "categorie": categorie,
        "eligible": True,
        "raison_ineligibilite": None,
        "scores_composants": {
            "moyenne": round(score_moyenne),
            "fitscore": round(score_fitscore),
            "psycho": round(score_psycho),
            "motivation": round(score_motivation)
        },
        "points_forts": points_forts,
        "points_faibles": points_faibles,
        "conseils": conseils,
        "bourse_estimee": bourse
    }

    print(f"[ADMISSION] ✅ Probabilité {filiere_id} : {probabilite}% — {categorie}")
    return resultat


def calculer_probabilite_toutes_filieres(profil_etudiant, fitscore_resultats=None):
    """
    Calcule les probabilités d'admission pour toutes les filières
    et retourne un classement
    """
    resultats = []

    for filiere_id in FILIERES.keys():
        # Récupérer le FitScore pour cette filière si disponible
        fitscore = None
        if fitscore_resultats:
            for item in fitscore_resultats.get("classement", []):
                if item["filiere_id"] == filiere_id:
                    fitscore = item["score_total"]
                    break

        resultat = calculer_probabilite_admission(
            profil_etudiant, filiere_id, fitscore
        )
        resultats.append(resultat)

    # Classer par probabilité décroissante
    resultats_tries = sorted(
        resultats,
        key=lambda x: x["probabilite"],
        reverse=True
    )

    return {
        "classement": resultats_tries,
        "meilleure_chance": resultats_tries[0] if resultats_tries else None
    }


# ── Score Moyenne vs Historique ──
def calculer_score_moyenne_admission(moyenne, moyenne_admis):
    """
    Compare la moyenne de l'étudiant avec la moyenne historique des admis
    Retourne un score entre 0 et 100
    """
    if moyenne == 0:
        return 50  # Score neutre

    ratio = moyenne / moyenne_admis

    if ratio >= 1.3:
        return 100
    elif ratio >= 1.2:
        return 90
    elif ratio >= 1.1:
        return 80
    elif ratio >= 1.0:
        return 70
    elif ratio >= 0.9:
        return 55
    elif ratio >= 0.8:
        return 40
    else:
        return 20


# ── Score FitScore ──
def calculer_score_fitscore_admission(fitscore, fitscore_moyen):
    """
    Compare le FitScore de l'étudiant avec le FitScore moyen des admis
    """
    if fitscore is None:
        return 60  # Score neutre

    ratio = fitscore / fitscore_moyen

    if ratio >= 1.3:
        return 100
    elif ratio >= 1.1:
        return 85
    elif ratio >= 1.0:
        return 75
    elif ratio >= 0.9:
        return 60
    elif ratio >= 0.8:
        return 45
    else:
        return 25


# ── Score Psychométrique ──
def calculer_score_psycho_admission(profil_etudiant):
    """
    Évalue l'adéquation psychologique globale
    """
    profil_psycho = profil_etudiant.get("profil_psychometrique")

    if not profil_psycho:
        return 60  # Score neutre si pas de test

    scores = profil_psycho.get("scores", {})
    if not scores:
        return 60

    moyenne_psycho = sum(scores.values()) / len(scores)
    return min(100, round(moyenne_psycho))


# ── Score Motivation ──
def calculer_score_motivation(profil_etudiant, filiere_id):
    """
    Évalue la motivation apparente de l'étudiant pour cette filière
    """
    preferences = profil_etudiant.get("preferences", {})
    interets = preferences.get("centres_interet", [])
    ambition = preferences.get("ambition_professionnelle", "")
    scores_interets = preferences.get("scores_interets_filieres", {})

    score_interet = scores_interets.get(filiere_id, 0)

    if score_interet >= 5:
        return 90
    elif score_interet >= 3:
        return 75
    elif score_interet >= 1:
        return 60
    elif interets or ambition:
        return 50
    else:
        return 40


# ── Catégoriser la probabilité ──
def categoriser_probabilite(probabilite):
    """
    Retourne une catégorie textuelle selon la probabilité
    """
    if probabilite >= 80:
        return "Très bonnes chances ✅"
    elif probabilite >= 60:
        return "Bonnes chances 👍"
    elif probabilite >= 40:
        return "Chances moyennes 🤔"
    elif probabilite >= 20:
        return "Chances faibles ⚠️"
    else:
        return "Très faibles chances ❌"


# ── Identifier Points Forts et Faibles ──
def identifier_points(
    profil_etudiant, filiere_id,
    moyenne, moyenne_admis, fitscore, fitscore_moyen
):
    """
    Identifie les points forts et faibles du dossier
    """
    points_forts = []
    points_faibles = []

    type_bac = profil_etudiant.get(
        "parcours_academique", {}
    ).get("type_bac", "")
    mention = profil_etudiant.get(
        "parcours_academique", {}
    ).get("mention", "")

    # Analyse de la moyenne
    if moyenne >= moyenne_admis * 1.1:
        points_forts.append(
            f"Moyenne {moyenne}/20 supérieure à la moyenne des admis ({moyenne_admis}/20)"
        )
    elif moyenne < moyenne_admis * 0.9:
        points_faibles.append(
            f"Moyenne {moyenne}/20 inférieure à la moyenne des admis ({moyenne_admis}/20)"
        )

    # Analyse de la mention
    if mention in ["très_bien", "bien"]:
        points_forts.append(f"Mention {mention.replace('_', ' ')} au BAC")
    elif mention == "passable":
        points_faibles.append("Mention passable au BAC")

    # Analyse du FitScore
    if fitscore and fitscore >= fitscore_moyen:
        points_forts.append(
            f"FitScore de {fitscore}% supérieur au score moyen des admis"
        )
    elif fitscore and fitscore < fitscore_moyen * 0.85:
        points_faibles.append(
            f"FitScore de {fitscore}% inférieur au score moyen des admis ({fitscore_moyen}%)"
        )

    # Analyse des intérêts
    scores_interets = profil_etudiant.get(
        "preferences", {}
    ).get("scores_interets_filieres", {})
    if scores_interets.get(filiere_id, 0) >= 3:
        points_forts.append("Centres d'intérêt bien alignés avec la filière")
    elif scores_interets.get(filiere_id, 0) == 0:
        points_faibles.append("Peu de centres d'intérêt déclarés pour cette filière")

    return points_forts, points_faibles


# ============================================================
# PARTIE 2 — ESTIMATION DE BOURSE
# ============================================================

def estimer_bourse(moyenne_bac):
    """
    Estime la bourse potentielle basée sur la moyenne au BAC.
    Note : La bourse réelle est basée sur le concours d'admission.
    """
    if moyenne_bac == 0:
        return None

    for palier in BOURSES["paliers"]:
        if palier["note_min"] <= moyenne_bac <= palier["note_max"]:
            if palier["pourcentage"] == 0:
                return {
                    "eligible": False,
                    "message": "Pas de bourse estimée avec cette moyenne"
                }
            return {
                "eligible": True,
                "pourcentage": palier["pourcentage"],
                "label": palier["label"],
                "reduction": palier["reduction"],
                "a_payer": palier["a_payer"],
                "note": BOURSES["note"]
            }

    return None


# ============================================================
# PARTIE 3 — CONSEILS PERSONNALISÉS
# ============================================================

def generer_conseils_admission(
    profil_etudiant, filiere_id, probabilite, eligible=True
):
    """
    Génère des conseils personnalisés pour améliorer
    les chances d'admission via GPT
    """
    prenom = profil_etudiant.get(
        "informations_personnelles", {}
    ).get("prenom", "")
    moyenne = profil_etudiant.get(
        "parcours_academique", {}
    ).get("moyenne_generale", 0)
    type_bac = profil_etudiant.get(
        "parcours_academique", {}
    ).get("type_bac", "")
    filiere_nom = FILIERES.get(filiere_id, {}).get("nom", filiere_id)

    if not eligible:
        prompt = f"""Un étudiant{'  ' + prenom if prenom else ''} avec BAC {type_bac} 
et moyenne {moyenne}/20 n'est pas éligible pour {filiere_nom} à SUPMTI Meknès.

Donne 3 conseils courts et constructifs pour améliorer sa situation.
Sois encourageant et propose des alternatives concrètes.
Maximum 100 mots."""
    else:
        prompt = f"""Un étudiant{'  ' + prenom if prenom else ''} avec BAC {type_bac}
et moyenne {moyenne}/20 a {probabilite}% de chances d'admission en {filiere_nom}.

Donne 3 conseils pratiques pour maximiser ses chances d'admission à SUPMTI.
Inclus des conseils sur le dossier, l'entretien et la préparation.
Sois encourageant. Maximum 100 mots."""

    try:
        reponse = client.chat.completions.create(
            model="gpt-5.2",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_completion_tokens=200
        )
        return reponse.choices[0].message.content.strip()

    except Exception as e:
        print(f"[ADMISSION] Erreur conseils : {e}")
        if probabilite >= 60:
            return "Prépare bien ton dossier, soigne ta lettre de motivation et entraîne-toi pour l'entretien !"
        else:
            return "Travaille ta moyenne, enrichis ton profil avec des projets personnels et prépare-toi bien pour le concours d'admission."


# ============================================================
# PARTIE 4 — RAPPORT COMPLET D'ADMISSION
# ============================================================

def generer_rapport_admission(profil_etudiant, fitscore_resultats=None):
    """
    Génère un rapport complet des probabilités d'admission
    pour toutes les filières
    """
    prenom = profil_etudiant.get(
        "informations_personnelles", {}
    ).get("prenom", "")

    resultats = calculer_probabilite_toutes_filieres(
        profil_etudiant, fitscore_resultats
    )

    classement = resultats["classement"]

    rapport = f"""🎯 **Simulation d'Admission SUPMTI Meknès**
{'Pour ' + prenom if prenom else ''}

"""
    for item in classement:
        barre = "█" * (item["probabilite"] // 10) + "░" * (10 - item["probabilite"] // 10)
        rapport += f"**{item['filiere_nom']}** ({item['filiere_niveau']})\n"
        rapport += f"{barre} {item['probabilite']}% — {item['categorie']}\n"

        if item.get("bourse_estimee") and item["bourse_estimee"].get("eligible"):
            bourse = item["bourse_estimee"]
            rapport += f"💰 Bourse estimée : {bourse['pourcentage']}% → {bourse['a_payer']} DH/an\n"

        rapport += "\n"

    meilleure = resultats["meilleure_chance"]
    if meilleure:
        rapport += f"""---
✨ **Meilleure opportunité : {meilleure['filiere_nom']}**
Probabilité : {meilleure['probabilite']}%

💡 **Conseil :** {meilleure['conseils']}"""

    return rapport