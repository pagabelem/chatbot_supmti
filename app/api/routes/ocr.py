"""
Routes pour l'OCR (reconnaissance de texte dans les images).
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
import shutil
import os

from app.services.ocr_service import OCRService
from app.services.profile_service import save_user_profile
from app.database.connection import get_db
from app.core.logging import logger

router = APIRouter(prefix="/ocr", tags=["ocr"])
ocr_service = OCRService()

@router.post("/extract")
async def extract_text(
    file: UploadFile = File(..., description="Image ou PDF à analyser")
):
    """
    Extrait tout le texte d'une image ou d'un PDF.
    """
    logger.info(f"📸 OCR Extract - Fichier: {file.filename}")
    
    # ✅ NOUVELLE VALIDATION: Accepter images ET PDFs
    allowed_types = ['image/', 'application/pdf']
    if not any(file.content_type.startswith(t) for t in allowed_types):
        raise HTTPException(400, "Le fichier doit être une image (jpg, png) ou un PDF")
    
    try:
        result = await ocr_service.extract_text(file)
        return result
    except Exception as e:
        logger.error(f"❌ Erreur OCR: {str(e)}")
        raise HTTPException(500, f"Erreur lors de l'analyse: {str(e)}")

@router.post("/bulletin")
async def extract_grades(
    file: UploadFile = File(..., description="Photo du bulletin de notes (image ou PDF)")
):
    """
    Extrait spécifiquement les notes d'un bulletin scolaire.
    Accepte les images et les PDFs.
    """
    logger.info(f"📝 OCR Bulletin - Fichier: {file.filename}")
    
    # ✅ MÊME VALIDATION
    allowed_types = ['image/', 'application/pdf']
    if not any(file.content_type.startswith(t) for t in allowed_types):
        raise HTTPException(400, "Le fichier doit être une image ou un PDF")
    
    try:
        result = await ocr_service.extract_grades_from_bulletin(file)
        return result
    except Exception as e:
        logger.error(f"❌ Erreur OCR bulletin: {str(e)}")
        raise HTTPException(500, f"Erreur lors de l'analyse: {str(e)}")

@router.post("/student-info")
async def extract_student_info(
    file: UploadFile = File(..., description="Photo d'un document étudiant (image ou PDF)")
):
    """
    Extrait les informations d'un étudiant (nom, bac, etc.)
    """
    logger.info(f"👤 OCR Student Info - Fichier: {file.filename}")
    
    allowed_types = ['image/', 'application/pdf']
    if not any(file.content_type.startswith(t) for t in allowed_types):
        raise HTTPException(400, "Le fichier doit être une image ou un PDF")
    
    try:
        result = await ocr_service.extract_student_info(file)
        return result
    except Exception as e:
        logger.error(f"❌ Erreur OCR student info: {str(e)}")
        raise HTTPException(500, f"Erreur lors de l'analyse: {str(e)}")

@router.post("/create-profile")
async def create_profile_from_bulletin(
    file: UploadFile = File(..., description="Photo du bulletin (image ou PDF)"),
    name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Crée automatiquement un profil étudiant à partir d'un bulletin scanné.
    """
    logger.info(f"✨ Création profil depuis bulletin - Fichier: {file.filename}")
    
    allowed_types = ['image/', 'application/pdf']
    if not any(file.content_type.startswith(t) for t in allowed_types):
        raise HTTPException(400, "Le fichier doit être une image ou un PDF")
    
    try:
        # 1. Extraire les informations du bulletin
        result = await ocr_service.extract_grades_from_bulletin(file)
        
        if not result['success']:
            raise HTTPException(500, f"Erreur OCR: {result.get('error', 'Inconnue')}")
        
        # 2. Calculer la moyenne à partir des notes
        grades = result.get('grades', [])
        if grades:
            average = sum(g['grade'] for g in grades) / len(grades)
        else:
            average = 0
        
        # 3. Utiliser le nom fourni ou un nom par défaut
        student_name = name if name else f"Étudiant_{file.filename[:10]}"
        
        # 4. Créer le profil avec des intérêts par défaut
        from app.services.profile_service import save_user_profile
        profile = save_user_profile(
            db, 
            student_name, 
            "Études, Sciences"  # Intérêts par défaut
        )
        
        return {
            "message": "Profil créé avec succès depuis le bulletin",
            "profile": profile,
            "extracted_grades": grades,
            "average": average
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur création profil: {str(e)}")
        raise HTTPException(500, f"Erreur: {str(e)}")