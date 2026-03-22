# app/api/routes/auth_routes.py
# ============================================================
# Endpoints d'authentification SUPMTI
# Utilise pbkdf2_sha256 — pas de bcrypt, pas de limite 72 bytes
# ============================================================

import uuid
from fastapi         import APIRouter, HTTPException, Request, Depends
from pydantic        import BaseModel, EmailStr
from passlib.context import CryptContext
from sqlalchemy.orm  import Session
from sqlalchemy      import text

from app.database.connection import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])

# ─── pbkdf2_sha256 : intégré Python, zéro dépendance externe ─
pwd_ctx = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# ── Schémas ───────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    full_name: str
    email:     EmailStr
    password:  str
    role:      str = "student"

class LoginRequest(BaseModel):
    email:    EmailStr
    password: str

# ── POST /api/auth/register ───────────────────────────────────

@router.post("/register")
def register(data: RegisterRequest, request: Request, db: Session = Depends(get_db)):

    existing = db.execute(
        text("SELECT id FROM users WHERE email = :email"),
        {"email": data.email}
    ).fetchone()

    if existing:
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé.")

    hashed  = pwd_ctx.hash(data.password)
    user_id = str(uuid.uuid4())

    db.execute(
        text("""
            INSERT INTO users (id, full_name, email, password_hash, role, is_active, created_at)
            VALUES (:id, :full_name, :email, :password_hash, :role, TRUE, NOW())
        """),
        {
            "id":            user_id,
            "full_name":     data.full_name,
            "email":         data.email,
            "password_hash": hashed,
            "role":          data.role,
        }
    )

    if data.role == "student":
        db.execute(
            text("INSERT INTO students (id, user_id, created_at) VALUES (:id, :user_id, NOW())"),
            {"id": str(uuid.uuid4()), "user_id": user_id}
        )

    db.commit()

    # Session automatique après inscription
    request.session["user_id"]   = str(user_id)
    request.session["user_role"] = data.role

    return {
        "success": True,
        "message": "Compte créé avec succès.",
        "user": {
            "id":        user_id,
            "full_name": data.full_name,
            "email":     data.email,
            "role":      data.role,
            "is_active": True,
        },
        "token": "session"
    }

# ── POST /api/auth/login ──────────────────────────────────────

@router.post("/login")
def login(data: LoginRequest, request: Request, db: Session = Depends(get_db)):

    row = db.execute(
        text("""
            SELECT id, full_name, email, password_hash, role, is_active
            FROM users WHERE email = :email
        """),
        {"email": data.email}
    ).fetchone()

    if not row:
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect.")

    if not pwd_ctx.verify(data.password, row.password_hash):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect.")

    if not row.is_active:
        raise HTTPException(status_code=403, detail="Compte désactivé. Contacte l'administration.")

    request.session["user_id"]   = str(row.id)
    request.session["user_role"] = row.role

    return {
        "success": True,
        "user": {
            "id":        row.id,
            "full_name": row.full_name,
            "email":     row.email,
            "role":      row.role,
            "is_active": row.is_active,
        },
        "token": "session"
    }

# ── POST /api/auth/logout ─────────────────────────────────────

@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"success": True}

# ── GET /api/auth/me ──────────────────────────────────────────

@router.get("/me")
def me(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Non authentifié.")

    row = db.execute(
        text("SELECT id, full_name, email, role FROM users WHERE id = :id"),
        {"id": user_id}
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")

    return {
        "user": {
            "id":        row.id,
            "full_name": row.full_name,
            "email":     row.email,
            "role":      row.role,
        }
    }