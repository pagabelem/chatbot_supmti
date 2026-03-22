# app/services/peermatch_service.py — VERSION MISE À JOUR

from sqlalchemy.orm import Session
from app.database.models import Ambassadeur, DemandePeerMatch
from sqlalchemy import func

def trouver_ambassadeur(db: Session, filiere: str):
    """Trouve un ambassadeur actif pour une filière donnée de manière aléatoire."""
    return (
        db.query(Ambassadeur)
        .filter(
            Ambassadeur.program_id == filiere,
            Ambassadeur.is_active  == True
        )
        .order_by(func.random())
        .first()
    )

def creer_demande_peermatch(
    db: Session,
    filiere: str,
    prenom: str,
    email: str,
    message: str
):
    """Crée une demande de mise en relation et l'assigne à un ambassadeur."""

    # 1. Chercher un ambassadeur disponible pour cette filière
    ambassadeur = trouver_ambassadeur(db, filiere)

    # 2. Créer la demande même sans ambassadeur (statut en_attente)
    demande = DemandePeerMatch(
        ambassadeur_id  = ambassadeur.id if ambassadeur else None,
        prenom_etudiant = prenom,
        email_etudiant  = email,
        filiere         = filiere,
        message         = message,
        statut          = "en_attente",
    )

    try:
        db.add(demande)
        db.commit()
        db.refresh(demande)

        # 3. Retourner les infos + demande_id pour le suivi côté étudiant
        return {
            "demande_id":           str(demande.id),
            "ambassadeur":          ambassadeur.nom       if ambassadeur else None,
            "contact_email":        ambassadeur.email     if ambassadeur else None,
            "contact_wa":           ambassadeur.whatsapp  if ambassadeur else None,
            # Rétrocompatibilité avec l'ancien format
            "ambassadeur_nom":      ambassadeur.nom       if ambassadeur else None,
            "ambassadeur_email":    ambassadeur.email     if ambassadeur else None,
            "ambassadeur_whatsapp": ambassadeur.whatsapp  if ambassadeur else None,
            "statut": "success",
        }
    except Exception as e:
        db.rollback()
        print(f"Erreur PeerMatch: {e}")
        return None