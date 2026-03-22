from sqlalchemy.orm import Session
from typing import List, Dict, Optional
import json

def demarrer_test_psychometrique():
    """Initialise un nouveau test avec la première question."""
    return {
        "step": 1,
        "total_steps": 5,
        "question": "Préférez-vous concevoir des solutions techniques ou gérer des équipes de projet ?",
        "options": [
            {"id": "A", "text": "Concevoir des solutions techniques"},
            {"id": "B", "text": "Gérer des équipes et des ressources"}
        ]
    }

def generer_question_suivante(step: int, reponses_precedentes: List[str]):
    """Logique pour envoyer la question suivante selon l'avancement."""
    questions = {
        2: {
            "question": "Face à un problème complexe, quelle est votre approche ?",
            "options": [
                {"id": "A", "text": "Analyser les données et coder une solution"},
                {"id": "B", "text": "Chercher une approche innovante et visuelle"}
            ]
        },
        3: {
            "question": "Quel environnement de travail vous attire le plus ?",
            "options": [
                {"id": "A", "text": "Un laboratoire de R&D ou un centre de données"},
                {"id": "B", "text": "Un cabinet de conseil ou une agence créative"}
            ]
        },
        4: {
            "question": "Aimez-vous manipuler des infrastructures réseau et serveurs ?",
            "options": [
                {"id": "A", "text": "Oui, énormément"},
                {"id": "B", "text": "Je préfère les aspects marketing et business"}
            ]
        },
        5: {
            "question": "Dernière question : Quelle est votre priorité pour votre future carrière ?",
            "options": [
                {"id": "A", "text": "Devenir un expert technique reconnu"},
                {"id": "B", "text": "Devenir un leader ou entrepreneur"}
            ]
        }
    }
    return questions.get(step)

def calculer_profil_psychometrique_final(reponses: List[str]) -> str:
    """Analyse les réponses pour déterminer un profil type."""
    count_a = reponses.count("A")
    if count_a >= 4:
        return "Technique Pur (Ingénierie/Développement)"
    elif count_a == 3:
        return "Hybride (Systèmes et Management)"
    else:
        return "Managérial et Stratégique"

def generer_rapport_psychometrique(profil: str) -> str:
    """Génère un court texte de synthèse pour l'étudiant."""
    rapports = {
        "Technique Pur (Ingénierie/Développement)": "Votre profil montre une forte appétence pour la résolution de problèmes complexes et l'architecture logicielle.",
        "Hybride (Systèmes et Management)": "Vous avez un profil équilibré, capable de comprendre les enjeux techniques tout en pilotant des projets.",
        "Managérial et Stratégique": "Vous êtes orienté vers la prise de décision, la stratégie digitale et le leadership."
    }
    return rapports.get(profil, "Profil varié")

def construire_profil_etudiant(db: Session, user_id: str, reponses: List[str]):
    """Sauvegarde ou prépare l'objet profil pour la base de données."""
    profil_type = calculer_profil_psychometrique_final(reponses)
    return {
        "user_id": user_id,
        "profil": profil_type,
        "date_test": "2026-03-12"
    }