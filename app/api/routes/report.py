"""
Route pour générer des rapports PDF d'orientation.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import datetime

from app.database.connection import get_db
from app.database.models import Student, Program, Interest, StudentInterest
from app.services.pdf_service import PDFService, calculate_scores
from app.core.logging import logger

router = APIRouter(prefix="/report", tags=["rapport"])

@router.get("/orientation/{student_id}")
def generate_orientation_report(
    student_id: str,
    limit: Optional[int] = 5,
    db: Session = Depends(get_db)
):
    """
    Génère un rapport PDF d'orientation pour un étudiant.
    
    - **student_id**: UUID de l'étudiant
    - **limit**: Nombre de recommandations à inclure (défaut: 5)
    
    Retourne un fichier PDF téléchargeable.
    """
    logger.info(f"📄 GET /report/orientation/{student_id}")
    
    # === NETTOYAGE DE L'ID ===
    clean_id = student_id.strip()
    logger.info(f"ID nettoyé: {clean_id}")
    
    # Récupérer l'étudiant
    try:
        student_uuid = UUID(clean_id)
        student = db.query(Student).filter(Student.id == student_uuid).first()
    except ValueError:
        raise HTTPException(status_code=400, detail="ID étudiant invalide")
    
    if not student:
        raise HTTPException(status_code=404, detail="Étudiant non trouvé")
    
    # Récupérer les intérêts de l'étudiant de manière fiable
    interests = []
    try:
        interest_records = db.query(Interest).join(
            StudentInterest
        ).filter(
            StudentInterest.student_id == student.id
        ).all()
        interests = [i.name for i in interest_records]
        logger.info(f"✅ Intérêts trouvés via requête directe: {interests}")
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération des intérêts: {e}")
    
    # Récupérer tous les programmes
    programs = db.query(Program).all()
    logger.info(f"📚 {len(programs)} programmes trouvés")
    
    # Calculer les scores
    recommendations = calculate_scores(interests, programs)
    logger.info(f"📊 {len(recommendations)} recommandations calculées")
    
    # Limiter le nombre de recommandations
    recommendations = recommendations[:limit]
    
    # Générer le PDF avec la session DB
    pdf_service = PDFService(db=db)
    pdf_buffer = pdf_service.generate_orientation_report(student, recommendations)
    
    # Retourner le PDF
    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=orientation_report_{clean_id[:8]}.pdf"
        }
    )


@router.get("/orientation/{student_id}/preview")
def preview_orientation_report(
    student_id: str,
    limit: Optional[int] = 5,
    db: Session = Depends(get_db)
):
    """
    Aperçu JSON du rapport avant génération PDF.
    Utile pour le frontend.
    """
    logger.info(f"📄 GET /report/orientation/{student_id}/preview")
    
    # === NETTOYAGE DE L'ID ===
    clean_id = student_id.strip()
    logger.info(f"ID nettoyé: {clean_id}")
    
    # Récupérer l'étudiant
    try:
        student_uuid = UUID(clean_id)
        student = db.query(Student).filter(Student.id == student_uuid).first()
    except ValueError:
        raise HTTPException(status_code=400, detail="ID étudiant invalide")
    
    if not student:
        raise HTTPException(status_code=404, detail="Étudiant non trouvé")
    
    # Récupérer les intérêts DIRECTEMENT avec une requête (méthode fiable)
    interests = []
    try:
        interest_records = db.query(Interest).join(
            StudentInterest
        ).filter(
            StudentInterest.student_id == student.id
        ).all()
        interests = [i.name for i in interest_records]
        logger.info(f"✅ Intérêts trouvés: {interests}")
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération des intérêts: {e}")
    
    # Récupérer tous les programmes
    programs = db.query(Program).all()
    
    # Calculer les scores
    recommendations = calculate_scores(interests, programs)
    recommendations = recommendations[:limit]
    
    # Nom de l'étudiant
    student_name = student.user.full_name if student.user else "Non renseigné"
    
    return {
        "student": {
            "id": str(student.id),
            "name": student_name,
            "level": student.level or "Non renseigné",
            "bac_type": student.bac_type or "Non renseigné",
            "city": student.city or "Non renseigné",
            "interests": interests  # ← Maintenant avec les vrais intérêts !
        },
        "recommendations": recommendations,
        "generated_at": datetime.now().isoformat()
    }


@router.get("/orientation/{student_id}/debug")
def debug_student_interests(
    student_id: str,
    db: Session = Depends(get_db)
):
    """
    Route de débogage pour voir tous les détails d'un étudiant.
    """
    logger.info(f"🔍 GET /report/orientation/{student_id}/debug")
    
    clean_id = student_id.strip()
    
    try:
        student_uuid = UUID(clean_id)
        student = db.query(Student).filter(Student.id == student_uuid).first()
    except ValueError:
        raise HTTPException(status_code=400, detail="ID étudiant invalide")
    
    if not student:
        raise HTTPException(status_code=404, detail="Étudiant non trouvé")
    
    # Récupérer les intérêts
    interest_records = db.query(Interest).join(
        StudentInterest
    ).filter(
        StudentInterest.student_id == student.id
    ).all()
    
    # Récupérer toutes les relations student_interests
    student_interests = db.query(StudentInterest).filter(
        StudentInterest.student_id == student.id
    ).all()
    
    return {
        "student": {
            "id": str(student.id),
            "user_id": str(student.user_id) if student.user_id else None,
            "name": student.user.full_name if student.user else None,
            "level": student.level,
            "bac_type": student.bac_type,
            "city": student.city,
            "created_at": student.created_at.isoformat() if student.created_at else None
        },
        "interests": [i.name for i in interest_records],
        "raw_relations": [
            {
                "student_id": str(si.student_id),
                "interest_id": str(si.interest_id)
            }
            for si in student_interests
        ],
        "counts": {
            "interests_found": len(interest_records),
            "relations_found": len(student_interests)
        }
    }