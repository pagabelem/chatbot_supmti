"""
Service de gestion des profils étudiants.
"""
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
import uuid
import random
from datetime import datetime

from app.database.models import User, Student, Interest, StudentInterest
from app.core.exceptions import ValidationError, NotFoundError
from app.core.logging import logger

def save_user_profile(db: Session, name: str, interests: str) -> Dict[str, Any]:
    """
    Sauvegarde un profil utilisateur avec ses centres d'intérêt.
    
    Args:
        db: Session SQLAlchemy
        name: Nom complet de l'utilisateur
        interests: Liste d'intérêts séparés par des virgules
    
    Returns:
        Dictionnaire avec les informations du profil créé
    
    Raises:
        ValidationError: Si les données sont invalides
    """
    logger.info(f"📝 Création de profil pour: {name}")
    
    # === Validation ===
    if not name or not name.strip():
        logger.warning("❌ Nom vide")
        raise ValidationError("Le nom ne peut pas être vide")
    
    if not interests or not interests.strip():
        logger.warning("❌ Intérêts vides")
        raise ValidationError("Au moins un intérêt est requis")
    
    # Nettoyer les intérêts
    interest_list = [i.strip() for i in interests.split(',') if i.strip()]
    if not interest_list:
        logger.warning("❌ Aucun intérêt valide")
        raise ValidationError("Au moins un intérêt valide requis")
    
    try:
        # === 1. Créer l'utilisateur ===
        random_suffix = random.randint(1000, 9999)
        email = f"{name.lower().replace(' ', '.')}.{random_suffix}@example.com"
        
        user = User(
            id=uuid.uuid4(),
            full_name=name.strip(),
            email=email,
            password_hash="temp_hash",  # À remplacer par vrai hash
            is_active=True,
            role="student"
        )
        db.add(user)
        db.flush()
        logger.debug(f"✅ Utilisateur créé: {user.id}")
        
        # === 2. Créer l'étudiant ===
        student = Student(
            id=uuid.uuid4(),
            user_id=user.id,
            average=14.5,  # Valeur par défaut
            level="BAC",
            bac_type="Scientifique",
            city="Non spécifié"
        )
        db.add(student)
        db.flush()
        logger.debug(f"✅ Étudiant créé: {student.id}")
        
        # === 3. Traiter les intérêts ===
        for interest_name in interest_list:
            # Chercher ou créer l'intérêt
            interest = db.query(Interest).filter(Interest.name == interest_name).first()
            if not interest:
                interest = Interest(id=uuid.uuid4(), name=interest_name)
                db.add(interest)
                db.flush()
                logger.debug(f"✅ Intérêt créé: {interest_name}")
            
            # Lier l'étudiant à l'intérêt
            student_interest = StudentInterest(
                student_id=student.id,
                interest_id=interest.id
            )
            db.add(student_interest)
        
        db.commit()
        logger.info(f"✅ Profil créé avec succès: {student.id}")
        
        return {
            "name": name.strip(),
            "interests": ', '.join(interest_list),
            "student_id": str(student.id),
            "created_at": datetime.utcnow().isoformat()
        }
        
    except ValidationError:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur création profil: {str(e)}")
        raise

def get_user_profile(db: Session, student_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Récupère un profil étudiant.
    
    Args:
        db: Session SQLAlchemy
        student_id: ID de l'étudiant (optionnel)
    
    Returns:
        Dictionnaire avec les informations du profil ou None
    """
    try:
        # Récupérer l'étudiant
        if student_id:
            from uuid import UUID
            logger.info(f"🔍 Recherche étudiant: {student_id}")
            student = db.query(Student).filter(Student.id == UUID(student_id)).first()
            if not student:
                raise NotFoundError("Étudiant", student_id)
        else:
            logger.info("🔍 Recherche du dernier étudiant")
            student = db.query(Student).order_by(Student.created_at.desc()).first()
            if not student:
                logger.info("ℹ️ Aucun étudiant trouvé")
                return None
        
        # Récupérer les intérêts
        interests = db.query(Interest).join(
            StudentInterest
        ).filter(
            StudentInterest.student_id == student.id
        ).all()
        
        interests_str = ", ".join([i.name for i in interests]) if interests else ""
        
        logger.debug(f"✅ Profil trouvé: {student.id}")
        
        return {
            "name": student.user.full_name if student.user else "Inconnu",
            "interests": interests_str,
            "student_id": str(student.id),
            "created_at": student.created_at.isoformat() if student.created_at else None
        }
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur récupération profil: {str(e)}")
        raise

def list_all_profiles(db: Session, skip: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Liste tous les profils étudiants (pour admin).
    
    Args:
        db: Session SQLAlchemy
        skip: Nombre d'éléments à sauter
        limit: Nombre maximum d'éléments
    
    Returns:
        Liste des profils
    """
    logger.info(f"📋 Liste des profils: skip={skip}, limit={limit}")
    
    students = db.query(Student).order_by(
        Student.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return [
        {
            "student_id": str(s.id),
            "name": s.user.full_name if s.user else "Inconnu",
            "created_at": s.created_at.isoformat() if s.created_at else None
        }
        for s in students
    ]