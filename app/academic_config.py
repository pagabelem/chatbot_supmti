# ============================================================
# FICHIER DE CONFIGURATION ACADÉMIQUE — SUPMTI MEKNÈS
# Toutes les données académiques du système
# Modifiable facilement sans toucher au reste du code
# ============================================================

# ============================================================
# 1. INFORMATIONS GÉNÉRALES DE L'ÉCOLE
# ============================================================

SCHOOL_INFO = {
    "nom": "SUP MTI Meknès",
    "nom_complet": "École Supérieure de Management, de Télécommunication et d'Informatique",
    "slogan": "Le Plaisir d'Être Excellent !",
    "fondation": 2014,
    "telephone": "+212 5 35 51 10 11",
    "email": "contact@supmtimeknes.ac.ma",
    "site_web": "https://www.supmtimeknes.ac.ma",
    "adresse": "Centre-ville, Meknès, Maroc",
    "horaires": {
        "lundi_vendredi": "08:30 - 18:00",
        "samedi": "08:30 - 12:00"
    },
    "reseaux_sociaux": {
        "facebook": "https://www.facebook.com/ecolesupmtimeknes",
        "linkedin": "https://www.linkedin.com/company/ecolesupmti/",
        "youtube": "https://www.youtube.com/channel/UCzZnrI4YdZnRJgosOd71RDQ"
    },
    "statistiques": {
        "filieres": 6,
        "laureats": 450,
        "nationalites": 10
    }
}

# ============================================================
# 2. FRAIS DE SCOLARITÉ
# ============================================================

FRAIS_SCOLARITE = {
    "frais_annuels": 35000,
    "frais_inscription": 3500,
    "total_annuel": 38500,
    "mensualites": 10,
    "montant_mensuel": 3500,
    "devise": "MAD (Dirhams Marocains)"
}

# ============================================================
# 3. GRILLE DES BOURSES
# ============================================================

BOURSES = {
    "description": "Bourses basées sur les résultats du concours d'admission",
    "paliers": [
        {
            "note_min": 18,
            "note_max": 20,
            "pourcentage": 100,
            "label": "Bourse Excellence Totale",
            "reduction": 35000,
            "a_payer": 3500
        },
        {
            "note_min": 16,
            "note_max": 17.99,
            "pourcentage": 70,
            "label": "Bourse Excellence",
            "reduction": 24500,
            "a_payer": 14000
        },
        {
            "note_min": 14,
            "note_max": 15.99,
            "pourcentage": 50,
            "label": "Bourse Mérite",
            "reduction": 17500,
            "a_payer": 21000
        },
        {
            "note_min": 12,
            "note_max": 13.99,
            "pourcentage": 30,
            "label": "Bourse Encouragement",
            "reduction": 10500,
            "a_payer": 28000
        },
        {
            "note_min": 0,
            "note_max": 11.99,
            "pourcentage": 0,
            "label": "Pas de bourse",
            "reduction": 0,
            "a_payer": 38500
        }
    ],
    "note": "La bourse s'applique uniquement sur les frais de scolarité (35000 MAD). Les frais d'inscription (3500 MAD) restent fixes."
}

# ============================================================
# 4. LES 6 FILIÈRES DE SUPMTI
# ============================================================

FILIERES = {
    "ME": {
        "id": "ME",
        "nom": "Management des Entreprises",
        "niveau": "BAC+3",
        "departement": "Management",
        "duree": 3,
        "description": "Formation en management digital, informatique de gestion, marketing digital et e-commerce. Prépare à des carrières en management ou à des poursuites d'études.",
        "competences_cles": [
            "Management et organisation d'entreprise",
            "Marketing digital et e-commerce",
            "Informatique de gestion",
            "Comptabilité et contrôle de gestion",
            "Droit des affaires",
            "Communication professionnelle"
        ],
        "debouches": [
            "Cadre bancaire",
            "Responsable commercial",
            "Chargé d'opérations",
            "Analyste financier",
            "Chargé d'études marketing",
            "Assistant RH",
            "Cadre administratif"
        ],
        "salaire_depart_maroc": "4000-6000 MAD/mois",
        "salaire_3ans": "6000-10000 MAD/mois",
        "salaire_7ans": "10000-18000 MAD/mois",
        "poursuite_etudes": ["FACG", "MSTIC"],
        "difficulte": 2,
        "orientation_dominante": "gestion"
    },
    "FACG": {
        "id": "FACG",
        "nom": "Finance, Audit et Contrôle de Gestion",
        "niveau": "BAC+5",
        "departement": "Management",
        "duree": 2,
        "description": "Formation de cadres financiers et contrôleurs de gestion hautement qualifiés pour des postes à responsabilités dans des entreprises nationales et internationales.",
        "competences_cles": [
            "Audit comptable et financier",
            "Contrôle de gestion",
            "Finance internationale",
            "Normes d'audit",
            "Fiscalité et droit",
            "Systèmes d'information"
        ],
        "debouches": [
            "Auditeur interne ou externe",
            "Auditeur financier",
            "Commissaire aux comptes",
            "Contrôleur de gestion",
            "Expert-comptable",
            "Directeur comptable et financier",
            "Conseiller en finance internationale"
        ],
        "salaire_depart_maroc": "6000-9000 MAD/mois",
        "salaire_3ans": "9000-15000 MAD/mois",
        "salaire_7ans": "15000-30000 MAD/mois",
        "poursuite_etudes": [],
        "difficulte": 4,
        "orientation_dominante": "finance"
    },
    "MSTIC": {
        "id": "MSTIC",
        "nom": "Management des Systèmes et Technologies de l'Information et de la Communication",
        "niveau": "BAC+5",
        "departement": "Management",
        "duree": 2,
        "description": "Formation de cadres supérieurs capables de manager des entreprises en s'appuyant sur les nouvelles technologies (Big Data, IoT, Cloud, IA, Blockchain).",
        "competences_cles": [
            "Management des systèmes d'information",
            "Transformation digitale",
            "Data Science",
            "Management de projet",
            "Commerce international",
            "Conduite du changement"
        ],
        "debouches": [
            "Manager d'entreprise",
            "Responsable des systèmes d'information",
            "Responsable marketing digital",
            "Responsable commercial",
            "Responsable RH",
            "Responsable administratif et financier"
        ],
        "salaire_depart_maroc": "6000-9000 MAD/mois",
        "salaire_3ans": "9000-15000 MAD/mois",
        "salaire_7ans": "15000-28000 MAD/mois",
        "poursuite_etudes": [],
        "difficulte": 3,
        "orientation_dominante": "management_tech"
    },
    "ISI": {
        "id": "ISI",
        "nom": "Ingénierie Intelligente des Systèmes Informatiques",
        "niveau": "BAC+3",
        "departement": "Ingénierie",
        "duree": 3,
        "description": "Formation de techniciens spécialisés capables de concevoir, déployer et gérer des solutions informatiques performantes.",
        "competences_cles": [
            "Développement logiciel",
            "Réseaux informatiques",
            "Bases de données",
            "Systèmes d'exploitation",
            "Génie logiciel",
            "Programmation web"
        ],
        "debouches": [
            "Développeur web",
            "Analyste programmeur",
            "Administrateur réseaux",
            "Responsable informatique",
            "Webmaster",
            "Intégrateur de solutions"
        ],
        "salaire_depart_maroc": "4000-7000 MAD/mois",
        "salaire_3ans": "7000-12000 MAD/mois",
        "salaire_7ans": "12000-22000 MAD/mois",
        "poursuite_etudes": ["IISRT", "IISIC"],
        "difficulte": 3,
        "orientation_dominante": "informatique"
    },
    "IISIC": {
        "id": "IISIC",
        "nom": "Ingénierie Intelligente des Systèmes d'Information et Communications",
        "niveau": "BAC+5",
        "departement": "Ingénierie",
        "duree": 2,
        "description": "Formation d'ingénieurs spécialisés dans la conception et le développement de solutions technologiques intelligentes alliant systèmes d'information et intelligence artificielle.",
        "competences_cles": [
            "Intelligence Artificielle",
            "Data Science",
            "Systèmes d'information",
            "IoT",
            "Cloud Computing",
            "Sécurité informatique"
        ],
        "debouches": [
            "Architecte des systèmes d'information",
            "Ingénieur IA",
            "Data Scientist",
            "Chef de projet informatique",
            "Consultant en transformation digitale"
        ],
        "salaire_depart_maroc": "7000-12000 MAD/mois",
        "salaire_3ans": "12000-20000 MAD/mois",
        "salaire_7ans": "20000-40000 MAD/mois",
        "poursuite_etudes": [],
        "difficulte": 5,
        "orientation_dominante": "ia_data"
    },
    "IISRT": {
        "id": "IISRT",
        "nom": "Ingénierie Intelligente des Systèmes Réseaux et Télécommunications",
        "niveau": "BAC+5",
        "departement": "Ingénierie",
        "duree": 2,
        "description": "Formation d'ingénieurs spécialisés dans les réseaux intelligents, les télécommunications et les technologies de l'Industrie 4.0.",
        "competences_cles": [
            "Réseaux intelligents",
            "Télécommunications",
            "Data Science",
            "Systèmes embarqués",
            "Communications mobiles",
            "Intelligence Artificielle"
        ],
        "debouches": [
            "Architecte des systèmes réseaux",
            "Administrateur réseaux",
            "Responsable infrastructures télécoms",
            "Ingénieur en télécommunications",
            "Technico-commercial en solutions réseaux"
        ],
        "salaire_depart_maroc": "7000-12000 MAD/mois",
        "salaire_3ans": "12000-20000 MAD/mois",
        "salaire_7ans": "20000-38000 MAD/mois",
        "poursuite_etudes": [],
        "difficulte": 5,
        "orientation_dominante": "reseaux_telecoms"
    }
}

# ============================================================
# 5. TYPES DE BAC ET LEURS MATIÈRES
# ============================================================

TYPES_BAC = {
    # ---- MAROC ----
    "SMA": {
        "pays": "Maroc",
        "label": "Sciences Mathématiques A",
        "type": "scientifique",
        "matieres_principales": ["Mathématiques", "Physique-Chimie"],
        "matieres_secondaires": ["SVT", "Philosophie", "Français", "Anglais"],
        "force_maths": 5,
        "force_physique": 4,
        "force_info": 2,
        "force_economie": 1,
        "force_gestion": 1,
        "force_langues": 2
    },
    "SMB": {
        "pays": "Maroc",
        "label": "Sciences Mathématiques B",
        "type": "scientifique",
        "matieres_principales": ["Mathématiques", "Physique-Chimie", "SVT"],
        "matieres_secondaires": ["Philosophie", "Français", "Anglais"],
        "force_maths": 5,
        "force_physique": 4,
        "force_info": 2,
        "force_economie": 1,
        "force_gestion": 1,
        "force_langues": 2
    },
    "SP": {
        "pays": "Maroc",
        "label": "Sciences Physiques",
        "type": "scientifique",
        "matieres_principales": ["Physique-Chimie", "Mathématiques"],
        "matieres_secondaires": ["SVT", "Philosophie", "Français", "Anglais"],
        "force_maths": 4,
        "force_physique": 5,
        "force_info": 2,
        "force_economie": 1,
        "force_gestion": 1,
        "force_langues": 2
    },
    "SVT": {
        "pays": "Maroc",
        "label": "Sciences de la Vie et de la Terre",
        "type": "scientifique",
        "matieres_principales": ["SVT", "Mathématiques", "Physique-Chimie"],
        "matieres_secondaires": ["Philosophie", "Français", "Anglais"],
        "force_maths": 3,
        "force_physique": 3,
        "force_info": 1,
        "force_economie": 1,
        "force_gestion": 1,
        "force_langues": 2
    },
    "STE": {
        "pays": "Maroc",
        "label": "Sciences et Technologies Électriques",
        "type": "technique",
        "matieres_principales": ["Électrotechnique", "Mathématiques", "Physique"],
        "matieres_secondaires": ["Français", "Anglais"],
        "force_maths": 4,
        "force_physique": 4,
        "force_info": 3,
        "force_economie": 1,
        "force_gestion": 1,
        "force_langues": 2
    },
    "STM": {
        "pays": "Maroc",
        "label": "Sciences et Technologies Mécaniques",
        "type": "technique",
        "matieres_principales": ["Mécanique", "Mathématiques", "Physique"],
        "matieres_secondaires": ["Français", "Anglais"],
        "force_maths": 4,
        "force_physique": 4,
        "force_info": 2,
        "force_economie": 1,
        "force_gestion": 1,
        "force_langues": 2
    },
    "STGC": {
        "pays": "Maroc",
        "label": "Sciences et Technologies de Gestion Comptable",
        "type": "gestion",
        "matieres_principales": ["Comptabilité", "Mathématiques", "Économie"],
        "matieres_secondaires": ["Droit", "Français", "Anglais"],
        "force_maths": 3,
        "force_physique": 1,
        "force_info": 1,
        "force_economie": 4,
        "force_gestion": 5,
        "force_langues": 2
    },
    "SEG": {
        "pays": "Maroc",
        "label": "Sciences Économiques et Gestion",
        "type": "economique",
        "matieres_principales": ["Économie", "Mathématiques", "Comptabilité"],
        "matieres_secondaires": ["Droit", "Français", "Anglais"],
        "force_maths": 3,
        "force_physique": 1,
        "force_info": 1,
        "force_economie": 5,
        "force_gestion": 4,
        "force_langues": 2
    },
    "SGC": {
        "pays": "Maroc",
        "label": "Sciences de Gestion Comptable",
        "type": "gestion",
        "matieres_principales": ["Comptabilité", "Mathématiques", "Économie"],
        "matieres_secondaires": ["Droit", "Français", "Anglais"],
        "force_maths": 3,
        "force_physique": 1,
        "force_info": 1,
        "force_economie": 4,
        "force_gestion": 5,
        "force_langues": 2
    },
    "LSH": {
        "pays": "Maroc",
        "label": "Lettres et Sciences Humaines",
        "type": "litteraire",
        "matieres_principales": ["Philosophie", "Histoire-Géographie", "Langues"],
        "matieres_secondaires": ["Mathématiques basiques"],
        "force_maths": 1,
        "force_physique": 1,
        "force_info": 1,
        "force_economie": 2,
        "force_gestion": 1,
        "force_langues": 5
    },
    # ---- AFRIQUE SUBSAHARIENNE ----
    "S": {
        "pays": "Afrique Subsaharienne",
        "label": "BAC S — Sciences",
        "type": "scientifique",
        "matieres_principales": ["Physique-Chimie", "Mathématiques", "SVT"],
        "matieres_secondaires": ["Philosophie", "Français", "Anglais"],
        "force_maths": 4,
        "force_physique": 5,
        "force_info": 2,
        "force_economie": 1,
        "force_gestion": 1,
        "force_langues": 3
    },
    "SM": {
        "pays": "Afrique Subsaharienne",
        "label": "BAC SM — Sciences et Mathématiques",
        "type": "scientifique",
        "matieres_principales": ["Mathématiques", "Physique-Chimie"],
        "matieres_secondaires": ["SVT", "Philosophie", "Français", "Anglais"],
        "force_maths": 5,
        "force_physique": 4,
        "force_info": 2,
        "force_economie": 1,
        "force_gestion": 1,
        "force_langues": 3
    },
    "D": {
        "pays": "Afrique Subsaharienne",
        "label": "BAC D — Sciences de la Nature",
        "type": "scientifique",
        "matieres_principales": ["SVT", "Mathématiques", "Physique"],
        "matieres_secondaires": ["Philosophie", "Français", "Anglais"],
        "force_maths": 3,
        "force_physique": 3,
        "force_info": 1,
        "force_economie": 1,
        "force_gestion": 1,
        "force_langues": 3
    },
    "E": {
        "pays": "Afrique Subsaharienne",
        "label": "BAC E — Sciences et Technologie",
        "type": "technique",
        "matieres_principales": ["Mathématiques", "Physique", "Technologie"],
        "matieres_secondaires": ["Français", "Anglais"],
        "force_maths": 4,
        "force_physique": 4,
        "force_info": 3,
        "force_economie": 1,
        "force_gestion": 1,
        "force_langues": 3
    },
    "C": {
        "pays": "Afrique Subsaharienne",
        "label": "BAC C — Sciences Économiques et Mathématiques",
        "type": "economique",
        "matieres_principales": ["Mathématiques", "Économie", "Comptabilité"],
        "matieres_secondaires": ["Droit", "Français", "Anglais"],
        "force_maths": 3,
        "force_physique": 1,
        "force_info": 1,
        "force_economie": 5,
        "force_gestion": 4,
        "force_langues": 3
    },
    "L": {
        "pays": "Afrique Subsaharienne",
        "label": "BAC L — Lettres et Sciences Humaines",
        "type": "litteraire",
        "matieres_principales": ["Philosophie", "Langues", "Histoire-Géographie"],
        "matieres_secondaires": ["Mathématiques basiques"],
        "force_maths": 1,
        "force_physique": 1,
        "force_info": 1,
        "force_economie": 2,
        "force_gestion": 1,
        "force_langues": 5
    },
    "A": {
        "pays": "Afrique Subsaharienne",
        "label": "BAC A — Lettres et Arts",
        "type": "litteraire",
        "matieres_principales": ["Langues", "Philosophie", "Arts"],
        "matieres_secondaires": ["Histoire", "Mathématiques basiques"],
        "force_maths": 1,
        "force_physique": 1,
        "force_info": 1,
        "force_economie": 2,
        "force_gestion": 1,
        "force_langues": 5
    },
    # ---- FRANCE / TUNISIE / ALGÉRIE ----
    "BAC_GENERAL_FR": {
        "pays": "France/Tunisie/Algérie",
        "label": "Baccalauréat Général",
        "type": "scientifique",
        "matieres_principales": ["Mathématiques", "Physique", "NSI ou Éco"],
        "matieres_secondaires": ["Philosophie", "Français", "Anglais"],
        "force_maths": 4,
        "force_physique": 4,
        "force_info": 3,
        "force_economie": 2,
        "force_gestion": 2,
        "force_langues": 3
    },
    "AUTRE": {
        "pays": "Autre",
        "label": "Diplôme étranger autre",
        "type": "inconnu",
        "matieres_principales": [],
        "matieres_secondaires": [],
        "force_maths": 3,
        "force_physique": 3,
        "force_info": 2,
        "force_economie": 2,
        "force_gestion": 2,
        "force_langues": 3
    }
}

# ============================================================
# 6. GRILLE DE COMPATIBILITÉ BAC → FILIÈRE
# Score de 1 à 5 (5 = idéal, 1 = très faible)
# ============================================================

COMPATIBILITE_BAC_FILIERE = {
    "SMA":            {"ME": 3, "FACG": 3, "MSTIC": 3, "ISI": 5, "IISIC": 5, "IISRT": 5},
    "SMB":            {"ME": 3, "FACG": 3, "MSTIC": 3, "ISI": 5, "IISIC": 5, "IISRT": 5},
    "SP":             {"ME": 3, "FACG": 3, "MSTIC": 3, "ISI": 4, "IISIC": 4, "IISRT": 5},
    "SVT":            {"ME": 4, "FACG": 3, "MSTIC": 3, "ISI": 3, "IISIC": 2, "IISRT": 2},
    "STE":            {"ME": 2, "FACG": 1, "MSTIC": 2, "ISI": 4, "IISIC": 4, "IISRT": 5},
    "STM":            {"ME": 2, "FACG": 1, "MSTIC": 2, "ISI": 4, "IISIC": 3, "IISRT": 4},
    "STGC":           {"ME": 5, "FACG": 5, "MSTIC": 4, "ISI": 2, "IISIC": 2, "IISRT": 1},
    "SEG":            {"ME": 5, "FACG": 5, "MSTIC": 4, "ISI": 2, "IISIC": 2, "IISRT": 1},
    "SGC":            {"ME": 5, "FACG": 5, "MSTIC": 4, "ISI": 2, "IISIC": 2, "IISRT": 1},
    "LSH":            {"ME": 3, "FACG": 2, "MSTIC": 2, "ISI": 1, "IISIC": 1, "IISRT": 1},
    "S":              {"ME": 3, "FACG": 3, "MSTIC": 3, "ISI": 4, "IISIC": 4, "IISRT": 5},
    "SM":             {"ME": 3, "FACG": 3, "MSTIC": 3, "ISI": 5, "IISIC": 5, "IISRT": 5},
    "D":              {"ME": 4, "FACG": 3, "MSTIC": 3, "ISI": 3, "IISIC": 2, "IISRT": 2},
    "E":              {"ME": 2, "FACG": 1, "MSTIC": 2, "ISI": 4, "IISIC": 4, "IISRT": 5},
    "C":              {"ME": 5, "FACG": 5, "MSTIC": 4, "ISI": 2, "IISIC": 2, "IISRT": 1},
    "L":              {"ME": 3, "FACG": 2, "MSTIC": 2, "ISI": 1, "IISIC": 1, "IISRT": 1},
    "A":              {"ME": 3, "FACG": 2, "MSTIC": 2, "ISI": 1, "IISIC": 1, "IISRT": 1},
    "BAC_GENERAL_FR": {"ME": 3, "FACG": 3, "MSTIC": 3, "ISI": 4, "IISIC": 4, "IISRT": 4},
    "AUTRE":          {"ME": 3, "FACG": 3, "MSTIC": 3, "ISI": 3, "IISIC": 3, "IISRT": 3}
}

# ============================================================
# 7. PONDÉRATION DES CRITÈRES POUR LE FITSCORE
# Total = 100 points
# ============================================================

POIDS_FITSCORE = {
    "compatibilite_bac": 25,
    "moyenne_academique": 20,
    "notes_matieres_cles": 20,
    "profil_psychometrique": 20,
    "centres_interet": 10,
    "ambitions_professionnelles": 5
}

# ============================================================
# 8. PONDÉRATION DES MATIÈRES PAR FILIÈRE
# ============================================================

POIDS_MATIERES_FILIERES = {
    "ISI": {
        "Mathématiques": 35,
        "Physique": 30,
        "Informatique": 20,
        "Autres": 15
    },
    "IISRT": {
        "Mathématiques": 35,
        "Physique": 30,
        "Informatique": 20,
        "Autres": 15
    },
    "IISIC": {
        "Mathématiques": 35,
        "Physique": 25,
        "Informatique": 25,
        "Autres": 15
    },
    "ME": {
        "Économie_Gestion": 35,
        "Mathématiques": 30,
        "Droit_Fiscalite": 20,
        "Autres": 15
    },
    "FACG": {
        "Économie_Gestion": 35,
        "Mathématiques": 30,
        "Droit_Fiscalite": 20,
        "Autres": 15
    },
    "MSTIC": {
        "Économie_Gestion": 30,
        "Mathématiques": 25,
        "Informatique": 25,
        "Autres": 20
    }
}

# ============================================================
# 9. BONUS DE MENTION BAC
# ============================================================

BONUS_MENTION = {
    "tres_bien": 15,
    "bien": 10,
    "assez_bien": 5,
    "passable": 0
}

SEUILS_MENTION = {
    "tres_bien": 16,
    "bien": 14,
    "assez_bien": 12,
    "passable": 10
}

# ============================================================
# 10. CONDITIONS D'ADMISSION PAR FILIÈRE ET PAR ANNÉE
# ============================================================

CONDITIONS_ADMISSION = {
    "1ere_annee": {
        "ISI": {
            "bac_requis": ["SMA", "SMB", "SP", "SVT", "STE", "STM", "S", "SM", "D", "E", "BAC_GENERAL_FR"],
            "type_requis": ["scientifique", "technique"],
            "moyenne_min": 10,
            "description": "Baccalauréat scientifique ou technique obligatoire"
        },
        "IISRT": {
            "bac_requis": ["SMA", "SMB", "SP", "STE", "STM", "S", "SM", "E", "BAC_GENERAL_FR"],
            "type_requis": ["scientifique", "technique"],
            "moyenne_min": 10,
            "description": "Baccalauréat scientifique ou technique obligatoire"
        },
        "IISIC": {
            "bac_requis": ["SMA", "SMB", "SP", "STE", "STM", "S", "SM", "E", "BAC_GENERAL_FR"],
            "type_requis": ["scientifique", "technique"],
            "moyenne_min": 10,
            "description": "Baccalauréat scientifique ou technique obligatoire"
        },
        "ME": {
            "bac_requis": ["SMA", "SMB", "SP", "SVT", "STE", "STM", "STGC", "SEG", "SGC", "LSH", "S", "SM", "D", "E", "C", "L", "A", "BAC_GENERAL_FR"],
            "type_requis": ["scientifique", "technique", "economique", "gestion", "litteraire"],
            "moyenne_min": 10,
            "description": "Tous types de baccalauréat acceptés"
        },
        "FACG": {
            "bac_requis": ["STGC", "SEG", "SGC", "SMA", "SMB", "C", "BAC_GENERAL_FR"],
            "type_requis": ["economique", "gestion", "scientifique"],
            "moyenne_min": 10,
            "description": "Baccalauréat à dominante gestion, économie ou scientifique"
        },
        "MSTIC": {
            "bac_requis": ["SMA", "SMB", "SP", "STGC", "SEG", "SGC", "STE", "S", "SM", "C", "BAC_GENERAL_FR"],
            "type_requis": ["scientifique", "technique", "economique", "gestion"],
            "moyenne_min": 10,
            "description": "Baccalauréat scientifique, technique ou économique"
        }
    },
    "2eme_annee": {
        "diplomes_requis": ["Bac + 1ère année validée dans filière accréditée"],
        "moyenne_min": 11,
        "procedure": "Étude de dossier + entretien"
    },
    "3eme_annee": {
        "diplomes_requis": ["DUT", "BTS", "DEUG", "TS", "2ème année CPGE", "2ème année Licence"],
        "filieres_compatibles": {
            "ISI": ["DUT Informatique", "BTS Informatique", "DEUG Informatique", "DUT Réseaux", "Licence 2 Informatique"],
            "IISRT": ["DUT Réseaux", "DUT Télécoms", "BTS Électronique", "Licence 2 Informatique"],
            "IISIC": ["DUT Informatique", "BTS Informatique", "Licence 2 Informatique"],
            "ME": ["BTS Gestion", "DUT GEA", "DEUG Économie", "Licence 2 Gestion"],
            "FACG": ["BTS Comptabilité", "DUT GEA", "DEUG Économie", "Licence 2 Comptabilité"],
            "MSTIC": ["DUT Informatique", "BTS Informatique", "DUT GEA", "Licence 2 Management"]
        },
        "moyenne_min": 12,
        "procedure": "Étude de dossier + entretien"
    },
    "4eme_annee": {
        "diplomes_requis": ["Licence", "BAC+3 SUPMTI", "Diplôme équivalent BAC+3"],
        "filieres_compatibles": {
            "IISIC": ["Licence Informatique", "BAC+3 ISI SUPMTI", "Licence Réseaux"],
            "IISRT": ["Licence Informatique", "BAC+3 ISI SUPMTI", "Licence Réseaux", "Licence Télécoms"],
            "FACG": ["Licence Gestion", "Licence Économie", "BAC+3 ME SUPMTI", "Licence Comptabilité"],
            "MSTIC": ["Licence Informatique", "Licence Management", "BAC+3 ISI SUPMTI", "BAC+3 ME SUPMTI"]
        },
        "moyenne_min": 12,
        "procedure": "Étude de dossier + entretien"
    }
}

# ============================================================
# 11. PROFIL PSYCHOMÉTRIQUE PAR FILIÈRE
# Dimensions prioritaires pour chaque filière
# ============================================================

PROFIL_PSYCHO_FILIERE = {
    "ISI": {
        "logique": 5,
        "creativite": 3,
        "leadership": 2,
        "gestion_stress": 3,
        "travail_equipe": 3,
        "style_cognitif_analytique": 5
    },
    "IISRT": {
        "logique": 5,
        "creativite": 2,
        "leadership": 2,
        "gestion_stress": 4,
        "travail_equipe": 3,
        "style_cognitif_analytique": 5
    },
    "IISIC": {
        "logique": 5,
        "creativite": 4,
        "leadership": 3,
        "gestion_stress": 3,
        "travail_equipe": 4,
        "style_cognitif_analytique": 5
    },
    "ME": {
        "logique": 3,
        "creativite": 4,
        "leadership": 5,
        "gestion_stress": 4,
        "travail_equipe": 5,
        "style_cognitif_analytique": 3
    },
    "FACG": {
        "logique": 5,
        "creativite": 2,
        "leadership": 3,
        "gestion_stress": 4,
        "travail_equipe": 3,
        "style_cognitif_analytique": 5
    },
    "MSTIC": {
        "logique": 4,
        "creativite": 4,
        "leadership": 5,
        "gestion_stress": 4,
        "travail_equipe": 5,
        "style_cognitif_analytique": 4
    }
}

# ============================================================
# 12. MOTS-CLÉS D'INTÉRÊTS PAR FILIÈRE
# ============================================================

INTERETS_FILIERE = {
    "ISI": [
        "informatique", "programmation", "code", "développement", "logiciel",
        "web", "application", "algorithme", "bases de données", "réseaux",
        "cybersécurité", "intelligence artificielle", "technologie"
    ],
    "IISRT": [
        "réseaux", "télécommunications", "internet", "wifi", "infrastructure",
        "connectivité", "fibres optiques", "mobile", "4G", "5G",
        "systèmes embarqués", "IoT", "objets connectés"
    ],
    "IISIC": [
        "intelligence artificielle", "machine learning", "data science",
        "big data", "cloud", "IA", "algorithmes", "innovation",
        "transformation digitale", "systèmes intelligents"
    ],
    "ME": [
        "management", "entreprise", "marketing", "commerce", "vente",
        "ressources humaines", "organisation", "stratégie", "entrepreneuriat",
        "communication", "leadership", "gestion"
    ],
    "FACG": [
        "finance", "comptabilité", "audit", "bourse", "investissement",
        "contrôle de gestion", "fiscalité", "chiffres", "analyse financière",
        "banque", "assurance"
    ],
    "MSTIC": [
        "management digital", "systèmes d'information", "transformation",
        "technologie", "innovation", "gestion de projet", "big data",
        "entrepreneuriat tech", "startup", "digital"
    ]
}

# ============================================================
# 13. DONNÉES HISTORIQUES SIMULÉES POUR L'ADMISSION PREDICTOR
# ============================================================

HISTORIQUE_ADMISSION = {
    "ISI": {
        "moyenne_admis": 12.5,
        "fitscore_moyen": 65,
        "taux_admission": 0.75,
        "profil_type": "BAC scientifique, bonne moyenne en maths"
    },
    "IISRT": {
        "moyenne_admis": 13.0,
        "fitscore_moyen": 68,
        "taux_admission": 0.70,
        "profil_type": "BAC scientifique ou technique, fort en physique"
    },
    "IISIC": {
        "moyenne_admis": 13.5,
        "fitscore_moyen": 72,
        "taux_admission": 0.65,
        "profil_type": "BAC scientifique, intérêt pour l'IA et la data"
    },
    "ME": {
        "moyenne_admis": 11.5,
        "fitscore_moyen": 60,
        "taux_admission": 0.80,
        "profil_type": "Tout BAC, intérêt pour le commerce et la gestion"
    },
    "FACG": {
        "moyenne_admis": 13.0,
        "fitscore_moyen": 68,
        "taux_admission": 0.70,
        "profil_type": "BAC gestion ou économie, bon en maths"
    },
    "MSTIC": {
        "moyenne_admis": 12.5,
        "fitscore_moyen": 65,
        "taux_admission": 0.72,
        "profil_type": "BAC scientifique ou gestion, intérêt pour le digital"
    }
}

# ============================================================
# 14. SIGNAUX D'HÉSITATION POUR LE PEER MATCH
# ============================================================

SIGNAUX_HESITATION = [
    "je sais pas trop",
    "j'hésite",
    "pas sûr",
    "pas sure",
    "j'suis pas certain",
    "j'ai peur",
    "je suis perdu",
    "c'est difficile de choisir",
    "j'arrive pas à décider",
    "vous pensez vraiment",
    "t'es sûr",
    "vraiment fait pour moi",
    "j'aimerais avoir l'avis",
    "quelqu'un qui a vécu",
    "témoignage",
    "parler avec un étudiant",
    "khayef",
    "machi mdrass",
    "ma3arfch",
    "hésitation",
    "indécis"
]

# ============================================================
# 15. CONFIGURATION DU CHATBOT
# ============================================================

CHATBOT_CONFIG = {
    "nom": "Sami",
    "description": "Assistant Intelligent d'Orientation Académique de SUPMTI Meknès",
    "langue_defaut": "français",
    "langues_supportees": ["français", "darija", "anglais"],
    "min_echanges_peer_match": 15,
    "max_historique_tokens": 3000,
    "temperature_gpt": 0.7,
    "modele_gpt": "gpt-5.2",
    "modele_embedding": "text-embedding-ada-002",
    "chunk_size": 500,
    "chunk_overlap": 50,
    "top_k_recherche": 5
}

# ============================================================
# 16. URL DU SITE SUPMTI POUR SYNCHRONISATION AUTO
# ============================================================

SUPMTI_URLS = [
    "https://www.supmtimeknes.ac.ma",
    "https://supmtimeknes.ac.ma/supmti/",
    "https://supmtimeknes.ac.ma/programme-management-des-entreprises/",
    "https://supmtimeknes.ac.ma/management-et-relations-internationales/",
    "https://supmtimeknes.ac.ma/finance-audit-et-controle-de-gestion/",
    "https://supmtimeknes.ac.ma/ingenierie-des-systemes-informatiques/",
    "https://supmtimeknes.ac.ma/ingenierie-intelligente-des-systemes-reseaux-et-telecommunication/",
    "https://supmtimeknes.ac.ma/ingenierie-intelligente-des-systemes-de-l-information-et-de-la-communication/",
    "https://supmtimeknes.ac.ma/certifications-supmti-meknes/",
    "https://supmtimeknes.ac.ma/formations-continues/",
    "https://supmtimeknes.ac.ma/admission_ecole_d_ingenierie/",
    "https://supmtimeknes.ac.ma/admission-en-ecole-de-management/",
    "https://supmtimeknes.ac.ma/etudiants-internationaux/",
    "https://supmtimeknes.ac.ma/ecoles-partenaires/",
    "https://supmtimeknes.ac.ma/bde-supmti-meknes/",
    "https://supmtimeknes.ac.ma/les-clubs/"

]
