"""
Routes pour la gestion des profils étudiants.
"""
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, validator, Field
from typing import Optional, List
from uuid import UUID
import uuid

from app.database.connection import get_db
from app.services.profile_service import save_user_profile, get_user_profile, list_all_profiles
from app.database.models import Student, Interest, StudentInterest
from app.core.exceptions import NotFoundError
from app.core.logging import logger

router = APIRouter(prefix="/profile", tags=["profils"])

# === Schémas Pydantic ===
class ProfileRequest(BaseModel):
    """Schéma pour la création de profil"""
    name: str = Field(..., min_length=1, max_length=100, description="Nom complet de l'étudiant")
    interests: str = Field(..., min_length=1, description="Centres d'intérêt séparés par des virgules")
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Le nom ne peut pas être vide')
        return v.strip()
    
    @validator('interests')
    def validate_interests(cls, v):
        if not v or not v.strip():
            raise ValueError('Au moins un intérêt est requis')
        interests = [i.strip() for i in v.split(',') if i.strip()]
        if not interests:
            raise ValueError('Au moins un intérêt valide requis')
        return ', '.join(interests)

class ProfileResponse(BaseModel):
    """Schéma pour la réponse de profil"""
    name: str
    interests: str
    student_id: str
    created_at: Optional[str] = None

class InterestsResponse(BaseModel):
    """Schéma pour la réponse des intérêts"""
    student_id: str
    student_name: str
    interests: List[str]

# === Routes existantes (inchangées) ===
@router.post(
    "",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un profil étudiant",
    description="Crée un nouvel étudiant avec ses centres d'intérêt"
)
def create_profile(
    request: ProfileRequest,
    db: Session = Depends(get_db)
):
    """
    Crée un nouveau profil étudiant.
    
    - **name**: Nom complet de l'étudiant (obligatoire)
    - **interests**: Liste d'intérêts séparés par des virgules (obligatoire)
    
    Retourne les informations du profil créé avec son ID unique.
    """
    logger.info(f"POST /profile - Création pour: {request.name}")
    
    profile = save_user_profile(db, request.name, request.interests)
    
    return {
        "message": "Profil enregistré avec succès",
        "profile": profile
    }

@router.get(
    "",
    response_model=dict,
    summary="Récupérer un profil",
    description="Récupère un profil étudiant par son ID ou le dernier profil"
)
def read_profile(
    student_id: Optional[str] = Query(
        None,
        description="ID de l'étudiant (UUID). Si non fourni, retourne le dernier profil"
    ),
    db: Session = Depends(get_db)
):
    """
    Récupère un profil étudiant.
    
    - **student_id**: ID de l'étudiant (optionnel)
    
    Si **student_id** est fourni, retourne ce profil spécifique.
    Sinon, retourne le dernier profil créé.
    """
    logger.info(f"GET /profile - Récupération: {student_id or 'dernier'}")
    
    profile = get_user_profile(db, student_id)
    
    if not profile:
        if student_id:
            raise NotFoundError("Étudiant", student_id)
        return {"profile": None, "message": "Aucun profil trouvé"}
    
    return {"profile": profile}

@router.get(
    "/all",
    response_model=List[dict],
    summary="Lister tous les profils",
    description="Liste tous les profils étudiants (pour administration)"
)
def list_profiles(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(10, ge=1, le=100, description="Nombre maximum d'éléments"),
    db: Session = Depends(get_db)
):
    """
    Liste tous les profils étudiants avec pagination.
    
    - **skip**: Combien de profils sauter (pour pagination)
    - **limit**: Combien de profils maximum à retourner
    """
    logger.info(f"GET /profile/all - skip={skip}, limit={limit}")
    
    profiles = list_all_profiles(db, skip, limit)
    
    return profiles


# === NOUVELLES ROUTES POUR LA GESTION DES INTÉRÊTS ===

@router.post(
    "/{student_id}/interests",
    status_code=status.HTTP_200_OK,
    summary="Ajouter des intérêts à un étudiant",
    description="Ajoute ou remplace les centres d'intérêt d'un étudiant existant"
)
def add_student_interests(
    student_id: str,
    interests: str = Query(..., description="Liste d'intérêts séparés par des virgules (ex: IA, Cybersécurité, Cloud)"),
    db: Session = Depends(get_db)
):
    """
    Ajoute des centres d'intérêt à un étudiant existant.
    
    - **student_id**: UUID de l'étudiant
    - **interests**: Liste d'intérêts séparés par des virgules
    
    Cette route remplace tous les intérêts existants par les nouveaux.
    """
    logger.info(f"📝 POST /profile/{student_id}/interests - Ajout d'intérêts")
    
    # Nettoyer l'ID
    clean_id = student_id.strip()
    
    # Récupérer l'étudiant
    try:
        student_uuid = UUID(clean_id)
        student = db.query(Student).filter(Student.id == student_uuid).first()
    except ValueError:
        raise HTTPException(status_code=400, detail="ID étudiant invalide")
    
    if not student:
        raise HTTPException(status_code=404, detail="Étudiant non trouvé")
    
    # Supprimer les anciens intérêts
    deleted = db.query(StudentInterest).filter(StudentInterest.student_id == student.id).delete()
    logger.info(f"🗑️ {deleted} anciens intérêts supprimés")
    
    # Ajouter les nouveaux intérêts
    interest_list = [i.strip() for i in interests.split(',') if i.strip()]
    
    if not interest_list:
        raise HTTPException(status_code=400, detail="Au moins un intérêt est requis")
    
    added_count = 0
    for interest_name in interest_list:
        # Chercher si l'intérêt existe déjà
        interest = db.query(Interest).filter(Interest.name == interest_name).first()
        if not interest:
            interest = Interest(id=uuid.uuid4(), name=interest_name)
            db.add(interest)
            db.flush()
            logger.debug(f"➕ Nouvel intérêt créé: {interest_name}")
        
        # Lier l'étudiant à l'intérêt
        student_interest = StudentInterest(
            student_id=student.id,
            interest_id=interest.id
        )
        db.add(student_interest)
        added_count += 1
    
    db.commit()
    
    return {
        "message": f"{added_count} intérêt(s) ajouté(s) avec succès",
        "student_id": str(student.id),
        "student_name": student.user.full_name if student.user else "Inconnu",
        "interests": interest_list
    }


@router.get(
    "/{student_id}/interests",
    response_model=InterestsResponse,
    summary="Voir les intérêts d'un étudiant",
    description="Récupère la liste des centres d'intérêt d'un étudiant"
)
def get_student_interests(
    student_id: str,
    db: Session = Depends(get_db)
):
    """
    Récupère les centres d'intérêt d'un étudiant.
    
    - **student_id**: UUID de l'étudiant
    """
    logger.info(f"📋 GET /profile/{student_id}/interests")
    
    clean_id = student_id.strip()
    
    try:
        student_uuid = UUID(clean_id)
        student = db.query(Student).filter(Student.id == student_uuid).first()
    except ValueError:
        raise HTTPException(status_code=400, detail="ID étudiant invalide")
    
    if not student:
        raise HTTPException(status_code=404, detail="Étudiant non trouvé")
    
    # Récupérer les intérêts
    interests = db.query(Interest).join(
        StudentInterest
    ).filter(
        StudentInterest.student_id == student.id
    ).all()
    
    return {
        "student_id": str(student.id),
        "student_name": student.user.full_name if student.user else "Inconnu",
        "interests": [i.name for i in interests]
    }


@router.delete(
    "/{student_id}/interests",
    status_code=status.HTTP_200_OK,
    summary="Supprimer tous les intérêts",
    description="Supprime tous les centres d'intérêt d'un étudiant"
)
def delete_student_interests(
    student_id: str,
    db: Session = Depends(get_db)
):
    """
    Supprime tous les centres d'intérêt d'un étudiant.
    
    - **student_id**: UUID de l'étudiant
    """
    logger.info(f"🗑️ DELETE /profile/{student_id}/interests")
    
    clean_id = student_id.strip()
    
    try:
        student_uuid = UUID(clean_id)
        student = db.query(Student).filter(Student.id == student_uuid).first()
    except ValueError:
        raise HTTPException(status_code=400, detail="ID étudiant invalide")
    
    if not student:
        raise HTTPException(status_code=404, detail="Étudiant non trouvé")
    
    deleted = db.query(StudentInterest).filter(StudentInterest.student_id == student.id).delete()
    db.commit()
    
    return {
        "message": f"{deleted} intérêt(s) supprimé(s)",
        "student_id": str(student.id)
    }