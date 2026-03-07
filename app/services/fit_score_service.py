# ============================================================
# FIT SCORE SERVICE — SUPMTI
# FitScore AI Engine (4.6)
# Vérification d'Éligibilité (4.7)
# IA Explicable (4.23)
# Tahirou — backend-tahirou
# ============================================================

import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from app.academic_config import (
    FILIERES,
    POIDS_FITSCORE,
    POIDS_MATIERES_FILIERES,
    BONUS_MENTION,
    SEUILS_MENTION,
    CONDITIONS_ADMISSION,
    COMPATIBILITE_BAC_FILIERE,
    PROFIL_PSYCHO_FILIERE,
    INTERETS_FILIERE,
    HISTORIQUE_ADMISSION
)

# ============================================================
# INITIALISATION
# ============================================================

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ============================================================
# PARTIE 1 — CALCUL DU FITSCORE (4.6)
# ============================================================

def calculer_fitscore_complet(profil_etudiant, profil_psychometrique=None):
    """
    Calcule le FitScore pour toutes les filières SUPMTI.
    Retourne un classement complet avec scores et explications.

    profil_etudiant : résultat de construire_profil_etudiant()
    profil_psychometrique : résultat de calculer_profil_psychometrique_final()
    """
    print("[FITSCORE] Calcul du FitScore en cours...")

    resultats = {}

    for filiere_id in FILIERES.keys():
        score_details = calculer_fitscore_filiere(
            profil_etudiant,
            filiere_id,
            profil_psychometrique
        )
        resultats[filiere_id] = score_details

    # Classer les filières par score décroissant
    classement = sorted(
        resultats.items(),
        key=lambda x: x[1]["score_total"],
        reverse=True
    )

    # Construire le résultat final
    resultat_final = {
        "classement": [
            {
                "rang": i + 1,
                "filiere_id": filiere_id,
                "filiere_nom": FILIERES[filiere_id]["nom"],
                "filiere_niveau": FILIERES[filiere_id]["niveau"],
                "score_total": details["score_total"],
                "score_details": details["scores_par_critere"],
                "eligible": details["eligible"],
                "explication": details["explication"]
            }
            for i, (filiere_id, details) in enumerate(classement)
        ],
        "meilleure_filiere": classement[0][0] if classement else None,
        "profil_resume": generer_resume_profil(profil_etudiant)
    }

    print(f"[FITSCORE] ✅ Calcul terminé — Meilleure filière : {resultat_final['meilleure_filiere']}")
    return resultat_final


def calculer_fitscore_filiere(profil_etudiant, filiere_id, profil_psychometrique=None):
    """
    Calcule le FitScore pour UNE filière spécifique.
    Retourne le score détaillé avec explication.
    """
    scores = {}

    # ── CRITÈRE 1 : Compatibilité BAC (25 points) ──
    score_bac = calculer_score_bac(profil_etudiant, filiere_id)
    scores["compatibilite_bac"] = score_bac

    # ── CRITÈRE 2 : Moyenne académique (20 points) ──
    score_moyenne = calculer_score_moyenne(profil_etudiant, filiere_id)
    scores["moyenne_academique"] = score_moyenne

    # ── CRITÈRE 3 : Notes matières clés (20 points) ──
    score_matieres = calculer_score_matieres(profil_etudiant, filiere_id)
    scores["notes_matieres_cles"] = score_matieres

    # ── CRITÈRE 4 : Profil psychométrique (20 points) ──
    score_psycho = calculer_score_psychometrique(
        profil_psychometrique, filiere_id
    )
    scores["profil_psychometrique"] = score_psycho

    # ── CRITÈRE 5 : Centres d'intérêt (10 points) ──
    score_interets = calculer_score_interets(profil_etudiant, filiere_id)
    scores["centres_interet"] = score_interets

    # ── CRITÈRE 6 : Ambitions professionnelles (5 points) ──
    score_ambition = calculer_score_ambition(profil_etudiant, filiere_id)
    scores["ambitions_professionnelles"] = score_ambition

    # ── SCORE TOTAL ──
    score_total = sum(scores.values())
    score_total = min(100, round(score_total))

    # ── VÉRIFICATION ÉLIGIBILITÉ ──
    eligible, raison_ineligibilite = verifier_eligibilite(
        profil_etudiant, filiere_id
    )

    # Si non éligible, pénaliser le score
    if not eligible:
        score_total = min(score_total, 30)

    # ── EXPLICATION ──
    explication = generer_explication_score(
        profil_etudiant,
        filiere_id,
        scores,
        score_total,
        eligible,
        raison_ineligibilite
    )

    return {
        "score_total": score_total,
        "scores_par_critere": scores,
        "eligible": eligible,
        "raison_ineligibilite": raison_ineligibilite,
        "explication": explication
    }


# ── Calcul Score BAC (25 points max) ──
def calculer_score_bac(profil_etudiant, filiere_id):
    """
    Calcule le score de compatibilité BAC → Filière
    Sur 25 points
    """
    type_bac = profil_etudiant.get(
        "parcours_academique", {}
    ).get("type_bac", "AUTRE")

    compatibilites = COMPATIBILITE_BAC_FILIERE.get(type_bac, {})
    score_compatibilite = compatibilites.get(filiere_id, 3)

    # Convertir sur 25 points (score de 1 à 5 → 5 à 25)
    score = score_compatibilite * 5
    return min(25, score)


# ── Calcul Score Moyenne (20 points max) ──
def calculer_score_moyenne(profil_etudiant, filiere_id):
    """
    Calcule le score basé sur la moyenne générale
    Sur 20 points avec bonus de mention
    """
    parcours = profil_etudiant.get("parcours_academique", {})
    moyenne = float(parcours.get("moyenne_generale", 0))
    mention = parcours.get("mention", "passable")

    if moyenne == 0:
        return 10  # Score neutre si pas de moyenne

    # Score de base sur 20
    if moyenne >= 18:
        score_base = 20
    elif moyenne >= 16:
        score_base = 17
    elif moyenne >= 14:
        score_base = 14
    elif moyenne >= 12:
        score_base = 11
    elif moyenne >= 10:
        score_base = 8
    else:
        score_base = 4

    # Appliquer le bonus de mention
    bonus = BONUS_MENTION.get(mention, 0)
    score_avec_bonus = score_base * (1 + bonus / 100)

    return min(20, round(score_avec_bonus))


# ── Calcul Score Matières Clés (20 points max) ──
def calculer_score_matieres(profil_etudiant, filiere_id):
    """
    Calcule le score basé sur les notes des matières clés
    selon la pondération de la filière visée
    Sur 20 points
    """
    notes = profil_etudiant.get(
        "parcours_academique", {}
    ).get("notes_matieres", {})

    forces = profil_etudiant.get("forces_academiques", {})
    poids_filiere = POIDS_MATIERES_FILIERES.get(filiere_id, {})

    if not notes and not forces:
        return 10  # Score neutre

    score_total = 0
    poids_total = 0

    # Utiliser les notes réelles si disponibles
    if notes:
        for matiere, poids in poids_filiere.items():
            note_trouvee = None

            # Chercher la note de la matière
            for nom_matiere, note in notes.items():
                if matiere.lower() in nom_matiere.lower() or \
                   nom_matiere.lower() in matiere.lower():
                    note_trouvee = float(note)
                    break

            if note_trouvee is not None:
                score_matiere = (note_trouvee / 20) * poids
                score_total += score_matiere
                poids_total += poids

    # Compléter avec les forces du BAC si notes insuffisantes
    if poids_total < 50:
        for matiere, poids in poids_filiere.items():
            matiere_lower = matiere.lower()
            force = 3  # valeur par défaut

            if "math" in matiere_lower:
                force = forces.get("force_maths", 3)
            elif "physique" in matiere_lower:
                force = forces.get("force_physique", 3)
            elif "info" in matiere_lower:
                force = forces.get("force_info", 2)
            elif "econom" in matiere_lower or "gestion" in matiere_lower:
                force = forces.get("force_economie", 2)
            elif "droit" in matiere_lower:
                force = forces.get("force_gestion", 2)

            score_force = (force / 5) * poids
            score_total += score_force * 0.5
            poids_total += poids * 0.5

    if poids_total == 0:
        return 10

    score_final = (score_total / poids_total) * 20
    return min(20, round(score_final))


# ── Calcul Score Psychométrique (20 points max) ──
def calculer_score_psychometrique(profil_psychometrique, filiere_id):
    """
    Calcule la compatibilité psychologique avec la filière
    Sur 20 points
    """
    if not profil_psychometrique:
        return 10  # Score neutre si pas de test

    compatibilite = profil_psychometrique.get(
        "compatibilite_filieres", {}
    ).get(filiere_id, 50)

    # Convertir de % (0-100) vers points (0-20)
    score = (compatibilite / 100) * 20
    return min(20, round(score))


# ── Calcul Score Intérêts (10 points max) ──
def calculer_score_interets(profil_etudiant, filiere_id):
    """
    Calcule la compatibilité des centres d'intérêt avec la filière
    Sur 10 points
    """
    scores_interets = profil_etudiant.get(
        "preferences", {}
    ).get("scores_interets_filieres", {})

    score_brut = scores_interets.get(filiere_id, 0)
    mots_cles_filiere = INTERETS_FILIERE.get(filiere_id, [])

    if not mots_cles_filiere:
        return 5

    # Normaliser sur 10 points
    max_possible = len(mots_cles_filiere)
    score = min(10, round((score_brut / max(max_possible, 1)) * 10))

    # Score minimum de 3 si aucun intérêt déclaré
    return max(3, score)


# ── Calcul Score Ambition (5 points max) ──
def calculer_score_ambition(profil_etudiant, filiere_id):
    """
    Calcule la compatibilité des ambitions professionnelles
    Sur 5 points
    """
    ambition = profil_etudiant.get(
        "preferences", {}
    ).get("ambition_professionnelle", "").lower()

    if not ambition:
        return 3

    debouches = [
        d.lower() for d in FILIERES.get(filiere_id, {}).get("debouches", [])
    ]

    mots_ambition = ambition.split()
    correspondances = sum(
        1 for mot in mots_ambition
        if any(mot in debouche for debouche in debouches)
    )

    if correspondances >= 3:
        return 5
    elif correspondances >= 2:
        return 4
    elif correspondances >= 1:
        return 3
    else:
        return 2


# ============================================================
# PARTIE 2 — VÉRIFICATION D'ÉLIGIBILITÉ (4.7)
# ============================================================

def verifier_eligibilite(profil_etudiant, filiere_id):
    """
    Vérifie si l'étudiant est éligible pour une filière.
    Retourne (eligible: bool, raison: str)
    """
    parcours = profil_etudiant.get("parcours_academique", {})
    type_bac = parcours.get("type_bac", "AUTRE")
    moyenne = float(parcours.get("moyenne_generale", 0))
    niveau = parcours.get("niveau_actuel", "post_bac")
    diplome = parcours.get("diplome_actuel", None)

    # ── Vérification selon le niveau actuel ──
    if niveau == "post_bac":
        return verifier_eligibilite_1ere_annee(
            type_bac, moyenne, filiere_id
        )
    elif niveau == "bac2":
        return verifier_eligibilite_3eme_annee(
            diplome, moyenne, filiere_id
        )
    elif niveau == "bac3":
        return verifier_eligibilite_4eme_annee(
            diplome, moyenne, filiere_id
        )
    else:
        return True, None


def verifier_eligibilite_1ere_annee(type_bac, moyenne, filiere_id):
    """
    Vérifie l'éligibilité pour une admission en 1ère année
    """
    conditions = CONDITIONS_ADMISSION.get("1ere_annee", {}).get(filiere_id, {})

    if not conditions:
        return True, None

    # Vérifier le type de BAC
    bac_requis = conditions.get("bac_requis", [])
    if bac_requis and type_bac not in bac_requis:
        type_requis = conditions.get("type_requis", [])
        return False, f"Ton BAC {type_bac} n'est pas dans la liste des BAC acceptés pour {filiere_id}. {conditions.get('description', '')}"

    # Vérifier la moyenne minimale
    moyenne_min = conditions.get("moyenne_min", 10)
    if moyenne > 0 and moyenne < moyenne_min:
        return False, f"Ta moyenne ({moyenne}/20) est inférieure à la moyenne minimale requise ({moyenne_min}/20) pour {filiere_id}."

    return True, None


def verifier_eligibilite_3eme_annee(diplome, moyenne, filiere_id):
    """
    Vérifie l'éligibilité pour une admission en 3ème année
    """
    conditions = CONDITIONS_ADMISSION.get("3eme_annee", {})
    moyenne_min = conditions.get("moyenne_min", 12)

    if moyenne > 0 and moyenne < moyenne_min:
        return False, f"Ta moyenne ({moyenne}/20) est inférieure au minimum requis ({moyenne_min}/20) pour l'admission en 3ème année."

    diplomes_compatibles = conditions.get(
        "filieres_compatibles", {}
    ).get(filiere_id, [])

    if diplome and diplomes_compatibles:
        diplome_lower = diplome.lower()
        compatible = any(
            d.lower() in diplome_lower or diplome_lower in d.lower()
            for d in diplomes_compatibles
        )
        if not compatible:
            return False, f"Ton diplôme '{diplome}' n'est pas dans la liste des diplômes compatibles pour {filiere_id} en 3ème année."

    return True, None


def verifier_eligibilite_4eme_annee(diplome, moyenne, filiere_id):
    """
    Vérifie l'éligibilité pour une admission en 4ème année
    """
    conditions = CONDITIONS_ADMISSION.get("4eme_annee", {})
    moyenne_min = conditions.get("moyenne_min", 12)

    if moyenne > 0 and moyenne < moyenne_min:
        return False, f"Ta moyenne ({moyenne}/20) est inférieure au minimum requis ({moyenne_min}/20) pour l'admission en 4ème année."

    diplomes_compatibles = conditions.get(
        "filieres_compatibles", {}
    ).get(filiere_id, [])

    if diplome and diplomes_compatibles:
        diplome_lower = diplome.lower()
        compatible = any(
            d.lower() in diplome_lower or diplome_lower in d.lower()
            for d in diplomes_compatibles
        )
        if not compatible:
            return False, f"Ton diplôme '{diplome}' n'est pas dans la liste des diplômes compatibles pour {filiere_id} en 4ème année."

    return True, None


def proposer_alternatives(profil_etudiant, filiere_refusee):
    """
    Propose des filières alternatives si l'étudiant
    n'est pas éligible pour sa filière souhaitée
    """
    resultats = calculer_fitscore_complet(profil_etudiant)
    alternatives = []

    for item in resultats["classement"]:
        if item["filiere_id"] != filiere_refusee and item["eligible"]:
            alternatives.append({
                "filiere_id": item["filiere_id"],
                "filiere_nom": item["filiere_nom"],
                "score": item["score_total"],
                "niveau": item["filiere_niveau"]
            })

    return alternatives[:3]  # Top 3 alternatives


# ============================================================
# PARTIE 3 — IA EXPLICABLE (4.23)
# ============================================================

def generer_explication_score(
    profil_etudiant,
    filiere_id,
    scores,
    score_total,
    eligible,
    raison_ineligibilite
):
    """
    Génère une explication claire et personnalisée du FitScore
    """
    filiere = FILIERES.get(filiere_id, {})
    prenom = profil_etudiant.get(
        "informations_personnelles", {}
    ).get("prenom", "")
    type_bac = profil_etudiant.get(
        "parcours_academique", {}
    ).get("type_bac", "")
    moyenne = profil_etudiant.get(
        "parcours_academique", {}
    ).get("moyenne_generale", 0)

    points_forts = []
    points_faibles = []

    if scores.get("compatibilite_bac", 0) >= 20:
        points_forts.append(f"ton BAC {type_bac} est très compatible avec cette filière")
    elif scores.get("compatibilite_bac", 0) <= 10:
        points_faibles.append(f"ton BAC {type_bac} est peu orienté vers cette filière")

    if scores.get("moyenne_academique", 0) >= 15:
        points_forts.append(f"ta moyenne de {moyenne}/20 est excellente")
    elif scores.get("moyenne_academique", 0) <= 8:
        points_faibles.append(f"ta moyenne de {moyenne}/20 est en dessous des attentes")

    if scores.get("centres_interet", 0) >= 7:
        points_forts.append("tes centres d'intérêt correspondent bien à cette filière")
    elif scores.get("centres_interet", 0) <= 4:
        points_faibles.append("tes centres d'intérêt semblent peu orientés vers cette filière")

    if scores.get("profil_psychometrique", 0) >= 15:
        points_forts.append("ton profil psychologique est bien adapté à cette filière")

    explication = {
        "score": score_total,
        "eligible": eligible,
        "points_forts": points_forts,
        "points_faibles": points_faibles,
        "raison_ineligibilite": raison_ineligibilite
    }

    return explication


def generer_rapport_fitscore(resultats_fitscore, profil_etudiant):
    """
    Génère un rapport complet et lisible du FitScore
    avec explications naturelles via GPT
    """
    prenom = profil_etudiant.get(
        "informations_personnelles", {}
    ).get("prenom", "")

    classement = resultats_fitscore["classement"]
    top3 = classement[:3]

    # Construire le résumé pour GPT
    resume_scores = "\n".join([
        f"- {item['rang']}. {item['filiere_nom']} ({item['filiere_niveau']}) : "
        f"{item['score_total']}% | Éligible: {'Oui' if item['eligible'] else 'Non'}"
        for item in classement
    ])

    prompt = f"""Tu es Sami, conseiller académique de SUPMTI Meknès.
Génère un rapport d'orientation personnalisé et chaleureux.

Étudiant : {prenom if prenom else 'un étudiant'}
BAC : {profil_etudiant.get('parcours_academique', {}).get('type_bac', 'inconnu')}
Moyenne : {profil_etudiant.get('parcours_academique', {}).get('moyenne_generale', 'inconnue')}/20

Scores FitScore :
{resume_scores}

Génère un rapport qui :
1. Annonce la meilleure filière recommandée avec enthousiasme
2. Explique pourquoi cette filière correspond au profil (2-3 raisons)
3. Mentionne la 2ème et 3ème option brièvement
4. Encourage l'étudiant
5. Utilise des emojis appropriés

Style : chaleureux, encourageant, naturel. Max 250 mots."""

    try:
        reponse_gpt = client.chat.completions.create(
            model="gpt-5.2",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_completion_tokens=500
        )

        return reponse_gpt.choices[0].message.content.strip()

    except Exception as e:
        print(f"[FITSCORE] Erreur génération rapport : {e}")

        top1 = classement[0] if classement else None
        if not top1:
            return "Je n'ai pas pu calculer ton FitScore. Réessaie plus tard."

        return f"""🎯 **Ton orientation personnalisée {prenom} :**

🥇 **{top1['filiere_nom']}** — Score : {top1['score_total']}%
{'✅ Tu es éligible !' if top1['eligible'] else '⚠️ Conditions d\'admission à vérifier'}

{f"🥈 **{classement[1]['filiere_nom']}** — {classement[1]['score_total']}%" if len(classement) > 1 else ""}
{f"🥉 **{classement[2]['filiere_nom']}** — {classement[2]['score_total']}%" if len(classement) > 2 else ""}

Ces résultats sont basés sur ton profil académique et tes centres d'intérêt."""


def generer_resume_profil(profil_etudiant):
    """
    Génère un résumé court du profil étudiant
    """
    parcours = profil_etudiant.get("parcours_academique", {})
    infos = profil_etudiant.get("informations_personnelles", {})

    return {
        "prenom": infos.get("prenom", ""),
        "bac": parcours.get("type_bac", ""),
        "moyenne": parcours.get("moyenne_generale", 0),
        "mention": parcours.get("mention", ""),
        "niveau": parcours.get("niveau_actuel", "post_bac")
    }
