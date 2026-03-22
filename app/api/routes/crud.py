# ============================================================
# app/api/routes/crud.py
# CRUD complet pour toutes les tables — visible dans Swagger
# Ajouter dans main.py : app.include_router(crud.router)
# ============================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

from app.database.connection import get_db
from app.database.models import (
    User, Student, Interest, StudentInterest,
    Program, FitScore, Conversation, Message,
    Document, DocumentChunk, Ambassadeur, DemandePeerMatch,
)

router = APIRouter(prefix="/api/db", tags=["🗄️ Base de données"])

# ============================================================
# SCHEMAS
# ============================================================

class UserCreate(BaseModel):
    full_name: str
    email: str
    password_hash: str
    role: str = "student"

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class StudentCreate(BaseModel):
    user_id: str
    average: Optional[float] = None
    level: Optional[str] = None
    bac_type: Optional[str] = None
    city: Optional[str] = None

class StudentUpdate(BaseModel):
    average: Optional[float] = None
    level: Optional[str] = None
    bac_type: Optional[str] = None
    city: Optional[str] = None

class InterestCreate(BaseModel):
    name: str

class StudentInterestCreate(BaseModel):
    student_id: str
    interest_id: str

class ProgramCreate(BaseModel):
    name: str
    description: Optional[str] = None
    required_average: Optional[float] = None
    duration: Optional[int] = None
    diploma: Optional[str] = None

class ProgramUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    required_average: Optional[float] = None
    duration: Optional[int] = None
    diploma: Optional[str] = None

class FitScoreCreate(BaseModel):
    student_id: str
    program_id: str
    score: float
    explanation: Optional[str] = None

class ConversationCreate(BaseModel):
    student_id: str

class MessageCreate(BaseModel):
    conversation_id: str
    content: str
    sender: str  # 'user' ou 'bot'

class DocumentCreate(BaseModel):
    title: str
    source: Optional[str] = None

class DocumentChunkCreate(BaseModel):
    document_id: str
    content: str
    embedding: Optional[str] = None

class AmbassadeurCreate(BaseModel):
    nom: str
    program_id: str
    niveau: str
    email: Optional[str] = None
    whatsapp: Optional[str] = None

class AmbassadeurUpdate(BaseModel):
    nom: Optional[str] = None
    niveau: Optional[str] = None
    email: Optional[str] = None
    whatsapp: Optional[str] = None
    is_active: Optional[bool] = None

class DemandePeerMatchCreate(BaseModel):
    ambassadeur_id: str
    prenom_etudiant: str
    email_etudiant: Optional[str] = None
    filiere: str
    message: Optional[str] = None

class DemandePeerMatchUpdate(BaseModel):
    statut: str  # 'en_attente' | 'traite' | 'annule'

# ============================================================
# USERS
# ============================================================

@router.post("/users", summary="Créer un utilisateur")
def create_user(body: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    user = User(**body.model_dump())
    db.add(user); db.commit(); db.refresh(user)
    return {"success": True, "id": str(user.id), "email": user.email}

@router.get("/users", summary="Lister tous les utilisateurs")
def list_users(db: Session = Depends(get_db)):
    return [
        {"id": str(u.id), "full_name": u.full_name, "email": u.email,
         "role": u.role, "is_active": u.is_active, "created_at": str(u.created_at)}
        for u in db.query(User).all()
    ]

@router.get("/users/{user_id}", summary="Voir un utilisateur")
def get_user(user_id: str, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u: raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return {"id": str(u.id), "full_name": u.full_name, "email": u.email,
            "role": u.role, "is_active": u.is_active, "created_at": str(u.created_at)}

@router.patch("/users/{user_id}", summary="Modifier un utilisateur")
def update_user(user_id: str, body: UserUpdate, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u: raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(u, k, v)
    db.commit(); db.refresh(u)
    return {"success": True, "id": str(u.id)}

@router.delete("/users/{user_id}", summary="Supprimer un utilisateur")
def delete_user(user_id: str, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u: raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    db.delete(u); db.commit()
    return {"success": True, "deleted_id": user_id}

# ============================================================
# STUDENTS
# ============================================================

@router.post("/students", summary="Créer un étudiant")
def create_student(body: StudentCreate, db: Session = Depends(get_db)):
    student = Student(**body.model_dump())
    db.add(student); db.commit(); db.refresh(student)
    return {"success": True, "id": str(student.id)}

@router.get("/students", summary="Lister tous les étudiants")
def list_students(db: Session = Depends(get_db)):
    return [
        {"id": str(s.id), "user_id": str(s.user_id), "bac_type": s.bac_type,
         "average": s.average, "level": s.level, "city": s.city,
         "created_at": str(s.created_at)}
        for s in db.query(Student).all()
    ]

@router.get("/students/{student_id}", summary="Voir un étudiant")
def get_student(student_id: str, db: Session = Depends(get_db)):
    s = db.query(Student).filter(Student.id == student_id).first()
    if not s: raise HTTPException(status_code=404, detail="Étudiant introuvable")
    return {"id": str(s.id), "user_id": str(s.user_id), "bac_type": s.bac_type,
            "average": s.average, "level": s.level, "city": s.city}

@router.patch("/students/{student_id}", summary="Modifier un étudiant")
def update_student(student_id: str, body: StudentUpdate, db: Session = Depends(get_db)):
    s = db.query(Student).filter(Student.id == student_id).first()
    if not s: raise HTTPException(status_code=404, detail="Étudiant introuvable")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(s, k, v)
    db.commit(); db.refresh(s)
    return {"success": True, "id": str(s.id)}

@router.delete("/students/{student_id}", summary="Supprimer un étudiant")
def delete_student(student_id: str, db: Session = Depends(get_db)):
    s = db.query(Student).filter(Student.id == student_id).first()
    if not s: raise HTTPException(status_code=404, detail="Étudiant introuvable")
    db.delete(s); db.commit()
    return {"success": True, "deleted_id": student_id}

# ============================================================
# INTERESTS
# ============================================================

@router.post("/interests", summary="Créer un intérêt")
def create_interest(body: InterestCreate, db: Session = Depends(get_db)):
    interest = Interest(**body.model_dump())
    db.add(interest); db.commit(); db.refresh(interest)
    return {"success": True, "id": str(interest.id), "name": interest.name}

@router.get("/interests", summary="Lister tous les intérêts")
def list_interests(db: Session = Depends(get_db)):
    return [{"id": str(i.id), "name": i.name} for i in db.query(Interest).all()]

@router.delete("/interests/{interest_id}", summary="Supprimer un intérêt")
def delete_interest(interest_id: str, db: Session = Depends(get_db)):
    i = db.query(Interest).filter(Interest.id == interest_id).first()
    if not i: raise HTTPException(status_code=404, detail="Intérêt introuvable")
    db.delete(i); db.commit()
    return {"success": True, "deleted_id": interest_id}

# ── Student ↔ Interest ────────────────────────────────────────
@router.post("/student-interests", summary="Lier un intérêt à un étudiant")
def add_student_interest(body: StudentInterestCreate, db: Session = Depends(get_db)):
    si = StudentInterest(student_id=body.student_id, interest_id=body.interest_id)
    db.add(si); db.commit()
    return {"success": True}

@router.delete("/student-interests", summary="Délier un intérêt d'un étudiant")
def remove_student_interest(student_id: str, interest_id: str, db: Session = Depends(get_db)):
    si = db.query(StudentInterest).filter(
        StudentInterest.student_id == student_id,
        StudentInterest.interest_id == interest_id
    ).first()
    if not si: raise HTTPException(status_code=404, detail="Liaison introuvable")
    db.delete(si); db.commit()
    return {"success": True}

# ============================================================
# PROGRAMS
# ============================================================

@router.post("/programs", summary="Créer un programme / filière")
def create_program(body: ProgramCreate, db: Session = Depends(get_db)):
    prog = Program(**body.model_dump())
    db.add(prog); db.commit(); db.refresh(prog)
    return {"success": True, "id": str(prog.id), "name": prog.name}

@router.get("/programs", summary="Lister tous les programmes")
def list_programs(db: Session = Depends(get_db)):
    return [
        {"id": str(p.id), "name": p.name, "required_average": p.required_average,
         "duration": p.duration, "diploma": p.diploma}
        for p in db.query(Program).all()
    ]

@router.get("/programs/{program_id}", summary="Voir un programme")
def get_program(program_id: str, db: Session = Depends(get_db)):
    p = db.query(Program).filter(Program.id == program_id).first()
    if not p: raise HTTPException(status_code=404, detail="Programme introuvable")
    return {"id": str(p.id), "name": p.name, "description": p.description,
            "required_average": p.required_average, "duration": p.duration, "diploma": p.diploma}

@router.patch("/programs/{program_id}", summary="Modifier un programme")
def update_program(program_id: str, body: ProgramUpdate, db: Session = Depends(get_db)):
    p = db.query(Program).filter(Program.id == program_id).first()
    if not p: raise HTTPException(status_code=404, detail="Programme introuvable")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(p, k, v)
    db.commit(); db.refresh(p)
    return {"success": True, "id": str(p.id)}

@router.delete("/programs/{program_id}", summary="Supprimer un programme")
def delete_program(program_id: str, db: Session = Depends(get_db)):
    p = db.query(Program).filter(Program.id == program_id).first()
    if not p: raise HTTPException(status_code=404, detail="Programme introuvable")
    db.delete(p); db.commit()
    return {"success": True, "deleted_id": program_id}

# ============================================================
# FIT SCORES
# ============================================================

@router.post("/fit-scores", summary="Créer un FitScore")
def create_fitscore(body: FitScoreCreate, db: Session = Depends(get_db)):
    fs = FitScore(**body.model_dump())
    db.add(fs); db.commit(); db.refresh(fs)
    return {"success": True, "id": str(fs.id), "score": fs.score}

@router.get("/fit-scores", summary="Lister tous les FitScores")
def list_fitscores(db: Session = Depends(get_db)):
    return [
        {"id": str(f.id), "student_id": str(f.student_id), "program_id": str(f.program_id),
         "score": f.score, "explanation": f.explanation, "created_at": str(f.created_at)}
        for f in db.query(FitScore).all()
    ]

@router.get("/fit-scores/student/{student_id}", summary="FitScores d'un étudiant")
def get_fitscores_by_student(student_id: str, db: Session = Depends(get_db)):
    scores = db.query(FitScore).filter(FitScore.student_id == student_id).all()
    return [{"id": str(f.id), "program_id": str(f.program_id),
             "score": f.score, "explanation": f.explanation} for f in scores]

@router.delete("/fit-scores/{fitscore_id}", summary="Supprimer un FitScore")
def delete_fitscore(fitscore_id: str, db: Session = Depends(get_db)):
    f = db.query(FitScore).filter(FitScore.id == fitscore_id).first()
    if not f: raise HTTPException(status_code=404, detail="FitScore introuvable")
    db.delete(f); db.commit()
    return {"success": True, "deleted_id": fitscore_id}

# ============================================================
# CONVERSATIONS
# ============================================================

@router.post("/conversations", summary="Créer une conversation")
def create_conversation(body: ConversationCreate, db: Session = Depends(get_db)):
    conv = Conversation(**body.model_dump())
    db.add(conv); db.commit(); db.refresh(conv)
    return {"success": True, "id": str(conv.id)}

@router.get("/conversations", summary="Lister toutes les conversations")
def list_conversations(db: Session = Depends(get_db)):
    return [
        {"id": str(c.id), "student_id": str(c.student_id), "started_at": str(c.started_at)}
        for c in db.query(Conversation).all()
    ]

@router.get("/conversations/{conv_id}/messages", summary="Messages d'une conversation")
def get_conversation_messages(conv_id: str, db: Session = Depends(get_db)):
    msgs = db.query(Message).filter(Message.conversation_id == conv_id).order_by(Message.created_at).all()
    return [{"id": str(m.id), "content": m.content, "sender": m.sender,
             "created_at": str(m.created_at)} for m in msgs]

@router.delete("/conversations/{conv_id}", summary="Supprimer une conversation")
def delete_conversation(conv_id: str, db: Session = Depends(get_db)):
    c = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not c: raise HTTPException(status_code=404, detail="Conversation introuvable")
    db.delete(c); db.commit()
    return {"success": True, "deleted_id": conv_id}

# ============================================================
# MESSAGES
# ============================================================

@router.post("/messages", summary="Ajouter un message")
def create_message(body: MessageCreate, db: Session = Depends(get_db)):
    msg = Message(**body.model_dump())
    db.add(msg); db.commit(); db.refresh(msg)
    return {"success": True, "id": str(msg.id)}

@router.get("/messages", summary="Lister tous les messages")
def list_messages(db: Session = Depends(get_db)):
    return [
        {"id": str(m.id), "conversation_id": str(m.conversation_id),
         "content": m.content, "sender": m.sender, "created_at": str(m.created_at)}
        for m in db.query(Message).all()
    ]

@router.delete("/messages/{message_id}", summary="Supprimer un message")
def delete_message(message_id: str, db: Session = Depends(get_db)):
    m = db.query(Message).filter(Message.id == message_id).first()
    if not m: raise HTTPException(status_code=404, detail="Message introuvable")
    db.delete(m); db.commit()
    return {"success": True, "deleted_id": message_id}

# ============================================================
# DOCUMENTS
# ============================================================

@router.post("/documents", summary="Créer un document")
def create_document(body: DocumentCreate, db: Session = Depends(get_db)):
    doc = Document(**body.model_dump())
    db.add(doc); db.commit(); db.refresh(doc)
    return {"success": True, "id": str(doc.id), "title": doc.title}

@router.get("/documents", summary="Lister tous les documents")
def list_documents(db: Session = Depends(get_db)):
    return [{"id": str(d.id), "title": d.title, "source": d.source,
             "uploaded_at": str(d.uploaded_at)} for d in db.query(Document).all()]

@router.delete("/documents/{document_id}", summary="Supprimer un document")
def delete_document(document_id: str, db: Session = Depends(get_db)):
    d = db.query(Document).filter(Document.id == document_id).first()
    if not d: raise HTTPException(status_code=404, detail="Document introuvable")
    db.delete(d); db.commit()
    return {"success": True, "deleted_id": document_id}

# ============================================================
# DOCUMENT CHUNKS
# ============================================================

@router.post("/document-chunks", summary="Ajouter un chunk de document")
def create_chunk(body: DocumentChunkCreate, db: Session = Depends(get_db)):
    chunk = DocumentChunk(**body.model_dump())
    db.add(chunk); db.commit(); db.refresh(chunk)
    return {"success": True, "id": str(chunk.id)}

@router.get("/document-chunks/{document_id}", summary="Chunks d'un document")
def get_chunks(document_id: str, db: Session = Depends(get_db)):
    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()
    return [{"id": str(c.id), "content": c.content[:200],
             "created_at": str(c.created_at)} for c in chunks]

@router.delete("/document-chunks/{chunk_id}", summary="Supprimer un chunk")
def delete_chunk(chunk_id: str, db: Session = Depends(get_db)):
    c = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not c: raise HTTPException(status_code=404, detail="Chunk introuvable")
    db.delete(c); db.commit()
    return {"success": True, "deleted_id": chunk_id}

# ============================================================
# AMBASSADEURS
# ============================================================

@router.post("/ambassadeurs", summary="Créer un ambassadeur")
def create_ambassadeur(body: AmbassadeurCreate, db: Session = Depends(get_db)):
    amb = Ambassadeur(**body.model_dump())
    db.add(amb); db.commit(); db.refresh(amb)
    return {"success": True, "id": str(amb.id), "nom": amb.nom}

@router.get("/ambassadeurs", summary="Lister tous les ambassadeurs")
def list_ambassadeurs(actif_seulement: bool = False, db: Session = Depends(get_db)):
    q = db.query(Ambassadeur)
    if actif_seulement:
        q = q.filter(Ambassadeur.is_active == True)
    return [
        {"id": str(a.id), "nom": a.nom, "program_id": a.program_id,
         "niveau": a.niveau, "email": a.email, "whatsapp": a.whatsapp,
         "is_active": a.is_active}
        for a in q.all()
    ]

@router.get("/ambassadeurs/{amb_id}", summary="Voir un ambassadeur")
def get_ambassadeur(amb_id: str, db: Session = Depends(get_db)):
    a = db.query(Ambassadeur).filter(Ambassadeur.id == amb_id).first()
    if not a: raise HTTPException(status_code=404, detail="Ambassadeur introuvable")
    return {"id": str(a.id), "nom": a.nom, "program_id": a.program_id,
            "niveau": a.niveau, "email": a.email, "whatsapp": a.whatsapp, "is_active": a.is_active}

@router.patch("/ambassadeurs/{amb_id}", summary="Modifier un ambassadeur")
def update_ambassadeur(amb_id: str, body: AmbassadeurUpdate, db: Session = Depends(get_db)):
    a = db.query(Ambassadeur).filter(Ambassadeur.id == amb_id).first()
    if not a: raise HTTPException(status_code=404, detail="Ambassadeur introuvable")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(a, k, v)
    db.commit(); db.refresh(a)
    return {"success": True, "id": str(a.id)}

@router.delete("/ambassadeurs/{amb_id}", summary="Supprimer un ambassadeur")
def delete_ambassadeur(amb_id: str, db: Session = Depends(get_db)):
    a = db.query(Ambassadeur).filter(Ambassadeur.id == amb_id).first()
    if not a: raise HTTPException(status_code=404, detail="Ambassadeur introuvable")
    db.delete(a); db.commit()
    return {"success": True, "deleted_id": amb_id}

# ============================================================
# DEMANDES PEERMATCH
# ============================================================

@router.post("/peermatch-demandes", summary="Créer une demande PeerMatch")
def create_demande(body: DemandePeerMatchCreate, db: Session = Depends(get_db)):
    demande = DemandePeerMatch(**body.model_dump())
    db.add(demande); db.commit(); db.refresh(demande)
    return {"success": True, "id": str(demande.id)}

@router.get("/peermatch-demandes", summary="Lister toutes les demandes PeerMatch")
def list_demandes(statut: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(DemandePeerMatch)
    if statut:
        q = q.filter(DemandePeerMatch.statut == statut)
    return [
        {"id": str(d.id), "prenom_etudiant": d.prenom_etudiant,
         "email_etudiant": d.email_etudiant, "filiere": d.filiere,
         "message": d.message, "statut": d.statut,
         "ambassadeur_id": str(d.ambassadeur_id), "created_at": str(d.created_at)}
        for d in q.order_by(DemandePeerMatch.created_at.desc()).all()
    ]

@router.patch("/peermatch-demandes/{demande_id}", summary="Changer le statut d'une demande")
def update_demande(demande_id: str, body: DemandePeerMatchUpdate, db: Session = Depends(get_db)):
    d = db.query(DemandePeerMatch).filter(DemandePeerMatch.id == demande_id).first()
    if not d: raise HTTPException(status_code=404, detail="Demande introuvable")
    d.statut = body.statut
    db.commit(); db.refresh(d)
    return {"success": True, "id": str(d.id), "statut": d.statut}

@router.delete("/peermatch-demandes/{demande_id}", summary="Supprimer une demande PeerMatch")
def delete_demande(demande_id: str, db: Session = Depends(get_db)):
    d = db.query(DemandePeerMatch).filter(DemandePeerMatch.id == demande_id).first()
    if not d: raise HTTPException(status_code=404, detail="Demande introuvable")
    db.delete(d); db.commit()
    return {"success": True, "deleted_id": demande_id}

# ── Stats rapides ─────────────────────────────────────────────
@router.get("/stats", summary="Statistiques globales de la base")
def get_stats(db: Session = Depends(get_db)):
    return {
        "users":              db.query(User).count(),
        "students":           db.query(Student).count(),
        "programs":           db.query(Program).count(),
        "interests":          db.query(Interest).count(),
        "fit_scores":         db.query(FitScore).count(),
        "conversations":      db.query(Conversation).count(),
        "messages":           db.query(Message).count(),
        "documents":          db.query(Document).count(),
        "document_chunks":    db.query(DocumentChunk).count(),
        "ambassadeurs":       db.query(Ambassadeur).count(),
        "ambassadeurs_actifs": db.query(Ambassadeur).filter(Ambassadeur.is_active == True).count(),
        "peermatch_demandes": db.query(DemandePeerMatch).count(),
        "peermatch_en_attente": db.query(DemandePeerMatch).filter(DemandePeerMatch.statut == "en_attente").count(),
    }