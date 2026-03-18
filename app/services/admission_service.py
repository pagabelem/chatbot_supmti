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
    Calcule la probabilité d'admission d'un étudiant dans une filière.
    Retourne un résultat détaillé avec :
    - Probabilité en %
    - Catégorie (Très bonnes chances / Bonnes / Moyennes / Faibles)
    - Points forts et points faibles
    - Conseils pour améliorer les chances

    NOTE : verifier_eligibilite() utilise désormais niveau default ''
    (fix dans fit_score_service.py) — plus de faux-positif post_bac.
    """
    print(f"[ADMISSION] Calcul probabilité pour filière {filiere_id}...")

    parcours = profil_etudiant.get("parcours_academique", {})
    moyenne  = float(parcours.get("moyenne_generale", 0))
    type_bac = parcours.get("type_bac", "AUTRE")
    mention  = parcours.get("mention", "passable")

    eligible, raison = verifier_eligibilite(profil_etudiant, filiere_id)

    if not eligible:
        return {
            "filiere_id":           filiere_id,
            "filiere_nom":          FILIERES.get(filiere_id, {}).get("nom", filiere_id),
            "probabilite":          0,
            "categorie":            "Non éligible",
            "eligible":             False,
            "raison_ineligibilite": raison,
            "points_forts":         [],
            "points_faibles":       [raison],
            "conseils":             generer_conseils_admission(
                profil_etudiant, filiere_id, 0, eligible=False
            ),
            "bourse_estimee": None
        }

    historique   = HISTORIQUE_ADMISSION.get(filiere_id, {})
    moyenne_admis  = historique.get("moyenne_admis", 12.5)
    fitscore_moyen = historique.get("fitscore_moyen", 65)
    taux_base    = historique.get("taux_admission", 0.70)

    score_moyenne   = calculer_score_moyenne_admission(moyenne, moyenne_admis)
    score_fitscore  = calculer_score_fitscore_admission(fitscore, fitscore_moyen)
    score_psycho    = calculer_score_psycho_admission(profil_etudiant)
    score_motivation = calculer_score_motivation(profil_etudiant, filiere_id)

    probabilite = (
        score_moyenne    * 0.25 +
        score_fitscore   * 0.45 +
        score_psycho     * 0.20 +
        score_motivation * 0.10
    )

    probabilite = probabilite * taux_base * 1.3
    if fitscore and fitscore >= fitscore_moyen:
        probabilite *= 1.05

    probabilite = min(95, max(5, round(probabilite)))
    categorie   = categoriser_probabilite(probabilite)

    points_forts, points_faibles = identifier_points(
        profil_etudiant, filiere_id,
        moyenne, moyenne_admis, fitscore, fitscore_moyen
    )

    bourse  = estimer_bourse(moyenne)
    conseils = generer_conseils_admission(
        profil_etudiant, filiere_id, probabilite, eligible=True
    )

    resultat = {
        "filiere_id":           filiere_id,
        "filiere_nom":          FILIERES.get(filiere_id, {}).get("nom", filiere_id),
        "filiere_niveau":       FILIERES.get(filiere_id, {}).get("niveau", ""),
        "probabilite":          probabilite,
        "categorie":            categorie,
        "eligible":             True,
        "raison_ineligibilite": None,
        "scores_composants": {
            "moyenne":    round(score_moyenne),
            "fitscore":   round(score_fitscore),
            "psycho":     round(score_psycho),
            "motivation": round(score_motivation)
        },
        "points_forts":   points_forts,
        "points_faibles": points_faibles,
        "conseils":       conseils,
        "bourse_estimee": bourse
    }

    print(f"[ADMISSION] ✅ Probabilité {filiere_id} : {probabilite}% — {categorie}")
    return resultat


def calculer_probabilite_toutes_filieres(profil_etudiant, fitscore_resultats=None):
    """Calcule les probabilités pour toutes les filières et retourne un classement."""
    resultats = []

    for filiere_id in FILIERES.keys():
        fitscore = None
        if fitscore_resultats:
            for item in fitscore_resultats.get("classement", []):
                if item["filiere_id"] == filiere_id:
                    fitscore = item["score_total"]
                    break

        resultat = calculer_probabilite_admission(profil_etudiant, filiere_id, fitscore)
        resultats.append(resultat)

    resultats_tries = sorted(resultats, key=lambda x: x["probabilite"], reverse=True)

    return {
        "classement":     resultats_tries,
        "meilleure_chance": resultats_tries[0] if resultats_tries else None
    }


# ── Score Moyenne vs Historique ──
def calculer_score_moyenne_admission(moyenne, moyenne_admis):
    if moyenne == 0:
        return 50
    ratio = moyenne / moyenne_admis
    if ratio >= 1.3:   return 100
    elif ratio >= 1.2: return 90
    elif ratio >= 1.1: return 80
    elif ratio >= 1.0: return 70
    elif ratio >= 0.9: return 55
    elif ratio >= 0.8: return 40
    else:              return 20


# ── Score FitScore ──
def calculer_score_fitscore_admission(fitscore, fitscore_moyen):
    if fitscore is None:
        return 60
    ratio = fitscore / fitscore_moyen
    if ratio >= 1.3:   return 100
    elif ratio >= 1.1: return 85
    elif ratio >= 1.0: return 75
    elif ratio >= 0.9: return 60
    elif ratio >= 0.8: return 45
    else:              return 25


# ── Score Psychométrique ──
def calculer_score_psycho_admission(profil_etudiant):
    profil_psycho = profil_etudiant.get("profil_psychometrique")
    if not profil_psycho:
        return 60
    scores = profil_psycho.get("scores", {})
    if not scores:
        return 60
    return min(100, round(sum(scores.values()) / len(scores)))


# ── Score Motivation ──
def calculer_score_motivation(profil_etudiant, filiere_id):
    preferences   = profil_etudiant.get("preferences", {})
    interets      = preferences.get("centres_interet", [])
    ambition      = preferences.get("ambition_professionnelle", "")
    scores_interets = preferences.get("scores_interets_filieres", {})
    score_interet = scores_interets.get(filiere_id, 0)

    if score_interet >= 5:   return 90
    elif score_interet >= 3: return 75
    elif score_interet >= 1: return 60
    elif interets or ambition: return 50
    else:                    return 40


# ── Catégoriser la probabilité ──
def categoriser_probabilite(probabilite):
    if probabilite >= 80:   return "Très bonnes chances ✅"
    elif probabilite >= 60: return "Bonnes chances 👍"
    elif probabilite >= 40: return "Chances moyennes 🤔"
    elif probabilite >= 20: return "Chances faibles ⚠️"
    else:                   return "Très faibles chances ❌"


# ── Identifier Points Forts et Faibles ──
def identifier_points(
    profil_etudiant, filiere_id,
    moyenne, moyenne_admis, fitscore, fitscore_moyen
):
    points_forts   = []
    points_faibles = []

    mention         = profil_etudiant.get("parcours_academique", {}).get("mention", "")
    scores_interets = profil_etudiant.get("preferences", {}).get("scores_interets_filieres", {})

    if moyenne >= moyenne_admis * 1.1:
        points_forts.append(
            f"Moyenne {moyenne}/20 supérieure à la moyenne des admis ({moyenne_admis}/20)"
        )
    elif moyenne < moyenne_admis * 0.9:
        points_faibles.append(
            f"Moyenne {moyenne}/20 inférieure à la moyenne des admis ({moyenne_admis}/20)"
        )

    if mention in ["très_bien", "bien"]:
        points_forts.append(f"Mention {mention.replace('_', ' ')} au BAC")
    elif mention == "passable":
        points_faibles.append("Mention passable au BAC")

    if fitscore and fitscore >= fitscore_moyen:
        points_forts.append(
            f"FitScore de {fitscore}% supérieur au score moyen des admis"
        )
    elif fitscore and fitscore < fitscore_moyen * 0.85:
        points_faibles.append(
            f"FitScore de {fitscore}% inférieur au score moyen des admis ({fitscore_moyen}%)"
        )

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
    Note : La bourse réelle est basée sur le concours d'admission SUPMTI.
    """
    if moyenne_bac == 0:
        return None

    for palier in BOURSES["paliers"]:
        if palier["note_min"] <= moyenne_bac <= palier["note_max"]:
            if palier["pourcentage"] == 0:
                return {
                    "eligible": False,
                    "message":  "Pas de bourse estimée avec cette moyenne"
                }
            return {
                "eligible":    True,
                "pourcentage": palier["pourcentage"],
                "label":       palier["label"],
                "reduction":   palier["reduction"],
                "a_payer":     palier["a_payer"],
                "note":        BOURSES["note"]
            }

    return None


# ============================================================
# PARTIE 3 — CONSEILS PERSONNALISÉS
# ============================================================

def generer_conseils_admission(profil_etudiant, filiere_id, probabilite, eligible=True):
    """Génère des conseils personnalisés via GPT."""
    prenom     = profil_etudiant.get("informations_personnelles", {}).get("prenom", "")
    moyenne    = profil_etudiant.get("parcours_academique", {}).get("moyenne_generale", 0)
    type_bac   = profil_etudiant.get("parcours_academique", {}).get("type_bac", "")
    filiere_nom = FILIERES.get(filiere_id, {}).get("nom", filiere_id)

    if not eligible:
        prompt = (
            f"Étudiant{' ' + prenom if prenom else ''} : BAC {type_bac}, moyenne {moyenne}/20.\n"
            f"Non éligible pour {filiere_nom} à SUPMTI Meknès.\n\n"
            f"Donne 3 conseils courts et constructifs en tirets (- conseil).\n"
            f"FORMAT : tirets - uniquement, pas de **, pas de titres ##, max 80 mots."
        )
    else:
        prompt = (
            f"Étudiant{' ' + prenom if prenom else ''} : BAC {type_bac}, moyenne {moyenne}/20.\n"
            f"Probabilité d'admission en {filiere_nom} : {probabilite}%.\n\n"
            f"Donne 3 conseils pratiques en tirets (dossier, entretien, préparation).\n"
            f"FORMAT : tirets - uniquement, pas de **, pas de titres ##, max 80 mots."
        )

    try:
        r = client.chat.completions.create(
            model="gpt-5.2",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_completion_tokens=200
        )
        return r.choices[0].message.content.strip()

    except Exception as e:
        print(f"[ADMISSION] Erreur conseils : {e}")
        if probabilite >= 60:
            return (
                "- Prépare ton dossier avec soin (relevés de notes, lettre de motivation personnalisée)\n"
                "- Entraîne-toi pour l'entretien oral (pitch de 60 secondes, exemples concrets)\n"
                "- Renseigne-toi sur SUPMTI avant l'entretien"
            )
        return (
            "- Travaille ta moyenne et vise un meilleur résultat au concours d'admission\n"
            "- Développe des projets personnels liés à ta filière cible\n"
            "- Prépare-toi sérieusement au test écrit et à l'entretien"
        )


# ============================================================
# PARTIE 4 — RAPPORT COMPLET D'ADMISSION
# ============================================================

def generer_rapport_admission(profil_etudiant, fitscore_resultats=None):
    """
    Retourne un DICT structuré (pas une string) pour manipulation par app_web.py.
    Frontend attend : { classement:[...], conseil:"...", meilleure_chance:{...} }
    """
    prenom = profil_etudiant.get("informations_personnelles", {}).get("prenom", "")

    resultats  = calculer_probabilite_toutes_filieres(profil_etudiant, fitscore_resultats)
    classement = resultats["classement"]

    classement_clean = []
    for item in classement:
        bourse_str = None
        be = item.get("bourse_estimee")
        if be and isinstance(be, dict) and be.get("eligible"):
            bourse_str = f"{be['pourcentage']}% — {be['a_payer']:,} DH/an"

        classement_clean.append({
            "filiere_id":     item["filiere_id"],
            "filiere_nom":    item["filiere_nom"],
            "filiere_niveau": item.get("filiere_niveau", ""),
            "probabilite":    item["probabilite"],
            "categorie":      item["categorie"],
            "eligible":       item["eligible"],
            "bourse_estimee": bourse_str,
            "points_forts":   item.get("points_forts", []),
            "points_faibles": item.get("points_faibles", []),
        })

    meilleure = resultats["meilleure_chance"]
    conseil   = meilleure.get("conseils", "") if meilleure else ""

    return {
        "classement": classement_clean,
        "meilleure_chance": {
            "filiere_id":  meilleure["filiere_id"],
            "filiere_nom": meilleure["filiere_nom"],
            "probabilite": meilleure["probabilite"],
            "conseils":    conseil,
        } if meilleure else None,
        "conseil": conseil,
        "prenom":  prenom,
    }