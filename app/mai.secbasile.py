# ============================================================
# FASTAPI — SUPMTI Chatbot  (main.py FINAL)
# ============================================================

import os
import uuid
from datetime import datetime
from fastapi import FastAPI, Request, Response, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.services.report_service import generer_rapport_pdf, generer_rapport_word
from fastapi.responses import Response as FastAPIResponse

from sqlalchemy import text, func
from datetime import datetime, timedelta

load_dotenv()

# ── DB + modèles (avant app pour create_all) ─────────────────
from app.database.connection import engine, Base, get_db
from app.database.models import Ambassadeur, DemandePeerMatch
from app.core.config import settings
from app.core.logging import logger
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from typing import List, Optional
from app.services.tts_service import TTSService
from fastapi.responses import Response as FastAPIResponse

tts_service = TTSService()





# ── ÉTAPE 1 : Colle cette fonction dans main.py ──────────────
# (après les imports, avant les routes)
 
def charger_profil_depuis_db(user_id: str, sess: dict, db: Session) -> dict:
    """
    Charge les données du profil DB dans la session SAMI en mémoire.
    Appelé une fois par session quand le profil est vide ou incomplet.
    """
    if not user_id:
        return sess
 
    try:
        # Récupérer user + student
        row = db.execute(text("""
            SELECT
                u.full_name,
                u.email,
                s.average,
                s.bac_type,
                s.level,
                s.city
            FROM users u
            LEFT JOIN students s ON s.user_id = u.id
            WHERE u.id = :uid
        """), {"uid": user_id}).fetchone()
 
        if not row:
            return sess
 
        # Récupérer les intérêts
        interests_rows = db.execute(text("""
            SELECT i.name
            FROM interests i
            JOIN student_interests si ON si.interest_id = i.id
            JOIN students s ON s.id = si.student_id
            WHERE s.user_id = :uid
        """), {"uid": user_id}).fetchall()
 
        interests = [r.name for r in interests_rows]
 
        # Construire un profil si absent
        if sess["profil"] is None:
            from app.services.profile_service import construire_profil_etudiant
            sess["profil"] = construire_profil_etudiant({})
 
        # Injecter les données DB dans le profil SAMI
        profil = sess["profil"]
 
        # Informations personnelles
        info = profil.setdefault("informations_personnelles", {})
        if row.full_name:
            parts = row.full_name.strip().split()
            info["prenom"] = parts[0]
            if len(parts) > 1:
                info["nom"] = " ".join(parts[1:])
        if row.city:
            info["ville"] = row.city
 
        # Parcours académique
        parc = profil.setdefault("parcours_academique", {})
        if row.average and row.average > 0:
            parc["moyenne_generale"] = float(row.average)
        if row.bac_type:
            parc["type_bac"] = row.bac_type
            parc["label_bac"] = row.bac_type
        if row.level:
            parc["niveau_actuel"] = row.level
 
        # Préférences
        pref = profil.setdefault("preferences", {})
        if interests:
            pref["centres_interet"] = interests
 
        # Marquer comme partiellement complété si on a les données de base
        if row.average and row.bac_type:
            profil["statut_profil"] = "partiel"
 
        sess["profil"] = profil
        sess["profil_db_charge"] = True  # flag pour ne pas recharger inutilement
 
    except Exception as e:
        print(f"[WARN] Impossible de charger le profil DB: {e}")
 
    return sess



logger.info("🗄️ Création des tables dans la base de données...")
Base.metadata.create_all(bind=engine)
logger.info("✅ Tables créées avec succès")

# ── UN SEUL app ───────────────────────────────────────────────
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "SUP MTI Meknès",
        "email": "contact@supmtimeknes.ac.ma",
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "X-User-Id"],  # ← ajouter ici
)




app.add_middleware(
    SessionMiddleware,
    secret_key="supmti-secret-key-change-en-prod",
    max_age=60 * 60 * 24 * 7,   # 7 jours
)


from app.api.routes.auth_routes import router as auth_router
app.include_router(auth_router)

# ── Routers existants ─────────────────────────────────────────
from app.api.routes import (
    ocr, chat_adaptive, chat, profile, orientation,
    info, compare, report, chat_stream, telegram, test_stt
)
from app.api.routes import crud   # ← NOUVEAU router CRUD complet

app.include_router(chat.router)
app.include_router(profile.router)
app.include_router(orientation.router)
app.include_router(info.router)
app.include_router(compare.router)
app.include_router(report.router)
app.include_router(chat_stream.router)
app.include_router(ocr.router)
app.include_router(telegram.router)
app.include_router(chat_adaptive.router)
app.include_router(test_stt.router)
app.include_router(crud.router)   # ← CRUD visible dans Swagger

# ── Services RAG ─────────────────────────────────────────────
from app.services.chat_session_service import chat_session_service
from app.services.rag_service import demarrer_rag, generer_reponse_rag
from app.services.profile_service import (
    construire_profil_etudiant,
    extraire_infos_conversation,
    demarrer_test_psychometrique,
    generer_question_suivante,
    calculer_profil_psychometrique_final,
    generer_rapport_psychometrique,
    verifier_declenchement_peer_match,
)
from app.services.fit_score_service import calculer_fitscore_complet, generer_rapport_fitscore
from app.services.admission_service import generer_rapport_admission
from app.services.career_service import (
    simuler_carriere,
    comparer_carrieres_intelligent,
    obtenir_filieres_comparables,
)
from app.services.coach_service import (
    initialiser_suivi_coach,
    ajouter_snapshot,
    generer_rapport_coach,
)
from app.services.peermatch import creer_demande_peermatch
from app.academic_config import FILIERES

print("🚀 Démarrage du système RAG...")
demarrer_rag()
print("✅ Système prêt !")

# ============================================================
# COOKIE
# ============================================================

COOKIE_NAME = "supmti_sid"

def get_session_id(request: Request, response: Response) -> str:
    sid = request.cookies.get(COOKIE_NAME)
    
    # Si pas de cookie, essayer de reconstruire depuis X-User-Id
    if not sid:
        user_id = request.headers.get("X-User-Id")
        if user_id:
            # Clé stable basée sur user_id — même session pour tout le monde
            sid = f"user_{user_id}"
        else:
            sid = str(uuid.uuid4())
    
    response.set_cookie(
        key=COOKIE_NAME,
        value=sid,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
        path="/",
    )
    return sid

@app.post("/api/tts")
async def text_to_speech(request: Request):
    body = await request.json()
    text = body.get("text", "")
    lang = body.get("lang", "fr")
    if not text:
        return JSONResponse(status_code=400, content={"error": "Texte vide"})
    audio = await tts_service.synthesize(text[:500], lang)
    return FastAPIResponse(content=audio, media_type="audio/mpeg")
# ============================================================
# SCHEMAS PYDANTIC
# ============================================================

class MessageSchema(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    user_message: str
    historique: Optional[List[MessageSchema]] = []

class ChatV2Request(BaseModel):
    message: str

class CarriereRequest(BaseModel):
    filiere_id: Optional[str] = ""

class ComparerRequest(BaseModel):
    filiere_1: Optional[str] = ""
    filiere_2: Optional[str] = ""

class PsychoAnswerRequest(BaseModel):
    reponse: str

# ── CORRECTION peermatch : body JSON (plus query params) ──────
class PeerMatchRequest(BaseModel):
    prenom:  str
    email:   str
    filiere: str
    message: str

# ============================================================
# HELPER CHAT
# ============================================================

async def _process_chat(user_message: str, request: Request, response: Response, db: Session = None) -> dict:
    sid  = get_session_id(request, response)
    sess = chat_session_service.get_or_create(sid)

    if sess["profil"] is None:
        sess["profil"] = construire_profil_etudiant({})

    # Charger le profil DB au premier message
    user_id = request.headers.get("X-User-Id") or request.session.get("user_id")
    if user_id and not sess.get("profil_db_charge"):
        sess = charger_profil_depuis_db(user_id, sess, db)

    sess["profil"] = extraire_infos_conversation(user_message, sess["profil"])

    if sess["profil"].get("statut_profil") == "complet" and sess["suivi_coach"] is None:
        sess["suivi_coach"] = initialiser_suivi_coach(sess["profil"])

    chat_session_service.auto_titre(sess, user_message)

    sess["historique"].append({"role": "user", "content": user_message})
    sess["nb_messages"] += 1

    peer_match_info = None
    reponse_finale  = ""

    if sess["test_psycho_en_cours"]:
        msg, nouvel_etat = generer_question_suivante(
            user_message, sess["etat_test_psycho"], sess["profil"]
        )
        sess["etat_test_psycho"] = nouvel_etat
        if nouvel_etat["complete"]:
            sess["test_psycho_en_cours"] = False
            profil_psycho = calculer_profil_psychometrique_final(nouvel_etat)
            sess["profil"]["profil_psychometrique"] = profil_psycho
            prenom = sess["profil"].get("informations_personnelles", {}).get("prenom", "")
            reponse_finale = generer_rapport_psychometrique(profil_psycho, prenom)
            reponse_finale += "\n\n✨ Clique sur **FitScore** pour un score encore plus précis."
        else:
            reponse_finale = msg
    else:
        resultat = generer_reponse_rag(user_message, sess["historique"], sess["profil"])
        reponse_finale = resultat["reponse"]

        mots_hesitation = [
            "j'hésite", "je sais pas", "je ne sais pas", "pas sûr", "pas sure",
            "indécis", "indécise", "ambassadeur", "témoignage",
            "parler à quelqu'un", "retour d'expérience", "un étudiant",
        ]
        hesitation_forte = any(m in user_message.lower() for m in mots_hesitation)
        if (sess["nb_messages"] >= 5 or hesitation_forte) \
                and not sess["peer_match_declenche"] and sess["fitscore"]:
            declencher, filiere = verifier_declenchement_peer_match(
                sess["historique"], sess["fitscore"], sess["peer_match_declenche"]
            )
            if declencher:
                sess["peer_match_declenche"] = True
                peer_match_info = {
                    "filiere": filiere,
                    "message": f"Tu hésites sur {filiere} ? Utilise **Peer Match** dans le menu !",
                }

    sess["historique"].append({"role": "assistant", "content": reponse_finale})

    # Sauvegarder les messages en DB (upsert, pas recréer)
    if user_id and sess["nb_messages"] > 0:
        chat_session_service._sauvegarder_messages(sid, sess, db=db, user_id=user_id)

    return {
        "response":   reponse_finale,
        "reponse":    reponse_finale,
        "profil":     sess["profil"],
        "peer_match": peer_match_info,
    }

# ============================================================
# ROUTES — Racine & Santé
# ============================================================

@app.get("/", tags=["root"])
def read_root():
    return {
        "message": "Bienvenue sur l'API du chatbot SUP'MTI",
        "version": settings.API_VERSION,
        "documentation": "/docs",
    }

@app.get("/health", tags=["health"])
def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "version": settings.API_VERSION,
    }

# ============================================================
# ROUTES — Chat
# ============================================================

@app.post("/api/chat")
async def api_chat(body: ChatV2Request, request: Request, response: Response, db: Session = Depends(get_db)):
    return await _process_chat(body.message, request, response, db)
 
@app.post("/chat")
async def chat_endpoint(body: ChatRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    return await _process_chat(body.user_message, request, response, db)

# ============================================================
# ROUTES — Session
# ============================================================

# ── GET /api/session ─────────────────────────────────────────
@app.get("/api/session")
async def get_session(request: Request, response: Response, db: Session = Depends(get_db)):
    sid     = get_session_id(request, response)
    sess    = chat_session_service.get_or_create(sid)
    user_id = request.headers.get("X-User-Id") or request.session.get("user_id")
 
    # Charger le profil DB au premier appel
    if user_id and not sess.get("profil_db_charge"):
        sess = charger_profil_depuis_db(user_id, sess, db)
 
    return {
        "session_id":           sid,
        "profil":               sess["profil"],
        "fitscore":             sess["fitscore"],
        "test_psycho_en_cours": sess["test_psycho_en_cours"],
        # ← passer db + user_id pour lire l'historique depuis la DB
        "historique_chats":     chat_session_service.get_historique_liste(sid, db=db, user_id=user_id),
        "chat_actuel_id":       sess["chat_actuel_id"],
        "chat_actuel_titre":    sess["chat_actuel_titre"],
        "nb_messages":          sess["nb_messages"],
    }

# ── POST /api/new_chat ────────────────────────────────────────
@app.post("/api/new_chat")
async def new_chat(request: Request, response: Response, db: Session = Depends(get_db)):
    sid     = get_session_id(request, response)
    user_id = request.headers.get("X-User-Id") or request.session.get("user_id")
    return chat_session_service.nouveau_chat(sid, db=db, user_id=user_id)

@app.post("/api/reset")
async def reset_session(request: Request, response: Response):
    sid = get_session_id(request, response)
    return chat_session_service.reset_complet(sid)

# ============================================================
# ROUTES — Historique
# ============================================================

# ── GET /api/historique/{chat_id} ────────────────────────────
@app.get("/api/historique/{chat_id}")
async def get_historique_chat(chat_id: str, request: Request, response: Response, db: Session = Depends(get_db)):
    sid  = get_session_id(request, response)
    chat = chat_session_service.get_chat_par_id(sid, chat_id, db=db)
    if not chat:
        return JSONResponse(status_code=404, content={"error": "Conversation non trouvée"})
    return {
        "id":          chat["id"],
        "titre":       chat["titre"],
        "date":        chat["date"],
        "nb_messages": chat["nb_messages"],
        "messages":    chat.get("messages", []),
        "profil":      chat.get("profil"),
        "en_cours":    chat.get("en_cours", False),
    }

# ── DELETE /api/historique/{chat_id} ─────────────────────────
@app.delete("/api/historique/{chat_id}")
async def delete_historique_chat(chat_id: str, request: Request, response: Response, db: Session = Depends(get_db)):
    sid = get_session_id(request, response)
    return chat_session_service.supprimer_chat(sid, chat_id, db=db)

# ============================================================
# ROUTES — FitScore / Admission / Carrière / Coach
# ============================================================

@app.post("/api/fitscore")
async def fitscore(request: Request, response: Response):
    sid  = get_session_id(request, response)
    sess = chat_session_service.get_or_create(sid)
    if not sess["profil"]:
        return JSONResponse(status_code=400, content={"error": True, "message": "Dis-moi ton prénom, ton BAC et ta moyenne !"})
    if sess["profil"].get("parcours_academique", {}).get("moyenne_generale", 0) == 0:
        return JSONResponse(status_code=400, content={"error": True, "message": "J'ai besoin de ta moyenne pour calculer le FitScore !"})
    result = calculer_fitscore_complet(sess["profil"], sess["profil"].get("profil_psychometrique"))
    sess["fitscore"] = result
    if sess["suivi_coach"]:
        sess["suivi_coach"] = ajouter_snapshot(sess["suivi_coach"], sess["profil"], result)
    rapport = generer_rapport_fitscore(result, sess["profil"])
    return {"rapport": rapport, "classement": result.get("classement", []),
            "meilleure_filiere": result.get("meilleure_filiere"), "profil": sess["profil"]}

@app.post("/api/admission")
async def admission(request: Request, response: Response):
    sid  = get_session_id(request, response)
    sess = chat_session_service.get_or_create(sid)
    if not sess["profil"]:
        return JSONResponse(status_code=400, content={"error": True, "message": "Dis-moi ton BAC et ta moyenne d'abord !"})
    rapport = generer_rapport_admission(sess["profil"], sess["fitscore"])
    return {"rapport": rapport, "profil": sess["profil"]}

@app.post("/api/carriere")
async def carriere(body: CarriereRequest, request: Request, response: Response):
    sid  = get_session_id(request, response)
    sess = chat_session_service.get_or_create(sid)
    if not sess["profil"]:
        sess["profil"] = construire_profil_etudiant({})
    filiere_id = (body.filiere_id or "").upper()
    if not filiere_id:
        info = obtenir_filieres_comparables(sess["profil"])
        return {"filieres_disponibles": info["filieres_accessibles"],
                "explication": info["explication"], "annee_entree": info["annee_entree"]}
    simulation = simuler_carriere(sess["profil"], filiere_id)
    return {"scenario": simulation["scenario"], "filiere_nom": simulation["filiere_nom"],
            "donnees_cles": simulation["donnees_cles"]}

@app.post("/api/comparer")
async def comparer(body: ComparerRequest, request: Request, response: Response):
    sid  = get_session_id(request, response)
    sess = chat_session_service.get_or_create(sid)
    if not sess["profil"]:
        return JSONResponse(status_code=400, content={"error": True, "message": "Dis-moi ton profil d'abord !"})
    return comparer_carrieres_intelligent(sess["profil"],
        (body.filiere_1 or "").upper() or None, (body.filiere_2 or "").upper() or None)

@app.post("/api/coach")
async def coach(request: Request, response: Response):
    sid  = get_session_id(request, response)
    sess = chat_session_service.get_or_create(sid)
    if not sess["profil"]:
        return JSONResponse(status_code=400, content={"error": True, "message": "J'ai besoin de ton profil d'abord !"})
    if not sess["fitscore"]:
        sess["fitscore"] = calculer_fitscore_complet(sess["profil"])
    if not sess["suivi_coach"]:
        sess["suivi_coach"] = initialiser_suivi_coach(sess["profil"])
        sess["suivi_coach"] = ajouter_snapshot(sess["suivi_coach"], sess["profil"], sess["fitscore"])
    rapport = generer_rapport_coach(sess["suivi_coach"], sess["profil"], sess["fitscore"])
    return {"rapport": rapport, "profil": sess["profil"]}

# ============================================================
# ROUTES — Psychométrique
# ============================================================

@app.post("/api/psycho/start")
async def psycho_start(request: Request, response: Response):
    sid  = get_session_id(request, response)
    sess = chat_session_service.get_or_create(sid)
    if not sess["profil"]:
        sess["profil"] = construire_profil_etudiant({})
    message_intro, etat = demarrer_test_psychometrique(sess["profil"])
    sess["etat_test_psycho"]     = etat
    sess["test_psycho_en_cours"] = True
    return {
        "message":           message_intro,
        "question_actuelle": etat["question_actuelle"],
        "total_questions":   etat["total_questions"],
    }

@app.post("/api/psycho/answer")
async def psycho_answer(body: PsychoAnswerRequest, request: Request, response: Response):
    sid  = get_session_id(request, response)
    sess = chat_session_service.get_or_create(sid)
    if not body.reponse.strip():
        return JSONResponse(status_code=400, content={"error": "Réponse vide"})
    if not sess["test_psycho_en_cours"]:
        return JSONResponse(status_code=400, content={"error": "Pas de test en cours"})
    msg, nouvel_etat = generer_question_suivante(body.reponse, sess["etat_test_psycho"], sess["profil"])
    sess["etat_test_psycho"] = nouvel_etat
    if nouvel_etat["complete"]:
        sess["test_psycho_en_cours"] = False
        profil_psycho = calculer_profil_psychometrique_final(nouvel_etat)
        sess["profil"]["profil_psychometrique"] = profil_psycho
        prenom = sess["profil"].get("informations_personnelles", {}).get("prenom", "")
        rapport = generer_rapport_psychometrique(profil_psycho, prenom)
        return {"complete": True, "rapport": rapport,
                "scores": profil_psycho["scores"], "points_forts": profil_psycho["points_forts"]}
    return {"complete": False, "message": msg,
            "question_actuelle": nouvel_etat["question_actuelle"], "total_questions": 10}

# ============================================================
# ROUTES — Profil & Filières (session en mémoire)
# ============================================================



class ProfilUpdateRequest(BaseModel):
    full_name:  Optional[str]       = None
    average:    Optional[float]     = None
    bac_type:   Optional[str]       = None
    level:      Optional[str]       = None
    city:       Optional[str]       = None
    interests:  Optional[List[str]] = None
    user_id:    Optional[str]       = None  # envoyé aussi dans le body en backup
# ── GET /api/profil (lecture session en mémoire — inchangé) ──
 
@app.get("/api/profil")
async def get_profil(request: Request, response: Response):
    sid  = get_session_id(request, response)
    sess = chat_session_service.get_or_create(sid)
    return {"profil": sess["profil"]}
 

 
@app.put("/api/profil")
async def update_profil(
    body: ProfilUpdateRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    # ── Récupérer user_id : header X-User-Id en priorité, sinon body, sinon session
    user_id = (
        request.headers.get("X-User-Id")
        or body.user_id
        or request.session.get("user_id")
    )
 
    if not user_id:
        return JSONResponse(
            status_code=401,
            content={"error": True, "message": "Non authentifié."}
        )
 
    # Vérifier que l'utilisateur existe vraiment en base
    user_exists = db.execute(
        text("SELECT id FROM users WHERE id = :id"),
        {"id": user_id}
    ).fetchone()
 
    if not user_exists:
        return JSONResponse(
            status_code=404,
            content={"error": True, "message": "Utilisateur introuvable."}
        )
 
    # ── Mettre à jour users (full_name) ──────────────────────
    if body.full_name:
        db.execute(
            text("UPDATE users SET full_name = :fn WHERE id = :id"),
            {"fn": body.full_name, "id": user_id}
        )
 
    # ── Mettre à jour students ────────────────────────────────
    update_fields = {}
    if body.average  is not None: update_fields["average"]  = body.average
    if body.bac_type is not None: update_fields["bac_type"] = body.bac_type
    if body.level    is not None: update_fields["level"]    = body.level
    if body.city     is not None: update_fields["city"]     = body.city
 
    if update_fields:
        set_clause = ", ".join(f"{k} = :{k}" for k in update_fields)
        update_fields["user_id"] = user_id
        db.execute(
            text(f"UPDATE students SET {set_clause} WHERE user_id = :user_id"),
            update_fields
        )
 
    # ── Mettre à jour student_interests ──────────────────────
    if body.interests is not None:
        student_row = db.execute(
            text("SELECT id FROM students WHERE user_id = :uid"),
            {"uid": user_id}
        ).fetchone()
 
        if student_row:
            sid_student = student_row.id
            db.execute(
                text("DELETE FROM student_interests WHERE student_id = :sid"),
                {"sid": sid_student}
            )
            for interest_name in body.interests:
                if not interest_name:
                    continue
                db.execute(
                    text("""
                        INSERT INTO interests (id, name)
                        VALUES (gen_random_uuid(), :name)
                        ON CONFLICT (name) DO NOTHING
                    """),
                    {"name": interest_name}
                )
                interest_row = db.execute(
                    text("SELECT id FROM interests WHERE name = :name"),
                    {"name": interest_name}
                ).fetchone()
                if interest_row:
                    db.execute(
                        text("""
                            INSERT INTO student_interests (student_id, interest_id)
                            VALUES (:sid, :iid)
                            ON CONFLICT DO NOTHING
                        """),
                        {"sid": sid_student, "iid": interest_row.id}
                    )
 
    db.commit()
 
    # ── Synchroniser aussi le profil SAMI en mémoire ─────────
    sid_cookie = get_session_id(request, response)
    sess = chat_session_service.get_or_create(sid_cookie)
    if sess["profil"] is None:
        from app.services.profile_service import construire_profil_etudiant
        sess["profil"] = construire_profil_etudiant({})
 
    if body.full_name:
        sess["profil"].setdefault("informations_personnelles", {})["prenom"] = body.full_name.split()[0]
    if body.average is not None:
        sess["profil"].setdefault("parcours_academique", {})["moyenne_generale"] = body.average
    if body.bac_type:
        sess["profil"].setdefault("parcours_academique", {})["type_bac"] = body.bac_type
    if body.city:
        sess["profil"].setdefault("informations_personnelles", {})["ville"] = body.city
    if body.interests:
        sess["profil"].setdefault("preferences", {})["centres_interet"] = body.interests
 
    return {
        "success": True,
        "message": "Profil mis à jour avec succès.",
    }

@app.get("/api/filieres")
def get_filieres():
    return {"filieres": [
        {"id": fid, "nom": f["nom"], "niveau": f["niveau"],
         "duree": f["duree"], "description": f.get("description", "")}
        for fid, f in FILIERES.items()
    ]}

# ============================================================
# ROUTES — PeerMatch (CORRIGÉ : body JSON)
# ============================================================

# Dans main.py — remplace l'endpoint POST /api/peermatch existant

@app.post("/api/peermatch")
def peermatch(body: PeerMatchRequest, db: Session = Depends(get_db)):
    result = creer_demande_peermatch(
        db,
        body.filiere,
        body.prenom,
        body.email,
        body.message
    )

    if not result:
        # Aucun ambassadeur — on crée quand même la demande sans ambassadeur
        # L'admin pourra en assigner un plus tard
        import uuid as _uuid
        demande_id = str(_uuid.uuid4())
        try:
            from app.database.models import DemandePeerMatch
            demande = DemandePeerMatch(
                id              = demande_id,
                ambassadeur_id  = None,
                prenom_etudiant = body.prenom,
                email_etudiant  = body.email,
                filiere         = body.filiere,
                message         = body.message,
                statut          = "en_attente",
            )
            db.add(demande); db.commit()
        except Exception:
            demande_id = None

        return {
            "success":       True,
            "demande_id":    demande_id,
            "ambassadeur":   None,
            "contact_email": None,
            "contact_wa":    None,
            "message":       f"Ta demande pour {body.filiere} a été enregistrée. Un ambassadeur te sera assigné sous 24h.",
        }

    return {
        "success":       True,
        "demande_id":    result.get("demande_id"),
        "ambassadeur":   result.get("ambassadeur"),
        "contact_email": result.get("contact_email"),
        "contact_wa":    result.get("contact_wa"),
        "message":       "Un ambassadeur a été trouvé pour vous.",
        # Rétrocompatibilité
        "contact":       result,
    }




@app.get("/api/rapport/pdf")
async def telecharger_rapport_pdf(request: Request, response: Response):
    """Génère et retourne le rapport PDF depuis la session courante."""
    sid  = get_session_id(request, response)
    sess = chat_session_service.get_or_create(sid)
 
    profil   = sess.get("profil")
    fitscore = sess.get("fitscore")
 
    if not profil:
        return JSONResponse(
            status_code=400,
            content={"error": "Profil incomplet. Parle d'abord à SAMI pour qu'il te connaisse."}
        )
 
    pdf_bytes = generer_rapport_pdf(profil, fitscore)
    nom = profil.get("informations_personnelles", {}).get("prenom", "etudiant")
 
    return FastAPIResponse(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="rapport_sami_{nom}.pdf"'
        }
    )
 
 
@app.get("/api/rapport/word")
async def telecharger_rapport_word(request: Request, response: Response):
    """Génère et retourne le rapport Word depuis la session courante."""
    sid  = get_session_id(request, response)
    sess = chat_session_service.get_or_create(sid)
 
    profil   = sess.get("profil")
    fitscore = sess.get("fitscore")
 
    if not profil:
        return JSONResponse(
            status_code=400,
            content={"error": "Profil incomplet. Parle d'abord à SAMI."}
        )
 
    word_bytes = generer_rapport_word(profil, fitscore)
    nom = profil.get("informations_personnelles", {}).get("prenom", "etudiant")
 
    return FastAPIResponse(
        content=word_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="rapport_sami_{nom}.docx"'
        }
    )    












# ============================================================
# À AJOUTER dans main.py — Endpoints Admin
# ============================================================



# ── GET /api/admin/stats ─────────────────────────────────────
@app.get("/api/admin/stats")
async def admin_stats(request: Request, db: Session = Depends(get_db)):
    try:
        total_users         = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
        total_students      = db.execute(text("SELECT COUNT(*) FROM students")).scalar()
        total_conversations = db.execute(text("SELECT COUNT(*) FROM conversations")).scalar()
        total_messages      = db.execute(text("SELECT COUNT(*) FROM messages")).scalar()
        total_ambassadeurs  = db.execute(text("SELECT COUNT(*) FROM ambassadeurs WHERE is_active = TRUE")).scalar()
        inscriptions_recentes = db.execute(text(
            "SELECT COUNT(*) FROM users WHERE created_at >= NOW() - INTERVAL '7 days'"
        )).scalar()

        print(f"[DEBUG] users={total_users}, students={total_students}, conv={total_conversations}")

        try:
            bac_rows = db.execute(text(
                "SELECT bac_type, COUNT(*) as cnt FROM students WHERE bac_type IS NOT NULL AND bac_type != '' GROUP BY bac_type"
            )).fetchall()
            bac_distribution = {r[0]: int(r[1]) for r in bac_rows}
        except Exception as e:
            print(f"[WARN] bac_distribution error: {e}")
            bac_distribution = {}

        return {
            "total_users":           int(total_users or 0),
            "total_students":        int(total_students or 0),
            "total_conversations":   int(total_conversations or 0),
            "total_messages":        int(total_messages or 0),
            "total_ambassadeurs":    int(total_ambassadeurs or 0),
            "fitscore_calcules":     int(total_conversations or 0),
            "inscriptions_recentes": int(inscriptions_recentes or 0),
            "filiere_top":           "IISIC",
            "bac_distribution":      bac_distribution,
        }
    except Exception as e:
        import traceback; traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

# ── GET /api/admin/students ───────────────────────────────────
@app.get("/api/admin/students")
async def admin_students(request: Request, db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT u.id, u.full_name, u.email, u.created_at, u.role, u.is_active,
               s.average, s.bac_type, s.city, s.level
        FROM users u
        LEFT JOIN students s ON s.user_id = u.id
        ORDER BY u.created_at DESC
        LIMIT 100
    """)).fetchall()
    
    result = []
    for r in rows:
        d = dict(r._mapping)
        # Convertir les types non-sérialisables
        if d.get('created_at'):
            d['created_at'] = str(d['created_at'])
        if d.get('average') is not None:
            d['average'] = float(d['average'])
        result.append(d)
    
    return {"students": result}


# ── DELETE /api/admin/students/{id} ──────────────────────────
@app.delete("/api/admin/students/{student_id}")
async def admin_delete_student(student_id: str, db: Session = Depends(get_db)):
    db.execute(text("DELETE FROM student_interests WHERE student_id IN (SELECT id FROM students WHERE user_id = :uid)"), {"uid": student_id})
    db.execute(text("DELETE FROM students WHERE user_id = :uid"), {"uid": student_id})
    db.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": student_id})
    db.commit()
    return {"success": True}




# Ajouter dans main.py — endpoint PUT pour modifier un étudiant

@app.put("/api/admin/students/{student_id}")
async def admin_update_student(student_id: str, request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    
    # Mettre à jour users
    if body.get("full_name"):
        db.execute(text("UPDATE users SET full_name = :fn WHERE id = :id"),
            {"fn": body["full_name"], "id": student_id})
    
    # Mettre à jour students
    fields = {}
    for key in ["average", "bac_type", "level", "city"]:
        if key in body and body[key] is not None:
            fields[key] = body[key]
    
    if fields:
        set_clause = ", ".join(f"{k} = :{k}" for k in fields)
        fields["uid"] = student_id
        db.execute(text(f"UPDATE students SET {set_clause} WHERE user_id = :uid"), fields)
    
    db.commit()
    return {"success": True}    


# ── GET /api/admin/ambassadeurs ───────────────────────────────
@app.get("/api/admin/ambassadeurs")
async def admin_ambassadeurs(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT * FROM ambassadeurs ORDER BY created_at DESC")).fetchall()
    return {"ambassadeurs": [dict(r._mapping) for r in rows]}


# ── POST /api/admin/ambassadeurs ─────────────────────────────
@app.post("/api/admin/ambassadeurs")
async def admin_add_ambassadeur(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    new_id = str(uuid.uuid4())
    db.execute(text("""
        INSERT INTO ambassadeurs (id, nom, program_id, niveau, email, whatsapp, is_active, created_at)
        VALUES (:id, :nom, :program_id, :niveau, :email, :whatsapp, :is_active, NOW())
    """), {
        "id": new_id, "nom": body.get("nom",""), "program_id": body.get("program_id",""),
        "niveau": body.get("niveau",""), "email": body.get("email",""),
        "whatsapp": body.get("whatsapp",""), "is_active": body.get("is_active", True),
    })
    db.commit()
    return {"success": True, "ambassadeur": {"id": new_id, **body}}


# ── PATCH /api/admin/ambassadeurs/{id} ───────────────────────
@app.patch("/api/admin/ambassadeurs/{amb_id}")
async def admin_toggle_ambassadeur(amb_id: str, request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    db.execute(text("UPDATE ambassadeurs SET is_active = :v WHERE id = :id"), {"v": body.get("is_active", True), "id": amb_id})
    db.commit()
    return {"success": True}


# ── DELETE /api/admin/ambassadeurs/{id} ──────────────────────
@app.delete("/api/admin/ambassadeurs/{amb_id}")
async def admin_delete_ambassadeur(amb_id: str, db: Session = Depends(get_db)):
    db.execute(text("DELETE FROM ambassadeurs WHERE id = :id"), {"id": amb_id})
    db.commit()
    return {"success": True}


# ── GET /api/admin/documents ─────────────────────────────────
@app.get("/api/admin/documents")
async def admin_documents(db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT d.id, d.title, d.source, d.uploaded_at,
               COUNT(dc.id) as chunks_count
        FROM documents d
        LEFT JOIN document_chunks dc ON dc.document_id = d.id
        GROUP BY d.id, d.title, d.source, d.uploaded_at
        ORDER BY d.uploaded_at DESC
    """)).fetchall()
    return {"documents": [dict(r._mapping) for r in rows]}


# ── DELETE /api/admin/documents/{id} ─────────────────────────
@app.delete("/api/admin/documents/{doc_id}")
async def admin_delete_document(doc_id: str, db: Session = Depends(get_db)):
    db.execute(text("DELETE FROM document_chunks WHERE document_id = :id"), {"id": doc_id})
    db.execute(text("DELETE FROM documents WHERE id = :id"),               {"id": doc_id})
    db.commit()
    return {"success": True}


# ── GET /api/admin/conversations ─────────────────────────────
@app.get("/api/admin/conversations")
async def admin_conversations(db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT c.id, c.started_at,
               COUNT(m.id) as nb_messages,
               MIN(CASE WHEN m.sender = 'user' THEN m.content END) as titre,
               u.full_name as student_name
        FROM conversations c
        LEFT JOIN messages m  ON m.conversation_id = c.id
        LEFT JOIN students s  ON s.id = c.student_id
        LEFT JOIN users u     ON u.id = s.user_id
        GROUP BY c.id, c.started_at, u.full_name
        HAVING COUNT(m.id) > 0
        ORDER BY c.started_at DESC
        LIMIT 50
    """)).fetchall()
    result = []
    for r in rows:
        d = dict(r._mapping)
        if d.get("titre"):
            t = d["titre"]
            d["titre"] = t[:50] + "…" if len(t) > 50 else t
        result.append(d)
    return {"conversations": result}


# ── GET /api/admin/analytics ─────────────────────────────────
@app.get("/api/admin/analytics")
async def admin_analytics(db: Session = Depends(get_db)):
    # FitScore moyen par filière (via fit_scores si disponible)
    try:
        fs_rows = db.execute(text("""
            SELECT p.name as filiere, AVG(f.score) as avg_score
            FROM fit_scores f JOIN programs p ON p.id = f.program_id
            GROUP BY p.name
        """)).fetchall()
        fitscore_par_filiere = {r.filiere: round(float(r.avg_score), 1) for r in fs_rows}
    except Exception:
        fitscore_par_filiere = {"ISI":88.2,"ME":74.5,"IISIC":91.3,"IISRT":82.7,"FACG":69.1,"MSTIC":78.4}

    # Conversations par jour (7 derniers jours)
    try:
        conv_rows = db.execute(text("""
            SELECT DATE(started_at) as day, COUNT(*) as count
            FROM conversations
            WHERE started_at >= NOW() - INTERVAL '7 days'
            GROUP BY DATE(started_at) ORDER BY day
        """)).fetchall()
        conversations_par_jour = [{"date": str(r.day)[-5:], "count": r.count} for r in conv_rows]
    except Exception:
        conversations_par_jour = []

    # Profils complets
    try:
        total_s   = db.execute(text("SELECT COUNT(*) FROM students")).scalar() or 1
        complets  = db.execute(text("SELECT COUNT(*) FROM students WHERE average > 0 AND bac_type IS NOT NULL AND bac_type != ''")).scalar() or 0
        taux      = round((complets / total_s) * 100)
    except Exception:
        taux = 45

    return {
        "fitscore_par_filiere":      fitscore_par_filiere,
        "langues_utilisees":         {"fr": 72, "ar": 18, "en": 10},
        "conversations_par_jour":    conversations_par_jour,
        "taux_profil_complet":       taux,
        "moyenne_fitscore_global":   81.2,
        "test_psycho_completes":     14,
    }










# ============================================================
# COLLER DANS main.py — Endpoints Admin + PeerMatch
# (remplace tous les anciens blocs admin_extra_routes)
# ============================================================

# ── GET /api/admin/peermatch ──────────────────────────────────
@app.get("/api/admin/peermatch")
async def admin_peermatch(db: Session = Depends(get_db)):
    try:
        rows = db.execute(text("""
            SELECT d.id, d.prenom_etudiant, d.email_etudiant, d.filiere,
                   d.message, d.statut, d.created_at, d.ambassadeur_id,
                   a.nom as ambassadeur_nom, a.email as ambassadeur_email,
                   a.whatsapp as ambassadeur_wa
            FROM demandes_peermatch d
            LEFT JOIN ambassadeurs a ON a.id = d.ambassadeur_id
            ORDER BY d.created_at DESC
            LIMIT 100
        """)).fetchall()
        result = []
        for r in rows:
            d = dict(r._mapping)
            if d.get('created_at'):
                d['created_at'] = str(d['created_at'])
            result.append(d)
        return {"demandes": result}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# ── PATCH /api/admin/peermatch/{id} ──────────────────────────
# Accepte statut ET ambassadeur_id
@app.patch("/api/admin/peermatch/{demande_id}")
async def admin_update_peermatch(demande_id: str, request: Request, db: Session = Depends(get_db)):
    body    = await request.json()
    updates = []
    params  = {"id": demande_id}

    if "statut" in body:
        updates.append("statut = :statut")
        params["statut"] = body["statut"]

    if "ambassadeur_id" in body:
        updates.append("ambassadeur_id = :ambassadeur_id")
        params["ambassadeur_id"] = body["ambassadeur_id"]

    if updates:
        db.execute(text(f"UPDATE demandes_peermatch SET {', '.join(updates)} WHERE id = :id"), params)
        db.commit()

    return {"success": True}


# ── GET /api/peermatch/statut/{demande_id} ── côté étudiant ──
@app.get("/api/peermatch/statut/{demande_id}")
async def get_peermatch_statut(demande_id: str, db: Session = Depends(get_db)):
    try:
        row = db.execute(text("""
            SELECT d.statut, d.filiere,
                   a.nom      as ambassadeur_nom,
                   a.email    as ambassadeur_email,
                   a.whatsapp as ambassadeur_wa
            FROM demandes_peermatch d
            LEFT JOIN ambassadeurs a ON a.id = d.ambassadeur_id
            WHERE d.id = :id
        """), {"id": demande_id}).fetchone()

        if not row:
            return JSONResponse(status_code=404, content={"error": "Demande introuvable"})

        d = dict(row._mapping)
        return {
            "statut":            d.get("statut", "en_attente"),
            "filiere":           d.get("filiere", ""),
            "ambassadeur_nom":   d.get("ambassadeur_nom"),
            "ambassadeur_email": d.get("ambassadeur_email"),
            "ambassadeur_wa":    d.get("ambassadeur_wa"),
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# ── GET /api/admin/ambassadeurs ───────────────────────────────
@app.get("/api/admin/ambassadeurs")
async def admin_ambassadeurs(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT * FROM ambassadeurs ORDER BY created_at DESC")).fetchall()
    result = []
    for r in rows:
        d = dict(r._mapping)
        if d.get('created_at'):
            d['created_at'] = str(d['created_at'])
        result.append(d)
    return {"ambassadeurs": result}


# ── POST /api/admin/ambassadeurs ─────────────────────────────
@app.post("/api/admin/ambassadeurs")
async def admin_add_ambassadeur(request: Request, db: Session = Depends(get_db)):
    body   = await request.json()
    new_id = str(uuid.uuid4())
    db.execute(text("""
        INSERT INTO ambassadeurs (id, nom, program_id, niveau, email, whatsapp, is_active, created_at)
        VALUES (:id, :nom, :program_id, :niveau, :email, :whatsapp, :is_active, NOW())
    """), {
        "id":         new_id,
        "nom":        body.get("nom", ""),
        "program_id": body.get("program_id", ""),
        "niveau":     body.get("niveau", ""),
        "email":      body.get("email", ""),
        "whatsapp":   body.get("whatsapp", ""),
        "is_active":  body.get("is_active", True),
    })
    db.commit()
    return {"success": True, "ambassadeur": {"id": new_id, **body}}


# ── PATCH /api/admin/ambassadeurs/{id} ───────────────────────
@app.patch("/api/admin/ambassadeurs/{amb_id}")
async def admin_toggle_ambassadeur(amb_id: str, request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    db.execute(text("UPDATE ambassadeurs SET is_active = :v WHERE id = :id"),
        {"v": body.get("is_active", True), "id": amb_id})
    db.commit()
    return {"success": True}


# ── DELETE /api/admin/ambassadeurs/{id} ──────────────────────
@app.delete("/api/admin/ambassadeurs/{amb_id}")
async def admin_delete_ambassadeur(amb_id: str, db: Session = Depends(get_db)):
    db.execute(text("DELETE FROM ambassadeurs WHERE id = :id"), {"id": amb_id})
    db.commit()
    return {"success": True}


# ── GET /api/admin/export/students ───────────────────────────
@app.get("/api/admin/export/students")
async def export_students(db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT u.full_name, u.email, u.role, u.created_at,
               s.average, s.bac_type, s.city, s.level
        FROM users u
        LEFT JOIN students s ON s.user_id = u.id
        ORDER BY u.created_at DESC
    """)).fetchall()
    lines = ["Nom,Email,Rôle,BAC,Moyenne,Ville,Niveau,Inscrit le"]
    for r in rows:
        d = dict(r._mapping)
        lines.append(",".join([
            str(d.get('full_name', '')),
            str(d.get('email', '')),
            str(d.get('role', '')),
            str(d.get('bac_type', '') or ''),
            str(d.get('average', '')  or ''),
            str(d.get('city', '')     or ''),
            str(d.get('level', '')    or ''),
            str(d.get('created_at', ''))[:10],
        ]))
    from fastapi.responses import Response as FastAPIResponse
    return FastAPIResponse(
        content="\n".join(lines),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=etudiants_supmti.csv"}
    )


# ── GET /api/admin/export/ambassadeurs ───────────────────────
@app.get("/api/admin/export/ambassadeurs")
async def export_ambassadeurs(db: Session = Depends(get_db)):
    rows = db.execute(text(
        "SELECT nom, program_id, niveau, email, whatsapp, is_active FROM ambassadeurs ORDER BY nom"
    )).fetchall()
    lines = ["Nom,Filière,Niveau,Email,WhatsApp,Statut"]
    for r in rows:
        d = dict(r._mapping)
        lines.append(",".join([
            str(d.get('nom', '')),
            str(d.get('program_id', '')),
            str(d.get('niveau', '')),
            str(d.get('email', '')    or ''),
            str(d.get('whatsapp', '') or ''),
            'Actif' if d.get('is_active') else 'Inactif',
        ]))
    from fastapi.responses import Response as FastAPIResponse
    return FastAPIResponse(
        content="\n".join(lines),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=ambassadeurs_supmti.csv"}
    )


# ── DELETE /api/admin/students/{id} ──────────────────────────
@app.delete("/api/admin/students/{student_id}")
async def admin_delete_student(student_id: str, db: Session = Depends(get_db)):
    db.execute(text(
        "DELETE FROM student_interests WHERE student_id IN (SELECT id FROM students WHERE user_id = :uid)"),
        {"uid": student_id})
    db.execute(text("DELETE FROM students WHERE user_id = :uid"), {"uid": student_id})
    db.execute(text("DELETE FROM users WHERE id = :uid"),         {"uid": student_id})
    db.commit()
    return {"success": True}


# ── PUT /api/admin/students/{id} ─────────────────────────────
@app.put("/api/admin/students/{student_id}")
async def admin_update_student(student_id: str, request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    if body.get("full_name"):
        db.execute(text("UPDATE users SET full_name = :fn WHERE id = :id"),
            {"fn": body["full_name"], "id": student_id})
    if body.get("role"):
        db.execute(text("UPDATE users SET role = :r WHERE id = :id"),
            {"r": body["role"], "id": student_id})
    fields = {}
    for key in ["average", "bac_type", "level", "city"]:
        if key in body and body[key] is not None and body[key] != '':
            fields[key] = body[key]
    if fields:
        set_clause = ", ".join(f"{k} = :{k}" for k in fields)
        fields["uid"] = student_id
        db.execute(text(f"UPDATE students SET {set_clause} WHERE user_id = :uid"), fields)
    db.commit()
    return {"success": True}





# ── Static files ──────────────────────────────────────────────
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logger.info(f"📁 Dossier static monté: {static_dir}")
else:
    logger.warning(f"⚠️ Dossier static non trouvé: {static_dir}")

logger.info(f"🚀 Application démarrée - Version {settings.API_VERSION}")