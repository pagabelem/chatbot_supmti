from sqlalchemy.orm import Session
from app.database.models import Student, Program, FitScore
import uuid
from datetime import datetime

def generate_orientation(db: Session, student_id: str):
    print(f"Recherche de l'étudiant avec ID: {student_id}")
    
    # Convertir le string en UUID si nécessaire
    from uuid import UUID
    student_uuid = UUID(student_id) if isinstance(student_id, str) else student_id
    
    student = db.query(Student).filter(Student.id == student_uuid).first()
    
    if not student:
        print(f"Étudiant non trouvé avec ID: {student_uuid}")
        return {"error": "Étudiant non trouvé"}
    
    print(f"Étudiant trouvé: {student.id}")
    
    programs = db.query(Program).all()
    print(f"Nombre de programmes trouvés: {len(programs)}")
    
    results = []
    
    for program in programs:
        # Exemple simple de score (à remplacer par votre vrai FitScore)
        score = 85.5
        
        fit = FitScore(
            id=uuid.uuid4(),
            student_id=student.id,
            program_id=program.id,
            score=score,
            explanation=f"Bon match avec le profil",
            created_at=datetime.utcnow()
        )
        
        db.add(fit)
        results.append({
            "program_id": str(program.id),
            "program_name": program.name,
            "score": score
        })
    
    db.commit()
    
    return {
        "student_id": str(student.id),
        "student_name": student.user.full_name if student.user else "Inconnu",
        "recommendations": results
    }