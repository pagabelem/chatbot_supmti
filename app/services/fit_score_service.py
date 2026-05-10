# # ============================================================
# # FIT SCORE SERVICE — SUPMTI
# # FitScore AI Engine (4.6)
# # Vérification d'Éligibilité (4.7)
# # IA Explicable (4.23)
# # Tahirou — backend-tahirou
# # ============================================================

# import os
# import json
# from openai import OpenAI
# from dotenv import load_dotenv
# from app.academic_config import (
#     FILIERES,
#     POIDS_FITSCORE,
#     POIDS_MATIERES_FILIERES,
#     BONUS_MENTION,
#     SEUILS_MENTION,
#     CONDITIONS_ADMISSION,
#     COMPATIBILITE_BAC_FILIERE,
#     PROFIL_PSYCHO_FILIERE,
#     INTERETS_FILIERE,
#     HISTORIQUE_ADMISSION
# )

# # ============================================================
# # INITIALISATION
# # ============================================================

# load_dotenv()
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# # ============================================================
# # PARTIE 1 — CALCUL DU FITSCORE (4.6)
# # ============================================================

# def calculer_fitscore_complet(profil_etudiant, profil_psychometrique=None):
#     """
#     Calcule le FitScore pour toutes les filières SUPMTI.
#     Retourne un classement complet avec scores et explications.

#     profil_etudiant : résultat de construire_profil_etudiant()
#     profil_psychometrique : résultat de calculer_profil_psychometrique_final()
#     """
#     print("[FITSCORE] Calcul du FitScore en cours...")

#     resultats = {}

#     for filiere_id in FILIERES.keys():
#         score_details = calculer_fitscore_filiere(
#             profil_etudiant,
#             filiere_id,
#             profil_psychometrique
#         )
#         resultats[filiere_id] = score_details

#     # Classer les filières par score décroissant
#     classement = sorted(
#         resultats.items(),
#         key=lambda x: x[1]["score_total"],
#         reverse=True
#     )

#     # Construire le résultat final
#     resultat_final = {
#         "classement": [
#             {
#                 "rang": i + 1,
#                 "filiere_id": filiere_id,
#                 "filiere_nom": FILIERES[filiere_id]["nom"],
#                 "filiere_niveau": FILIERES[filiere_id]["niveau"],
#                 "score_total": details["score_total"],
#                 "score_details": details["scores_par_critere"],
#                 "eligible": details["eligible"],
#                 "explication": details["explication"]
#             }
#             for i, (filiere_id, details) in enumerate(classement)
#         ],
#         "meilleure_filiere": classement[0][0] if classement else None,
#         "profil_resume": generer_resume_profil(profil_etudiant)
#     }

#     print(f"[FITSCORE] ✅ Calcul terminé — Meilleure filière : {resultat_final['meilleure_filiere']}")
#     return resultat_final


# def calculer_fitscore_filiere(profil_etudiant, filiere_id, profil_psychometrique=None):
#     """
#     Calcule le FitScore pour UNE filière spécifique.
#     Retourne le score détaillé avec explication.
#     """
#     scores = {}

#     # ── CRITÈRE 1 : Compatibilité BAC (25 points) ──
#     score_bac = calculer_score_bac(profil_etudiant, filiere_id)
#     scores["compatibilite_bac"] = score_bac

#     # ── CRITÈRE 2 : Moyenne académique (20 points) ──
#     score_moyenne = calculer_score_moyenne(profil_etudiant, filiere_id)
#     scores["moyenne_academique"] = score_moyenne

#     # ── CRITÈRE 3 : Notes matières clés (20 points) ──
#     score_matieres = calculer_score_matieres(profil_etudiant, filiere_id)
#     scores["notes_matieres_cles"] = score_matieres

#     # ── CRITÈRE 4 : Profil psychométrique (20 points) ──
#     score_psycho = calculer_score_psychometrique(
#         profil_psychometrique, filiere_id
#     )
#     scores["profil_psychometrique"] = score_psycho

#     # ── CRITÈRE 5 : Centres d'intérêt (10 points) ──
#     score_interets = calculer_score_interets(profil_etudiant, filiere_id)
#     scores["centres_interet"] = score_interets

#     # ── CRITÈRE 6 : Ambitions professionnelles (5 points) ──
#     score_ambition = calculer_score_ambition(profil_etudiant, filiere_id)
#     scores["ambitions_professionnelles"] = score_ambition

#     # ── SCORE TOTAL ──
#     score_total = sum(scores.values())
#     score_total = min(100, round(score_total))

#     # ── VÉRIFICATION ÉLIGIBILITÉ ──
#     eligible, raison_ineligibilite = verifier_eligibilite(
#         profil_etudiant, filiere_id
#     )

#     # Si non éligible, pénaliser le score
#     if not eligible:
#         score_total = min(score_total, 30)

#     # ── EXPLICATION ──
#     explication = generer_explication_score(
#         profil_etudiant,
#         filiere_id,
#         scores,
#         score_total,
#         eligible,
#         raison_ineligibilite
#     )

#     return {
#         "score_total": score_total,
#         "scores_par_critere": scores,
#         "eligible": eligible,
#         "raison_ineligibilite": raison_ineligibilite,
#         "explication": explication
#     }


# # ── Calcul Score BAC (25 points max) ──
# def calculer_score_bac(profil_etudiant, filiere_id):
#     """
#     Calcule le score de compatibilité BAC → Filière
#     Sur 25 points
#     """
#     type_bac = profil_etudiant.get(
#         "parcours_academique", {}
#     ).get("type_bac", "AUTRE")

#     compatibilites = COMPATIBILITE_BAC_FILIERE.get(type_bac, {})
#     score_compatibilite = compatibilites.get(filiere_id, 3)

#     # Convertir sur 25 points (score de 1 à 5 → 5 à 25)
#     score = score_compatibilite * 5
#     return min(25, score)


# # ── Calcul Score Moyenne (20 points max) ──
# def calculer_score_moyenne(profil_etudiant, filiere_id):
#     """
#     Calcule le score basé sur la moyenne générale
#     Sur 20 points avec bonus de mention
#     """
#     parcours = profil_etudiant.get("parcours_academique", {})
#     moyenne = float(parcours.get("moyenne_generale", 0))
#     mention = parcours.get("mention", "passable")

#     if moyenne == 0:
#         return 10  # Score neutre si pas de moyenne

#     # Score de base sur 20
#     if moyenne >= 18:
#         score_base = 20
#     elif moyenne >= 16:
#         score_base = 17
#     elif moyenne >= 14:
#         score_base = 14
#     elif moyenne >= 12:
#         score_base = 11
#     elif moyenne >= 10:
#         score_base = 8
#     else:
#         score_base = 4

#     # Appliquer le bonus de mention
#     bonus = BONUS_MENTION.get(mention, 0)
#     score_avec_bonus = score_base * (1 + bonus / 100)

#     return min(20, round(score_avec_bonus))


# # ── Calcul Score Matières Clés (20 points max) ──
# def calculer_score_matieres(profil_etudiant, filiere_id):
#     """
#     Calcule le score basé sur les notes des matières clés
#     selon la pondération de la filière visée
#     Sur 20 points
#     """
#     notes = profil_etudiant.get(
#         "parcours_academique", {}
#     ).get("notes_matieres", {})

#     forces = profil_etudiant.get("forces_academiques", {})
#     poids_filiere = POIDS_MATIERES_FILIERES.get(filiere_id, {})

#     if not notes and not forces:
#         return 10  # Score neutre

#     score_total = 0
#     poids_total = 0

#     # Utiliser les notes réelles si disponibles
#     if notes:
#         for matiere, poids in poids_filiere.items():
#             note_trouvee = None

#             # Chercher la note de la matière
#             for nom_matiere, note in notes.items():
#                 if matiere.lower() in nom_matiere.lower() or \
#                    nom_matiere.lower() in matiere.lower():
#                     note_trouvee = float(note)
#                     break

#             if note_trouvee is not None:
#                 score_matiere = (note_trouvee / 20) * poids
#                 score_total += score_matiere
#                 poids_total += poids

#     # Compléter avec les forces du BAC si notes insuffisantes
#     if poids_total < 50:
#         for matiere, poids in poids_filiere.items():
#             matiere_lower = matiere.lower()
#             force = 3  # valeur par défaut

#             if "math" in matiere_lower:
#                 force = forces.get("force_maths", 3)
#             elif "physique" in matiere_lower:
#                 force = forces.get("force_physique", 3)
#             elif "info" in matiere_lower:
#                 force = forces.get("force_info", 2)
#             elif "econom" in matiere_lower or "gestion" in matiere_lower:
#                 force = forces.get("force_economie", 2)
#             elif "droit" in matiere_lower:
#                 force = forces.get("force_gestion", 2)

#             score_force = (force / 5) * poids
#             score_total += score_force * 0.5
#             poids_total += poids * 0.5

#     if poids_total == 0:
#         return 10

#     score_final = (score_total / poids_total) * 20
#     return min(20, round(score_final))


# # ── Calcul Score Psychométrique (20 points max) ──
# def calculer_score_psychometrique(profil_psychometrique, filiere_id):
#     """
#     Calcule la compatibilité psychologique avec la filière
#     Sur 20 points
#     """
#     if not profil_psychometrique:
#         return 10  # Score neutre si pas de test

#     compatibilite = profil_psychometrique.get(
#         "compatibilite_filieres", {}
#     ).get(filiere_id, 50)

#     # Convertir de % (0-100) vers points (0-20)
#     score = (compatibilite / 100) * 20
#     return min(20, round(score))


# # ── Calcul Score Intérêts (10 points max) ──
# def calculer_score_interets(profil_etudiant, filiere_id):
#     """
#     Calcule la compatibilité des centres d'intérêt avec la filière
#     Sur 10 points
#     """
#     scores_interets = profil_etudiant.get(
#         "preferences", {}
#     ).get("scores_interets_filieres", {})

#     score_brut = scores_interets.get(filiere_id, 0)
#     mots_cles_filiere = INTERETS_FILIERE.get(filiere_id, [])

#     if not mots_cles_filiere:
#         return 5

#     # Normaliser sur 10 points
#     max_possible = len(mots_cles_filiere)
#     score = min(10, round((score_brut / max(max_possible, 1)) * 10))

#     # Score minimum de 3 si aucun intérêt déclaré
#     return max(3, score)


# # ── Calcul Score Ambition (5 points max) ──
# def calculer_score_ambition(profil_etudiant, filiere_id):
#     """
#     Calcule la compatibilité des ambitions professionnelles
#     Sur 5 points
#     """
#     ambition = profil_etudiant.get(
#         "preferences", {}
#     ).get("ambition_professionnelle", "").lower()

#     if not ambition:
#         return 3

#     debouches = [
#         d.lower() for d in FILIERES.get(filiere_id, {}).get("debouches", [])
#     ]

#     mots_ambition = ambition.split()
#     correspondances = sum(
#         1 for mot in mots_ambition
#         if any(mot in debouche for debouche in debouches)
#     )

#     if correspondances >= 3:
#         return 5
#     elif correspondances >= 2:
#         return 4
#     elif correspondances >= 1:
#         return 3
#     else:
#         return 2


# # ============================================================
# # PARTIE 2 — VÉRIFICATION D'ÉLIGIBILITÉ (4.7)
# # ============================================================

# def verifier_eligibilite(profil_etudiant, filiere_id):
#     """
#     Vérifie si l'étudiant est éligible pour une filière.
#     Retourne (eligible: bool, raison: str)
#     """
#     parcours = profil_etudiant.get("parcours_academique", {})
#     type_bac = parcours.get("type_bac", "AUTRE")
#     moyenne = float(parcours.get("moyenne_generale", 0))

#     niveau = parcours.get("niveau_actuel", "")
# # Bloquer BAC+5 aux bacheliers
#         if niveau in ("post_bac", "bac1"):
#             filiere_niveau = FILIERES.get(filiere_id, {}).get("niveau", "")
#             if filiere_niveau == "BAC+5":
#                 return False, f"{filiere_id} est un cycle BAC+5 accessible après le BAC+3."


    
#     diplome = parcours.get("diplome_actuel", None)

#     # ── Vérification selon le niveau actuel ──
#     if niveau == "post_bac":
#         return verifier_eligibilite_1ere_annee(
#             type_bac, moyenne, filiere_id
#         )
#     elif niveau == "bac2":
#         return verifier_eligibilite_3eme_annee(
#             diplome, moyenne, filiere_id
#         )
#     elif niveau == "bac3":
#         return verifier_eligibilite_4eme_annee(
#             diplome, moyenne, filiere_id
#         )
#     else:
#         return True, None


# def verifier_eligibilite_1ere_annee(type_bac, moyenne, filiere_id):
#     """
#     Vérifie l'éligibilité pour une admission en 1ère année
#     """
#     conditions = CONDITIONS_ADMISSION.get("1ere_annee", {}).get(filiere_id, {})

#     if not conditions:
#         return True, None

#     # Vérifier le type de BAC
#     bac_requis = conditions.get("bac_requis", [])
#     if bac_requis and type_bac not in bac_requis:
#         type_requis = conditions.get("type_requis", [])
#         return False, f"Ton BAC {type_bac} n'est pas dans la liste des BAC acceptés pour {filiere_id}. {conditions.get('description', '')}"

#     # Vérifier la moyenne minimale
#     moyenne_min = conditions.get("moyenne_min", 10)
#     if moyenne > 0 and moyenne < moyenne_min:
#         return False, f"Ta moyenne ({moyenne}/20) est inférieure à la moyenne minimale requise ({moyenne_min}/20) pour {filiere_id}."

#     return True, None


# def verifier_eligibilite_3eme_annee(diplome, moyenne, filiere_id):
#     """
#     Vérifie l'éligibilité pour une admission en 3ème année
#     """
#     conditions = CONDITIONS_ADMISSION.get("3eme_annee", {})
#     moyenne_min = conditions.get("moyenne_min", 12)

#     if moyenne > 0 and moyenne < moyenne_min:
#         return False, f"Ta moyenne ({moyenne}/20) est inférieure au minimum requis ({moyenne_min}/20) pour l'admission en 3ème année."

#     diplomes_compatibles = conditions.get(
#         "filieres_compatibles", {}
#     ).get(filiere_id, [])

#     if diplome and diplomes_compatibles:
#         diplome_lower = diplome.lower()
#         compatible = any(
#             d.lower() in diplome_lower or diplome_lower in d.lower()
#             for d in diplomes_compatibles
#         )
#         if not compatible:
#             return False, f"Ton diplôme '{diplome}' n'est pas dans la liste des diplômes compatibles pour {filiere_id} en 3ème année."

#     return True, None


# def verifier_eligibilite_4eme_annee(diplome, moyenne, filiere_id):
#     """
#     Vérifie l'éligibilité pour une admission en 4ème année
#     """
#     conditions = CONDITIONS_ADMISSION.get("4eme_annee", {})
#     moyenne_min = conditions.get("moyenne_min", 12)

#     if moyenne > 0 and moyenne < moyenne_min:
#         return False, f"Ta moyenne ({moyenne}/20) est inférieure au minimum requis ({moyenne_min}/20) pour l'admission en 4ème année."

#     diplomes_compatibles = conditions.get(
#         "filieres_compatibles", {}
#     ).get(filiere_id, [])

#     if diplome and diplomes_compatibles:
#         diplome_lower = diplome.lower()
#         compatible = any(
#             d.lower() in diplome_lower or diplome_lower in d.lower()
#             for d in diplomes_compatibles
#         )
#         if not compatible:
#             return False, f"Ton diplôme '{diplome}' n'est pas dans la liste des diplômes compatibles pour {filiere_id} en 4ème année."

#     return True, None


# def proposer_alternatives(profil_etudiant, filiere_refusee):
#     """
#     Propose des filières alternatives si l'étudiant
#     n'est pas éligible pour sa filière souhaitée
#     """
#     resultats = calculer_fitscore_complet(profil_etudiant)
#     alternatives = []

#     for item in resultats["classement"]:
#         if item["filiere_id"] != filiere_refusee and item["eligible"]:
#             alternatives.append({
#                 "filiere_id": item["filiere_id"],
#                 "filiere_nom": item["filiere_nom"],
#                 "score": item["score_total"],
#                 "niveau": item["filiere_niveau"]
#             })

#     return alternatives[:3]  # Top 3 alternatives


# # ============================================================
# # PARTIE 3 — IA EXPLICABLE (4.23)
# # ============================================================

# def generer_explication_score(
#     profil_etudiant,
#     filiere_id,
#     scores,
#     score_total,
#     eligible,
#     raison_ineligibilite
# ):
#     """
#     Génère une explication claire et personnalisée du FitScore
#     """
#     filiere = FILIERES.get(filiere_id, {})
#     prenom = profil_etudiant.get(
#         "informations_personnelles", {}
#     ).get("prenom", "")
#     type_bac = profil_etudiant.get(
#         "parcours_academique", {}
#     ).get("type_bac", "")
#     moyenne = profil_etudiant.get(
#         "parcours_academique", {}
#     ).get("moyenne_generale", 0)

#     points_forts = []
#     points_faibles = []

#     if scores.get("compatibilite_bac", 0) >= 20:
#         points_forts.append(f"ton BAC {type_bac} est très compatible avec cette filière")
#     elif scores.get("compatibilite_bac", 0) <= 10:
#         points_faibles.append(f"ton BAC {type_bac} est peu orienté vers cette filière")

#     if scores.get("moyenne_academique", 0) >= 15:
#         points_forts.append(f"ta moyenne de {moyenne}/20 est excellente")
#     elif scores.get("moyenne_academique", 0) <= 8:
#         points_faibles.append(f"ta moyenne de {moyenne}/20 est en dessous des attentes")

#     if scores.get("centres_interet", 0) >= 7:
#         points_forts.append("tes centres d'intérêt correspondent bien à cette filière")
#     elif scores.get("centres_interet", 0) <= 4:
#         points_faibles.append("tes centres d'intérêt semblent peu orientés vers cette filière")

#     if scores.get("profil_psychometrique", 0) >= 15:
#         points_forts.append("ton profil psychologique est bien adapté à cette filière")

#     explication = {
#         "score": score_total,
#         "eligible": eligible,
#         "points_forts": points_forts,
#         "points_faibles": points_faibles,
#         "raison_ineligibilite": raison_ineligibilite
#     }

#     return explication


# def generer_rapport_fitscore(resultats_fitscore, profil_etudiant):
#     """
#     Génère un rapport complet et lisible du FitScore
#     avec explications naturelles via GPT
#     """
#     prenom = profil_etudiant.get(
#         "informations_personnelles", {}
#     ).get("prenom", "")

#     classement = resultats_fitscore["classement"]
#     top3 = classement[:3]

#     # Construire le résumé pour GPT
#     resume_scores = "\n".join([
#         f"- {item['rang']}. {item['filiere_nom']} ({item['filiere_niveau']}) : "
#         f"{item['score_total']}% | Éligible: {'Oui' if item['eligible'] else 'Non'}"
#         for item in classement
#     ])

#     prompt = f"""Tu es Sami, conseiller académique de SUPMTI Meknès.
# Génère un rapport d'orientation personnalisé et chaleureux.

# Étudiant : {prenom if prenom else 'un étudiant'}
# BAC : {profil_etudiant.get('parcours_academique', {}).get('type_bac', 'inconnu')}
# Moyenne : {profil_etudiant.get('parcours_academique', {}).get('moyenne_generale', 'inconnue')}/20

# Scores FitScore :
# {resume_scores}

# Génère un rapport qui :
# 1. Annonce la meilleure filière recommandée avec enthousiasme
# 2. Explique pourquoi cette filière correspond au profil (2-3 raisons)
# 3. Mentionne la 2ème et 3ème option brièvement
# 4. Encourage l'étudiant
# 5. Utilise des emojis appropriés

# Style : chaleureux, encourageant, naturel. Max 250 mots."""

#     try:
#         reponse_gpt = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0.7,
#             max_completion_tokens=500
#         )

#         return reponse_gpt.choices[0].message.content.strip()

#     except Exception as e:
#         print(f"[FITSCORE] Erreur génération rapport : {e}")

#         top1 = classement[0] if classement else None
#         if not top1:
#             return "Je n'ai pas pu calculer ton FitScore. Réessaie plus tard."

#         return f"""🎯 **Ton orientation personnalisée {prenom} :**

# 🥇 **{top1['filiere_nom']}** — Score : {top1['score_total']}%
# {'✅ Tu es éligible !' if top1['eligible'] else '⚠️ Conditions d\'admission à vérifier'}

# {f"🥈 **{classement[1]['filiere_nom']}** — {classement[1]['score_total']}%" if len(classement) > 1 else ""}
# {f"🥉 **{classement[2]['filiere_nom']}** — {classement[2]['score_total']}%" if len(classement) > 2 else ""}

# Ces résultats sont basés sur ton profil académique et tes centres d'intérêt."""


# def generer_resume_profil(profil_etudiant):
#     """
#     Génère un résumé court du profil étudiant
#     """
#     parcours = profil_etudiant.get("parcours_academique", {})
#     infos = profil_etudiant.get("informations_personnelles", {})

#     return {
#         "prenom": infos.get("prenom", ""),
#         "bac": parcours.get("type_bac", ""),
#         "moyenne": parcours.get("moyenne_generale", 0),
#         "mention": parcours.get("mention", ""),
#         "niveau": parcours.get("niveau_actuel", "post_bac")
#     }

# ============================================================
# FIT SCORE SERVICE — SUPMTI
# FitScore AI Engine (4.6)
# Vérification d'Éligibilité (4.7)
# IA Explicable (4.23)
# Tahirou — backend-tahirou
# ============================================================

# import os
# import json
# from openai import OpenAI
# from dotenv import load_dotenv
# from app.academic_config import (
#     FILIERES,
#     POIDS_FITSCORE,
#     POIDS_MATIERES_FILIERES,
#     BONUS_MENTION,
#     SEUILS_MENTION,
#     CONDITIONS_ADMISSION,
#     COMPATIBILITE_BAC_FILIERE,
#     PROFIL_PSYCHO_FILIERE,
#     INTERETS_FILIERE,
#     HISTORIQUE_ADMISSION
# )

# # ============================================================
# # INITIALISATION
# # ============================================================

# load_dotenv()
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# # ============================================================
# # PARTIE 1 — CALCUL DU FITSCORE (4.6)
# # ============================================================

# def calculer_fitscore_complet(profil_etudiant, profil_psychometrique=None):
#     """
#     Calcule le FitScore pour toutes les filières SUPMTI.
#     Retourne un classement complet avec scores et explications.

#     profil_etudiant      : résultat de construire_profil_etudiant()
#     profil_psychometrique: résultat de calculer_profil_psychometrique_final()
#                            (optionnel — score neutre si absent)
#     """
#     print("[FITSCORE] Calcul du FitScore en cours...")

#     resultats = {}
#     for filiere_id in FILIERES.keys():
#         score_details = calculer_fitscore_filiere(
#             profil_etudiant, filiere_id, profil_psychometrique
#         )
#         resultats[filiere_id] = score_details

#     classement = sorted(
#         resultats.items(),
#         key=lambda x: x[1]["score_total"],
#         reverse=True
#     )

#     resultat_final = {
#         "classement": [
#             {
#                 "rang":            i + 1,
#                 "filiere_id":      filiere_id,
#                 "filiere_nom":     FILIERES[filiere_id]["nom"],
#                 "filiere_niveau":  FILIERES[filiere_id]["niveau"],
#                 "score_total":     details["score_total"],
#                 "score":           details["score_total"],   # alias frontend
#                 "nom":             FILIERES[filiere_id]["nom"],    # alias frontend
#                 "niveau":          FILIERES[filiere_id]["niveau"], # alias frontend
#                 "score_details":   details["scores_par_critere"],
#                 "eligible":        details["eligible"],
#                 "explication":     details["explication"]
#             }
#             for i, (filiere_id, details) in enumerate(classement)
#         ],
#         "meilleure_filiere": classement[0][0] if classement else None,
#         "profil_resume":     generer_resume_profil(profil_etudiant)
#     }

#     print(f"[FITSCORE] ✅ Calcul terminé — Meilleure filière : {resultat_final['meilleure_filiere']}")
#     return resultat_final


# def calculer_fitscore_filiere(profil_etudiant, filiere_id, profil_psychometrique=None):
#     """Calcule le FitScore pour UNE filière spécifique."""
#     scores = {}

#     scores["compatibilite_bac"]          = calculer_score_bac(profil_etudiant, filiere_id)
#     scores["moyenne_academique"]          = calculer_score_moyenne(profil_etudiant, filiere_id)
#     scores["notes_matieres_cles"]         = calculer_score_matieres(profil_etudiant, filiere_id)
#     scores["profil_psychometrique"]       = calculer_score_psychometrique(profil_psychometrique, filiere_id)
#     scores["centres_interet"]             = calculer_score_interets(profil_etudiant, filiere_id)
#     scores["ambitions_professionnelles"]  = calculer_score_ambition(profil_etudiant, filiere_id)

#     score_total = min(100, round(sum(scores.values())))

#     eligible, raison_ineligibilite = verifier_eligibilite(profil_etudiant, filiere_id)
#     if not eligible:
#         score_total = min(score_total, 30)

#     explication = generer_explication_score(
#         profil_etudiant, filiere_id, scores,
#         score_total, eligible, raison_ineligibilite
#     )

#     return {
#         "score_total":          score_total,
#         "scores_par_critere":   scores,
#         "eligible":             eligible,
#         "raison_ineligibilite": raison_ineligibilite,
#         "explication":          explication
#     }


# # ── Score BAC (25 points max) ──
# def calculer_score_bac(profil_etudiant, filiere_id):
#     type_bac       = profil_etudiant.get("parcours_academique", {}).get("type_bac", "AUTRE")
#     compatibilites = COMPATIBILITE_BAC_FILIERE.get(type_bac, {})
#     score_compat   = compatibilites.get(filiere_id, 3)
#     return min(25, score_compat * 5)


# # ── Score Moyenne (20 points max) ──
# def calculer_score_moyenne(profil_etudiant, filiere_id):
#     parcours = profil_etudiant.get("parcours_academique", {})
#     moyenne  = float(parcours.get("moyenne_generale", 0))
#     mention  = parcours.get("mention", "passable")

#     if moyenne == 0:
#         return 10

#     if moyenne >= 18:   score_base = 20
#     elif moyenne >= 16: score_base = 17
#     elif moyenne >= 14: score_base = 14
#     elif moyenne >= 12: score_base = 11
#     elif moyenne >= 10: score_base = 8
#     else:               score_base = 4

#     bonus = BONUS_MENTION.get(mention, 0)
#     return min(20, round(score_base * (1 + bonus / 100)))


# # ── Score Matières Clés (20 points max) ──
# def calculer_score_matieres(profil_etudiant, filiere_id):
#     notes         = profil_etudiant.get("parcours_academique", {}).get("notes_matieres", {})
#     forces        = profil_etudiant.get("forces_academiques", {})
#     poids_filiere = POIDS_MATIERES_FILIERES.get(filiere_id, {})

#     if not notes and not forces:
#         return 10

#     score_total = 0
#     poids_total = 0

#     if notes:
#         for matiere, poids in poids_filiere.items():
#             note_trouvee = None
#             for nom_matiere, note in notes.items():
#                 if (matiere.lower() in nom_matiere.lower()
#                         or nom_matiere.lower() in matiere.lower()):
#                     note_trouvee = float(note)
#                     break
#             if note_trouvee is not None:
#                 score_total += (note_trouvee / 20) * poids
#                 poids_total += poids

#     if poids_total < 50:
#         for matiere, poids in poids_filiere.items():
#             matiere_lower = matiere.lower()
#             force = 3
#             if "math"    in matiere_lower: force = forces.get("force_maths", 3)
#             elif "physi"  in matiere_lower: force = forces.get("force_physique", 3)
#             elif "info"   in matiere_lower: force = forces.get("force_info", 2)
#             elif "econom" in matiere_lower or "gestion" in matiere_lower:
#                 force = forces.get("force_economie", 2)
#             elif "droit"  in matiere_lower: force = forces.get("force_gestion", 2)

#             score_total += (force / 5) * poids * 0.5
#             poids_total += poids * 0.5

#     if poids_total == 0:
#         return 10
#     return min(20, round((score_total / poids_total) * 20))


# # ── Score Psychométrique (20 points max) ──
# def calculer_score_psychometrique(profil_psychometrique, filiere_id):
#     if not profil_psychometrique:
#         return 10
#     compatibilite = profil_psychometrique.get(
#         "compatibilite_filieres", {}
#     ).get(filiere_id, 50)
#     return min(20, round((compatibilite / 100) * 20))


# # ── Score Intérêts (10 points max) ──
# def calculer_score_interets(profil_etudiant, filiere_id):
#     scores_interets   = profil_etudiant.get("preferences", {}).get("scores_interets_filieres", {})
#     score_brut        = scores_interets.get(filiere_id, 0)
#     mots_cles_filiere = INTERETS_FILIERE.get(filiere_id, [])

#     if not mots_cles_filiere:
#         return 5

#     score = min(10, round((score_brut / max(len(mots_cles_filiere), 1)) * 10))
#     return max(3, score)


# # ── Score Ambition (5 points max) ──
# def calculer_score_ambition(profil_etudiant, filiere_id):
#     ambition = profil_etudiant.get("preferences", {}).get("ambition_professionnelle", "").lower()
#     if not ambition:
#         return 3
#     debouches      = [d.lower() for d in FILIERES.get(filiere_id, {}).get("debouches", [])]
#     mots_ambition  = ambition.split()
#     correspondances = sum(
#         1 for mot in mots_ambition if any(mot in d for d in debouches)
#     )
#     if correspondances >= 3:   return 5
#     elif correspondances >= 2: return 4
#     elif correspondances >= 1: return 3
#     else:                      return 2


# # ============================================================
# # PARTIE 2 — VÉRIFICATION D'ÉLIGIBILITÉ (4.7)
# # ============================================================

# def verifier_eligibilite(profil_etudiant, filiere_id):
#     """
#     Vérifie si l'étudiant est éligible pour une filière.
#     Retourne (eligible: bool, raison: str|None)

#     RÈGLE STRICTE niveau ↔ cycle filière :
#     - post_bac / bac1 → UNIQUEMENT BAC+3 (IISI, MGE, MDI)
#     - bac2            → UNIQUEMENT BAC+3 selon spécialité
#     - bac3            → UNIQUEMENT BAC+5 selon spécialité
#     - niveau vide     → pas de blocage (profil incomplet)
#     """
#     parcours = profil_etudiant.get("parcours_academique", {})
#     type_bac = parcours.get("type_bac", "AUTRE")
#     moyenne  = float(parcours.get("moyenne_generale", 0))
#     niveau   = parcours.get("niveau_actuel", "")
#     diplome  = parcours.get("diplome_actuel", None)

#     # Niveau non déclaré → on ne bloque pas
#     if not niveau:
#         return True, None

#     # Récupérer le cycle de la filière (BAC+3 ou BAC+5)
#     filiere_niv = FILIERES.get(filiere_id, {}).get("niveau", "")

#     if niveau in ("post_bac", "bac1"):
#         # Bacheliers → UNIQUEMENT les filières BAC+3
#         if filiere_niv == "BAC+5":
#             return False, (
#                 f"{filiere_id} est un cycle BAC+5 accessible après le BAC+3. "
#                 f"En tant que bachelier, tu intègres IISI, MGE ou MDI (BAC+3) d'abord."
#             )
#         return verifier_eligibilite_1ere_annee(type_bac, moyenne, filiere_id)

#     elif niveau == "bac2":
#         # BAC+2 → UNIQUEMENT les filières BAC+3
#         if filiere_niv == "BAC+5":
#             return False, (
#                 f"{filiere_id} est un cycle BAC+5. "
#                 f"Avec un BAC+2, tu intègres en 3ème année de IISI, MGE ou MDI."
#             )
#         return verifier_eligibilite_3eme_annee(diplome, moyenne, filiere_id)

#     elif niveau == "bac3":
#         # BAC+3 → UNIQUEMENT les filières BAC+5
#         if filiere_niv == "BAC+3":
#             return False, (
#                 f"{filiere_id} est un cycle BAC+3. "
#                 f"Avec un BAC+3, tu intègres directement les filières BAC+5 (IISIC, IISRT, FACG, MRI)."
#             )
#         return verifier_eligibilite_4eme_annee(diplome, moyenne, filiere_id)

#     else:
#         return True, None


# def verifier_eligibilite_1ere_annee(type_bac, moyenne, filiere_id):
#     conditions  = CONDITIONS_ADMISSION.get("1ere_annee", {}).get(filiere_id, {})
#     if not conditions:
#         return True, None

#     bac_requis = conditions.get("bac_requis", [])
#     if bac_requis and type_bac not in bac_requis:
#         return False, (
#             f"Ton BAC {type_bac} n'est pas dans la liste des BAC acceptés pour {filiere_id}. "
#             f"{conditions.get('description', '')}"
#         )

#     moyenne_min = conditions.get("moyenne_min", 10)
#     if moyenne > 0 and moyenne < moyenne_min:
#         return False, (
#             f"Ta moyenne ({moyenne}/20) est inférieure au minimum requis "
#             f"({moyenne_min}/20) pour {filiere_id}."
#         )

#     return True, None


# def verifier_eligibilite_3eme_annee(diplome, moyenne, filiere_id):
#     conditions  = CONDITIONS_ADMISSION.get("3eme_annee", {})
#     moyenne_min = conditions.get("moyenne_min", 12)

#     if moyenne > 0 and moyenne < moyenne_min:
#         return False, (
#             f"Ta moyenne ({moyenne}/20) est inférieure au minimum requis "
#             f"({moyenne_min}/20) pour l'admission en 3ème année."
#         )

#     diplomes_compatibles = conditions.get("filieres_compatibles", {}).get(filiere_id, [])
#     if diplome and diplomes_compatibles:
#         diplome_lower = diplome.lower()

#         compatible = any(
#             d.lower() in diplome_lower or diplome_lower in d.lower()
#             for d in diplomes_compatibles
#         )

#         if not compatible:
#             tech_kw = [
#                 "info", "informatique", "réseau", "reseau", "cyber", "securite",
#                 "sécurité", "telecom", "système", "systeme", "tech", "numérique",
#                 "numerique", "électronique", "electronique", "ingénierie", "ingenierie",
#                 "web", "dev", "développement", "developpement", "mobile", "cloud",
#                 "data", "ia", "intelligence", "artificielle", "machine", "learning",
#                 "logiciel", "software", "appli", "programmation", "digital", "code",
#                 "iot", "embarqué", "embarque", "python", "java", "sql", "linux",
#             ]
#             gestion_kw = [
#                 "gestion", "management", "économie", "economie", "commerce",
#                 "finance", "comptabilit", "iscae", "marketing", "business",
#                 "administration", "entreprise", "audit", "rh", "ressources",
#                 "international", "export", "import", "juridique", "droit",
#                 "fiscal", "bancaire", "assurance",
#             ]
#             if filiere_id == "IISI":
#                 compatible = any(k in diplome_lower for k in tech_kw)
#             elif filiere_id in ("MGE", "MDI"):
#                 compatible = any(k in diplome_lower for k in gestion_kw)
#                 if not compatible:
#                     compatible = any(k in diplome_lower for k in tech_kw)

#         if not compatible:
#             return False, (
#                 f"Ton diplôme '{diplome}' ne semble pas aligné avec {filiere_id}. "
#                 f"Étude de dossier recommandée — contacte SUPMTI."
#             )

#     return True, None


# def verifier_eligibilite_4eme_annee(diplome, moyenne, filiere_id):
#     conditions  = CONDITIONS_ADMISSION.get("4eme_annee", {})
#     moyenne_min = conditions.get("moyenne_min", 12)

#     if moyenne > 0 and moyenne < moyenne_min:
#         return False, (
#             f"Ta moyenne ({moyenne}/20) est inférieure au minimum requis "
#             f"({moyenne_min}/20) pour l'admission en 4ème année."
#         )

#     diplomes_compatibles = conditions.get("filieres_compatibles", {}).get(filiere_id, [])
#     if diplome and diplomes_compatibles:
#         diplome_lower = diplome.lower()

#         compatible = any(
#             d.lower() in diplome_lower or diplome_lower in d.lower()
#             for d in diplomes_compatibles
#         )

#         if not compatible:
#             tech_kw = [
#                 "info", "informatique", "réseau", "reseau", "cyber", "securite",
#                 "sécurité", "telecom", "système", "systeme", "tech", "numérique",
#                 "numerique", "électronique", "electronique", "ingénierie", "ingenierie",
#                 "web", "dev", "développement", "developpement", "mobile", "cloud",
#                 "data", "ia", "intelligence", "artificielle", "machine", "learning",
#                 "logiciel", "software", "appli", "programmation", "digital", "code",
#                 "iot", "embarqué", "embarque", "python", "java", "sql", "linux",
#             ]
#             gestion_kw = [
#                 "gestion", "management", "économie", "economie", "commerce",
#                 "finance", "comptabilit", "iscae", "marketing", "business",
#                 "administration", "entreprise", "audit", "rh", "ressources",
#                 "international", "export", "import", "juridique", "droit",
#                 "fiscal", "bancaire", "assurance",
#             ]

#             if filiere_id in ("IISIC", "IISRT"):
#                 compatible = any(k in diplome_lower for k in tech_kw)
#             elif filiere_id in ("FACG", "MRI"):
#                 compatible = any(k in diplome_lower for k in gestion_kw)

#         if not compatible:
#             return False, (
#                 f"Ton diplôme '{diplome}' ne semble pas aligné avec {filiere_id}. "
#                 f"Étude de dossier recommandée — contacte SUPMTI."
#             )

#     return True, None


# def proposer_alternatives(profil_etudiant, filiere_refusee):
#     resultats    = calculer_fitscore_complet(profil_etudiant)
#     alternatives = []
#     for item in resultats["classement"]:
#         if item["filiere_id"] != filiere_refusee and item["eligible"]:
#             alternatives.append({
#                 "filiere_id":  item["filiere_id"],
#                 "filiere_nom": item["filiere_nom"],
#                 "score":       item["score_total"],
#                 "niveau":      item["filiere_niveau"]
#             })
#     return alternatives[:3]


# # ============================================================
# # PARTIE 3 — IA EXPLICABLE (4.23)
# # ============================================================

# def generer_explication_score(
#     profil_etudiant, filiere_id, scores, score_total, eligible, raison_ineligibilite
# ):
#     type_bac = profil_etudiant.get("parcours_academique", {}).get("type_bac", "")
#     moyenne  = profil_etudiant.get("parcours_academique", {}).get("moyenne_generale", 0)

#     points_forts   = []
#     points_faibles = []

#     if scores.get("compatibilite_bac", 0) >= 20:
#         points_forts.append(f"ton BAC {type_bac} est très compatible avec cette filière")
#     elif scores.get("compatibilite_bac", 0) <= 10:
#         points_faibles.append(f"ton BAC {type_bac} est peu orienté vers cette filière")

#     if scores.get("moyenne_academique", 0) >= 15:
#         points_forts.append(f"ta moyenne de {moyenne}/20 est excellente")
#     elif scores.get("moyenne_academique", 0) <= 8:
#         points_faibles.append(f"ta moyenne de {moyenne}/20 est en dessous des attentes")

#     if scores.get("centres_interet", 0) >= 7:
#         points_forts.append("tes centres d'intérêt correspondent bien à cette filière")
#     elif scores.get("centres_interet", 0) <= 4:
#         points_faibles.append("tes centres d'intérêt semblent peu orientés vers cette filière")

#     if scores.get("profil_psychometrique", 0) >= 15:
#         points_forts.append("ton profil psychologique est bien adapté à cette filière")

#     return {
#         "score":                score_total,
#         "eligible":             eligible,
#         "points_forts":         points_forts,
#         "points_faibles":       points_faibles,
#         "raison_ineligibilite": raison_ineligibilite
#     }


# def generer_rapport_fitscore(resultats_fitscore, profil_etudiant):
#     """Génère un rapport complet et lisible du FitScore via GPT."""
#     prenom    = profil_etudiant.get("informations_personnelles", {}).get("prenom", "")
#     classement = resultats_fitscore["classement"]

#     resume_scores = "\n".join([
#         f"- {item['rang']}. {item['filiere_nom']} ({item['filiere_niveau']}) : "
#         f"{item['score_total']}% | Éligible: {'Oui' if item['eligible'] else 'Non'}"
#         for item in classement
#     ])

#     prompt = f"""Tu es Sami, conseiller académique de SUPMTI Meknès.
# Génère un rapport d'orientation personnalisé et chaleureux.

# Étudiant : {prenom if prenom else 'un étudiant'}
# BAC : {profil_etudiant.get('parcours_academique', {}).get('type_bac', 'inconnu')}
# Moyenne : {profil_etudiant.get('parcours_academique', {}).get('moyenne_generale', 'inconnue')}/20

# Scores FitScore :
# {resume_scores}

# FORMAT OBLIGATOIRE :
# - ## pour les titres (ex: ## Filière recommandée)
# - **texte** pour les données importantes
# - - tirets pour les listes
# - Jamais de : •, ►, ════, ─────, ####

# Génère un rapport qui :
# 1. Annonce la meilleure filière avec ## et enthousiasme
# 2. Explique pourquoi cette filière correspond (2-3 raisons en tirets)
# 3. Mentionne les 2ème et 3ème options brièvement
# 4. Encourage l'étudiant (1-2 phrases)
# Max 200 mots."""

#     try:
#         r = client.chat.completions.create(
#             model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0.7,
#             max_tokens=500
#         )
#         return r.choices[0].message.content.strip()

#     except Exception as e:
#         print(f"[FITSCORE] Erreur génération rapport : {e}")
#         top1 = classement[0] if classement else None
#         if not top1:
#             return "Je n'ai pas pu calculer ton FitScore. Réessaie plus tard."

#         elig_msg = "✅ Éligible" if top1['eligible'] else "📋 Dossier à étudier (critères à renforcer)"
#         ligne2 = f"- {classement[1]['filiere_nom']} — **{classement[1]['score_total']}%**\n" if len(classement) > 1 else ""
#         ligne3 = f"- {classement[2]['filiere_nom']} — **{classement[2]['score_total']}%**\n" if len(classement) > 2 else ""
#         return (
#             f"## Ton orientation personnalisée\n\n"
#             f"**Filière recommandée : {top1['filiere_nom']}**\n"
#             f"Score de compatibilité : **{top1['score_total']}%** — {elig_msg}\n\n"
#             f"## Autres options\n"
#             + ligne2
#             + ligne3
#             + "\nCes résultats sont basés sur ton profil académique et tes centres d'intérêt."
#         )


# def generer_resume_profil(profil_etudiant):
#     """
#     Génère un résumé court du profil étudiant.
#     FIX : niveau default '' — cohérence avec profile_service.
#     """
#     parcours = profil_etudiant.get("parcours_academique", {})
#     infos    = profil_etudiant.get("informations_personnelles", {})
#     return {
#         "prenom":  infos.get("prenom", ""),
#         "bac":     parcours.get("type_bac", ""),
#         "moyenne": parcours.get("moyenne_generale", 0),
#         "mention": parcours.get("mention", ""),
#         "niveau":  parcours.get("niveau_actuel", "")   # FIX : default "" pas "post_bac"
#     }





# import os
# import json
# from openai import OpenAI
# from dotenv import load_dotenv
# from app.academic_config import (
#     FILIERES,
#     POIDS_FITSCORE,
#     POIDS_MATIERES_FILIERES,
#     BONUS_MENTION,
#     SEUILS_MENTION,
#     CONDITIONS_ADMISSION,
#     COMPATIBILITE_BAC_FILIERE,
#     PROFIL_PSYCHO_FILIERE,
#     INTERETS_FILIERE,
#     HISTORIQUE_ADMISSION
# )

# load_dotenv()
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# # ============================================================
# # PARTIE 1 — CALCUL DU FITSCORE
# # ============================================================

# def calculer_fitscore_complet(profil_etudiant, profil_psychometrique=None):
#     print("[FITSCORE] Calcul du FitScore en cours...")
#     resultats = {}
#     for filiere_id in FILIERES.keys():
#         score_details = calculer_fitscore_filiere(profil_etudiant, filiere_id, profil_psychometrique)
#         resultats[filiere_id] = score_details

#     classement = sorted(resultats.items(), key=lambda x: x[1]["score_total"], reverse=True)

#     resultat_final = {
#         "classement": [
#             {
#                 "rang":           i + 1,
#                 "filiere_id":     filiere_id,
#                 "filiere_nom":    FILIERES[filiere_id]["nom"],
#                 "filiere_niveau": FILIERES[filiere_id]["niveau"],
#                 "score_total":    details["score_total"],
#                 "score":          details["score_total"],
#                 "nom":            FILIERES[filiere_id]["nom"],
#                 "niveau":         FILIERES[filiere_id]["niveau"],
#                 "score_details":  details["scores_par_critere"],
#                 "eligible":       details["eligible"],
#                 "explication":    details["explication"]
#             }
#             for i, (filiere_id, details) in enumerate(classement)
#         ],
#         "meilleure_filiere": classement[0][0] if classement else None,
#         "profil_resume":     generer_resume_profil(profil_etudiant)
#     }
#     print(f"[FITSCORE] ✅ Calcul terminé — Meilleure filière : {resultat_final['meilleure_filiere']}")
#     return resultat_final


# def calculer_fitscore_filiere(profil_etudiant, filiere_id, profil_psychometrique=None):
#     scores = {}
#     scores["compatibilite_bac"]         = calculer_score_bac(profil_etudiant, filiere_id)
#     scores["moyenne_academique"]         = calculer_score_moyenne(profil_etudiant, filiere_id)
#     scores["notes_matieres_cles"]        = calculer_score_matieres(profil_etudiant, filiere_id)
#     scores["profil_psychometrique"]      = calculer_score_psychometrique(profil_psychometrique, filiere_id)
#     scores["centres_interet"]            = calculer_score_interets(profil_etudiant, filiere_id)
#     scores["ambitions_professionnelles"] = calculer_score_ambition(profil_etudiant, filiere_id)

#     score_total = min(100, round(sum(scores.values())))

#     eligible, raison_ineligibilite = verifier_eligibilite(profil_etudiant, filiere_id)
#     if not eligible:
#         score_total = min(score_total, 30)

#     explication = generer_explication_score(
#         profil_etudiant, filiere_id, scores, score_total, eligible, raison_ineligibilite
#     )

#     return {
#         "score_total":          score_total,
#         "scores_par_critere":   scores,
#         "eligible":             eligible,
#         "raison_ineligibilite": raison_ineligibilite,
#         "explication":          explication
#     }


# def calculer_score_bac(profil_etudiant, filiere_id):
#     type_bac       = profil_etudiant.get("parcours_academique", {}).get("type_bac", "AUTRE")
#     compatibilites = COMPATIBILITE_BAC_FILIERE.get(type_bac, {})
#     score_compat   = compatibilites.get(filiere_id, 3)
#     return min(25, score_compat * 5)


# def calculer_score_moyenne(profil_etudiant, filiere_id):
#     parcours = profil_etudiant.get("parcours_academique", {})
#     moyenne  = float(parcours.get("moyenne_generale", 0))
#     mention  = parcours.get("mention", "passable")

#     if moyenne == 0:
#         return 10

#     if moyenne >= 18:   score_base = 20
#     elif moyenne >= 16: score_base = 17
#     elif moyenne >= 14: score_base = 14
#     elif moyenne >= 12: score_base = 11
#     elif moyenne >= 10: score_base = 8
#     else:               score_base = 4

#     bonus = BONUS_MENTION.get(mention, 0)
#     return min(20, round(score_base * (1 + bonus / 100)))


# def calculer_score_matieres(profil_etudiant, filiere_id):
#     notes         = profil_etudiant.get("parcours_academique", {}).get("notes_matieres", {})
#     forces        = profil_etudiant.get("forces_academiques", {})
#     poids_filiere = POIDS_MATIERES_FILIERES.get(filiere_id, {})

#     if not notes and not forces:
#         return 10

#     score_total = 0
#     poids_total = 0

#     if notes:
#         for matiere, poids in poids_filiere.items():
#             note_trouvee = None
#             for nom_matiere, note in notes.items():
#                 if matiere.lower() in nom_matiere.lower() or nom_matiere.lower() in matiere.lower():
#                     note_trouvee = float(note)
#                     break
#             if note_trouvee is not None:
#                 score_total += (note_trouvee / 20) * poids
#                 poids_total += poids

#     if poids_total < 50:
#         for matiere, poids in poids_filiere.items():
#             matiere_lower = matiere.lower()
#             force = 3
#             if "math"    in matiere_lower: force = forces.get("force_maths", 3)
#             elif "physi"  in matiere_lower: force = forces.get("force_physique", 3)
#             elif "info"   in matiere_lower: force = forces.get("force_info", 2)
#             elif "econom" in matiere_lower or "gestion" in matiere_lower:
#                 force = forces.get("force_economie", 2)
#             elif "droit"  in matiere_lower: force = forces.get("force_gestion", 2)
#             score_total += (force / 5) * poids * 0.5
#             poids_total += poids * 0.5

#     if poids_total == 0:
#         return 10
#     return min(20, round((score_total / poids_total) * 20))


# def calculer_score_psychometrique(profil_psychometrique, filiere_id):
#     if not profil_psychometrique:
#         return 10
#     compatibilite = profil_psychometrique.get("compatibilite_filieres", {}).get(filiere_id, 50)
#     return min(20, round((compatibilite / 100) * 20))


# def calculer_score_interets(profil_etudiant, filiere_id):
#     scores_interets   = profil_etudiant.get("preferences", {}).get("scores_interets_filieres", {})
#     score_brut        = scores_interets.get(filiere_id, 0)
#     mots_cles_filiere = INTERETS_FILIERE.get(filiere_id, [])
#     if not mots_cles_filiere:
#         return 5
#     score = min(10, round((score_brut / max(len(mots_cles_filiere), 1)) * 10))
#     return max(3, score)


# def calculer_score_ambition(profil_etudiant, filiere_id):
#     ambition = profil_etudiant.get("preferences", {}).get("ambition_professionnelle", "").lower()
#     if not ambition:
#         return 3
#     debouches      = [d.lower() for d in FILIERES.get(filiere_id, {}).get("debouches", [])]
#     mots_ambition  = ambition.split()
#     correspondances = sum(1 for mot in mots_ambition if any(mot in d for d in debouches))
#     if correspondances >= 3:   return 5
#     elif correspondances >= 2: return 4
#     elif correspondances >= 1: return 3
#     else:                      return 2


# # ============================================================
# # PARTIE 2 — VÉRIFICATION D'ÉLIGIBILITÉ (FIX COMPLET)
# # ============================================================

# # Toutes les variantes de "bachelier"
# _NIVEAUX_BACHELIER = {
#     "post_bac", "bac1",
#     "bac", "BAC",
#     "terminale", "Terminale", "TERMINALE",
#     "baccalaureat", "baccalauréat",
#     "lycee", "lycée",
#     "1ere_annee", "1ère_annee",
# }

# # BAC+2 (entrée en 3ème année BAC+3)
# _NIVEAUX_BAC2 = {
#     "bac2", "BAC+2", "bac+2",
#     "deug", "dut", "bts", "cpge",
#     "2eme_annee", "2ème_annee",
#     "classes préparatoires", "classesprepa", "prepa",
# }

# # BAC+3 (entrée BAC+5 seulement)
# _NIVEAUX_BAC3 = {
#     "bac3", "BAC+3", "bac+3",
#     "licence", "bachelor",
#     "3eme_annee", "3ème_annee",
#     "4eme_annee", "4ème_annee",
#     "licenceprofessionnelle", "licence professionnelle",
#     "l3",
# }

# # BAC+4/5
# _NIVEAUX_BAC4 = {
#     "bac4", "bac5", "BAC+4", "BAC+5",
#     "master", "m1", "m2",
#     "ingenieur", "ingénieur",
#     "5eme_annee", "5ème_annee",
# }


# def verifier_eligibilite(profil_etudiant, filiere_id):
#     """
#     Vérifie si l'étudiant est éligible pour une filière.
#     Retourne (eligible: bool, raison: str|None)

#     Règles :
#     - bachelier / terminale / BAC (toutes variantes) → BAC+3 seulement
#     - bac2 / DUT / BTS / CPGE                       → BAC+3 seulement
#     - bac3 / licence / bachelor                      → BAC+5 seulement
#     - niveau vide / non reconnu                      → pas de blocage
#     """
#     parcours = profil_etudiant.get("parcours_academique", {})
#     type_bac = parcours.get("type_bac", "AUTRE")
#     moyenne  = float(parcours.get("moyenne_generale", 0))
#     niveau   = (parcours.get("niveau_actuel") or "").strip()
#     diplome  = parcours.get("diplome_actuel", None)

#     # Niveau non déclaré → pas de blocage
#     if not niveau:
#         return True, None

#     filiere_niv = FILIERES.get(filiere_id, {}).get("niveau", "")

#     # ── Bachelier ───────────────────────────────────────────────────────────────
#     if niveau in _NIVEAUX_BACHELIER:
#         if filiere_niv == "BAC+5":
#             return False, (
#                 f"{filiere_id} est un cycle BAC+5 accessible après le BAC+3. "
#                 f"En tant que bachelier, tu intègres IISI, MGE ou MDI (BAC+3) d'abord."
#             )
#         return verifier_eligibilite_1ere_annee(type_bac, moyenne, filiere_id)

#     # ── BAC+2 ────────────────────────────────────────────────────────────────────
#     elif niveau in _NIVEAUX_BAC2:
#         if filiere_niv == "BAC+5":
#             return False, (
#                 f"{filiere_id} est un cycle BAC+5. "
#                 f"Avec un BAC+2, tu intègres en 3ème année de IISI, MGE ou MDI."
#             )
#         return verifier_eligibilite_3eme_annee(diplome, moyenne, filiere_id)

#     # ── BAC+3 ────────────────────────────────────────────────────────────────────
#     elif niveau in _NIVEAUX_BAC3:
#         if filiere_niv == "BAC+3":
#             return False, (
#                 f"{filiere_id} est un cycle BAC+3. "
#                 f"Avec un BAC+3, tu intègres directement les filières BAC+5 (IISIC, IISRT, FACG, MRI)."
#             )
#         return verifier_eligibilite_4eme_annee(diplome, moyenne, filiere_id)

#     # ── BAC+4/5 déjà diplômé ─────────────────────────────────────────────────────
#     elif niveau in _NIVEAUX_BAC4:
#         if filiere_niv == "BAC+3":
#             return False, (
#                 f"{filiere_id} est un cycle BAC+3. "
#                 f"Avec ton niveau, tu peux intégrer directement les filières BAC+5."
#             )
#         return verifier_eligibilite_4eme_annee(diplome, moyenne, filiere_id)

#     # ── Niveau non reconnu → pas de blocage ──────────────────────────────────────
#     else:
#         return True, None


# def verifier_eligibilite_1ere_annee(type_bac, moyenne, filiere_id):
#     conditions = CONDITIONS_ADMISSION.get("1ere_annee", {}).get(filiere_id, {})
#     if not conditions:
#         return True, None

#     bac_requis = conditions.get("bac_requis", [])
#     if bac_requis and type_bac not in bac_requis:
#         return False, (
#             f"Ton BAC {type_bac} n'est pas dans la liste des BAC acceptés pour {filiere_id}. "
#             f"{conditions.get('description', '')}"
#         )

#     moyenne_min = conditions.get("moyenne_min", 10)
#     if moyenne > 0 and moyenne < moyenne_min:
#         return False, (
#             f"Ta moyenne ({moyenne}/20) est inférieure au minimum requis "
#             f"({moyenne_min}/20) pour {filiere_id}."
#         )

#     return True, None


# def verifier_eligibilite_3eme_annee(diplome, moyenne, filiere_id):
#     conditions  = CONDITIONS_ADMISSION.get("3eme_annee", {})
#     moyenne_min = conditions.get("moyenne_min", 12)

#     if moyenne > 0 and moyenne < moyenne_min:
#         return False, (
#             f"Ta moyenne ({moyenne}/20) est inférieure au minimum requis "
#             f"({moyenne_min}/20) pour l'admission en 3ème année."
#         )

#     diplomes_compatibles = conditions.get("filieres_compatibles", {}).get(filiere_id, [])
#     if diplome and diplomes_compatibles:
#         diplome_lower = diplome.lower()
#         compatible = any(
#             d.lower() in diplome_lower or diplome_lower in d.lower()
#             for d in diplomes_compatibles
#         )
#         if not compatible:
#             tech_kw = [
#                 "info", "informatique", "réseau", "reseau", "cyber", "securite",
#                 "sécurité", "telecom", "système", "systeme", "tech", "numérique",
#                 "numerique", "électronique", "electronique", "ingénierie", "ingenierie",
#                 "web", "dev", "développement", "developpement", "mobile", "cloud",
#                 "data", "ia", "intelligence", "artificielle", "machine", "learning",
#                 "logiciel", "software", "appli", "programmation", "digital", "code",
#                 "iot", "embarqué", "embarque", "python", "java", "sql", "linux",
#                 "full", "stack", "fullstack", "front", "back", "angular", "react",
#             ]
#             gestion_kw = [
#                 "gestion", "management", "économie", "economie", "commerce",
#                 "finance", "comptabilit", "iscae", "marketing", "business",
#                 "administration", "entreprise", "audit", "rh", "ressources",
#                 "international", "export", "import", "juridique", "droit",
#                 "fiscal", "bancaire", "assurance",
#             ]
#             if filiere_id == "IISI":
#                 compatible = any(k in diplome_lower for k in tech_kw)
#             elif filiere_id in ("MGE", "MDI"):
#                 compatible = any(k in diplome_lower for k in gestion_kw)
#                 if not compatible:
#                     compatible = any(k in diplome_lower for k in tech_kw)

#         if not compatible:
#             return False, (
#                 f"Ton diplôme '{diplome}' ne semble pas aligné avec {filiere_id}. "
#                 f"Étude de dossier recommandée — contacte SUPMTI."
#             )

#     return True, None


# def verifier_eligibilite_4eme_annee(diplome, moyenne, filiere_id):
#     conditions  = CONDITIONS_ADMISSION.get("4eme_annee", {})
#     moyenne_min = conditions.get("moyenne_min", 12)

#     if moyenne > 0 and moyenne < moyenne_min:
#         return False, (
#             f"Ta moyenne ({moyenne}/20) est inférieure au minimum requis "
#             f"({moyenne_min}/20) pour l'admission en 4ème année."
#         )

#     diplomes_compatibles = conditions.get("filieres_compatibles", {}).get(filiere_id, [])
#     if diplome and diplomes_compatibles:
#         diplome_lower = diplome.lower()
#         compatible = any(
#             d.lower() in diplome_lower or diplome_lower in d.lower()
#             for d in diplomes_compatibles
#         )
#         if not compatible:
#             tech_kw = [
#                 "info", "informatique", "réseau", "reseau", "cyber", "securite",
#                 "sécurité", "telecom", "système", "systeme", "tech", "numérique",
#                 "numerique", "électronique", "electronique", "ingénierie", "ingenierie",
#                 "web", "dev", "développement", "developpement", "mobile", "cloud",
#                 "data", "ia", "intelligence", "artificielle", "machine", "learning",
#                 "logiciel", "software", "appli", "programmation", "digital", "code",
#                 "iot", "embarqué", "embarque", "python", "java", "sql", "linux",
#                 "full", "stack", "fullstack", "front", "back", "angular", "react",
#             ]
#             gestion_kw = [
#                 "gestion", "management", "économie", "economie", "commerce",
#                 "finance", "comptabilit", "iscae", "marketing", "business",
#                 "administration", "entreprise", "audit", "rh", "ressources",
#                 "international", "export", "import", "juridique", "droit",
#                 "fiscal", "bancaire", "assurance",
#             ]
#             if filiere_id in ("IISIC", "IISRT"):
#                 compatible = any(k in diplome_lower for k in tech_kw)
#             elif filiere_id in ("FACG", "MRI"):
#                 compatible = any(k in diplome_lower for k in gestion_kw)

#         if not compatible:
#             return False, (
#                 f"Ton diplôme '{diplome}' ne semble pas aligné avec {filiere_id}. "
#                 f"Étude de dossier recommandée — contacte SUPMTI."
#             )

#     return True, None


# def proposer_alternatives(profil_etudiant, filiere_refusee):
#     resultats    = calculer_fitscore_complet(profil_etudiant)
#     alternatives = []
#     for item in resultats["classement"]:
#         if item["filiere_id"] != filiere_refusee and item["eligible"]:
#             alternatives.append({
#                 "filiere_id":  item["filiere_id"],
#                 "filiere_nom": item["filiere_nom"],
#                 "score":       item["score_total"],
#                 "niveau":      item["filiere_niveau"]
#             })
#     return alternatives[:3]


# # ============================================================
# # PARTIE 3 — IA EXPLICABLE
# # ============================================================

# def generer_explication_score(profil_etudiant, filiere_id, scores, score_total, eligible, raison_ineligibilite):
#     type_bac = profil_etudiant.get("parcours_academique", {}).get("type_bac", "")
#     moyenne  = profil_etudiant.get("parcours_academique", {}).get("moyenne_generale", 0)

#     points_forts   = []
#     points_faibles = []

#     if scores.get("compatibilite_bac", 0) >= 20:
#         points_forts.append(f"ton BAC {type_bac} est très compatible avec cette filière")
#     elif scores.get("compatibilite_bac", 0) <= 10:
#         points_faibles.append(f"ton BAC {type_bac} est peu orienté vers cette filière")

#     if scores.get("moyenne_academique", 0) >= 15:
#         points_forts.append(f"ta moyenne de {moyenne}/20 est excellente")
#     elif scores.get("moyenne_academique", 0) <= 8:
#         points_faibles.append(f"ta moyenne de {moyenne}/20 est en dessous des attentes")

#     if scores.get("centres_interet", 0) >= 7:
#         points_forts.append("tes centres d'intérêt correspondent bien à cette filière")
#     elif scores.get("centres_interet", 0) <= 4:
#         points_faibles.append("tes centres d'intérêt semblent peu orientés vers cette filière")

#     if scores.get("profil_psychometrique", 0) >= 15:
#         points_forts.append("ton profil psychologique est bien adapté à cette filière")

#     return {
#         "score":                score_total,
#         "eligible":             eligible,
#         "points_forts":         points_forts,
#         "points_faibles":       points_faibles,
#         "raison_ineligibilite": raison_ineligibilite
#     }


# def generer_rapport_fitscore(resultats_fitscore, profil_etudiant):
#     prenom    = profil_etudiant.get("informations_personnelles", {}).get("prenom", "")
#     classement = resultats_fitscore["classement"]

#     resume_scores = "\n".join([
#         f"- {item['rang']}. {item['filiere_nom']} ({item['filiere_niveau']}) : "
#         f"{item['score_total']}% | Éligible: {'Oui' if item['eligible'] else 'Non'}"
#         for item in classement
#     ])

#     prompt = f"""Tu es Sami, conseiller académique de SUPMTI Meknès.
# Génère un rapport d'orientation personnalisé et chaleureux.

# Étudiant : {prenom if prenom else 'un étudiant'}
# BAC : {profil_etudiant.get('parcours_academique', {}).get('type_bac', 'inconnu')}
# Moyenne : {profil_etudiant.get('parcours_academique', {}).get('moyenne_generale', 'inconnue')}/20
# Diplôme actuel : {profil_etudiant.get('parcours_academique', {}).get('diplome_actuel', 'non précisé')}

# Scores FitScore :
# {resume_scores}

# FORMAT OBLIGATOIRE :
# - ## pour les titres
# - **texte** pour les données importantes
# - - tirets pour les listes
# - Jamais de : •, ►, ════, ─────, ####

# Génère un rapport qui :
# 1. Annonce la meilleure filière ÉLIGIBLE avec ## et enthousiasme
# 2. Explique pourquoi cette filière correspond (2-3 raisons en tirets)
# 3. Mentionne les 2ème et 3ème options brièvement
# 4. Encourage l'étudiant (1-2 phrases)
# Max 200 mots."""

#     try:
#         r = client.chat.completions.create(
#             model=os.getenv("MODEL_NAME", "gpt-4o-mini"),
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0.7,
#             max_tokens=500
#         )
#         return r.choices[0].message.content.strip()
#     except Exception as e:
#         print(f"[FITSCORE] Erreur génération rapport : {e}")
#         # Trouver la meilleure filière éligible pour le fallback
#         top_eligible = next((item for item in classement if item["eligible"]), classement[0] if classement else None)
#         if not top_eligible:
#             return "Je n'ai pas pu calculer ton FitScore. Réessaie plus tard."

#         elig_msg = "✅ Éligible" if top_eligible["eligible"] else "📋 Dossier à étudier"
#         ligne2 = f"- {classement[1]['filiere_nom']} — **{classement[1]['score_total']}%**\n" if len(classement) > 1 else ""
#         ligne3 = f"- {classement[2]['filiere_nom']} — **{classement[2]['score_total']}%**\n" if len(classement) > 2 else ""
#         return (
#             f"## Ton orientation personnalisée\n\n"
#             f"**Filière recommandée : {top_eligible['filiere_nom']}**\n"
#             f"Score de compatibilité : **{top_eligible['score_total']}%** — {elig_msg}\n\n"
#             f"## Autres options\n" + ligne2 + ligne3 +
#             "\nCes résultats sont basés sur ton profil académique et tes centres d'intérêt."
#         )


# def generer_resume_profil(profil_etudiant):
#     parcours = profil_etudiant.get("parcours_academique", {})
#     infos    = profil_etudiant.get("informations_personnelles", {})
#     return {
#         "prenom":   infos.get("prenom", ""),
#         "bac":      parcours.get("type_bac", ""),
#         "moyenne":  parcours.get("moyenne_generale", 0),
#         "mention":  parcours.get("mention", ""),
#         "niveau":   parcours.get("niveau_actuel", ""),
#         "diplome":  parcours.get("diplome_actuel", ""),
#     }




# ============================================================
# FIT SCORE SERVICE — SUPMTI
# FitScore AI Engine (4.6)
# Vérification d'Éligibilité (4.7) — FIX COMPLET
# IA Explicable (4.23)
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

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ============================================================
# PARTIE 1 — CALCUL DU FITSCORE
# ============================================================

def calculer_fitscore_complet(profil_etudiant, profil_psychometrique=None):
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
                "rang":           i + 1,
                "filiere_id":     filiere_id,
                "filiere_nom":    FILIERES[filiere_id]["nom"],
                "filiere_niveau": FILIERES[filiere_id]["niveau"],
                "score_total":    details["score_total"],
                "score":          details["score_total"],
                "nom":            FILIERES[filiere_id]["nom"],
                "niveau":         FILIERES[filiere_id]["niveau"],
                "score_details":  details["scores_par_critere"],
                "eligible":       details["eligible"],
                "explication":    details["explication"]
            }
            for i, (filiere_id, details) in enumerate(classement)
        ],
        # meilleure_filiere = la 1ère filière ÉLIGIBLE (pas forcément la 1ère du classement)
        "meilleure_filiere": next(
            (fid for fid, det in classement if det["eligible"]),
            classement[0][0] if classement else None
        ),
        "profil_resume": generer_resume_profil(profil_etudiant)
    }

    print(f"[FITSCORE] ✅ Meilleure filière éligible : {resultat_final['meilleure_filiere']}")
    return resultat_final


def calculer_fitscore_filiere(profil_etudiant, filiere_id, profil_psychometrique=None):
    scores = {}
    scores["compatibilite_bac"]         = calculer_score_bac(profil_etudiant, filiere_id)
    scores["moyenne_academique"]         = calculer_score_moyenne(profil_etudiant, filiere_id)
    scores["notes_matieres_cles"]        = calculer_score_matieres(profil_etudiant, filiere_id)
    scores["profil_psychometrique"]      = calculer_score_psychometrique(profil_psychometrique, filiere_id)
    scores["centres_interet"]            = calculer_score_interets(profil_etudiant, filiere_id)
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
        "score_total":          score_total,
        "scores_par_critere":   scores,
        "eligible":             eligible,
        "raison_ineligibilite": raison_ineligibilite,
        "explication":          explication
    }


def calculer_score_bac(profil_etudiant, filiere_id):
    type_bac       = profil_etudiant.get("parcours_academique", {}).get("type_bac", "AUTRE")
    compatibilites = COMPATIBILITE_BAC_FILIERE.get(type_bac, {})
    score_compat   = compatibilites.get(filiere_id, 3)
    return min(25, score_compat * 5)


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
                if matiere.lower() in nom_matiere.lower() or nom_matiere.lower() in matiere.lower():
                    note_trouvee = float(note)
                    break
            if note_trouvee is not None:
                score_total += (note_trouvee / 20) * poids
                poids_total += poids
    if poids_total < 50:
        for matiere, poids in poids_filiere.items():
            matiere_lower = matiere.lower()
            force = 3
            if "math"    in matiere_lower: force = forces.get("force_maths", 3)
            elif "physi"  in matiere_lower: force = forces.get("force_physique", 3)
            elif "info"   in matiere_lower: force = forces.get("force_info", 2)
            elif "econom" in matiere_lower or "gestion" in matiere_lower:
                force = forces.get("force_economie", 2)
            elif "droit"  in matiere_lower: force = forces.get("force_gestion", 2)
            score_total += (force / 5) * poids * 0.5
            poids_total += poids * 0.5
    if poids_total == 0:
        return 10
    return min(20, round((score_total / poids_total) * 20))


def calculer_score_psychometrique(profil_psychometrique, filiere_id):
    if not profil_psychometrique:
        return 10
    compatibilite = profil_psychometrique.get("compatibilite_filieres", {}).get(filiere_id, 50)
    return min(20, round((compatibilite / 100) * 20))


def calculer_score_interets(profil_etudiant, filiere_id):
    scores_interets   = profil_etudiant.get("preferences", {}).get("scores_interets_filieres", {})
    score_brut        = scores_interets.get(filiere_id, 0)
    mots_cles_filiere = INTERETS_FILIERE.get(filiere_id, [])
    if not mots_cles_filiere:
        return 5
    score = min(10, round((score_brut / max(len(mots_cles_filiere), 1)) * 10))
    return max(3, score)


def calculer_score_ambition(profil_etudiant, filiere_id):
    ambition = profil_etudiant.get("preferences", {}).get("ambition_professionnelle", "").lower()
    if not ambition:
        return 3
    debouches      = [d.lower() for d in FILIERES.get(filiere_id, {}).get("debouches", [])]
    mots_ambition  = ambition.split()
    correspondances = sum(1 for mot in mots_ambition if any(mot in d for d in debouches))
    if correspondances >= 3:   return 5
    elif correspondances >= 2: return 4
    elif correspondances >= 1: return 3
    else:                      return 2


# ============================================================
# PARTIE 2 — VÉRIFICATION D'ÉLIGIBILITÉ (FIX COMPLET)
# ============================================================

# Toutes les variantes de "bachelier"
_NIVEAUX_BACHELIER = {
    "post_bac", "bac1",
    "bac", "BAC",
    "terminale", "Terminale", "TERMINALE",
    "baccalaureat", "baccalauréat",
    "lycee", "lycée",
    "1ere_annee", "1ère_annee",
}

_NIVEAUX_BAC2 = {
    "bac2", "BAC+2", "bac+2",
    "deug", "dut", "bts", "cpge",
    "2eme_annee", "2ème_annee",
    "classes préparatoires", "classesprepa", "prepa",
}

_NIVEAUX_BAC3 = {
    "bac3", "BAC+3", "bac+3",
    "licence", "bachelor",
    "3eme_annee", "3ème_annee",
    "4eme_annee", "4ème_annee",
    "licenceprofessionnelle", "licence professionnelle",
    "l3",
}

_NIVEAUX_BAC4 = {
    "bac4", "bac5", "BAC+4", "BAC+5",
    "master", "m1", "m2",
    "ingenieur", "ingénieur",
    "5eme_annee", "5ème_annee",
}


def verifier_eligibilite(profil_etudiant, filiere_id):
    """
    Vérifie si l'étudiant est éligible pour une filière.
    Retourne (eligible: bool, raison: str|None)
    """
    parcours = profil_etudiant.get("parcours_academique", {})
    type_bac = parcours.get("type_bac", "AUTRE")
    moyenne  = float(parcours.get("moyenne_generale", 0))
    niveau   = (parcours.get("niveau_actuel") or "").strip()
    diplome  = parcours.get("diplome_actuel", None)

    if not niveau:
        return True, None

    filiere_niv = FILIERES.get(filiere_id, {}).get("niveau", "")

    if niveau in _NIVEAUX_BACHELIER:
        if filiere_niv == "BAC+5":
            return False, (
                f"{filiere_id} est un cycle BAC+5 accessible après le BAC+3. "
                f"En tant que bachelier, tu intègres IISI, MGE ou MDI (BAC+3) d'abord."
            )
        return verifier_eligibilite_1ere_annee(type_bac, moyenne, filiere_id)

    elif niveau in _NIVEAUX_BAC2:
        if filiere_niv == "BAC+5":
            return False, (
                f"{filiere_id} est un cycle BAC+5. "
                f"Avec un BAC+2, tu intègres en 3ème année de IISI, MGE ou MDI."
            )
        return verifier_eligibilite_3eme_annee(diplome, moyenne, filiere_id)

    elif niveau in _NIVEAUX_BAC3:
        if filiere_niv == "BAC+3":
            return False, (
                f"{filiere_id} est un cycle BAC+3. "
                f"Avec un BAC+3, tu intègres directement les filières BAC+5 (IISIC, IISRT, FACG, MRI)."
            )
        return verifier_eligibilite_4eme_annee(diplome, moyenne, filiere_id)

    elif niveau in _NIVEAUX_BAC4:
        if filiere_niv == "BAC+3":
            return False, (
                f"{filiere_id} est un cycle BAC+3. "
                f"Avec ton niveau, tu peux intégrer directement les filières BAC+5."
            )
        return verifier_eligibilite_4eme_annee(diplome, moyenne, filiere_id)

    else:
        return True, None


def verifier_eligibilite_1ere_annee(type_bac, moyenne, filiere_id):
    conditions = CONDITIONS_ADMISSION.get("1ere_annee", {}).get(filiere_id, {})
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
        compatible = any(
            d.lower() in diplome_lower or diplome_lower in d.lower()
            for d in diplomes_compatibles
        )
        if not compatible:
            tech_kw = [
                "info", "informatique", "réseau", "reseau", "cyber", "securite",
                "sécurité", "telecom", "système", "systeme", "tech", "numérique",
                "numerique", "électronique", "electronique", "ingénierie", "ingenierie",
                "web", "dev", "développement", "developpement", "mobile", "cloud",
                "data", "ia", "intelligence", "artificielle", "machine", "learning",
                "logiciel", "software", "appli", "programmation", "digital", "code",
                "iot", "embarqué", "embarque", "python", "java", "sql", "linux",
                "full", "stack", "fullstack", "front", "back", "angular", "react",
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
        compatible = any(
            d.lower() in diplome_lower or diplome_lower in d.lower()
            for d in diplomes_compatibles
        )
        if not compatible:
            tech_kw = [
                "info", "informatique", "réseau", "reseau", "cyber", "securite",
                "sécurité", "telecom", "système", "systeme", "tech", "numérique",
                "numerique", "électronique", "electronique", "ingénierie", "ingenierie",
                "web", "dev", "développement", "developpement", "mobile", "cloud",
                "data", "ia", "intelligence", "artificielle", "machine", "learning",
                "logiciel", "software", "appli", "programmation", "digital", "code",
                "iot", "embarqué", "embarque", "python", "java", "sql", "linux",
                "full", "stack", "fullstack", "front", "back", "angular", "react",
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
# PARTIE 3 — IA EXPLICABLE
# ============================================================

def generer_explication_score(
    profil_etudiant, filiere_id, scores, score_total, eligible, raison_ineligibilite
):
    type_bac = profil_etudiant.get("parcours_academique", {}).get("type_bac", "")
    moyenne  = profil_etudiant.get("parcours_academique", {}).get("moyenne_generale", 0)

    points_forts   = []
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
        "score":                score_total,
        "eligible":             eligible,
        "points_forts":         points_forts,
        "points_faibles":       points_faibles,
        "raison_ineligibilite": raison_ineligibilite
    }


def generer_rapport_fitscore(resultats_fitscore, profil_etudiant):
    """
    Génère un rapport FitScore en recommandant UNIQUEMENT
    la meilleure filière ÉLIGIBLE — cohérence avec l'Admission.
    """
    prenom     = profil_etudiant.get("informations_personnelles", {}).get("prenom", "")
    classement = resultats_fitscore["classement"]

    # ── Séparer éligibles / non-éligibles ────────────────────
    eligibles    = [item for item in classement if item["eligible"]]
    non_eligibles = [item for item in classement if not item["eligible"]]

    if not eligibles:
        return "Complète ton profil (niveau, BAC, moyenne) pour obtenir des recommandations précises."

    top1 = eligibles[0]
    top2 = eligibles[1] if len(eligibles) > 1 else None
    top3 = eligibles[2] if len(eligibles) > 2 else None

    # ── Résumé scores pour le prompt ─────────────────────────
    resume_eligible = "\n".join([
        f"- {item['rang']}. {item['filiere_nom']} ({item['filiere_niveau']}) : "
        f"{item['score_total']}% ✅ Éligible"
        for item in eligibles
    ])
    resume_non_eligible = "\n".join([
        f"- {item['filiere_nom']} ({item['filiere_niveau']}) : "
        f"{item['score_total']}% ❌ Non éligible (niveau insuffisant)"
        for item in non_eligibles
    ]) if non_eligibles else ""

    prompt = f"""Tu es Sami, conseiller académique de SUPMTI Meknès.
Génère un rapport d'orientation personnalisé et chaleureux.

Étudiant : {prenom if prenom else 'un étudiant'}
BAC : {profil_etudiant.get('parcours_academique', {}).get('type_bac', 'inconnu')}
Moyenne : {profil_etudiant.get('parcours_academique', {}).get('moyenne_generale', 'inconnue')}/20
Diplôme actuel : {profil_etudiant.get('parcours_academique', {}).get('diplome_actuel', 'non précisé')}

Filières ÉLIGIBLES (selon le niveau) :
{resume_eligible}

{f"Filières non accessibles à son niveau : {resume_non_eligible}" if resume_non_eligible else ""}

FORMAT OBLIGATOIRE :
- ## pour les titres
- **texte** pour les données importantes
- - tirets pour les listes
- Jamais de : •, ►, ════, ─────, ####

RÈGLE ABSOLUE : recommande UNIQUEMENT parmi les filières éligibles.
Ne mentionne pas les filières non accessibles dans la recommandation principale.

Génère un rapport qui :
1. Annonce la meilleure filière éligible avec ## et enthousiasme
2. Explique pourquoi cette filière correspond (2-3 raisons en tirets)
3. Mentionne les autres options éligibles brièvement
4. Encourage l'étudiant (1-2 phrases)
Max 200 mots."""

    try:
        r = client.chat.completions.create(
            model=os.getenv("MODEL_NAME", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )
        return r.choices[0].message.content.strip()

    except Exception as e:
        print(f"[FITSCORE] Erreur génération rapport : {e}")
        # Fallback — utiliser uniquement les filières éligibles
        elig_msg = "✅ Éligible"
        ligne2 = f"- {top2['filiere_nom']} — **{top2['score_total']}%**\n" if top2 else ""
        ligne3 = f"- {top3['filiere_nom']} — **{top3['score_total']}%**\n" if top3 else ""
        return (
            f"## Ton orientation personnalisée\n\n"
            f"**Filière recommandée : {top1['filiere_nom']}**\n"
            f"Score de compatibilité : **{top1['score_total']}%** — {elig_msg}\n\n"
            f"## Autres options accessibles\n"
            + ligne2 + ligne3 +
            "\nCes résultats sont basés sur ton profil académique et tes centres d'intérêt."
        )


def generer_resume_profil(profil_etudiant):
    parcours = profil_etudiant.get("parcours_academique", {})
    infos    = profil_etudiant.get("informations_personnelles", {})
    return {
        "prenom":  infos.get("prenom", ""),
        "bac":     parcours.get("type_bac", ""),
        "moyenne": parcours.get("moyenne_generale", 0),
        "mention": parcours.get("mention", ""),
        "niveau":  parcours.get("niveau_actuel", ""),
        "diplome": parcours.get("diplome_actuel", ""),
    }