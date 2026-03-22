"""
Route pour comparer plusieurs programmes d'études.
Version robuste avec gestion des accents et caractères spéciaux.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from uuid import UUID
import unicodedata

from app.database.connection import get_db
from app.database.models import Program
from app.core.logging import logger

router = APIRouter(prefix="/compare", tags=["comparaison"])

# === CONSTANTES POUR LES DONNÉES STATIQUES ===
CAREERS_DB = {
    "Intelligence Artificielle": "🧠 Data Scientist, Ingénieur IA, ML Engineer, Chercheur",
    "IA": "🧠 Data Scientist, Ingénieur IA, ML Engineer, Chercheur",
    "Data Science": "📊 Data Scientist, Data Analyst, Data Engineer, Chief Data Officer",
    "Cybersécurité": "🛡️ Analyste Cyber, Pentester, RSSI, Consultant sécurité, Forensic Analyst",
    "Génie Logiciel": "💻 Développeur Full Stack, Architecte logiciel, DevOps, Tech Lead",
    "Cloud": "☁️ Cloud Architect, DevOps Engineer, Ingénieur Cloud, SRE",
    "Cloud Computing": "☁️ Cloud Architect, DevOps Engineer, Ingénieur Cloud, SRE",
    "Management": "📈 Chef de projet, DSI, Consultant, Manager, Product Owner",
    "Finance": "💰 Auditeur, Contrôleur de gestion, Analyste financier, Risk Manager",
    "Réseaux": "🌐 Administrateur réseau, Ingénieur télécoms, Architecte infrastructure",
    "Télécommunications": "📡 Ingénieur télécoms, Architecte réseau, Expert 5G"
}

SUBJECTS_DB = {
    "Intelligence Artificielle": "🧮 Machine Learning, Deep Learning, NLP, Computer Vision, Python, Mathématiques",
    "IA": "🧮 Machine Learning, Deep Learning, NLP, Computer Vision, Python, Mathématiques",
    "Data Science": "📉 Statistiques, Python, SQL, Big Data, Visualisation, Hadoop",
    "Cybersécurité": "🔐 Cryptographie, Ethical Hacking, Sécurité réseau, Forensique, SOC",
    "Génie Logiciel": "⚙️ Algorithmique, Bases de données, Web, Mobile, Architecture, Design Patterns",
    "Cloud": "🚀 Docker, Kubernetes, AWS/Azure/GCP, DevOps, CI/CD, Terraform",
    "Cloud Computing": "🚀 Docker, Kubernetes, AWS/Azure/GCP, DevOps, CI/CD, Terraform",
    "Management": "📋 Gestion de projet, RH, Marketing, Finance, Stratégie, Leadership",
    "Finance": "🧾 Comptabilité, Audit, Contrôle de gestion, Finance internationale, Excel",
    "Réseaux": "🖧 TCP/IP, Routage, Commutation, VLAN, VPN, Sécurité réseau",
    "Télécommunications": "📶 Transmission, 5G, IoT, Fibre optique, Signal, Antennes"
}

# === FONCTIONS DE NETTOYAGE ===
def normalize_text(text: str) -> str:
    """
    Normalise un texte en enlevant les accents et caractères spéciaux.
    Exemple: "Cybersécurité" -> "cybersecurite"
    """
    normalized = unicodedata.normalize('NFKD', text)
    normalized = normalized.encode('ASCII', 'ignore').decode('utf-8')
    return normalized.lower()

def get_career_by_keywords(program_name: str) -> str:
    """
    Recherche les débouchés par mots-clés (version ultra-robuste avec cas spéciaux).
    """
    # === CAS SPÉCIAUX EXPLICITES (priorité absolue) ===
    special_cases = {
        # Cybersécurité
        "Cybers‚curit‚": "🛡️ Analyste Cyber, Pentester, RSSI, Consultant sécurité, Forensic Analyst",
        "Cybersécurité": "🛡️ Analyste Cyber, Pentester, RSSI, Consultant sécurité, Forensic Analyst",
        "S‚curit‚": "🛡️ Analyste Cyber, Pentester, RSSI, Consultant sécurité, Forensic Analyst",
        "Sécurité": "🛡️ Analyste Cyber, Pentester, RSSI, Consultant sécurité, Forensic Analyst",
        
        # Réseaux
        "R‚seaux": "🌐 Administrateur réseau, Ingénieur télécoms, Architecte infrastructure",
        "Réseaux": "🌐 Administrateur réseau, Ingénieur télécoms, Architecte infrastructure",
        "Reseaux": "🌐 Administrateur réseau, Ingénieur télécoms, Architecte infrastructure",
        
        # Télécommunications
        "T‚l‚communications": "📡 Ingénieur télécoms, Architecte réseau, Expert 5G",
        "Télécommunications": "📡 Ingénieur télécoms, Architecte réseau, Expert 5G",
        "Telecommunications": "📡 Ingénieur télécoms, Architecte réseau, Expert 5G",
        "T‚l‚com": "📡 Ingénieur télécoms, Architecte réseau, Expert 5G",
        "Télécom": "📡 Ingénieur télécoms, Architecte réseau, Expert 5G",
    }
    
    for key, value in special_cases.items():
        if key in program_name:
            return value
    
    # Nettoyer le nom du programme
    clean_name = normalize_text(program_name)
    
    # Dictionnaire de mots-clés avec leurs débouchés
    career_map = {
        "ia": "🧠 Data Scientist, Ingénieur IA, ML Engineer, Chercheur",
        "intelligence": "🧠 Data Scientist, Ingénieur IA, ML Engineer, Chercheur",
        "artificielle": "🧠 Data Scientist, Ingénieur IA, ML Engineer, Chercheur",
        "data": "📊 Data Scientist, Data Analyst, Data Engineer, Chief Data Officer",
        "science": "📊 Data Scientist, Data Analyst, Data Engineer, Chief Data Officer",
        "cyber": "🛡️ Analyste Cyber, Pentester, RSSI, Consultant sécurité, Forensic Analyst",
        "securite": "🛡️ Analyste Cyber, Pentester, RSSI, Consultant sécurité, Forensic Analyst",
        "securit": "🛡️ Analyste Cyber, Pentester, RSSI, Consultant sécurité, Forensic Analyst",
        "secur": "🛡️ Analyste Cyber, Pentester, RSSI, Consultant sécurité, Forensic Analyst",
        "logiciel": "💻 Développeur Full Stack, Architecte logiciel, DevOps, Tech Lead",
        "software": "💻 Développeur Full Stack, Architecte logiciel, DevOps, Tech Lead",
        "cloud": "☁️ Cloud Architect, DevOps Engineer, Ingénieur Cloud, SRE",
        "computing": "☁️ Cloud Architect, DevOps Engineer, Ingénieur Cloud, SRE",
        "management": "📈 Chef de projet, DSI, Consultant, Manager, Product Owner",
        "manage": "📈 Chef de projet, DSI, Consultant, Manager, Product Owner",
        "finance": "💰 Auditeur, Contrôleur de gestion, Analyste financier, Risk Manager",
        "audit": "💰 Auditeur, Contrôleur de gestion, Analyste financier, Risk Manager",
        "reseau": "🌐 Administrateur réseau, Ingénieur télécoms, Architecte infrastructure",
        "res": "🌐 Administrateur réseau, Ingénieur télécoms, Architecte infrastructure",
        "telecom": "📡 Ingénieur télécoms, Architecte réseau, Expert 5G",
        "telecommunication": "📡 Ingénieur télécoms, Architecte réseau, Expert 5G"
    }
    
    for key, value in career_map.items():
        if key in clean_name:
            return value
    
    return "Consulter la documentation pour plus de détails"

def get_subjects_by_keywords(program_name: str) -> str:
    """
    Recherche les matières par mots-clés (version ultra-robuste avec cas spéciaux).
    """
    # === CAS SPÉCIAUX EXPLICITES (priorité absolue) ===
    special_cases = {
        # Cybersécurité
        "Cybers‚curit‚": "🔐 Cryptographie, Ethical Hacking, Sécurité réseau, Forensique, SOC",
        "Cybersécurité": "🔐 Cryptographie, Ethical Hacking, Sécurité réseau, Forensique, SOC",
        "S‚curit‚": "🔐 Cryptographie, Ethical Hacking, Sécurité réseau, Forensique, SOC",
        "Sécurité": "🔐 Cryptographie, Ethical Hacking, Sécurité réseau, Forensique, SOC",
        
        # Réseaux
        "R‚seaux": "🖧 TCP/IP, Routage, Commutation, VLAN, VPN, Sécurité réseau",
        "Réseaux": "🖧 TCP/IP, Routage, Commutation, VLAN, VPN, Sécurité réseau",
        "Reseaux": "🖧 TCP/IP, Routage, Commutation, VLAN, VPN, Sécurité réseau",
        
        # Télécommunications
        "T‚l‚communications": "📶 Transmission, 5G, IoT, Fibre optique, Signal, Antennes",
        "Télécommunications": "📶 Transmission, 5G, IoT, Fibre optique, Signal, Antennes",
        "Telecommunications": "📶 Transmission, 5G, IoT, Fibre optique, Signal, Antennes",
        "T‚l‚com": "📶 Transmission, 5G, IoT, Fibre optique, Signal, Antennes",
        "Télécom": "📶 Transmission, 5G, IoT, Fibre optique, Signal, Antennes",
    }
    
    for key, value in special_cases.items():
        if key in program_name:
            return value
    
    # Nettoyer le nom du programme
    clean_name = normalize_text(program_name)
    
    # Dictionnaire de mots-clés avec leurs matières
    subjects_map = {
        "ia": "🧮 Machine Learning, Deep Learning, NLP, Computer Vision, Python, Mathématiques",
        "intelligence": "🧮 Machine Learning, Deep Learning, NLP, Computer Vision, Python, Mathématiques",
        "artificielle": "🧮 Machine Learning, Deep Learning, NLP, Computer Vision, Python, Mathématiques",
        "data": "📉 Statistiques, Python, SQL, Big Data, Visualisation, Hadoop",
        "science": "📉 Statistiques, Python, SQL, Big Data, Visualisation, Hadoop",
        "cyber": "🔐 Cryptographie, Ethical Hacking, Sécurité réseau, Forensique, SOC",
        "securite": "🔐 Cryptographie, Ethical Hacking, Sécurité réseau, Forensique, SOC",
        "securit": "🔐 Cryptographie, Ethical Hacking, Sécurité réseau, Forensique, SOC",
        "secur": "🔐 Cryptographie, Ethical Hacking, Sécurité réseau, Forensique, SOC",
        "logiciel": "⚙️ Algorithmique, Bases de données, Web, Mobile, Architecture, Design Patterns",
        "software": "⚙️ Algorithmique, Bases de données, Web, Mobile, Architecture, Design Patterns",
        "cloud": "🚀 Docker, Kubernetes, AWS/Azure/GCP, DevOps, CI/CD, Terraform",
        "computing": "🚀 Docker, Kubernetes, AWS/Azure/GCP, DevOps, CI/CD, Terraform",
        "management": "📋 Gestion de projet, RH, Marketing, Finance, Stratégie, Leadership",
        "manage": "📋 Gestion de projet, RH, Marketing, Finance, Stratégie, Leadership",
        "finance": "🧾 Comptabilité, Audit, Contrôle de gestion, Finance internationale, Excel",
        "audit": "🧾 Comptabilité, Audit, Contrôle de gestion, Finance internationale, Excel",
        "reseau": "🖧 TCP/IP, Routage, Commutation, VLAN, VPN, Sécurité réseau",
        "res": "🖧 TCP/IP, Routage, Commutation, VLAN, VPN, Sécurité réseau",
        "telecom": "📶 Transmission, 5G, IoT, Fibre optique, Signal, Antennes",
        "telecommunication": "📶 Transmission, 5G, IoT, Fibre optique, Signal, Antennes"
    }
    
    for key, value in subjects_map.items():
        if key in clean_name:
            return value
    
    return "Programme pluridisciplinaire - consulter la documentation"

# === ROUTES ===
@router.get("/programs", response_model=List[Dict[str, Any]])
def compare_programs(
    program_ids: str = Query(
        ..., 
        description="IDs des programmes séparés par des virgules (ex: id1,id2,id3)",
        example="123e4567-e89b-12d3-a456-426614174000,123e4567-e89b-12d3-a456-426614174001"
    ),
    db: Session = Depends(get_db)
):
    """
    Compare plusieurs programmes côte à côte.
    
    - **program_ids**: Liste d'UUIDs séparés par des virgules (max 3)
    
    Retourne un tableau comparatif avec:
    - Nom du programme
    - Description
    - Durée
    - Diplôme
    - Moyenne requise
    - Débouchés
    - Matières principales
    """
    logger.info(f"📊 GET /compare/programs - IDs: {program_ids}")
    
    # Nettoyer et séparer les IDs
    id_list = [id.strip() for id in program_ids.split(',') if id.strip()]
    
    # Validation du nombre de programmes
    if len(id_list) > 3:
        raise HTTPException(
            status_code=400, 
            detail="Maximum 3 programmes à comparer"
        )
    
    if len(id_list) < 2:
        raise HTTPException(
            status_code=400, 
            detail="Minimum 2 programmes requis pour une comparaison"
        )
    
    programs = []
    errors = []
    
    for program_id in id_list:
        try:
            program_uuid = UUID(program_id)
            program = db.query(Program).filter(Program.id == program_uuid).first()
            
            if program:
                programs.append({
                    "id": str(program.id),
                    "name": program.name,
                    "description": program.description,
                    "duration": program.duration,
                    "diploma": program.diploma,
                    "required_average": program.required_average,
                    "career_opportunities": get_career_by_keywords(program.name),
                    "key_subjects": get_subjects_by_keywords(program.name)
                })
            else:
                errors.append(f"Programme non trouvé: {program_id}")
                
        except ValueError:
            errors.append(f"ID invalide (format UUID requis): {program_id}")
    
    # Gestion des erreurs
    if errors and not programs:
        raise HTTPException(
            status_code=404, 
            detail="; ".join(errors)
        )
    
    # Message d'avertissement si certains programmes n'ont pas été trouvés
    if errors and programs:
        logger.warning(f"⚠️ Certains programmes n'ont pas été trouvés: {errors}")
    
    return programs


@router.get("/summary", response_model=Dict[str, Any])
def compare_summary(
    program1: str = Query(
        ..., 
        description="ID du premier programme",
        example="123e4567-e89b-12d3-a456-426614174000"
    ),
    program2: str = Query(
        ..., 
        description="ID du second programme",
        example="123e4567-e89b-12d3-a456-426614174001"
    ),
    db: Session = Depends(get_db)
):
    """
    Version simplifiée pour comparer exactement 2 programmes.
    Retourne un tableau comparatif détaillé.
    """
    logger.info(f"📊 GET /compare/summary - {program1} vs {program2}")
    
    # Validation des UUIDs
    try:
        p1_uuid = UUID(program1)
        p2_uuid = UUID(program2)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail="Format UUID invalide pour un ou plusieurs IDs"
        )
    
    # Récupération des programmes
    p1 = db.query(Program).filter(Program.id == p1_uuid).first()
    p2 = db.query(Program).filter(Program.id == p2_uuid).first()
    
    if not p1 or not p2:
        missing = []
        if not p1:
            missing.append("programme 1")
        if not p2:
            missing.append("programme 2")
        raise HTTPException(
            status_code=404, 
            detail=f"Programme(s) non trouvé(s): {', '.join(missing)}"
        )
    
    # Création du tableau comparatif
    comparison = [
        {
            "critere": "🎓 Nom du programme",
            "programme1": p1.name,
            "programme2": p2.name
        },
        {
            "critere": "⏱️ Durée",
            "programme1": f"{p1.duration} ans",
            "programme2": f"{p2.duration} ans"
        },
        {
            "critere": "📜 Diplôme",
            "programme1": p1.diploma,
            "programme2": p2.diploma
        },
        {
            "critere": "📊 Moyenne requise",
            "programme1": f"{p1.required_average}/20",
            "programme2": f"{p2.required_average}/20"
        },
        {
            "critere": "💼 Débouchés",
            "programme1": get_career_by_keywords(p1.name),
            "programme2": get_career_by_keywords(p2.name)
        },
        {
            "critere": "📚 Matières principales",
            "programme1": get_subjects_by_keywords(p1.name),
            "programme2": get_subjects_by_keywords(p2.name)
        }
    ]
    
    return {
        "programs": {
            "program1": {
                "id": str(p1.id),
                "name": p1.name
            },
            "program2": {
                "id": str(p2.id),
                "name": p2.name
            }
        },
        "comparison": comparison,
        "total_criteria": len(comparison)
    }