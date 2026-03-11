from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.services.orientation_service import generate_orientation
from uuid import UUID

router = APIRouter(prefix="/orientation", tags=["orientation"])

@router.post("/generate/{student_id}")
def generate(student_id: UUID, db: Session = Depends(get_db)):
    results = generate_orientation(db, student_id)
    return {"orientation_results": results}