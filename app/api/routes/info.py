"""
Routes pour les informations publiques sur l'école et les programmes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database.connection import get_db
from app.database.models import Program
from app.core.logging import logger

router = APIRouter(prefix="/info", tags=["information"])

@router.get("/programs", response_model=List[dict])
def list_programs(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Liste tous les programmes disponibles à SUP MTI.
    
    - **skip**: Nombre d'éléments à sauter (pagination)
    - **limit**: Nombre maximum d'éléments à retourner
    """
    logger.info(f"GET /info/programs - skip={skip}, limit={limit}")
    
    programs = db.query(Program).order_by(Program.name).offset(skip).limit(limit).all()
    
    return [
        {
            "id": str(p.id),
            "name": p.name,
            "description": p.description[:200] + "..." if p.description and len(p.description) > 200 else p.description,
            "duration": p.duration,
            "diploma": p.diploma,
            "required_average": p.required_average
        }
        for p in programs
    ]

@router.get("/programs/{program_id}", response_model=dict)
def get_program(
    program_id: str,
    db: Session = Depends(get_db)
):
    """
    Détails complets d'un programme spécifique.
    
    - **program_id**: UUID du programme
    """
    logger.info(f"GET /info/programs/{program_id}")
    
    try:
        program = db.query(Program).filter(Program.id == UUID(program_id)).first()
        
        if not program:
            logger.warning(f"Programme non trouvé: {program_id}")
            raise HTTPException(status_code=404, detail="Programme non trouvé")
        
        return {
            "id": str(program.id),
            "name": program.name,
            "description": program.description,
            "required_average": program.required_average,
            "duration": program.duration,
            "diploma": program.diploma,
            "created_at": program.created_at.isoformat() if program.created_at else None
        }
        
    except ValueError:
        logger.warning(f"ID programme invalide: {program_id}")
        raise HTTPException(status_code=400, detail="ID de programme invalide")

@router.get("/stats", response_model=dict)
def get_stats(db: Session = Depends(get_db)):
    """
    Statistiques générales sur SUP MTI.
    """
    logger.info("GET /info/stats")
    
    total_programs = db.query(Program).count()
    
    return {
        "total_programs": total_programs,
        "school_name": "SUP MTI Meknès",
        "contact": "+212 5 35 51 10 11",
        "email": "contact@supmtimeknes.ac.ma",
        "address": "Meknès, Maroc"
    }