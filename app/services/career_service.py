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

    "IISI": {
        "metiers_principaux": [
            "Développeur web / mobile",
            "Analyste programmeur",
            "Administrateur réseaux",
            "Responsable informatique",
            "Chef de projet IT",
            "Intégrateur de solutions informatiques"
        ],
        "entreprises_maroc": [
            "OCP Group", "Maroc Telecom", "Inwi",
            "BMCE Bank", "Capgemini Maroc",
            "IBM Maroc", "startups tech Casablanca"
        ],
        "salaire_depart":         "4000-7000 MAD/mois",
        "salaire_3ans":           "7000-12000 MAD/mois",
        "salaire_7ans":           "12000-22000 MAD/mois",
        "salaire_international":  "2500-4000 EUR/mois",
        "duree_premier_emploi":   "2-4 mois après diplôme",
        "taux_insertion":         "85%",
        "possibilites_evolution": [
            "Chef de projet IT",
            "Architecte logiciel",
            "CTO d'une startup",
            "Consultant IT",
            "Entrepreneuriat tech"
        ],
        "certifications_utiles": [
            "Cisco CCNA", "Microsoft Azure",
            "AWS Cloud Practitioner", "Oracle Java"
        ],
        "poursuite_possible": ["IISIC", "IISRT", "Master France"]
    },

    "IISRT": {
        "metiers_principaux": [
            "Ingénieur réseaux",
            "Architecte systèmes réseaux",
            "Responsable infrastructure télécom",
            "Ingénieur 5G / IoT",
            "Expert cybersécurité réseaux",
            "Ingénieur en télécommunications"
        ],
        "entreprises_maroc": [
            "Maroc Telecom", "Inwi", "Orange Maroc",
            "Huawei Maroc", "Nokia Maroc",
            "ONEE", "RAM Maroc"
        ],
        "salaire_depart":         "7000-12000 MAD/mois",
        "salaire_3ans":           "12000-20000 MAD/mois",
        "salaire_7ans":           "20000-38000 MAD/mois",
        "salaire_international":  "3500-5500 EUR/mois",
        "duree_premier_emploi":   "1-3 mois après diplôme",
        "taux_insertion":         "90%",
        "possibilites_evolution": [
            "Directeur infrastructure",
            "Expert sécurité réseau",
            "Consultant télécom",
            "Ingénieur cloud",
            "Responsable IoT"
        ],
        "certifications_utiles": [
            "Cisco CCNP", "Cisco CCIE",
            "CompTIA Security+", "Huawei HCIA"
        ],
        "poursuite_possible": ["Master France", "Master Lorraine SUPMTI"]
    },

    "IISIC": {
        "metiers_principaux": [
            "Ingénieur IA / Machine Learning",
            "Data Scientist",
            "Architecte systèmes d'information",
            "Chef de projet digital",
            "Consultant transformation digitale",
            "Responsable cybersécurité SI"
        ],
        "entreprises_maroc": [
            "OCP Digital", "CDG Capital",
            "Bank Al-Maghrib", "Amadeus Maroc",
            "Capgemini", "Accenture Maroc",
            "startups IA Casablanca/Rabat"
        ],
        "salaire_depart":         "7000-12000 MAD/mois",
        "salaire_3ans":           "12000-20000 MAD/mois",
        "salaire_7ans":           "20000-40000 MAD/mois",
        "salaire_international":  "4000-7000 EUR/mois",
        "duree_premier_emploi":   "1-2 mois après diplôme",
        "taux_insertion":         "92%",
        "possibilites_evolution": [
            "Lead Data Scientist",
            "Directeur IA",
            "CTO / fondateur startup IA",
            "Chercheur en IA",
            "Consultant international"
        ],
        "certifications_utiles": [
            "TensorFlow Developer", "AWS Machine Learning",
            "Google Cloud ML", "Microsoft Azure AI"
        ],
        "poursuite_possible": ["Doctorat", "Master IA France", "Master Lorraine"]
    },

    "MGE": {
        "metiers_principaux": [
            "Responsable commercial",
            "Chargé marketing digital",
            "Assistant RH",
            "Analyste financier junior",
            "Chef de projet junior",
            "Cadre administratif"
        ],
        "entreprises_maroc": [
            "Banques marocaines (CIH, Attijari, BMCE)",
            "Sociétés d'assurance",
            "Entreprises de distribution",
            "Agences marketing digital",
            "PME marocaines"
        ],
        "salaire_depart":         "4000-6000 MAD/mois",
        "salaire_3ans":           "6000-10000 MAD/mois",
        "salaire_7ans":           "10000-18000 MAD/mois",
        "salaire_international":  "2000-3500 EUR/mois",
        "duree_premier_emploi":   "3-5 mois après diplôme",
        "taux_insertion":         "80%",
        "possibilites_evolution": [
            "Directeur commercial",
            "Responsable marketing",
            "DRH",
            "Directeur général PME",
            "Entrepreneur"
        ],
        "certifications_utiles": [
            "Google Analytics", "HubSpot Marketing",
            "PMP (Project Management)", "Certification RH"
        ],
        "poursuite_possible": ["FACG", "MRI", "Master Management France"]
    },

    "MDI": {
        "metiers_principaux": [
            "Responsable du commerce international",
            "Chargé de développement international",
            "Responsable import-export",
            "Chargé d'affaires internationales",
            "Responsable marketing international",
            "Consultant en développement international"
        ],
        "entreprises_maroc": [
            "OCP Group (export)", "RAM Cargo",
            "CIH Bank (international)", "BMCE Bank International",
            "Entreprises d'import-export", "Multinationales au Maroc"
        ],
        "salaire_depart":         "4000-6000 MAD/mois",
        "salaire_3ans":           "6000-10000 MAD/mois",
        "salaire_7ans":           "10000-18000 MAD/mois",
        "salaire_international":  "2500-4000 EUR/mois",
        "duree_premier_emploi":   "3-5 mois après diplôme",
        "taux_insertion":         "78%",
        "possibilites_evolution": [
            "Directeur du commerce international",
            "Responsable zone Afrique/Europe",
            "DG filiale internationale",
            "Consultant stratégie internationale",
            "Entrepreneur international"
        ],
        "certifications_utiles": [
            "Incoterms ICC", "CCI Export",
            "TOEIC/TOEFL", "Certificat Commerce International"
        ],
        "poursuite_possible": ["MRI", "FACG", "Master Commerce International France"]
    },

    "FACG": {
        "metiers_principaux": [
            "Auditeur financier ou comptable",
            "Contrôleur de gestion",
            "Expert-comptable",
            "Directeur financier",
            "Commissaire aux comptes",
            "Conseiller en finance internationale"
        ],
        "entreprises_maroc": [
            "Deloitte Maroc", "PwC Maroc",
            "KPMG Maroc", "Ernst & Young Maroc",
            "Bank Al-Maghrib", "CDG",
            "Grandes entreprises cotées à la bourse de Casablanca"
        ],
        "salaire_depart":         "6000-9000 MAD/mois",
        "salaire_3ans":           "9000-15000 MAD/mois",
        "salaire_7ans":           "15000-30000 MAD/mois",
        "salaire_international":  "3500-6000 EUR/mois",
        "duree_premier_emploi":   "2-3 mois après diplôme",
        "taux_insertion":         "88%",
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
            "ACCA", "Expertise Comptable Maroc"
        ],
        "poursuite_possible": ["Master Finance France", "CFA", "DSCG"]
    },

    "MRI": {
        "metiers_principaux": [
            "Manager d'entreprise internationale",
            "Responsable marketing international",
            "Consultant en stratégie internationale",
            "Responsable de la supply chain internationale",
            "Responsable des relations internationales",
            "Chargé d'affaires internationales"
        ],
        "entreprises_maroc": [
            "OCP Group", "RAM (international)",
            "BMCE Bank International", "Groupe Addoha",
            "Cabinets conseil internationaux", "Organisations internationales"
        ],
        "salaire_depart":         "6000-9000 MAD/mois",
        "salaire_3ans":           "9000-15000 MAD/mois",
        "salaire_7ans":           "15000-28000 MAD/mois",
        "salaire_international":  "3000-5500 EUR/mois",
        "duree_premier_emploi":   "2-4 mois après diplôme",
        "taux_insertion":         "82%",
        "possibilites_evolution": [
            "Directeur zone Afrique/MENA",
            "DG entreprise internationale",
            "Consultant stratégie internationale senior",
            "Responsable supply chain groupe",
            "Entrepreneur international"
        ],
        "certifications_utiles": [
            "PMP International", "CIPS (Supply Chain)",
            "TOEIC/TOEFL avancé", "Certificat Relations Internationales"
        ],
        "poursuite_possible": ["MBA International", "Master RI France", "Doctorat Sciences de Gestion"]
    }
}

# ============================================================
# PARTIE 1 — SIMULATION DE CARRIÈRE PRINCIPALE
# ============================================================

def simuler_carriere(profil_etudiant, filiere_id):
    """Génère une simulation de carrière complète et personnalisée."""
    print(f"[CAREER] Simulation carrière pour filière {filiere_id}...")

    prenom   = profil_etudiant.get("informations_personnelles", {}).get("prenom", "")
    ville    = profil_etudiant.get("informations_personnelles", {}).get("ville", "Maroc")
    ambition = profil_etudiant.get("preferences", {}).get("ambition_professionnelle", "")
    interets = profil_etudiant.get("preferences", {}).get("centres_interet", [])
    moyenne  = profil_etudiant.get("parcours_academique", {}).get("moyenne_generale", 0)

    filiere  = FILIERES.get(filiere_id, {})
    carriere = CARRIERES_FILIERES.get(filiere_id, {})

    # FIX : forcer int() sur duree pour éviter TypeError si la valeur est string
    duree = int(filiere.get("duree", 3))

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
Durée : {duree} ans

DONNÉES CARRIÈRE RÉELLES :
- Métiers : {', '.join(carriere.get('metiers_principaux', [])[:3])}
- Entreprises au Maroc : {', '.join(carriere.get('entreprises_maroc', [])[:4])}
- Salaire départ : {carriere.get('salaire_depart', '')}
- Salaire après 3 ans : {carriere.get('salaire_3ans', '')}
- Salaire après 7 ans : {carriere.get('salaire_7ans', '')}
- Taux insertion : {carriere.get('taux_insertion', '')}

GÉNÈRE une simulation narrative en 4 phases avec ce FORMAT EXACT :

## Formation à SUPMTI (Années 1-{duree})
Décris la vie étudiante, les projets, les stages, les certifications.

## Premier Emploi (Année {duree + 1})
Décris le premier poste, l'entreprise type, les défis, le salaire (**X 000 MAD/mois**).

## Évolution (Années {duree + 2}-{duree + 5})
Décris la progression professionnelle, les promotions, les projets.

## Perspectives Long Terme (Années {duree + 6}+)
Décris les opportunités futures, international, entrepreneuriat possible.

FORMAT OBLIGATOIRE :
- ## pour chaque titre de phase (ex: ## Formation à SUPMTI)
- **texte** pour les salaires, chiffres, noms d'entreprises
- - tirets pour les listes d'éléments
- Jamais de : •, ►, ════, ─────, ####

RÈGLES :
- Utilise le prénom {prenom if prenom else "l'étudiant"} pour personnaliser
- Sois réaliste mais optimiste
- Inclus des chiffres concrets (salaires en MAD)
- Mentionne des entreprises marocaines réelles
- Max 350 mots"""

    try:
        r = client.chat.completions.create(
            model="gpt-5.2",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_completion_tokens=700
        )
        scenario = r.choices[0].message.content.strip()
        print(f"[CAREER] ✅ Simulation générée pour {filiere_id}")

        return {
            "filiere_id":   filiere_id,
            "filiere_nom":  filiere.get("nom", filiere_id),
            "scenario":     scenario,
            "donnees_cles": {
                "salaire_depart":       carriere.get("salaire_depart"),
                "salaire_3ans":         carriere.get("salaire_3ans"),
                "salaire_7ans":         carriere.get("salaire_7ans"),
                "salaire_international": carriere.get("salaire_international"),
                "taux_insertion":       carriere.get("taux_insertion"),
                "duree_premier_emploi": carriere.get("duree_premier_emploi"),
                "certifications_utiles": carriere.get("certifications_utiles", []),
                "poursuite_possible":   carriere.get("poursuite_possible", [])
            }
        }

    except Exception as e:
        print(f"[CAREER] Erreur simulation : {e}")
        return generer_simulation_fallback(profil_etudiant, filiere_id)


def generer_simulation_fallback(profil_etudiant, filiere_id):
    """Simulation de base si GPT échoue."""
    prenom   = profil_etudiant.get("informations_personnelles", {}).get("prenom", "")
    filiere  = FILIERES.get(filiere_id, {})
    carriere = CARRIERES_FILIERES.get(filiere_id, {})
    duree    = int(filiere.get("duree", 3))  # FIX : int() forcé

    scenario = (
        f"## Formation à SUPMTI ({duree} ans)\n"
        f"{prenom + ' intègre' if prenom else 'Tu intègres'} SUPMTI Meknès en {filiere.get('nom', filiere_id)}.\n"
        f"Projets pratiques, stages en entreprise et certifications professionnelles.\n\n"
        f"## Premier Emploi\n"
        f"- Insertion en **{carriere.get('duree_premier_emploi', '2-4 mois')}**\n"
        f"- Salaire de départ : **{carriere.get('salaire_depart', 'variable')}**\n"
        f"- Taux d'insertion : **{carriere.get('taux_insertion', '80%')}**\n\n"
        f"## Évolution\n"
        f"- Après 3 ans : **{carriere.get('salaire_3ans', 'variable')}**\n"
        f"- Évolution vers : {', '.join(carriere.get('possibilites_evolution', [])[:2])}\n\n"
        f"## Long Terme\n"
        f"- Après 7 ans : **{carriere.get('salaire_7ans', 'variable')}**\n"
        f"- International : **{carriere.get('salaire_international', 'variable')}**"
    )

    return {
        "filiere_id":  filiere_id,
        "filiere_nom": filiere.get("nom", filiere_id),
        "scenario":    scenario,
        "donnees_cles": {
            "salaire_depart":  carriere.get("salaire_depart"),
            "salaire_3ans":    carriere.get("salaire_3ans"),
            "salaire_7ans":    carriere.get("salaire_7ans"),
            "taux_insertion":  carriere.get("taux_insertion")
        }
    }


# ============================================================
# PARTIE 2 — COMPARAISON DE CARRIÈRES
# ============================================================

def comparer_carrieres(profil_etudiant, filiere_id_1, filiere_id_2):
    """Compare les carrières de 2 filières côte à côte."""
    print(f"[CAREER] Comparaison {filiere_id_1} vs {filiere_id_2}...")

    carriere_1 = CARRIERES_FILIERES.get(filiere_id_1, {})
    carriere_2 = CARRIERES_FILIERES.get(filiere_id_2, {})
    filiere_1  = FILIERES.get(filiere_id_1, {})
    filiere_2  = FILIERES.get(filiere_id_2, {})
    prenom     = profil_etudiant.get("informations_personnelles", {}).get("prenom", "")

    comparaison = (
        f"⚖️ **Comparaison de Carrières**\n"
        f"{'Pour ' + prenom if prenom else ''}\n\n"
        f"{'─' * 50}\n"
        f"📊 **{filiere_1.get('nom', filiere_id_1)}** ({filiere_1.get('niveau', '')})\n"
        f"vs\n"
        f"📊 **{filiere_2.get('nom', filiere_id_2)}** ({filiere_2.get('niveau', '')})\n"
        f"{'─' * 50}\n\n"
        f"💰 **SALAIRES**\n"
        f"| Période | {filiere_id_1} | {filiere_id_2} |\n"
        f"|---------|-------|-------|\n"
        f"| Départ | {carriere_1.get('salaire_depart', 'N/A')} | {carriere_2.get('salaire_depart', 'N/A')} |\n"
        f"| 3 ans | {carriere_1.get('salaire_3ans', 'N/A')} | {carriere_2.get('salaire_3ans', 'N/A')} |\n"
        f"| 7 ans | {carriere_1.get('salaire_7ans', 'N/A')} | {carriere_2.get('salaire_7ans', 'N/A')} |\n"
        f"| International | {carriere_1.get('salaire_international', 'N/A')} | {carriere_2.get('salaire_international', 'N/A')} |\n\n"
        f"⏱️ **INSERTION PROFESSIONNELLE**\n"
        f"- {filiere_id_1} : {carriere_1.get('duree_premier_emploi', 'N/A')} — Taux : {carriere_1.get('taux_insertion', 'N/A')}\n"
        f"- {filiere_id_2} : {carriere_2.get('duree_premier_emploi', 'N/A')} — Taux : {carriere_2.get('taux_insertion', 'N/A')}\n\n"
        f"## Métiers principaux\n"
        f"**{filiere_id_1} :**\n"
        + "\n".join(['- ' + m for m in carriere_1.get('metiers_principaux', [])[:3]])
        + f"\n\n**{filiere_id_2} :**\n"
        + "\n".join(['- ' + m for m in carriere_2.get('metiers_principaux', [])[:3]])
        + f"\n\n## Entreprises au Maroc\n"
        f"- **{filiere_id_1} :** {', '.join(carriere_1.get('entreprises_maroc', [])[:3])}\n"
        f"- **{filiere_id_2} :** {', '.join(carriere_2.get('entreprises_maroc', [])[:3])}\n\n"
        f"## Évolution possible\n"
        f"- **{filiere_id_1} :** {', '.join(carriere_1.get('possibilites_evolution', [])[:2])}\n"
        f"- **{filiere_id_2} :** {', '.join(carriere_2.get('possibilites_evolution', [])[:2])}"
    )

    recommandation = generer_recommandation_comparative(
        profil_etudiant, filiere_id_1, filiere_id_2, carriere_1, carriere_2
    )

    return {
        "comparaison":    comparaison,
        "recommandation": recommandation,
        "filiere_1_id":   filiere_id_1,
        "filiere_2_id":   filiere_id_2
    }


def generer_recommandation_comparative(
    profil_etudiant, filiere_id_1, filiere_id_2, carriere_1, carriere_2
):
    prenom   = profil_etudiant.get("informations_personnelles", {}).get("prenom", "")
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
FORMAT : 2-4 lignes de texte, sans titres, sans tirets.
Style naturel, encourageant, comme un conseiller ami."""

    try:
        r = client.chat.completions.create(
            model="gpt-5.2",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_completion_tokens=200
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        print(f"[CAREER] Erreur recommandation : {e}")
        return "Les deux filières offrent de belles perspectives. Choisis selon tes passions !"


# ============================================================
# PARTIE 3 — PROGRESSION SALARIALE
# ============================================================

def generer_progression_salariale(filiere_id):
    """Retourne les données de progression salariale sous forme structurée."""
    carriere = CARRIERES_FILIERES.get(filiere_id, {})

    def extraire_milieu(fourchette):
        try:
            parties = (
                fourchette
                .replace(" MAD/mois", "")
                .replace(" EUR/mois", "")
                .split("-")
            )
            return (int(parties[0]) + int(parties[1])) // 2
        except Exception:
            return 0

    return {
        "filiere_id":  filiere_id,
        "filiere_nom": FILIERES.get(filiere_id, {}).get("nom", filiere_id),
        "progression": [
            {
                "periode":       "Départ",
                "annee":         0,
                "fourchette":    carriere.get("salaire_depart", "N/A"),
                "valeur_mediane": extraire_milieu(carriere.get("salaire_depart", "0-0"))
            },
            {
                "periode":       "Après 3 ans",
                "annee":         3,
                "fourchette":    carriere.get("salaire_3ans", "N/A"),
                "valeur_mediane": extraire_milieu(carriere.get("salaire_3ans", "0-0"))
            },
            {
                "periode":       "Après 7 ans",
                "annee":         7,
                "fourchette":    carriere.get("salaire_7ans", "N/A"),
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

    Logique SUPMTI officielle :
    - Post-BAC → IISI (ingénierie) ou MGE / MDI (management)
    - BAC+2 (DUT/BTS) → IISI, MGE ou MDI (3ème année) — PAS les BAC+5
    - BAC+3 IISI/SUPMTI ou Licence info → IISIC ou IISRT
    - BAC+3 MGE/MDI/SUPMTI ou Licence gestion → FACG ou MRI
    - Niveau non déclaré → IISI, MGE, MDI par défaut
    """
    parcours = profil_etudiant.get("parcours_academique", {})
    niveau   = parcours.get("niveau_actuel", "")
    diplome  = (parcours.get("diplome_actuel") or "").strip().upper()

    if niveau == "post_bac":
        return {
            "filieres_accessibles": ["IISI", "MGE", "MDI"],
            "explication": (
                "En tant que bachelier, tu intègres la 1ère année de SUPMTI. "
                "Trois portes d'entrée : IISI (Ingénierie), MGE (Management Entreprise) "
                "ou MDI (Management International). "
                "Les BAC+5 se préparent après le BAC+3."
            ),
            "note": (
                "IISI → IISIC ou IISRT (BAC+5). "
                "MGE → FACG ou MRI (BAC+5). "
                "MDI → MRI ou FACG (BAC+5)."
            ),
            "annee_entree": "1ère année"
        }

    elif niveau == "bac1":
        return {
            "filieres_accessibles": ["IISI", "MGE", "MDI"],
            "explication": (
                "Avec une 1ère année post-BAC validée, tu peux intégrer "
                "SUPMTI en 2ème année via admission parallèle."
            ),
            "note": "Étude de dossier et entretien requis.",
            "annee_entree": "2ème année"
        }

    elif niveau == "bac2" or any(d in diplome for d in ["DUT", "BTS", "DEUG", "TS"]):
        # Orientation selon spécialité BAC+2
        if any(d in diplome for d in [
            "INFO", "INFORMATIQUE", "RESEAUX", "RESEAU", "ELECTRONI", "TELECOM",
            "NUMERIQUE", "CYBER", "SECURITE", "SYST", "TECH", "INGENIERIE",
            "WEB", "DEV", "DEVELOPPEMENT", "MOBILE", "CLOUD", "DATA", "IA",
            "INTELLIGENCE", "MACHINE", "LEARNING", "LOGICIEL", "SOFTWARE",
            "APPLI", "PROGRAMMATION", "DIGITAL", "CODE", "PYTHON", "JAVA",
            "SQL", "LINUX", "IOT"]):
            filieres = ["IISI"]
            note = "Diplôme informatique/réseaux → IISI (3ème année ingénierie)."
        elif any(d in diplome for d in ["GESTION", "COMPTA", "ECONOMIE", "COMMERCE",
                                         "GEA", "MANAGEMENT"]):
            filieres = ["MGE", "MDI"]
            note = "Diplôme gestion/commerce → MGE ou MDI (3ème année management)."
        else:
            filieres = ["IISI", "MGE", "MDI"]
            note = (
                "Diplôme technique → IISI (ingénierie). "
                "Diplôme gestion/commerce → MGE ou MDI (management)."
            )
        return {
            "filieres_accessibles": filieres,
            "explication": (
                f"Avec ton diplôme BAC+2, tu intègres SUPMTI en 3ème année. "
                f"Les filières BAC+5 (IISIC, IISRT, FACG, MRI) sont accessibles "
                f"après validation du BAC+3."
            ),
            "note": note,
            "annee_entree": "3ème année"
        }

    elif niveau == "bac3" or any(d in diplome for d in ["LICENCE", "LICENSE", "BAC+3", "BAC 3"]):
        # IISI SUPMTI → IISIC ou IISRT
        if any(d in diplome for d in ["IISI", "ISI", "INGENIERIE DES SYSTEMES",
                                       "INGENIERIE INTELLIGENTE"]):
            return {
                "filieres_accessibles": ["IISIC", "IISRT"],
                "explication": (
                    "Avec ton BAC+3 IISI (SUPMTI), tu continues naturellement "
                    "en 4ème année IISIC ou IISRT."
                ),
                "note": "IISIC → IA et Data Science. IISRT → Réseaux et Télécommunications.",
                "annee_entree": "4ème année"
            }

        # MGE SUPMTI → FACG ou MRI
        elif any(d in diplome for d in ["MGE", "MANAGEMENT DE L'ENTREPRISE",
                                         "MANAGEMENT GESTION"]):
            return {
                "filieres_accessibles": ["FACG", "MRI"],
                "explication": (
                    "Avec ton BAC+3 MGE (SUPMTI), tu continues naturellement "
                    "en 4ème année FACG ou MRI."
                ),
                "note": "FACG → Finance et Audit. MRI → Management International.",
                "annee_entree": "4ème année"
            }

        # MDI SUPMTI → MRI ou FACG
        elif any(d in diplome for d in ["MDI", "MANAGEMENT ET DEVELOPPEMENT",
                                         "MANAGEMENT DEVELOPPEMENT INTERNATIONAL"]):
            return {
                "filieres_accessibles": ["MRI", "FACG"],
                "explication": (
                    "Avec ton BAC+3 MDI (SUPMTI), tu continues naturellement "
                    "en 4ème année MRI ou FACG."
                ),
                "note": "MRI → Management International. FACG → Finance et Audit.",
                "annee_entree": "4ème année"
            }

        # Licence informatique/réseaux/IA/web → IISIC ou IISRT
        elif any(d in diplome for d in [
            "INFO", "INFORMATIQUE", "RESEAU", "RESEAUX", "TELECOM", "SYSTEMES",
            "SCIENCES ET TECH", "CYBER", "SECURITE", "SYST", "TECH", "INGENIERIE",
            "ELECTRONI", "NUMERIQUE", "WEB", "DEV", "DEVELOPPEMENT", "MOBILE",
            "CLOUD", "DATA", "IA", "INTELLIGENCE", "MACHINE", "LEARNING",
            "LOGICIEL", "SOFTWARE", "APPLI", "PROGRAMMATION", "DIGITAL",
            "CODE", "PYTHON", "JAVA", "SQL", "LINUX", "IOT"]):
            return {
                "filieres_accessibles": ["IISIC", "IISRT"],
                "explication": (
                    "Avec ta Licence en informatique/réseaux, "
                    "tu intègres SUPMTI en 4ème année ingénierie."
                ),
                "note": "IISIC → IA, Data Science. IISRT → Réseaux, Télécommunications.",
                "annee_entree": "4ème année"
            }

        # Licence gestion/management/finance → FACG ou MRI
        elif any(d in diplome for d in ["GESTION", "MANAGEMENT", "ECONOMIE", "COMMERCE",
                                         "FINANCE", "COMPTABILITE", "ISCAE"]):
            return {
                "filieres_accessibles": ["FACG", "MRI"],
                "explication": (
                    "Avec ta Licence en gestion/économie, "
                    "tu intègres SUPMTI en 4ème année management."
                ),
                "note": "FACG → Finance, Audit, Contrôle de gestion. MRI → Management international.",
                "annee_entree": "4ème année"
            }

        else:
            return {
                "filieres_accessibles": ["IISIC", "IISRT", "FACG", "MRI"],
                "explication": (
                    "Avec un BAC+3, tu peux intégrer les filières BAC+5 "
                    "de SUPMTI en 4ème année selon ta spécialité."
                ),
                "note": (
                    "Ingénierie : IISIC ou IISRT. "
                    "Management : FACG ou MRI."
                ),
                "annee_entree": "4ème année"
            }

    else:
        return {
            "filieres_accessibles": ["IISI", "MGE", "MDI"],
            "explication": (
                "Tu peux intégrer la 1ère année de SUPMTI. "
                "Dis-moi ton niveau d'études pour une orientation plus précise !"
            ),
            "note": "IISI (Ingénierie) | MGE (Management Entreprise) | MDI (Management International).",
            "annee_entree": "1ère année"
        }


def comparer_carrieres_intelligent(
    profil_etudiant,
    filiere_id_1=None,
    filiere_id_2=None
):
    """
    Version intelligente du comparateur.
    Vérifie que les filières demandées sont accessibles selon le niveau.
    """
    info_filieres       = obtenir_filieres_comparables(profil_etudiant)
    filieres_accessibles = info_filieres["filieres_accessibles"]

    if not filiere_id_1 or not filiere_id_2:
        if len(filieres_accessibles) >= 2:
            filiere_id_1 = filieres_accessibles[0]
            filiere_id_2 = filieres_accessibles[1]
        else:
            return {
                "erreur":              "Pas assez de filières accessibles pour une comparaison.",
                "filieres_accessibles": filieres_accessibles,
                "info_niveau":         info_filieres
            }

    avertissements = []

    for fid in [filiere_id_1, filiere_id_2]:
        if fid not in filieres_accessibles:
            niveau_filiere = FILIERES.get(fid, {}).get("niveau", "")
            avertissements.append(
                f"⚠️ {fid} ({niveau_filiere}) n'est pas accessible "
                f"à ton niveau actuel. "
                f"Filières accessibles : {', '.join(filieres_accessibles)}."
            )

    resultat                       = comparer_carrieres(profil_etudiant, filiere_id_1, filiere_id_2)
    resultat["info_niveau"]        = info_filieres
    resultat["avertissements"]     = avertissements
    resultat["filieres_accessibles"] = filieres_accessibles

    if avertissements:
        resultat["comparaison"] = "\n".join(avertissements) + "\n\n" + resultat["comparaison"]

    return resultat