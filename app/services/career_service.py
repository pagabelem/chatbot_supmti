# ============================================================
# CAREER SERVICE — SUPMTI
# Career Simulation (4.8)
# Tahirou — backend-tahirou
# ============================================================

import os
from openai import OpenAI
from dotenv import load_dotenv
from app.academic_config import FILIERES

# ============================================================
# INITIALISATION
# ============================================================

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ============================================================
# BASE DE DONNÉES DES CARRIÈRES PAR FILIÈRE
# ============================================================

CARRIERES_FILIERES = {
    "ISI": {
        "metiers_principaux": [
            "Développeur web / mobile",
            "Analyste programmeur",
            "Administrateur réseaux",
            "Responsable informatique",
            "Chef de projet IT"
        ],
        "entreprises_maroc": [
            "OCP Group", "Maroc Telecom", "Inwi",
            "BMCE Bank", "Capgemini Maroc",
            "IBM Maroc", "startups tech Casablanca"
        ],
        "salaire_depart": "4000-7000 MAD/mois",
        "salaire_3ans": "7000-12000 MAD/mois",
        "salaire_7ans": "12000-22000 MAD/mois",
        "salaire_international": "2500-4000 EUR/mois",
        "duree_premier_emploi": "2-4 mois après diplôme",
        "taux_insertion": "85%",
        "possibilites_evolution": [
            "Chef de projet",
            "Architecte logiciel",
            "CTO d'une startup",
            "Consultant IT",
            "Entrepreneuriat tech"
        ],
        "certifications_utiles": [
            "Cisco CCNA",
            "Microsoft Azure",
            "AWS Cloud Practitioner",
            "Oracle Java"
        ],
        "poursuite_possible": ["IISIC", "IISRT", "Master France"]
    },
    "IISRT": {
        "metiers_principaux": [
            "Ingénieur réseaux",
            "Architecte systèmes réseaux",
            "Responsable infrastructure télécom",
            "Ingénieur 5G/IoT",
            "Expert cybersécurité"
        ],
        "entreprises_maroc": [
            "Maroc Telecom", "Inwi", "Orange Maroc",
            "Huawei Maroc", "Nokia Maroc",
            "ONEE", "RAM Maroc"
        ],
        "salaire_depart": "7000-12000 MAD/mois",
        "salaire_3ans": "12000-20000 MAD/mois",
        "salaire_7ans": "20000-38000 MAD/mois",
        "salaire_international": "3500-5500 EUR/mois",
        "duree_premier_emploi": "1-3 mois après diplôme",
        "taux_insertion": "90%",
        "possibilites_evolution": [
            "Directeur infrastructure",
            "Expert sécurité réseau",
            "Consultant télécom",
            "Ingénieur cloud",
            "Responsable IoT"
        ],
        "certifications_utiles": [
            "Cisco CCNP",
            "Cisco CCIE",
            "CompTIA Security+",
            "Huawei HCIA"
        ],
        "poursuite_possible": ["Master France", "Master Lorraine SUPMTI"]
    },
    "IISIC": {
        "metiers_principaux": [
            "Ingénieur IA / Machine Learning",
            "Data Scientist",
            "Architecte systèmes d'information",
            "Chef de projet digital",
            "Consultant transformation digitale"
        ],
        "entreprises_maroc": [
            "OCP Digital", "CDG Capital",
            "Bank Al-Maghrib", "Amadeus Maroc",
            "Capgemini", "Accenture Maroc",
            "startups IA Casablanca/Rabat"
        ],
        "salaire_depart": "7000-12000 MAD/mois",
        "salaire_3ans": "12000-20000 MAD/mois",
        "salaire_7ans": "20000-40000 MAD/mois",
        "salaire_international": "4000-7000 EUR/mois",
        "duree_premier_emploi": "1-2 mois après diplôme",
        "taux_insertion": "92%",
        "possibilites_evolution": [
            "Lead Data Scientist",
            "Directeur IA",
            "CTO / fondateur startup IA",
            "Chercheur en IA",
            "Consultant international"
        ],
        "certifications_utiles": [
            "TensorFlow Developer",
            "AWS Machine Learning",
            "Google Cloud ML",
            "Microsoft Azure AI"
        ],
        "poursuite_possible": ["Doctorat", "Master IA France", "Master Lorraine"]
    },
    "ME": {
        "metiers_principaux": [
            "Responsable commercial",
            "Chargé marketing digital",
            "Assistant RH",
            "Analyste financier junior",
            "Chef de projet junior"
        ],
        "entreprises_maroc": [
            "Banques marocaines (CIH, Attijari, BMCE)",
            "Sociétés d'assurance",
            "Entreprises de distribution",
            "Agences marketing digital",
            "PME marocaines"
        ],
        "salaire_depart": "4000-6000 MAD/mois",
        "salaire_3ans": "6000-10000 MAD/mois",
        "salaire_7ans": "10000-18000 MAD/mois",
        "salaire_international": "2000-3500 EUR/mois",
        "duree_premier_emploi": "3-5 mois après diplôme",
        "taux_insertion": "78%",
        "possibilites_evolution": [
            "Directeur commercial",
            "Responsable marketing",
            "DRH",
            "Directeur général PME",
            "Entrepreneur"
        ],
        "certifications_utiles": [
            "Google Analytics",
            "HubSpot Marketing",
            "PMP (Project Management)",
            "Certification RH"
        ],
        "poursuite_possible": ["FACG", "MSTIC", "Master Management France"]
    },
    "FACG": {
        "metiers_principaux": [
            "Auditeur financier",
            "Contrôleur de gestion",
            "Expert-comptable",
            "Directeur financier",
            "Commissaire aux comptes"
        ],
        "entreprises_maroc": [
            "Deloitte Maroc", "PwC Maroc",
            "KPMG Maroc", "Ernst & Young Maroc",
            "Bank Al-Maghrib", "CDG",
            "Grandes entreprises cotées"
        ],
        "salaire_depart": "6000-9000 MAD/mois",
        "salaire_3ans": "9000-15000 MAD/mois",
        "salaire_7ans": "15000-30000 MAD/mois",
        "salaire_international": "3500-6000 EUR/mois",
        "duree_premier_emploi": "2-3 mois après diplôme",
        "taux_insertion": "88%",
        "possibilites_evolution": [
            "Associé cabinet d'audit",
            "Directeur financier groupe",
            "Expert-comptable indépendant",
            "Directeur général",
            "Consultant finance internationale"
        ],
        "certifications_utiles": [
            "CPA (Certified Public Accountant)",
            "CFA (Chartered Financial Analyst)",
            "ACCA",
            "Expertise Comptable Maroc"
        ],
        "poursuite_possible": ["Master Finance France", "CFA", "DSCG"]
    },
    "MSTIC": {
        "metiers_principaux": [
            "Responsable systèmes d'information",
            "Manager transformation digitale",
            "Chef de projet SI",
            "Responsable e-commerce",
            "Consultant management digital"
        ],
        "entreprises_maroc": [
            "Groupe OCP", "Royal Air Maroc",
            "Maroc Telecom", "grandes banques",
            "cabinets conseil", "multinationales"
        ],
        "salaire_depart": "6000-9000 MAD/mois",
        "salaire_3ans": "9000-15000 MAD/mois",
        "salaire_7ans": "15000-28000 MAD/mois",
        "salaire_international": "3000-5000 EUR/mois",
        "duree_premier_emploi": "2-4 mois après diplôme",
        "taux_insertion": "82%",
        "possibilites_evolution": [
            "DSI (Directeur Systèmes d'Information)",
            "Directeur digital",
            "CEO startup",
            "Consultant international",
            "Entrepreneur tech"
        ],
        "certifications_utiles": [
            "PMP", "Scrum Master",
            "ITIL", "Microsoft 365"
        ],
        "poursuite_possible": ["Master Management France", "MBA"]
    }
}

# ============================================================
# PARTIE 1 — SIMULATION DE CARRIÈRE PRINCIPALE
# ============================================================

def simuler_carriere(profil_etudiant, filiere_id):
    """
    Génère une simulation de carrière complète et personnalisée.
    """
    print(f"[CAREER] Simulation carrière pour filière {filiere_id}...")

    prenom = profil_etudiant.get("informations_personnelles", {}).get("prenom", "")
    ville = profil_etudiant.get("informations_personnelles", {}).get("ville", "Maroc")
    ambition = profil_etudiant.get("preferences", {}).get("ambition_professionnelle", "")
    interets = profil_etudiant.get("preferences", {}).get("centres_interet", [])
    moyenne = profil_etudiant.get("parcours_academique", {}).get("moyenne_generale", 0)

    filiere = FILIERES.get(filiere_id, {})
    carriere = CARRIERES_FILIERES.get(filiere_id, {})

    prompt = f"""Tu es Sami, conseiller académique de SUPMTI Meknès.
Génère une simulation de carrière immersive et personnalisée.

PROFIL ÉTUDIANT :
- Prénom : {prenom if prenom else "l'étudiant"}
- Ville : {ville}
- Ambition : {ambition if ambition else 'non précisée'}
- Centres d'intérêt : {', '.join(interets) if interets else 'non précisés'}
- Moyenne : {moyenne}/20

FILIÈRE CHOISIE : {filiere.get('nom', filiere_id)}
Niveau : {filiere.get('niveau', '')}
Durée : {filiere.get('duree', '')} ans

DONNÉES CARRIÈRE RÉELLES :
- Métiers : {', '.join(carriere.get('metiers_principaux', [])[:3])}
- Entreprises au Maroc : {', '.join(carriere.get('entreprises_maroc', [])[:4])}
- Salaire départ : {carriere.get('salaire_depart', '')}
- Salaire après 3 ans : {carriere.get('salaire_3ans', '')}
- Salaire après 7 ans : {carriere.get('salaire_7ans', '')}
- Taux insertion : {carriere.get('taux_insertion', '')}

GÉNÈRE une simulation narrative en 4 phases :

📚 PHASE 1 — Formation à SUPMTI (Années 1-{filiere.get('duree', 3)}) :
Décris la vie étudiante, les projets, les stages, les certifications.

💼 PHASE 2 — Premier Emploi (Année {filiere.get('duree', 3) + 1}) :
Décris le premier poste, l'entreprise type, le salaire, les défis.

🚀 PHASE 3 — Évolution (Années {filiere.get('duree', 3) + 2}-{filiere.get('duree', 3) + 5}) :
Décris la progression professionnelle, les promotions, les projets.

🌟 PHASE 4 — Perspective Long Terme (Années {filiere.get('duree', 3) + 6}+) :
Décris les opportunités futures, international, entrepreneuriat possible.

RÈGLES :
- Utilise le prénom {prenom if prenom else "de l'étudiant"} pour personnaliser
- Sois réaliste mais optimiste
- Inclus des chiffres concrets (salaires en MAD)
- Mentionne des entreprises marocaines réelles
- Max 350 mots
- Utilise des emojis pour structurer"""

    try:
        reponse_gpt = client.chat.completions.create(
            model="gpt-5.2",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_completion_tokens=700
        )
        scenario = reponse_gpt.choices[0].message.content.strip()
        print(f"[CAREER] ✅ Simulation générée pour {filiere_id}")

        return {
            "filiere_id": filiere_id,
            "filiere_nom": filiere.get("nom", filiere_id),
            "scenario": scenario,
            "donnees_cles": {
                "salaire_depart": carriere.get("salaire_depart"),
                "salaire_3ans": carriere.get("salaire_3ans"),
                "salaire_7ans": carriere.get("salaire_7ans"),
                "salaire_international": carriere.get("salaire_international"),
                "taux_insertion": carriere.get("taux_insertion"),
                "duree_premier_emploi": carriere.get("duree_premier_emploi"),
                "certifications_utiles": carriere.get("certifications_utiles", []),
                "poursuite_possible": carriere.get("poursuite_possible", [])
            }
        }

    except Exception as e:
        print(f"[CAREER] Erreur simulation : {e}")
        return generer_simulation_fallback(profil_etudiant, filiere_id)


def generer_simulation_fallback(profil_etudiant, filiere_id):
    """Simulation de base si GPT échoue"""
    prenom = profil_etudiant.get("informations_personnelles", {}).get("prenom", "")
    filiere = FILIERES.get(filiere_id, {})
    carriere = CARRIERES_FILIERES.get(filiere_id, {})

    scenario = f"""📚 **PHASE 1 — Formation à SUPMTI ({filiere.get('duree', 3)} ans)**
{prenom + ' intègre' if prenom else 'Tu intègres'} SUPMTI Meknès en {filiere.get('nom', filiere_id)}.
Projets pratiques, stages en entreprise et certifications professionnelles.

💼 **PHASE 2 — Premier Emploi**
Insertion en {carriere.get('duree_premier_emploi', '2-4 mois')}.
Salaire de départ : {carriere.get('salaire_depart', 'variable')}.
Taux d'insertion : {carriere.get('taux_insertion', '80%')}.

🚀 **PHASE 3 — Évolution**
Après 3 ans : {carriere.get('salaire_3ans', 'variable')}.
Évolution vers : {', '.join(carriere.get('possibilites_evolution', [])[:2])}.

🌟 **PHASE 4 — Long Terme**
Après 7 ans : {carriere.get('salaire_7ans', 'variable')}.
Opportunités internationales : {carriere.get('salaire_international', 'variable')}."""

    return {
        "filiere_id": filiere_id,
        "filiere_nom": filiere.get("nom", filiere_id),
        "scenario": scenario,
        "donnees_cles": {
            "salaire_depart": carriere.get("salaire_depart"),
            "salaire_3ans": carriere.get("salaire_3ans"),
            "salaire_7ans": carriere.get("salaire_7ans"),
            "taux_insertion": carriere.get("taux_insertion")
        }
    }


# ============================================================
# PARTIE 2 — COMPARAISON DE CARRIÈRES
# ============================================================

def comparer_carrieres(profil_etudiant, filiere_id_1, filiere_id_2):
    """Compare les carrières de 2 filières côte à côte"""
    print(f"[CAREER] Comparaison {filiere_id_1} vs {filiere_id_2}...")

    carriere_1 = CARRIERES_FILIERES.get(filiere_id_1, {})
    carriere_2 = CARRIERES_FILIERES.get(filiere_id_2, {})
    filiere_1 = FILIERES.get(filiere_id_1, {})
    filiere_2 = FILIERES.get(filiere_id_2, {})
    prenom = profil_etudiant.get("informations_personnelles", {}).get("prenom", "")

    comparaison = f"""⚖️ **Comparaison de Carrières**
{'Pour ' + prenom if prenom else ''}

{'─' * 50}
📊 **{filiere_1.get('nom', filiere_id_1)}** ({filiere_1.get('niveau', '')})
vs
📊 **{filiere_2.get('nom', filiere_id_2)}** ({filiere_2.get('niveau', '')})
{'─' * 50}

💰 **SALAIRES**
| Période | {filiere_id_1} | {filiere_id_2} |
|---------|-------|-------|
| Départ | {carriere_1.get('salaire_depart', 'N/A')} | {carriere_2.get('salaire_depart', 'N/A')} |
| 3 ans | {carriere_1.get('salaire_3ans', 'N/A')} | {carriere_2.get('salaire_3ans', 'N/A')} |
| 7 ans | {carriere_1.get('salaire_7ans', 'N/A')} | {carriere_2.get('salaire_7ans', 'N/A')} |
| International | {carriere_1.get('salaire_international', 'N/A')} | {carriere_2.get('salaire_international', 'N/A')} |

⏱️ **INSERTION PROFESSIONNELLE**
- {filiere_id_1} : {carriere_1.get('duree_premier_emploi', 'N/A')} — Taux : {carriere_1.get('taux_insertion', 'N/A')}
- {filiere_id_2} : {carriere_2.get('duree_premier_emploi', 'N/A')} — Taux : {carriere_2.get('taux_insertion', 'N/A')}

🎯 **MÉTIERS PRINCIPAUX**
**{filiere_id_1} :**
{chr(10).join(['• ' + m for m in carriere_1.get('metiers_principaux', [])[:3]])}

**{filiere_id_2} :**
{chr(10).join(['• ' + m for m in carriere_2.get('metiers_principaux', [])[:3]])}

🏢 **ENTREPRISES QUI RECRUTENT AU MAROC**
**{filiere_id_1} :** {', '.join(carriere_1.get('entreprises_maroc', [])[:3])}
**{filiere_id_2} :** {', '.join(carriere_2.get('entreprises_maroc', [])[:3])}

📈 **ÉVOLUTION POSSIBLE**
**{filiere_id_1} :** {', '.join(carriere_1.get('possibilites_evolution', [])[:2])}
**{filiere_id_2} :** {', '.join(carriere_2.get('possibilites_evolution', [])[:2])}"""

    recommandation = generer_recommandation_comparative(
        profil_etudiant, filiere_id_1, filiere_id_2,
        carriere_1, carriere_2
    )

    return {
        "comparaison": comparaison,
        "recommandation": recommandation,
        "filiere_1": filiere_id_1,
        "filiere_2": filiere_id_2
    }


def generer_recommandation_comparative(
    profil_etudiant, filiere_id_1, filiere_id_2,
    carriere_1, carriere_2
):
    """Génère une recommandation personnalisée entre 2 filières"""
    prenom = profil_etudiant.get("informations_personnelles", {}).get("prenom", "")
    interets = profil_etudiant.get("preferences", {}).get("centres_interet", [])
    ambition = profil_etudiant.get("preferences", {}).get("ambition_professionnelle", "")

    prompt = f"""Tu es Sami, conseiller académique de SUPMTI Meknès.

Un étudiant {'(' + prenom + ') ' if prenom else ''}compare deux filières.
Intérêts : {', '.join(interets) if interets else 'non précisés'}
Ambition : {ambition if ambition else 'non précisée'}

Filière 1 — {filiere_id_1} :
- Salaire départ : {carriere_1.get('salaire_depart')}
- Taux insertion : {carriere_1.get('taux_insertion')}
- Métiers : {', '.join(carriere_1.get('metiers_principaux', [])[:2])}

Filière 2 — {filiere_id_2} :
- Salaire départ : {carriere_2.get('salaire_depart')}
- Taux insertion : {carriere_2.get('taux_insertion')}
- Métiers : {', '.join(carriere_2.get('metiers_principaux', [])[:2])}

Génère une recommandation personnalisée de 3-4 lignes.
Style naturel, encourageant."""

    try:
        reponse = client.chat.completions.create(
            model="gpt-5.2",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_completion_tokens=200
        )
        return reponse.choices[0].message.content.strip()

    except Exception as e:
        print(f"[CAREER] Erreur recommandation : {e}")
        return f"Les deux filières offrent de belles perspectives. Choisis selon tes passions !"


# ============================================================
# PARTIE 3 — PROGRESSION SALARIALE
# ============================================================

def generer_progression_salariale(filiere_id):
    """Retourne les données de progression salariale pour Basile"""
    carriere = CARRIERES_FILIERES.get(filiere_id, {})

    def extraire_milieu(fourchette):
        try:
            parties = fourchette.replace(
                " MAD/mois", ""
            ).replace(" EUR/mois", "").split("-")
            return (int(parties[0]) + int(parties[1])) // 2
        except:
            return 0

    return {
        "filiere_id": filiere_id,
        "filiere_nom": FILIERES.get(filiere_id, {}).get("nom", filiere_id),
        "progression": [
            {
                "periode": "Départ",
                "annee": 0,
                "fourchette": carriere.get("salaire_depart", "N/A"),
                "valeur_mediane": extraire_milieu(carriere.get("salaire_depart", "0-0"))
            },
            {
                "periode": "Après 3 ans",
                "annee": 3,
                "fourchette": carriere.get("salaire_3ans", "N/A"),
                "valeur_mediane": extraire_milieu(carriere.get("salaire_3ans", "0-0"))
            },
            {
                "periode": "Après 7 ans",
                "annee": 7,
                "fourchette": carriere.get("salaire_7ans", "N/A"),
                "valeur_mediane": extraire_milieu(carriere.get("salaire_7ans", "0-0"))
            }
        ],
        "taux_insertion": carriere.get("taux_insertion", "N/A"),
        "certifications": carriere.get("certifications_utiles", [])
    }


# ============================================================
# PARTIE 4 — COMPARAISON INTELLIGENTE SELON NIVEAU
# ============================================================

def obtenir_filieres_comparables(profil_etudiant):
    """
    Retourne uniquement les filières accessibles selon le niveau.

    Logique SUPMTI :
    Ingénierie  : Terminal → ISI (BAC+3) → IISIC ou IISRT (BAC+5)
    Management  : Terminal → ME  (BAC+3) → FACG  ou MSTIC  (BAC+5)
    """
    parcours = profil_etudiant.get("parcours_academique", {})
    niveau = parcours.get("niveau_actuel", "post_bac")
    diplome = parcours.get("diplome_actuel", "") or ""

    # ── Post-BAC (Terminale) ──
    if niveau == "post_bac":
        return {
            "filieres_accessibles": ["ISI", "ME"],
            "explication": (
                "En tant que bachelier, tu intègres la 1ère année de SUPMTI. "
                "Deux portes d'entrée : ISI (Ingénierie) ou ME (Management). "
                "Les BAC+5 se préparent après le BAC+3 ou via admission parallèle."
            ),
            "note": (
                "ISI mène naturellement vers IISIC ou IISRT. "
                "ME mène naturellement vers FACG ou MSTIC."
            ),
            "annee_entree": "1ère année"
        }

    # ── BAC+1 validé ──
    elif niveau == "bac1":
        return {
            "filieres_accessibles": ["ISI", "ME"],
            "explication": (
                "Avec une 1ère année post-BAC validée, tu peux intégrer "
                "SUPMTI en 2ème année via admission parallèle."
            ),
            "note": "Étude de dossier et entretien requis.",
            "annee_entree": "2ème année"
        }

    # ── BAC+2 : DUT, BTS, DEUG, TS ──
    elif niveau == "bac2" or any(
        d in diplome.upper() for d in ["DUT", "BTS", "DEUG", "TS"]
    ):
        return {
            "filieres_accessibles": ["ISI", "ME", "IISIC", "IISRT", "FACG", "MSTIC"],
            "explication": (
                "Avec ton diplôme BAC+2, tu peux intégrer SUPMTI "
                "en 3ème année selon ta spécialité."
            ),
            "note": (
                "Diplôme technique → Département Ingénierie. "
                "Diplôme gestion → Département Management."
            ),
            "annee_entree": "3ème année"
        }

    # ── BAC+3 : Licence, ISI SUPMTI, ME SUPMTI ──
    elif niveau == "bac3" or any(
        d in diplome.upper() for d in ["LICENCE", "LICENSE", "BAC+3", "BAC 3"]
    ):
        # Cas ISI SUPMTI → IISIC ou IISRT
        if "ISI" in diplome.upper():
            return {
                "filieres_accessibles": ["IISIC", "IISRT"],
                "explication": (
                    "Avec ton BAC+3 ISI de SUPMTI, tu continues "
                    "naturellement en 4ème année de IISIC ou IISRT."
                ),
                "note": (
                    "IISIC → IA et Data Science. "
                    "IISRT → Réseaux et Télécommunications."
                ),
                "annee_entree": "4ème année"
            }

        # Cas ME SUPMTI → FACG ou MSTIC
        elif any(d in diplome.upper() for d in ["ME", "MANAGEMENT DES ENTREPRISES"]):
            return {
                "filieres_accessibles": ["FACG", "MSTIC"],
                "explication": (
                    "Avec ton BAC+3 ME de SUPMTI, tu continues "
                    "naturellement en 4ème année de FACG ou MSTIC."
                ),
                "note": (
                    "FACG → Finance et Audit. "
                    "MSTIC → Management Digital."
                ),
                "annee_entree": "4ème année"
            }

        # Licence Informatique → Ingénierie
        elif any(
            d in diplome.upper()
            for d in ["INFO", "INFORMATIQUE", "RESEAU", "TELECOM"]
        ):
            return {
                "filieres_accessibles": ["IISIC", "IISRT"],
                "explication": (
                    "Avec ta Licence en informatique/réseaux, "
                    "tu intègres SUPMTI en 4ème année ingénierie."
                ),
                "note": (
                    "IISIC → IA, Data Science. "
                    "IISRT → Réseaux intelligents, Télécommunications."
                ),
                "annee_entree": "4ème année"
            }

        # Licence Gestion → Management
        elif any(
            d in diplome.upper()
            for d in ["GESTION", "MANAGEMENT", "ECONOMIE", "COMMERCE", "FINANCE", "COMPTABILITE"]
        ):
            return {
                "filieres_accessibles": ["FACG", "MSTIC"],
                "explication": (
                    "Avec ta Licence en gestion/économie, "
                    "tu intègres SUPMTI en 4ème année management."
                ),
                "note": (
                    "FACG → Finance, Audit, Contrôle de gestion. "
                    "MSTIC → Management digital, Systèmes d'information."
                ),
                "annee_entree": "4ème année"
            }

        # Licence autre → toutes les BAC+5
        else:
            return {
                "filieres_accessibles": ["IISIC", "IISRT", "FACG", "MSTIC"],
                "explication": (
                    "Avec un BAC+3, tu peux intégrer les filières "
                    "BAC+5 de SUPMTI en 4ème année."
                ),
                "note": (
                    "Ingénierie : IISIC ou IISRT. "
                    "Management : FACG ou MSTIC."
                ),
                "annee_entree": "4ème année"
            }

    # Par défaut : post-BAC
    else:
        return {
            "filieres_accessibles": ["ISI", "ME"],
            "explication": "Tu peux intégrer la 1ère année de SUPMTI.",
            "note": "ISI (Ingénierie) ou ME (Management).",
            "annee_entree": "1ère année"
        }


def comparer_carrieres_intelligent(
    profil_etudiant,
    filiere_id_1=None,
    filiere_id_2=None
):
    """
    Version intelligente du comparateur.
    Vérifie que les filières sont accessibles selon le niveau.
    """
    info_filieres = obtenir_filieres_comparables(profil_etudiant)
    filieres_accessibles = info_filieres["filieres_accessibles"]

    # Si filières non spécifiées → prendre les 2 premières accessibles
    if not filiere_id_1 or not filiere_id_2:
        if len(filieres_accessibles) >= 2:
            filiere_id_1 = filieres_accessibles[0]
            filiere_id_2 = filieres_accessibles[1]
        else:
            return {
                "erreur": "Pas assez de filières accessibles pour une comparaison.",
                "filieres_accessibles": filieres_accessibles,
                "info_niveau": info_filieres
            }

    # Vérifier que les filières demandées sont accessibles
    avertissements = []

    if filiere_id_1 not in filieres_accessibles:
        niveau_filiere = FILIERES.get(filiere_id_1, {}).get("niveau", "")
        avertissements.append(
            f"⚠️ {filiere_id_1} ({niveau_filiere}) n'est pas accessible "
            f"à ton niveau actuel. "
            f"Filières accessibles : {', '.join(filieres_accessibles)}."
        )

    if filiere_id_2 not in filieres_accessibles:
        niveau_filiere = FILIERES.get(filiere_id_2, {}).get("niveau", "")
        avertissements.append(
            f"⚠️ {filiere_id_2} ({niveau_filiere}) n'est pas accessible "
            f"à ton niveau actuel. "
            f"Filières accessibles : {', '.join(filieres_accessibles)}."
        )

    # Construire le résultat
    resultat = comparer_carrieres(profil_etudiant, filiere_id_1, filiere_id_2)
    resultat["info_niveau"] = info_filieres
    resultat["avertissements"] = avertissements
    resultat["filieres_accessibles"] = filieres_accessibles

    if avertissements:
        resultat["comparaison"] = (
            "\n".join(avertissements) + "\n\n" + resultat["comparaison"]
        )

    return resultat
