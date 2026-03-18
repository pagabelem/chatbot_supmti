# ============================================================
# FICHIER DE CONFIGURATION ACADÉMIQUE — SUPMTI MEKNÈS
# Source : Data1.txt v2 — Mars 2026
# 7 filières réelles (MGE, MDI, FACG, MRI, IISI, IISIC, IISRT)
# ============================================================

# ============================================================
# 1. INFORMATIONS GÉNÉRALES DE L'ÉCOLE
# ============================================================

SCHOOL_INFO = {
    "nom":          "SUP MTI Meknès",
    "nom_complet":  "École Supérieure de Management, de Télécommunication et d'Informatique",
    "slogan":       "Le Plaisir d'Être Excellent !",
    "fondation":    2014,
    "telephone":    "+212 5 35 51 10 11",
    "email":        "contact@supmtimeknes.ac.ma",
    "site_web":     "https://www.supmtimeknes.ac.ma",
    "adresse":      "Centre-ville, Meknès, Maroc",
    "horaires": {
        "lundi_vendredi": "08:30 - 18:00",
        "samedi":         "08:30 - 12:00"
    },
    "reseaux_sociaux": {
        "facebook":  "https://www.facebook.com/ecolesupmtimeknes",
        "linkedin":  "https://www.linkedin.com/company/ecolesupmti/",
        "youtube":   "https://www.youtube.com/channel/UCzZnrI4YdZnRJgosOd71RDQ"
    },
    "statistiques": {
        "filieres":    7,
        "laureats":    450,
        "nationalites": 10
    }
}

# ============================================================
# 2. FRAIS DE SCOLARITÉ
# ============================================================

FRAIS_SCOLARITE = {
    "frais_annuels":     35000,
    "frais_inscription": 3500,
    "total_annuel":      38500,
    "mensualites":       10,
    "montant_mensuel":   3500,
    "devise":            "MAD (Dirhams Marocains)"
}

# ============================================================
# 3. GRILLE DES BOURSES
# ============================================================

BOURSES = {
    "description": "Bourses basées sur les résultats du concours d'admission SUPMTI",
    "paliers": [
        {
            "note_min": 18, "note_max": 20,
            "pourcentage": 100, "label": "Bourse Excellence Totale",
            "reduction": 35000, "a_payer": 3500
        },
        {
            "note_min": 16, "note_max": 17.99,
            "pourcentage": 70, "label": "Bourse Excellence",
            "reduction": 24500, "a_payer": 14000
        },
        {
            "note_min": 14, "note_max": 15.99,
            "pourcentage": 50, "label": "Bourse Mérite",
            "reduction": 17500, "a_payer": 21000
        },
        {
            "note_min": 12, "note_max": 13.99,
            "pourcentage": 30, "label": "Bourse Encouragement",
            "reduction": 10500, "a_payer": 28000
        },
        {
            "note_min": 0, "note_max": 11.99,
            "pourcentage": 0, "label": "Pas de bourse",
            "reduction": 0, "a_payer": 38500
        }
    ],
    "note": (
        "La bourse s'applique uniquement sur les frais de scolarité (35 000 MAD). "
        "Les frais d'inscription (3 500 MAD) restent fixes."
    )
}

# ============================================================
# 4. LES 7 FILIÈRES DE SUPMTI
#
# STRUCTURE OFFICIELLE :
#   DÉPARTEMENT MANAGEMENT & FINANCE :
#     BAC+3 : MGE, MDI
#     BAC+5 : FACG, MRI
#   DÉPARTEMENT INGÉNIERIE (ISI) :
#     BAC+3 : IISI
#     BAC+5 : IISIC, IISRT
#
# PARCOURS :
#   IISI → IISIC ou IISRT
#   MGE  → FACG ou MRI
#   MDI  → MRI ou FACG
# ============================================================

FILIERES = {

    "MGE": {
        "id": "MGE",
        "nom": "Management de l'Entreprise",
        "nom_complet": "Management et Gestion des Entreprises",
        "intitule_arabe": "إدارة الشركة",
        "intitule_anglais": "Company Management",
        "niveau": "BAC+3",
        "departement": "Management et Finance",
        "duree": 3,
        "description": (
            "Formation de professionnels capables de comprendre et d'optimiser le "
            "fonctionnement des entreprises. Couvre le management digital, l'informatique "
            "de gestion, le marketing digital et l'e-commerce. Prépare à des carrières en "
            "management ou à la poursuite d'études en MRI ou FACG."
        ),
        "competences_cles": [
            "Management et organisation d'entreprise",
            "Marketing digital et e-commerce",
            "Informatique de gestion",
            "Comptabilité et contrôle de gestion",
            "Droit des affaires",
            "Communication professionnelle",
            "Entrepreneuriat et prise de décision stratégique"
        ],
        "debouches": [
            "Cadre bancaire",
            "Responsable commercial",
            "Chargé d'opérations dans une entreprise",
            "Analyste financier",
            "Chargé d'études marketing",
            "Assistant RH",
            "Cadre administratif"
        ],
        "salaire_depart_maroc": "4000-6000 MAD/mois",
        "salaire_3ans": "6000-10000 MAD/mois",
        "salaire_7ans": "10000-18000 MAD/mois",
        "poursuite_etudes": ["FACG", "MRI"],
        "difficulte": 2,
        "orientation_dominante": "gestion"
    },

    "MDI": {
        "id": "MDI",
        "nom": "Management et Développement International",
        "intitule_arabe": "الإدارة والتنمية الدولية",
        "intitule_anglais": "Management and International Development",
        "niveau": "BAC+3",
        "departement": "Management et Finance",
        "duree": 3,
        "description": (
            "Formation de professionnels capables de comprendre les dynamiques économiques "
            "internationales et de gérer des activités d'entreprise dans un environnement "
            "globalisé. Couvre le commerce international, la géopolitique, le marketing "
            "stratégique et la gestion financière internationale. Prépare à la poursuite "
            "d'études en MRI ou FACG."
        ),
        "competences_cles": [
            "Management international",
            "Commerce international",
            "Géopolitique et géoéconomie",
            "Marketing stratégique international",
            "Gestion financière internationale",
            "Systèmes d'information et e-management",
            "Leadership et gestion interculturelle"
        ],
        "debouches": [
            "Responsable du commerce international",
            "Chargé de développement international",
            "Responsable import-export",
            "Chargé d'affaires internationales",
            "Chargé d'études économiques et internationales",
            "Responsable marketing international",
            "Cadre administratif dans des entreprises multinationales",
            "Consultant en développement international"
        ],
        "salaire_depart_maroc": "4000-6000 MAD/mois",
        "salaire_3ans": "6000-10000 MAD/mois",
        "salaire_7ans": "10000-18000 MAD/mois",
        "poursuite_etudes": ["MRI", "FACG"],
        "difficulte": 2,
        "orientation_dominante": "international"
    },

    "FACG": {
        "id": "FACG",
        "nom": "Finance, Audit et Contrôle de Gestion",
        "intitule_arabe": "المالية والتدقيق والرقابة الإدارية",
        "intitule_anglais": "Finance, Audit and Management Control",
        "niveau": "BAC+5",
        "departement": "Management et Finance",
        "duree": 2,
        "description": (
            "Formation de cadres financiers et contrôleurs de gestion hautement qualifiés, "
            "capables d'occuper des postes à responsabilités au sein d'entreprises nationales "
            "et internationales. Maîtrise de la gestion financière, l'analyse des coûts, "
            "la mesure de la performance et les normes juridiques et fiscales."
        ),
        "competences_cles": [
            "Audit comptable et financier",
            "Contrôle de gestion stratégique",
            "Finance internationale",
            "Normes et méthodologie d'audit",
            "Fiscalité et droit des affaires",
            "Data Science et analyse des données financières",
            "Intelligence artificielle et automatisation en audit"
        ],
        "debouches": [
            "Auditeur interne ou externe",
            "Auditeur financier ou comptable",
            "Commissaire aux comptes",
            "Contrôleur de gestion",
            "Expert-comptable",
            "Directeur comptable et financier",
            "Conseiller en finance internationale",
            "Cadre dans le secteur bancaire ou des assurances"
        ],
        "salaire_depart_maroc": "6000-9000 MAD/mois",
        "salaire_3ans": "9000-15000 MAD/mois",
        "salaire_7ans": "15000-30000 MAD/mois",
        "poursuite_etudes": [],
        "admission_depuis": ["MGE", "MDI", "Licence gestion/économie/finance"],
        "difficulte": 4,
        "orientation_dominante": "finance"
    },

    "MRI": {
        "id": "MRI",
        "nom": "Management et Relations Internationales",
        "intitule_arabe": "الإدارة والعلاقات الدولية",
        "intitule_anglais": "Management and International Relations",
        "niveau": "BAC+5",
        "departement": "Management et Finance",
        "duree": 2,
        "description": (
            "Formation de cadres supérieurs capables de gérer des organisations dans un "
            "environnement économique globalisé, en intégrant les enjeux géopolitiques, "
            "économiques et stratégiques liés aux relations internationales. Solide maîtrise "
            "du management international avancé et de la finance internationale."
        ),
        "competences_cles": [
            "Stratégies de management international",
            "Relations économiques et géopolitiques internationales",
            "Commerce international et négociation",
            "Gestion des chaînes logistiques internationales",
            "Analyse et gestion des risques économiques et politiques",
            "Management d'équipes multiculturelles",
            "Finance internationale avancée"
        ],
        "debouches": [
            "Manager d'entreprise internationale",
            "Responsable du commerce international",
            "Responsable marketing international",
            "Chargé d'affaires internationales",
            "Responsable de la supply chain internationale",
            "Consultant en stratégie internationale",
            "Responsable des relations internationales",
            "Cadre administratif ou commercial dans des entreprises multinationales"
        ],
        "salaire_depart_maroc": "6000-9000 MAD/mois",
        "salaire_3ans": "9000-15000 MAD/mois",
        "salaire_7ans": "15000-28000 MAD/mois",
        "poursuite_etudes": [],
        "admission_depuis": ["MDI", "MGE", "Licence économie/gestion/management"],
        "difficulte": 3,
        "orientation_dominante": "international_avance"
    },

    "IISI": {
        "id": "IISI",
        "nom": "Ingénierie Intelligente des Systèmes Informatiques",
        "intitule_arabe": "الهندسة الذكية لأنظمة المعلوماتية",
        "intitule_anglais": "Intelligent Engineering of Computer Systems",
        "niveau": "BAC+3",
        "departement": "Ingénierie des Systèmes Informatiques (ISI)",
        "duree": 3,
        "description": (
            "Formation de techniciens spécialisés capables de concevoir, déployer et gérer "
            "des solutions informatiques performantes adaptées aux besoins opérationnels des "
            "entreprises. Le programme couvre le développement logiciel, les réseaux, la "
            "Data Science, la sécurité informatique et le cloud computing. Aussi référencé "
            "sous le sigle ISI en référence au département."
        ),
        "competences_cles": [
            "Développement logiciel et applications web",
            "Réseaux informatiques et infrastructure",
            "Bases de données et systèmes d'information",
            "Systèmes d'exploitation",
            "Machine learning et Data Science",
            "Sécurité informatique",
            "Cloud computing et industrie 4.0"
        ],
        "debouches": [
            "Responsable informatique",
            "Analyste programmeur",
            "Développeur de solutions web",
            "Webmaster",
            "Administrateur de réseaux",
            "Intégrateur de solutions informatiques clés en main"
        ],
        "salaire_depart_maroc": "4000-7000 MAD/mois",
        "salaire_3ans": "7000-12000 MAD/mois",
        "salaire_7ans": "12000-22000 MAD/mois",
        "poursuite_etudes": ["IISIC", "IISRT"],
        "difficulte": 3,
        "orientation_dominante": "informatique"
    },

    "IISIC": {
        "id": "IISIC",
        "nom": "Ingénierie Intelligente des Systèmes d'Information et Communication",
        "intitule_arabe": "الهندسة الذكية لأنظمة المعلومات والاتصالات",
        "intitule_anglais": "Intelligent Engineering of Information and Communication Systems",
        "niveau": "BAC+5",
        "departement": "Ingénierie des Systèmes Informatiques (ISI)",
        "duree": 2,
        "description": (
            "Formation d'ingénieurs opérationnels capables de concevoir et piloter la mise en "
            "place des systèmes de l'information avec des technologies de pointe pour la "
            "digitalisation des processus industriels. Intègre l'IA, la Data Science et "
            "les réseaux de communication intelligents."
        ),
        "competences_cles": [
            "Systèmes d'information et architecture SI",
            "Intelligence Artificielle et Machine Learning",
            "Data Science avancée",
            "Réseaux de communication intelligents",
            "Développement mobile et applications avancées",
            "Systèmes embarqués et IoT",
            "Cybersécurité des systèmes d'information"
        ],
        "debouches": [
            "Architecte des systèmes d'information",
            "Responsable de la cybersécurité des systèmes d'information",
            "Ingénieur IA / Machine Learning",
            "Data Scientist",
            "Technico-commercial en solutions TIC et systèmes d'information",
            "Chef de projet digital",
            "Consultant en transformation digitale"
        ],
        "salaire_depart_maroc": "7000-12000 MAD/mois",
        "salaire_3ans": "12000-20000 MAD/mois",
        "salaire_7ans": "20000-40000 MAD/mois",
        "poursuite_etudes": [],
        "admission_depuis": ["IISI", "Licence informatique/SI"],
        "difficulte": 5,
        "orientation_dominante": "ia_data"
    },

    "IISRT": {
        "id": "IISRT",
        "nom": "Ingénierie Intelligente des Systèmes Réseaux et Télécommunications",
        "intitule_arabe": "الهندسة الذكية لأنظمة الشبكات والاتصالات",
        "intitule_anglais": "Intelligent Engineering of Network and Telecommunication Systems",
        "niveau": "BAC+5",
        "departement": "Ingénierie des Systèmes Informatiques (ISI)",
        "duree": 2,
        "description": (
            "Formation d'ingénieurs spécialisés dans les réseaux intelligents, les "
            "télécommunications et les technologies de l'Industrie 4.0. Permet de superviser "
            "l'infrastructure hardware et software des entreprises et de maîtriser les "
            "solutions technologiques intelligentes des réseaux et télécommunications."
        ),
        "competences_cles": [
            "Infrastructure réseaux et télécommunication",
            "Architectures technologiques de réseaux",
            "Télécommunications mobiles et satellitaires",
            "Intelligence Artificielle et Data Science appliquées aux réseaux",
            "Systèmes embarqués et IoT",
            "Théorie de l'information et cryptologie",
            "Leadership technologique"
        ],
        "debouches": [
            "Architecte des systèmes réseaux",
            "Administrateur des réseaux informatiques et systèmes d'information",
            "Responsable des infrastructures télécoms et réseaux",
            "Technico-commercial en solutions réseaux et télécom",
            "Ingénieur en télécommunications",
            "Expert en sécurité réseaux",
            "Ingénieur IoT"
        ],
        "salaire_depart_maroc": "7000-12000 MAD/mois",
        "salaire_3ans": "12000-20000 MAD/mois",
        "salaire_7ans": "20000-38000 MAD/mois",
        "poursuite_etudes": [],
        "admission_depuis": ["IISI", "Licence informatique/réseaux/télécoms"],
        "difficulte": 5,
        "orientation_dominante": "reseaux_telecoms"
    }
}

# ============================================================
# 5. TYPES DE BAC ET LEURS MATIÈRES
# Source : conditions d'admission officielles Data1.txt v2
# ============================================================

TYPES_BAC = {
    # ── MAROC ──────────────────────────────────────────────
    "SMA": {
        "pays": "Maroc", "label": "Sciences Mathématiques A", "type": "scientifique",
        "matieres_principales": ["Mathématiques", "Langue française"],
        "matieres_secondaires": ["Physique-Chimie", "Philosophie", "Anglais"],
        "force_maths": 5, "force_physique": 4, "force_info": 3,
        "force_economie": 1, "force_gestion": 1, "force_langues": 2
    },
    "SMB": {
        "pays": "Maroc", "label": "Sciences Mathématiques B", "type": "scientifique",
        "matieres_principales": ["Mathématiques", "Langue française"],
        "matieres_secondaires": ["Physique-Chimie", "SVT", "Anglais"],
        "force_maths": 5, "force_physique": 4, "force_info": 3,
        "force_economie": 1, "force_gestion": 1, "force_langues": 2
    },
    "SP": {
        "pays": "Maroc", "label": "Sciences Physiques", "type": "scientifique",
        "matieres_principales": ["Physique-Chimie", "Langue française"],
        "matieres_secondaires": ["Mathématiques", "SVT", "Anglais"],
        "force_maths": 4, "force_physique": 5, "force_info": 2,
        "force_economie": 1, "force_gestion": 1, "force_langues": 2
    },
    "SVT": {
        "pays": "Maroc", "label": "Sciences de la Vie et de la Terre", "type": "scientifique",
        "matieres_principales": ["SVT", "Langue française"],
        "matieres_secondaires": ["Mathématiques", "Physique-Chimie", "Anglais"],
        "force_maths": 3, "force_physique": 3, "force_info": 1,
        "force_economie": 1, "force_gestion": 1, "force_langues": 3
    },
    "SGC": {
        "pays": "Maroc", "label": "Sciences de la Gestion Comptable", "type": "gestion",
        "matieres_principales": ["Économie et Organisation Administrative", "Comptabilité"],
        "matieres_secondaires": ["Mathématiques", "Droit", "Français", "Anglais"],
        "force_maths": 3, "force_physique": 1, "force_info": 1,
        "force_economie": 4, "force_gestion": 5, "force_langues": 2
    },
    "SEG": {
        "pays": "Maroc", "label": "Sciences Économiques et de Gestion", "type": "economique",
        "matieres_principales": ["Économie Générale et Statistiques", "Mathématiques"],
        "matieres_secondaires": ["Comptabilité", "Droit", "Français", "Anglais"],
        "force_maths": 3, "force_physique": 1, "force_info": 1,
        "force_economie": 5, "force_gestion": 4, "force_langues": 2
    },
    "STGC": {
        "pays": "Maroc", "label": "Sciences et Technologies de Gestion Comptable", "type": "gestion",
        "matieres_principales": ["Comptabilité", "Économie"],
        "matieres_secondaires": ["Mathématiques", "Droit", "Français", "Anglais"],
        "force_maths": 3, "force_physique": 1, "force_info": 1,
        "force_economie": 4, "force_gestion": 5, "force_langues": 2
    },
    "BAC_PRO_ECO": {
        "pays": "Maroc", "label": "Baccalauréat Professionnel Sciences Éco et de Gestion",
        "type": "professionnel_gestion",
        "matieres_principales": ["Matières professionnelles", "Économie"],
        "matieres_secondaires": ["Comptabilité", "Droit", "Français", "Anglais"],
        "force_maths": 2, "force_physique": 1, "force_info": 1,
        "force_economie": 4, "force_gestion": 4, "force_langues": 2
    },
    "STE": {
        "pays": "Maroc", "label": "Sciences et Technologies Électriques", "type": "technique",
        "matieres_principales": ["Électrotechnique", "Mathématiques", "Physique"],
        "matieres_secondaires": ["Français", "Anglais"],
        "force_maths": 4, "force_physique": 4, "force_info": 3,
        "force_economie": 1, "force_gestion": 1, "force_langues": 2
    },
    "STM": {
        "pays": "Maroc", "label": "Sciences et Technologies Mécaniques", "type": "technique",
        "matieres_principales": ["Mécanique", "Mathématiques", "Physique"],
        "matieres_secondaires": ["Français", "Anglais"],
        "force_maths": 4, "force_physique": 4, "force_info": 2,
        "force_economie": 1, "force_gestion": 1, "force_langues": 2
    },
    "LSH": {
        "pays": "Maroc", "label": "Lettres et Sciences Humaines", "type": "litteraire",
        "matieres_principales": ["Philosophie", "Histoire-Géographie", "Langues"],
        "matieres_secondaires": ["Mathématiques basiques"],
        "force_maths": 1, "force_physique": 1, "force_info": 1,
        "force_economie": 2, "force_gestion": 1, "force_langues": 5
    },
    # ── AFRIQUE SUBSAHARIENNE ───────────────────────────────
    "S": {
        "pays": "Afrique Subsaharienne", "label": "BAC S — Sciences", "type": "scientifique",
        "matieres_principales": ["Physique-Chimie", "Mathématiques", "SVT"],
        "matieres_secondaires": ["Philosophie", "Français", "Anglais"],
        "force_maths": 4, "force_physique": 5, "force_info": 2,
        "force_economie": 1, "force_gestion": 1, "force_langues": 3
    },
    "D": {
        "pays": "Afrique Subsaharienne", "label": "BAC D — Sciences de la Nature", "type": "scientifique",
        "matieres_principales": ["SVT", "Mathématiques", "Physique"],
        "matieres_secondaires": ["Philosophie", "Français", "Anglais"],
        "force_maths": 3, "force_physique": 3, "force_info": 1,
        "force_economie": 1, "force_gestion": 1, "force_langues": 3
    },
    "E_AFRIQUE": {
        "pays": "Afrique Subsaharienne", "label": "BAC E — Sciences et Technologie", "type": "technique",
        "matieres_principales": ["Mathématiques", "Physique", "Technologie"],
        "matieres_secondaires": ["Français", "Anglais"],
        "force_maths": 4, "force_physique": 4, "force_info": 3,
        "force_economie": 1, "force_gestion": 1, "force_langues": 3
    },
    "C": {
        "pays": "Afrique Subsaharienne", "label": "BAC C — Sciences Économiques et Mathématiques",
        "type": "economique",
        "matieres_principales": ["Mathématiques", "Économie", "Comptabilité"],
        "matieres_secondaires": ["Droit", "Français", "Anglais"],
        "force_maths": 3, "force_physique": 1, "force_info": 1,
        "force_economie": 5, "force_gestion": 4, "force_langues": 3
    },
    "G": {
        "pays": "Afrique Subsaharienne", "label": "BAC G — Gestion et Commerce", "type": "gestion",
        "matieres_principales": ["Gestion", "Économie", "Comptabilité"],
        "matieres_secondaires": ["Mathématiques", "Droit", "Français", "Anglais"],
        "force_maths": 2, "force_physique": 1, "force_info": 1,
        "force_economie": 4, "force_gestion": 5, "force_langues": 3
    },
    "L": {
        "pays": "Afrique Subsaharienne", "label": "BAC L — Lettres et Sciences Humaines",
        "type": "litteraire",
        "matieres_principales": ["Philosophie", "Langues", "Histoire-Géographie"],
        "matieres_secondaires": ["Mathématiques basiques"],
        "force_maths": 1, "force_physique": 1, "force_info": 1,
        "force_economie": 2, "force_gestion": 1, "force_langues": 5
    },
    # ── FRANCE / TUNISIE / ALGÉRIE ─────────────────────────
    "BAC_GENERAL_FR": {
        "pays": "France/Tunisie/Algérie", "label": "Baccalauréat Général", "type": "scientifique",
        "matieres_principales": ["Mathématiques", "Physique", "NSI ou Économie"],
        "matieres_secondaires": ["Philosophie", "Français", "Anglais"],
        "force_maths": 4, "force_physique": 4, "force_info": 3,
        "force_economie": 2, "force_gestion": 2, "force_langues": 3
    },
    "BAC_TECHNO_FR": {
        "pays": "France/Tunisie/Algérie", "label": "Baccalauréat Technologique", "type": "technique",
        "matieres_principales": ["Sciences et Technologies", "Mathématiques"],
        "matieres_secondaires": ["Physique", "Français", "Anglais"],
        "force_maths": 3, "force_physique": 3, "force_info": 3,
        "force_economie": 2, "force_gestion": 2, "force_langues": 3
    },
    "AUTRE": {
        "pays": "Autre", "label": "Diplôme étranger autre", "type": "inconnu",
        "matieres_principales": [], "matieres_secondaires": [],
        "force_maths": 3, "force_physique": 3, "force_info": 2,
        "force_economie": 2, "force_gestion": 2, "force_langues": 3
    }
}

# ============================================================
# 6. GRILLE DE COMPATIBILITÉ BAC → FILIÈRE
# Score de 1 à 5 (5 = idéal, 1 = très faible)
# ============================================================

COMPATIBILITE_BAC_FILIERE = {
    "SMA":           {"MGE": 3, "MDI": 3, "FACG": 3, "MRI": 3, "IISI": 5, "IISIC": 5, "IISRT": 5},
    "SMB":           {"MGE": 3, "MDI": 3, "FACG": 3, "MRI": 3, "IISI": 5, "IISIC": 5, "IISRT": 5},
    "SP":            {"MGE": 2, "MDI": 2, "FACG": 2, "MRI": 2, "IISI": 5, "IISIC": 4, "IISRT": 5},
    "SVT":           {"MGE": 3, "MDI": 3, "FACG": 2, "MRI": 2, "IISI": 4, "IISIC": 3, "IISRT": 3},
    "SGC":           {"MGE": 5, "MDI": 4, "FACG": 5, "MRI": 4, "IISI": 1, "IISIC": 1, "IISRT": 1},
    "SEG":           {"MGE": 5, "MDI": 5, "FACG": 5, "MRI": 5, "IISI": 1, "IISIC": 1, "IISRT": 1},
    "STGC":          {"MGE": 5, "MDI": 4, "FACG": 5, "MRI": 4, "IISI": 1, "IISIC": 1, "IISRT": 1},
    "BAC_PRO_ECO":   {"MGE": 4, "MDI": 4, "FACG": 4, "MRI": 4, "IISI": 1, "IISIC": 1, "IISRT": 1},
    "STE":           {"MGE": 2, "MDI": 2, "FACG": 1, "MRI": 1, "IISI": 4, "IISIC": 4, "IISRT": 5},
    "STM":           {"MGE": 2, "MDI": 2, "FACG": 1, "MRI": 1, "IISI": 4, "IISIC": 3, "IISRT": 4},
    "LSH":           {"MGE": 3, "MDI": 3, "FACG": 1, "MRI": 2, "IISI": 1, "IISIC": 1, "IISRT": 1},
    "S":             {"MGE": 3, "MDI": 3, "FACG": 2, "MRI": 2, "IISI": 5, "IISIC": 4, "IISRT": 5},
    "D":             {"MGE": 3, "MDI": 3, "FACG": 2, "MRI": 2, "IISI": 3, "IISIC": 3, "IISRT": 3},
    "E_AFRIQUE":     {"MGE": 2, "MDI": 2, "FACG": 1, "MRI": 1, "IISI": 4, "IISIC": 4, "IISRT": 5},
    "C":             {"MGE": 5, "MDI": 5, "FACG": 5, "MRI": 5, "IISI": 1, "IISIC": 1, "IISRT": 1},
    "G":             {"MGE": 5, "MDI": 4, "FACG": 4, "MRI": 4, "IISI": 1, "IISIC": 1, "IISRT": 1},
    "L":             {"MGE": 3, "MDI": 3, "FACG": 1, "MRI": 2, "IISI": 1, "IISIC": 1, "IISRT": 1},
    "BAC_GENERAL_FR": {"MGE": 3, "MDI": 3, "FACG": 3, "MRI": 3, "IISI": 4, "IISIC": 4, "IISRT": 4},
    "BAC_TECHNO_FR":  {"MGE": 2, "MDI": 2, "FACG": 2, "MRI": 2, "IISI": 4, "IISIC": 4, "IISRT": 4},
    "AUTRE":          {"MGE": 3, "MDI": 3, "FACG": 3, "MRI": 3, "IISI": 3, "IISIC": 3, "IISRT": 3}
}

# ============================================================
# 7. PONDÉRATION FITSCORE
# ============================================================

POIDS_FITSCORE = {
    "compatibilite_bac":          25,
    "moyenne_academique":         20,
    "notes_matieres_cles":        20,
    "profil_psychometrique":      20,
    "centres_interet":            10,
    "ambitions_professionnelles":  5
}

# ============================================================
# 8. PONDÉRATION DES MATIÈRES PAR FILIÈRE
# ============================================================

POIDS_MATIERES_FILIERES = {
    "IISI":  {"Mathématiques": 35, "Physique": 30, "Informatique": 20, "Autres": 15},
    "IISRT": {"Mathématiques": 35, "Physique": 30, "Informatique": 20, "Autres": 15},
    "IISIC": {"Mathématiques": 35, "Physique": 20, "Informatique": 30, "Autres": 15},
    "MGE":   {"Economie_Gestion": 35, "Mathématiques": 25, "Droit_Fiscalite": 20, "Autres": 20},
    "MDI":   {"Economie_Gestion": 30, "Mathématiques": 20, "Langues": 25, "Autres": 25},
    "FACG":  {"Economie_Gestion": 40, "Mathématiques": 30, "Droit_Fiscalite": 20, "Autres": 10},
    "MRI":   {"Economie_Gestion": 30, "Mathématiques": 15, "Langues": 30, "Autres": 25}
}

# ============================================================
# 9. BONUS MENTION BAC
# ============================================================

BONUS_MENTION  = {"tres_bien": 15, "bien": 10, "assez_bien": 5, "passable": 0}
SEUILS_MENTION = {"tres_bien": 16, "bien": 14, "assez_bien": 12, "passable": 10}

# ============================================================
# 10. CONDITIONS D'ADMISSION
# ============================================================

CONDITIONS_ADMISSION = {
    "1ere_annee": {
        "IISI": {
            "bac_requis": ["SMA", "SMB", "SP", "SVT", "STE", "STM",
                           "S", "D", "E_AFRIQUE", "BAC_GENERAL_FR", "BAC_TECHNO_FR"],
            "type_requis": ["scientifique", "technique"],
            "moyenne_min": 10,
            "description": "Baccalauréat scientifique ou technique obligatoire"
        },
        "MGE": {
            "bac_requis": ["SMA", "SMB", "SGC", "SVT", "SEG", "STGC", "BAC_PRO_ECO",
                           "STE", "STM", "S", "D", "C", "G", "L", "LSH",
                           "BAC_GENERAL_FR", "BAC_TECHNO_FR"],
            "type_requis": ["scientifique", "technique", "economique", "gestion",
                            "professionnel_gestion", "litteraire"],
            "moyenne_min": 10,
            "description": "Tous types de baccalauréat acceptés"
        },
        "MDI": {
            "bac_requis": ["SMA", "SMB", "SGC", "SVT", "SEG", "STGC", "BAC_PRO_ECO",
                           "STE", "STM", "S", "D", "C", "G", "L", "LSH",
                           "BAC_GENERAL_FR", "BAC_TECHNO_FR"],
            "type_requis": ["scientifique", "technique", "economique", "gestion",
                            "professionnel_gestion", "litteraire"],
            "moyenne_min": 10,
            "description": "Tous types de baccalauréat acceptés"
        }
    },
    "2eme_annee": {
        "diplomes_requis": ["BAC + 1ère année validée dans filière accréditée"],
        "moyenne_min": 11,
        "procedure": "Étude de dossier + entretien oral"
    },
    "3eme_annee": {
        "diplomes_requis": ["DUT", "BTS", "DEUG", "TS", "2ème année CPGE", "2ème année Licence"],
        "filieres_compatibles": {
            "IISI": ["DUT Informatique", "BTS Informatique", "DEUG Informatique",
                     "DUT Réseaux", "Licence 2 Informatique", "BTS Électronique"],
            "MGE":  ["BTS Gestion", "DUT GEA", "DEUG Économie",
                     "Licence 2 Gestion", "BTS Commerce", "DEUG Management"],
            "MDI":  ["BTS Commerce International", "DUT GEA", "DEUG Économie",
                     "Licence 2 Gestion", "BTS Commerce"]
        },
        "moyenne_min": 12,
        "procedure": "Étude de dossier + test écrit + entretien devant jury"
    },
    "4eme_annee": {
        "diplomes_requis": ["Licence BAC+3", "BAC+3 SUPMTI", "Diplôme équivalent BAC+3"],
        "filieres_compatibles": {
            "IISIC": ["BAC+3 IISI SUPMTI", "Licence Informatique", "Licence SI",
                      "Licence Réseaux", "Licence Sciences et Techniques"],
            "IISRT": ["BAC+3 IISI SUPMTI", "Licence Informatique", "Licence Réseaux",
                      "Licence Télécoms", "Licence Sciences et Techniques"],
            "FACG":  ["BAC+3 MGE SUPMTI", "BAC+3 MDI SUPMTI", "Licence Gestion",
                      "Licence Économie", "Licence Comptabilité", "Licence Finance", "Licence ISCAE"],
            "MRI":   ["BAC+3 MDI SUPMTI", "BAC+3 MGE SUPMTI", "Licence Économie",
                      "Licence Gestion", "Licence Commerce International", "Licence Management"]
        },
        "moyenne_min": 12,
        "procedure": "Étude de dossier + entretien oral + test écrit + concours bourse"
    }
}

# ============================================================
# 11. PROFIL PSYCHOMÉTRIQUE PAR FILIÈRE
# Clé exacte = "style_cognitif" (= DIMENSIONS_PSYCHO dans profile_service)
# ============================================================

PROFIL_PSYCHO_FILIERE = {
    "IISI":  {"logique": 5, "creativite": 3, "leadership": 2, "gestion_stress": 3, "travail_equipe": 3, "style_cognitif": 5},
    "IISRT": {"logique": 5, "creativite": 2, "leadership": 2, "gestion_stress": 4, "travail_equipe": 3, "style_cognitif": 5},
    "IISIC": {"logique": 5, "creativite": 4, "leadership": 3, "gestion_stress": 3, "travail_equipe": 4, "style_cognitif": 5},
    "MGE":   {"logique": 3, "creativite": 4, "leadership": 5, "gestion_stress": 4, "travail_equipe": 5, "style_cognitif": 3},
    "MDI":   {"logique": 3, "creativite": 4, "leadership": 5, "gestion_stress": 4, "travail_equipe": 5, "style_cognitif": 3},
    "FACG":  {"logique": 5, "creativite": 2, "leadership": 3, "gestion_stress": 4, "travail_equipe": 3, "style_cognitif": 5},
    "MRI":   {"logique": 3, "creativite": 4, "leadership": 5, "gestion_stress": 4, "travail_equipe": 5, "style_cognitif": 3}
}

# ============================================================
# 12. MOTS-CLÉS D'INTÉRÊTS PAR FILIÈRE
# ============================================================

INTERETS_FILIERE = {
    "IISI": [
        "informatique", "programmation", "code", "développement", "logiciel",
        "web", "application", "algorithme", "bases de données", "réseaux",
        "cybersécurité", "intelligence artificielle", "technologie", "python",
        "java", "cloud", "linux", "machine learning"
    ],
    "IISRT": [
        "réseaux", "télécommunications", "internet", "wifi", "infrastructure",
        "connectivité", "fibres optiques", "mobile", "4G", "5G",
        "systèmes embarqués", "IoT", "objets connectés", "cisco", "télécom",
        "industrie 4.0", "protocoles réseaux"
    ],
    "IISIC": [
        "intelligence artificielle", "machine learning", "data science",
        "big data", "cloud", "IA", "algorithmes", "innovation",
        "transformation digitale", "systèmes intelligents", "deep learning",
        "data", "analytique", "digitalisation"
    ],
    "MGE": [
        "management", "entreprise", "marketing", "commerce", "vente",
        "ressources humaines", "organisation", "stratégie", "entrepreneuriat",
        "communication", "leadership", "gestion", "finance",
        "comptabilité", "e-commerce", "digital"
    ],
    "MDI": [
        "international", "commerce international", "développement international",
        "géopolitique", "management international", "import export",
        "multinationale", "mondialisation", "langues", "diplomatie",
        "affaires internationales", "supply chain", "étranger", "global"
    ],
    "FACG": [
        "finance", "comptabilité", "audit", "bourse", "investissement",
        "contrôle de gestion", "fiscalité", "chiffres", "analyse financière",
        "banque", "assurance", "commissaire aux comptes", "expert comptable",
        "normes IFRS", "risk management"
    ],
    "MRI": [
        "relations internationales", "management international", "géopolitique",
        "commerce mondial", "stratégie internationale", "négociation internationale",
        "supply chain internationale", "marchés mondiaux", "diplomatie économique",
        "export", "affaires mondiales", "développement durable international"
    ]
}

# ============================================================
# 13. HISTORIQUE ADMISSION (SIMULÉ)
# ============================================================

HISTORIQUE_ADMISSION = {
    "IISI":  {"moyenne_admis": 12.5, "fitscore_moyen": 65, "taux_admission": 0.75,
              "profil_type": "BAC scientifique (SMA/SMB/SVT/SP), bonne moyenne en maths"},
    "IISRT": {"moyenne_admis": 13.5, "fitscore_moyen": 70, "taux_admission": 0.68,
              "profil_type": "BAC+3 IISI ou Licence informatique, fort en réseaux et maths"},
    "IISIC": {"moyenne_admis": 14.0, "fitscore_moyen": 72, "taux_admission": 0.65,
              "profil_type": "BAC+3 IISI ou Licence informatique, intérêt pour l'IA et la data"},
    "MGE":   {"moyenne_admis": 11.5, "fitscore_moyen": 60, "taux_admission": 0.80,
              "profil_type": "BAC économique ou gestion, intérêt pour le commerce et le management"},
    "MDI":   {"moyenne_admis": 11.5, "fitscore_moyen": 60, "taux_admission": 0.78,
              "profil_type": "BAC économique ou gestion, intérêt pour l'international et les langues"},
    "FACG":  {"moyenne_admis": 13.0, "fitscore_moyen": 68, "taux_admission": 0.70,
              "profil_type": "BAC+3 gestion ou économie (MGE/MDI), bon en maths et finance"},
    "MRI":   {"moyenne_admis": 12.5, "fitscore_moyen": 65, "taux_admission": 0.72,
              "profil_type": "BAC+3 MDI ou MGE, intérêt marqué pour l'international et les langues"}
}

# ============================================================
# 14. SIGNAUX D'HÉSITATION POUR LE PEER MATCH
# ============================================================

SIGNAUX_HESITATION = [
    # Français
    "je sais pas trop", "j'hésite", "pas sûr", "pas sure",
    "j'suis pas certain", "j'ai peur", "je suis perdu",
    "c'est difficile de choisir", "j'arrive pas à décider",
    "vous pensez vraiment", "t'es sûr", "vraiment fait pour moi",
    "j'aimerais avoir l'avis", "quelqu'un qui a vécu",
    "témoignage", "parler avec un étudiant", "hésitation", "indécis",
    # Darija latin
    "khayef", "khayfa", "machi mdrass", "ma3arfch",
    "mnin nbda", "wach hiya zwina", "machi 3aarif",
    # Darija arabe
    "خايف", "ما عارفش", "محتار", "مش واثق", "مترددة", "متردد", "ما قدرتش نختار"
]

# ============================================================
# 15. CONFIGURATION DU CHATBOT
# ============================================================

CHATBOT_CONFIG = {
    "nom":         "Sami",
    "description": "Assistant Intelligent d'Orientation Académique de SUPMTI Meknès",
    "langue_defaut":      "français",
    "langues_supportees": ["français", "darija_latin", "darija_arabe", "anglais"],
    "min_echanges_peer_match": 5,
    "max_historique_tokens":   3000,
    "temperature_gpt":         0.7,
    "modele_gpt":              "gpt-5.2",
    "modele_embedding":        "text-embedding-ada-002",
    # Optimisé pour Data1.txt officiel (69 000 chars / ~16 244 tokens)
    # 6 filières tiennent en 1 chunk | IISRT tient en 3 chunks
    # chunk_size=1600 garantit que chaque filière est dans ≤3 chunks cohérents
    # overlap=400 assure la continuité des semestres entre chunks
    "chunk_size":     1600,
    "chunk_overlap":  400,
    "top_k_recherche": 10   # conservateur : 10 chunks suffit pour tout récupérer
}

# ============================================================
# 16. URL DU SITE SUPMTI
# NOTE : scraping SUSPENDU (voir rag_service.py, variable SCRAPING_ACTIF)
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
    "https://supmtimeknes.ac.ma/les-clubs/",
    "https://supmtimeknes.ac.ma/contact/",
]