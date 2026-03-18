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

    profil_etudiant      : résultat de construire_profil_etudiant()
    profil_psychometrique: résultat de calculer_profil_psychometrique_final()
                           (optionnel — score neutre si absent)
    """
    print("[FITSCORE] Calcul du FitScore en cours...")

    resultats = {}
    for filiere_id in FILIERES.keys():
        score_details = calculer_fitscore_filiere(
            profil_etudiant, filiere_id, profil_psychometrique
        )
        resultats[filiere_id] = score_details

    classement = sorted(
        resultats.items(),
        key=lambda x: x[1]["score_total"],
        reverse=True
    )

    resultat_final = {
        "classement": [
            {
                "rang":            i + 1,
                "filiere_id":      filiere_id,
                "filiere_nom":     FILIERES[filiere_id]["nom"],
                "filiere_niveau":  FILIERES[filiere_id]["niveau"],
                "score_total":     details["score_total"],
                "score":           details["score_total"],   # alias frontend
                "nom":             FILIERES[filiere_id]["nom"],    # alias frontend
                "niveau":          FILIERES[filiere_id]["niveau"], # alias frontend
                "score_details":   details["scores_par_critere"],
                "eligible":        details["eligible"],
                "explication":     details["explication"]
            }
            for i, (filiere_id, details) in enumerate(classement)
        ],
        "meilleure_filiere": classement[0][0] if classement else None,
        "profil_resume":     generer_resume_profil(profil_etudiant)
    }

    print(f"[FITSCORE] ✅ Calcul terminé — Meilleure filière : {resultat_final['meilleure_filiere']}")
    return resultat_final


def calculer_fitscore_filiere(profil_etudiant, filiere_id, profil_psychometrique=None):
    """Calcule le FitScore pour UNE filière spécifique."""
    scores = {}

    scores["compatibilite_bac"]     = calculer_score_bac(profil_etudiant, filiere_id)
    scores["moyenne_academique"]     = calculer_score_moyenne(profil_etudiant, filiere_id)
    scores["notes_matieres_cles"]    = calculer_score_matieres(profil_etudiant, filiere_id)
    scores["profil_psychometrique"]  = calculer_score_psychometrique(profil_psychometrique, filiere_id)
    scores["centres_interet"]        = calculer_score_interets(profil_etudiant, filiere_id)
    scores["ambitions_professionnelles"] = calculer_score_ambition(profil_etudiant, filiere_id)

    score_total = min(100, round(sum(scores.values())))

    eligible, raison_ineligibilite = verifier_eligibilite(profil_etudiant, filiere_id)
    if not eligible:
        score_total = min(score_total, 30)

    explication = generer_explication_score(
        profil_etudiant, filiere_id, scores,
        score_total, eligible, raison_ineligibilite
    )

    return {
        "score_total":           score_total,
        "scores_par_critere":    scores,
        "eligible":              eligible,
        "raison_ineligibilite":  raison_ineligibilite,
        "explication":           explication
    }


# ── Score BAC (25 points max) ──
def calculer_score_bac(profil_etudiant, filiere_id):
    type_bac        = profil_etudiant.get("parcours_academique", {}).get("type_bac", "AUTRE")
    compatibilites  = COMPATIBILITE_BAC_FILIERE.get(type_bac, {})
    score_compat    = compatibilites.get(filiere_id, 3)
    return min(25, score_compat * 5)


# ── Score Moyenne (20 points max) ──
def calculer_score_moyenne(profil_etudiant, filiere_id):
    parcours = profil_etudiant.get("parcours_academique", {})
    moyenne  = float(parcours.get("moyenne_generale", 0))
    mention  = parcours.get("mention", "passable")

    if moyenne == 0:
        return 10

    if moyenne >= 18:   score_base = 20
    elif moyenne >= 16: score_base = 17
    elif moyenne >= 14: score_base = 14
    elif moyenne >= 12: score_base = 11
    elif moyenne >= 10: score_base = 8
    else:               score_base = 4

    bonus = BONUS_MENTION.get(mention, 0)
    return min(20, round(score_base * (1 + bonus / 100)))


# ── Score Matières Clés (20 points max) ──
def calculer_score_matieres(profil_etudiant, filiere_id):
    notes         = profil_etudiant.get("parcours_academique", {}).get("notes_matieres", {})
    forces        = profil_etudiant.get("forces_academiques", {})
    poids_filiere = POIDS_MATIERES_FILIERES.get(filiere_id, {})

    if not notes and not forces:
        return 10

    score_total = 0
    poids_total = 0

    if notes:
        for matiere, poids in poids_filiere.items():
            note_trouvee = None
            for nom_matiere, note in notes.items():
                if (matiere.lower() in nom_matiere.lower()
                        or nom_matiere.lower() in matiere.lower()):
                    note_trouvee = float(note)
                    break
            if note_trouvee is not None:
                score_total += (note_trouvee / 20) * poids
                poids_total += poids

    if poids_total < 50:
        for matiere, poids in poids_filiere.items():
            matiere_lower = matiere.lower()
            force = 3
            if "math"   in matiere_lower: force = forces.get("force_maths", 3)
            elif "physi" in matiere_lower: force = forces.get("force_physique", 3)
            elif "info"  in matiere_lower: force = forces.get("force_info", 2)
            elif "econom" in matiere_lower or "gestion" in matiere_lower:
                force = forces.get("force_economie", 2)
            elif "droit" in matiere_lower: force = forces.get("force_gestion", 2)

            score_total += (force / 5) * poids * 0.5
            poids_total += poids * 0.5

    if poids_total == 0:
        return 10
    return min(20, round((score_total / poids_total) * 20))


# ── Score Psychométrique (20 points max) ──
def calculer_score_psychometrique(profil_psychometrique, filiere_id):
    if not profil_psychometrique:
        return 10
    compatibilite = profil_psychometrique.get(
        "compatibilite_filieres", {}
    ).get(filiere_id, 50)
    return min(20, round((compatibilite / 100) * 20))


# ── Score Intérêts (10 points max) ──
def calculer_score_interets(profil_etudiant, filiere_id):
    scores_interets   = profil_etudiant.get("preferences", {}).get("scores_interets_filieres", {})
    score_brut        = scores_interets.get(filiere_id, 0)
    mots_cles_filiere = INTERETS_FILIERE.get(filiere_id, [])

    if not mots_cles_filiere:
        return 5

    score = min(10, round((score_brut / max(len(mots_cles_filiere), 1)) * 10))
    return max(3, score)


# ── Score Ambition (5 points max) ──
def calculer_score_ambition(profil_etudiant, filiere_id):
    ambition = profil_etudiant.get("preferences", {}).get("ambition_professionnelle", "").lower()
    if not ambition:
        return 3
    debouches      = [d.lower() for d in FILIERES.get(filiere_id, {}).get("debouches", [])]
    mots_ambition  = ambition.split()
    correspondances = sum(
        1 for mot in mots_ambition if any(mot in d for d in debouches)
    )
    if correspondances >= 3:   return 5
    elif correspondances >= 2: return 4
    elif correspondances >= 1: return 3
    else:                      return 2


# ============================================================
# PARTIE 2 — VÉRIFICATION D'ÉLIGIBILITÉ (4.7)
# ============================================================

def verifier_eligibilite(profil_etudiant, filiere_id):
    """
    Vérifie si l'étudiant est éligible pour une filière.
    Retourne (eligible: bool, raison: str|None)

    RÈGLE STRICTE niveau ↔ cycle filière :
    - post_bac / bac1 → UNIQUEMENT BAC+3 (IISI, MGE, MDI)
    - bac2            → UNIQUEMENT BAC+3 selon spécialité
    - bac3            → UNIQUEMENT BAC+5 selon spécialité
    - niveau vide     → pas de blocage (profil incomplet)
    """
    parcours = profil_etudiant.get("parcours_academique", {})
    type_bac = parcours.get("type_bac", "AUTRE")
    moyenne  = float(parcours.get("moyenne_generale", 0))
    niveau   = parcours.get("niveau_actuel", "")
    diplome  = parcours.get("diplome_actuel", None)

    # Niveau non déclaré → on ne bloque pas
    if not niveau:
        return True, None

    # Récupérer le cycle de la filière (BAC+3 ou BAC+5)
    filiere_niv = FILIERES.get(filiere_id, {}).get("niveau", "")

    if niveau in ("post_bac", "bac1"):
        # Bacheliers → UNIQUEMENT les filières BAC+3
        if filiere_niv == "BAC+5":
            return False, (
                f"{filiere_id} est un cycle BAC+5 accessible après le BAC+3. "
                f"En tant que bachelier, tu intègres IISI, MGE ou MDI (BAC+3) d'abord."
            )
        return verifier_eligibilite_1ere_annee(type_bac, moyenne, filiere_id)

    elif niveau == "bac2":
        # BAC+2 → UNIQUEMENT les filières BAC+3
        if filiere_niv == "BAC+5":
            return False, (
                f"{filiere_id} est un cycle BAC+5. "
                f"Avec un BAC+2, tu intègres en 3ème année de IISI, MGE ou MDI."
            )
        return verifier_eligibilite_3eme_annee(diplome, moyenne, filiere_id)

    elif niveau == "bac3":
        # BAC+3 → UNIQUEMENT les filières BAC+5
        if filiere_niv == "BAC+3":
            return False, (
                f"{filiere_id} est un cycle BAC+3. "
                f"Avec un BAC+3, tu intègres directement les filières BAC+5 (IISIC, IISRT, FACG, MRI)."
            )
        return verifier_eligibilite_4eme_annee(diplome, moyenne, filiere_id)

    else:
        return True, None


def verifier_eligibilite_1ere_annee(type_bac, moyenne, filiere_id):
    conditions  = CONDITIONS_ADMISSION.get("1ere_annee", {}).get(filiere_id, {})
    if not conditions:
        return True, None

    bac_requis = conditions.get("bac_requis", [])
    if bac_requis and type_bac not in bac_requis:
        return False, (
            f"Ton BAC {type_bac} n'est pas dans la liste des BAC acceptés pour {filiere_id}. "
            f"{conditions.get('description', '')}"
        )

    moyenne_min = conditions.get("moyenne_min", 10)
    if moyenne > 0 and moyenne < moyenne_min:
        return False, (
            f"Ta moyenne ({moyenne}/20) est inférieure au minimum requis "
            f"({moyenne_min}/20) pour {filiere_id}."
        )

    return True, None


def verifier_eligibilite_3eme_annee(diplome, moyenne, filiere_id):
    conditions  = CONDITIONS_ADMISSION.get("3eme_annee", {})
    moyenne_min = conditions.get("moyenne_min", 12)

    if moyenne > 0 and moyenne < moyenne_min:
        return False, (
            f"Ta moyenne ({moyenne}/20) est inférieure au minimum requis "
            f"({moyenne_min}/20) pour l'admission en 3ème année."
        )

    diplomes_compatibles = conditions.get("filieres_compatibles", {}).get(filiere_id, [])
    if diplome and diplomes_compatibles:
        diplome_lower = diplome.lower()

        # Correspondance exacte d'abord
        compatible = any(
            d.lower() in diplome_lower or diplome_lower in d.lower()
            for d in diplomes_compatibles
        )

        if not compatible:
            # Correspondance flexible par domaine — liste exhaustive
            tech_kw = [
                "info", "informatique", "réseau", "reseau", "cyber", "securite",
                "sécurité", "telecom", "système", "systeme", "tech", "numérique",
                "numerique", "électronique", "electronique", "ingénierie", "ingenierie",
                "web", "dev", "développement", "developpement", "mobile", "cloud",
                "data", "ia", "intelligence", "artificielle", "machine", "learning",
                "logiciel", "software", "appli", "programmation", "digital", "code",
                "iot", "embarqué", "embarque", "python", "java", "sql", "linux",
            ]
            gestion_kw = [
                "gestion", "management", "économie", "economie", "commerce",
                "finance", "comptabilit", "iscae", "marketing", "business",
                "administration", "entreprise", "audit", "rh", "ressources",
                "international", "export", "import", "juridique", "droit",
                "fiscal", "bancaire", "assurance",
            ]
            if filiere_id == "IISI":
                compatible = any(k in diplome_lower for k in tech_kw)
            elif filiere_id in ("MGE", "MDI"):
                compatible = any(k in diplome_lower for k in gestion_kw)
                # SMA/SMB avec une formation tech → compatible aussi avec IISI
                if not compatible:
                    compatible = any(k in diplome_lower for k in tech_kw)

        if not compatible:
            return False, (
                f"Ton diplôme '{diplome}' ne semble pas aligné avec {filiere_id}. "
                f"Étude de dossier recommandée — contacte SUPMTI."
            )

    return True, None


def verifier_eligibilite_4eme_annee(diplome, moyenne, filiere_id):
    conditions  = CONDITIONS_ADMISSION.get("4eme_annee", {})
    moyenne_min = conditions.get("moyenne_min", 12)

    if moyenne > 0 and moyenne < moyenne_min:
        return False, (
            f"Ta moyenne ({moyenne}/20) est inférieure au minimum requis "
            f"({moyenne_min}/20) pour l'admission en 4ème année."
        )

    diplomes_compatibles = conditions.get("filieres_compatibles", {}).get(filiere_id, [])
    if diplome and diplomes_compatibles:
        diplome_lower = diplome.lower()

        # Correspondance exacte d'abord
        compatible = any(
            d.lower() in diplome_lower or diplome_lower in d.lower()
            for d in diplomes_compatibles
        )

        if not compatible:
            # Correspondance flexible — liste étendue couvrant tous les cas réels
            tech_kw = [
                "info", "informatique", "réseau", "reseau", "cyber", "securite",
                "sécurité", "telecom", "système", "systeme", "tech", "numérique",
                "numerique", "électronique", "electronique", "ingénierie", "ingenierie",
                "web", "dev", "développement", "developpement", "mobile", "cloud",
                "data", "ia", "intelligence", "artificielle", "machine", "learning",
                "logiciel", "software", "appli", "programmation", "digital", "code",
                "iot", "embarqué", "embarque", "python", "java", "sql", "linux",
            ]
            gestion_kw = [
                "gestion", "management", "économie", "economie", "commerce",
                "finance", "comptabilit", "iscae", "marketing", "business",
                "administration", "entreprise", "audit", "rh", "ressources",
                "international", "export", "import", "juridique", "droit",
                "fiscal", "bancaire", "assurance",
            ]

            if filiere_id in ("IISIC", "IISRT"):
                compatible = any(k in diplome_lower for k in tech_kw)
            elif filiere_id in ("FACG", "MRI"):
                compatible = any(k in diplome_lower for k in gestion_kw)

        if not compatible:
            return False, (
                f"Ton diplôme '{diplome}' ne semble pas aligné avec {filiere_id}. "
                f"Étude de dossier recommandée — contacte SUPMTI."
            )

    return True, None


def proposer_alternatives(profil_etudiant, filiere_refusee):
    resultats    = calculer_fitscore_complet(profil_etudiant)
    alternatives = []
    for item in resultats["classement"]:
        if item["filiere_id"] != filiere_refusee and item["eligible"]:
            alternatives.append({
                "filiere_id":  item["filiere_id"],
                "filiere_nom": item["filiere_nom"],
                "score":       item["score_total"],
                "niveau":      item["filiere_niveau"]
            })
    return alternatives[:3]


# ============================================================
# PARTIE 3 — IA EXPLICABLE (4.23)
# ============================================================

def generer_explication_score(
    profil_etudiant, filiere_id, scores, score_total, eligible, raison_ineligibilite
):
    type_bac = profil_etudiant.get("parcours_academique", {}).get("type_bac", "")
    moyenne  = profil_etudiant.get("parcours_academique", {}).get("moyenne_generale", 0)

    points_forts  = []
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

    return {
        "score":                 score_total,
        "eligible":              eligible,
        "points_forts":          points_forts,
        "points_faibles":        points_faibles,
        "raison_ineligibilite":  raison_ineligibilite
    }


def generer_rapport_fitscore(resultats_fitscore, profil_etudiant):
    """Génère un rapport complet et lisible du FitScore via GPT."""
    prenom    = profil_etudiant.get("informations_personnelles", {}).get("prenom", "")
    classement = resultats_fitscore["classement"]

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

FORMAT OBLIGATOIRE :
- ## pour les titres (ex: ## Filière recommandée)
- **texte** pour les données importantes
- - tirets pour les listes
- Jamais de : •, ►, ════, ─────, ####

Génère un rapport qui :
1. Annonce la meilleure filière avec ## et enthousiasme
2. Explique pourquoi cette filière correspond (2-3 raisons en tirets)
3. Mentionne les 2ème et 3ème options brièvement
4. Encourage l'étudiant (1-2 phrases)
Max 200 mots."""

    try:
        r = client.chat.completions.create(
            model="gpt-5.2",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_completion_tokens=500
        )
        return r.choices[0].message.content.strip()

    except Exception as e:
        print(f"[FITSCORE] Erreur génération rapport : {e}")
        top1 = classement[0] if classement else None
        if not top1:
            return "Je n'ai pas pu calculer ton FitScore. Réessaie plus tard."

        elig_msg = "✅ Éligible" if top1['eligible'] else "📋 Dossier à étudier (critères à renforcer)"
        ligne2 = f"- {classement[1]['filiere_nom']} — **{classement[1]['score_total']}%**\n" if len(classement) > 1 else ""
        ligne3 = f"- {classement[2]['filiere_nom']} — **{classement[2]['score_total']}%**\n" if len(classement) > 2 else ""
        return (
            f"## Ton orientation personnalisée\n\n"
            f"**Filière recommandée : {top1['filiere_nom']}**\n"
            f"Score de compatibilité : **{top1['score_total']}%** — {elig_msg}\n\n"
            f"## Autres options\n"
            + ligne2
            + ligne3
            + "\nCes résultats sont basés sur ton profil académique et tes centres d'intérêt."
        )


def generer_resume_profil(profil_etudiant):
    """
    Génère un résumé court du profil étudiant.
    FIX : niveau default '' au lieu de 'post_bac' — cohérence avec profile_service.
    """
    parcours = profil_etudiant.get("parcours_academique", {})
    infos    = profil_etudiant.get("informations_personnelles", {})
    return {
        "prenom":  infos.get("prenom", ""),
        "bac":     parcours.get("type_bac", ""),
        "moyenne": parcours.get("moyenne_generale", 0),
        "mention": parcours.get("mention", ""),
        "niveau":  parcours.get("niveau_actuel", "")   # FIX : default "" pas "post_bac"
    }