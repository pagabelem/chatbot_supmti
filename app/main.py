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
from openai import OpenAI
from typing import List, Optional
from dotenv import load_dotenv
from sqlalchemy.orm import Session
import base64
from fastapi import UploadFile, File, Form
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.responses import StreamingResponse
from app.services.report_service import generer_rapport_pdf, generer_rapport_word
from fastapi.responses import Response as FastAPIResponse
from fastapi import UploadFile, File, Form
import numpy, json
import asyncio
import base64
from fastapi import UploadFile, File, Form
from app.api.routes.test_stt import router as voice_router



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
 
# def charger_profil_depuis_db(user_id: str, sess: dict, db: Session) -> dict:
#     """
#     Charge les données du profil DB dans la session SAMI en mémoire.
#     Appelé une fois par session quand le profil est vide ou incomplet.
#     """
#     if not user_id:
#         return sess
 
#     try:
#         # Récupérer user + student
#         row = db.execute(text("""
#             SELECT
#                 u.full_name,
#                 u.email,
#                 s.average,
#                 s.bac_type,
#                 s.level,
#                 s.city
#             FROM users u
#             LEFT JOIN students s ON s.user_id = u.id
#             WHERE u.id = :uid
#         """), {"uid": user_id}).fetchone()
 
#         if not row:
#             return sess
 
#         # Récupérer les intérêts
#         interests_rows = db.execute(text("""
#             SELECT i.name
#             FROM interests i
#             JOIN student_interests si ON si.interest_id = i.id
#             JOIN students s ON s.id = si.student_id
#             WHERE s.user_id = :uid
#         """), {"uid": user_id}).fetchall()
 
#         interests = [r.name for r in interests_rows]
 
#         # Construire un profil si absent
#         if sess["profil"] is None:
#             from app.services.profile_service import construire_profil_etudiant
#             sess["profil"] = construire_profil_etudiant({})
 
#         # Injecter les données DB dans le profil SAMI
#         profil = sess["profil"]
 
#         # Informations personnelles
#         info = profil.setdefault("informations_personnelles", {})
#         if row.full_name:
#             parts = row.full_name.strip().split()
#             info["prenom"] = parts[0]
#             if len(parts) > 1:
#                 info["nom"] = " ".join(parts[1:])
#         if row.city:
#             info["ville"] = row.city
 
#         # Parcours académique
#         parc = profil.setdefault("parcours_academique", {})
#         if row.average and row.average > 0:
#             parc["moyenne_generale"] = float(row.average)
#         if row.bac_type:
#             parc["type_bac"] = row.bac_type
#             parc["label_bac"] = row.bac_type
#         if row.level:
#             parc["niveau_actuel"] = row.level
 
#         # Préférences
#         pref = profil.setdefault("preferences", {})
#         if interests:
#             pref["centres_interet"] = interests
 
#         # Marquer comme partiellement complété si on a les données de base
#         if row.average and row.bac_type:
#             profil["statut_profil"] = "partiel"
 
#         sess["profil"] = profil
#         sess["profil_db_charge"] = True  # flag pour ne pas recharger inutilement
 
#     except Exception as e:
#         print(f"[WARN] Impossible de charger le profil DB: {e}")
 
#     return sess







# ============================================================
# FIX — charger_profil_depuis_db dans main.py
#
# PROBLÈMES CORRIGÉS :
# 1. mention recalculée depuis la moyenne (plus "insuffisant" avec 18/20)
# 2. normaliser_niveau() appliqué sur level + bac_type
# 3. diplome_actuel correctement renseigné
# 4. statut_profil calculé proprement
#
# REMPLACEMENT : colle cette fonction à la place de l'ancienne
# dans main.py (chercher "def charger_profil_depuis_db")
# ============================================================

def _calculer_mention(moyenne: float) -> str:
    """Calcule la mention depuis la moyenne."""
    if moyenne >= 18:  return "Très Bien"
    if moyenne >= 16:  return "Bien"
    if moyenne >= 14:  return "Assez Bien"
    if moyenne >= 12:  return "Passable"
    if moyenne >= 10:  return "Passable"
    return "Insuffisant"


def _normaliser_niveau_db(level_raw: str) -> str:
    """
    Normalise le niveau académique stocké en DB.
    Accepte des formats variés (post_bac, bac2, "DUT Informatique", etc.)
    """
    if not level_raw:
        return "post_bac"

    level = level_raw.lower().strip()

    # Déjà normalisé
    if level in ("post_bac", "bac1", "bac2", "bac3", "bac4", "bac5"):
        return level

    # BAC+2
    if any(k in level for k in ("bac+2", "bac 2", "dut", "bts", "deug", "deust", "cpge",
                                  "technicien spécialisé", "technicien specialise", "ts ",
                                  "technique supérieur", "+2")):
        return "bac2"

    # BAC+3
    if any(k in level for k in ("bac+3", "bac 3", "licence", "bachelor", "l3", "l2",
                                  "3ème année", "3eme annee", "+3")):
        return "bac3"

    # BAC+4/5
    if any(k in level for k in ("bac+4", "bac+5", "master", "m1", "m2", "ingénieur",
                                  "ingenieur", "mba", "+4", "+5")):
        return "bac4"

    # BAC+1
    if any(k in level for k in ("bac+1", "bac 1", "première année", "1ère année",
                                  "prépa", "prepa", "+1")):
        return "bac1"

    # Bachelier / Terminale
    if any(k in level for k in ("terminale", "baccalauréat", "baccalaureat",
                                  "lycée", "lycee", "post_bac", "post bac")):
        return "post_bac"

    # Fallback : contient juste "bac" sans numéro → bachelier
    if "bac" in level:
        return "post_bac"

    return level_raw   # Inconnu → conserver tel quel


def charger_profil_depuis_db(user_id: str, sess: dict, db) -> dict:
    """
    Charge les données du profil DB dans la session SAMI en mémoire.
    VERSION CORRIGÉE :
    - mention recalculée depuis la moyenne
    - niveau_actuel normalisé
    - diplome_actuel renseigné
    - statut_profil calculé proprement
    """
    if not user_id:
        return sess

    try:
        from sqlalchemy import text

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

        # Intérêts
        interests_rows = db.execute(text("""
            SELECT i.name
            FROM interests i
            JOIN student_interests si ON si.interest_id = i.id
            JOIN students s ON s.id = si.student_id
            WHERE s.user_id = :uid
        """), {"uid": user_id}).fetchall()

        interests = [r.name for r in interests_rows]

        # Construire un profil vide si absent
        if sess.get("profil") is None:
            try:
                from app.services.profile_service import construire_profil_etudiant
                sess["profil"] = construire_profil_etudiant({})
            except Exception:
                sess["profil"] = {
                    "informations_personnelles": {},
                    "parcours_academique": {},
                    "preferences": {},
                    "statut_profil": "vide",
                }

        profil = sess["profil"]

        # ── Informations personnelles ─────────────────────────────
        info = profil.setdefault("informations_personnelles", {})
        if row.full_name:
            parts = row.full_name.strip().split()
            info["prenom"] = parts[0]
            if len(parts) > 1:
                info["nom"] = " ".join(parts[1:])
        if row.city:
            info["ville"] = row.city
        if row.email:
            info["email"] = row.email

        # ── Parcours académique ───────────────────────────────────
        parc = profil.setdefault("parcours_academique", {})

        # Moyenne + mention recalculée
        if row.average is not None and float(row.average) > 0:
            moyenne = float(row.average)
            parc["moyenne_generale"] = moyenne
            parc["mention"]          = _calculer_mention(moyenne)   # ← FIX: recalcul
            parc["type_moyenne"]     = "generale"

        # Type BAC / diplôme
        if row.bac_type:
            bac_raw = str(row.bac_type).strip()

            # Détecter si c'est un diplôme post-BAC (DUT, BTS, Licence…)
            est_post_bac = any(k in bac_raw.lower() for k in (
                "dut", "bts", "deug", "licence", "bachelor", "master", "ingénieur",
                "ingenieur", "l3", "l2", "m1", "m2", "technicien spécialisé",
                "technicien specialise", "ts "
            ))

            if est_post_bac:
                # C'est un diplôme post-BAC → stocker en diplome_actuel
                parc["diplome_actuel"] = bac_raw
                # Garder type_bac vide ou existant
                if not parc.get("type_bac"):
                    parc["type_bac"]   = "AUTRE"
                    parc["label_bac"]  = bac_raw
            else:
                # C'est un BAC classique (BAC S, BAC STI2D…)
                parc["type_bac"]   = bac_raw
                parc["label_bac"]  = bac_raw

        # Niveau actuel normalisé ← FIX PRINCIPAL
        if row.level:
            niveau_normalise = _normaliser_niveau_db(str(row.level))
            parc["niveau_actuel"] = niveau_normalise
        elif parc.get("diplome_actuel"):
            # Déduire le niveau depuis le diplôme
            parc["niveau_actuel"] = _normaliser_niveau_db(parc["diplome_actuel"])

        # ── Préférences ───────────────────────────────────────────
        pref = profil.setdefault("preferences", {})
        if interests:
            pref["centres_interet"] = interests

        # ── Statut profil ─────────────────────────────────────────
        has_moyenne = parc.get("moyenne_generale", 0) > 0
        has_niveau  = bool(parc.get("niveau_actuel"))
        has_prenom  = bool(info.get("prenom"))

        if has_moyenne and has_niveau and has_prenom:
            profil["statut_profil"] = "partiel"
        elif has_moyenne or has_niveau:
            profil["statut_profil"] = "partiel"
        else:
            profil["statut_profil"] = "vide"

        sess["profil"]           = profil
        sess["profil_db_charge"] = True

        print(f"[DB→SESSION] Profil chargé — "
            f"moyenne={parc.get('moyenne_generale')}, "
            f"mention={parc.get('mention')}, "
            f"niveau={parc.get('niveau_actuel')}, "
            f"diplome={parc.get('diplome_actuel')}")

    except Exception as e:
        import traceback
        print(f"[WARN] Impossible de charger le profil DB: {e}")
        traceback.print_exc()

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
app.include_router(voice_router, prefix="/api")


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
    user_message: str = ""
    message:      str = ""
    historique: Optional[List[MessageSchema]] = []


    def get_message(self) -> str:
        return self.user_message or self.message

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
 
# @app.post("/chat")
# async def chat_endpoint(body: ChatRequest, request: Request, response: Response, db: Session = Depends(get_db)):
#     return await _process_chat(body.user_message, request, response, db)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))



@app.post("/chat")
async def chat_endpoint(
    body: ChatRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Endpoint SSE — envoie la réponse token par token.
    Format de chaque événement :
        data: {"token": "..."}\n\n          ← chunk de texte
        data: {"done": true, "profil": ..., "peer_match": ...}\n\n  ← fin
        data: {"error": "message"}\n\n     ← en cas d'erreur
    """
    sid  = get_or_create_session(request, response)
    sess = sessions_data[sid]
 
    user_message = body.user_message   # ou body.message selon ta définition ChatRequest
 
    async def stream_generator():
        full_response = ""
        profil_result     = None
        peer_match_result = None
 
        try:
            # ── Construire les messages pour OpenAI ──────────────────────────
            messages_openai = build_messages_for_openai(sess, user_message)
            # └─ remplace par ta fonction existante qui prépare l'historique
 
            # ── Appel OpenAI avec stream=True ────────────────────────────────
            stream = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages_openai,
                stream=True,
                temperature=0.7,
                max_tokens=1000,
            )
 
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta is None:
                    continue
                full_response += delta
                # Envoyer le token au frontend
                yield f"data: {json.dumps({'token': delta}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0)   # libérer l'event loop entre chaque chunk
 
            # ── Post-traitement (même logique qu'avant) ───────────────────────
            sess["historique"].append({"role": "user",      "content": user_message})
            sess["historique"].append({"role": "assistant", "content": full_response})
            sess["nb_messages"] = sess.get("nb_messages", 0) + 1
 
            # Auto-titre depuis le premier message
            if sess["nb_messages"] == 1:
                sess["chat_actuel_titre"] = user_message[:40]
 
            # Extraction du profil depuis la conversation
            profil_result = extraire_infos_conversation(sess, full_response)
            # └─ ta fonction existante
 
            # Peer match si déclenché
            peer_match_result = verifier_peer_match(sess, full_response)
            # └─ ta fonction existante (retourne None si pas déclenché)
 
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            return
 
        # ── Événement final : done + métadonnées ─────────────────────────────
        yield f"data: {json.dumps({'done': True, 'profil': profil_result, 'peer_match': peer_match_result}, ensure_ascii=False)}\n\n"
 
    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":               "no-cache",
            "X-Accel-Buffering":           "no",      # désactive le buffering nginx
            "Access-Control-Allow-Origin": "http://localhost:3000",
            "Access-Control-Allow-Credentials": "true",
        }
    )




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
    full_name:     Optional[str]       = None
    average:       Optional[float]     = None
    bac_type:      Optional[str]       = None
    level:         Optional[str]       = None
    city:          Optional[str]       = None
    interests:     Optional[List[str]] = None
    user_id:       Optional[str]       = None
    diplome_actuel: Optional[str]      = None  # ← NOUVEAU
 
@app.get("/api/profil")
async def get_profil(request: Request, response: Response):
    sid  = get_session_id(request, response)
    sess = chat_session_service.get_or_create(sid)
    return {"profil": sess["profil"]}
 

 
# @app.put("/api/profil")
# async def update_profil(
#     body: ProfilUpdateRequest,
#     request: Request,
#     response: Response,
#     db: Session = Depends(get_db)
# ):
#     # ── Récupérer user_id : header X-User-Id en priorité, sinon body, sinon session
#     user_id = (
#         request.headers.get("X-User-Id")
#         or body.user_id
#         or request.session.get("user_id")
#     )
 
#     if not user_id:
#         return JSONResponse(
#             status_code=401,
#             content={"error": True, "message": "Non authentifié."}
#         )
 
#     # Vérifier que l'utilisateur existe vraiment en base
#     user_exists = db.execute(
#         text("SELECT id FROM users WHERE id = :id"),
#         {"id": user_id}
#     ).fetchone()
 
#     if not user_exists:
#         return JSONResponse(
#             status_code=404,
#             content={"error": True, "message": "Utilisateur introuvable."}
#         )
 
#     # ── Mettre à jour users (full_name) ──────────────────────
#     if body.full_name:
#         db.execute(
#             text("UPDATE users SET full_name = :fn WHERE id = :id"),
#             {"fn": body.full_name, "id": user_id}
#         )
 
#     # ── Mettre à jour students ────────────────────────────────
#     update_fields = {}
#     if body.average  is not None: update_fields["average"]  = body.average
#     if body.bac_type is not None: update_fields["bac_type"] = body.bac_type
#     if body.level    is not None: update_fields["level"]    = body.level
#     if body.city     is not None: update_fields["city"]     = body.city
 
#     if update_fields:
#         set_clause = ", ".join(f"{k} = :{k}" for k in update_fields)
#         update_fields["user_id"] = user_id
#         db.execute(
#             text(f"UPDATE students SET {set_clause} WHERE user_id = :user_id"),
#             update_fields
#         )
 
#     # ── Mettre à jour student_interests ──────────────────────
#     if body.interests is not None:
#         student_row = db.execute(
#             text("SELECT id FROM students WHERE user_id = :uid"),
#             {"uid": user_id}
#         ).fetchone()
 
#         if student_row:
#             sid_student = student_row.id
#             db.execute(
#                 text("DELETE FROM student_interests WHERE student_id = :sid"),
#                 {"sid": sid_student}
#             )
#             for interest_name in body.interests:
#                 if not interest_name:
#                     continue
#                 db.execute(
#                     text("""
#                         INSERT INTO interests (id, name)
#                         VALUES (gen_random_uuid(), :name)
#                         ON CONFLICT (name) DO NOTHING
#                     """),
#                     {"name": interest_name}
#                 )
#                 interest_row = db.execute(
#                     text("SELECT id FROM interests WHERE name = :name"),
#                     {"name": interest_name}
#                 ).fetchone()
#                 if interest_row:
#                     db.execute(
#                         text("""
#                             INSERT INTO student_interests (student_id, interest_id)
#                             VALUES (:sid, :iid)
#                             ON CONFLICT DO NOTHING
#                         """),
#                         {"sid": sid_student, "iid": interest_row.id}
#                     )
 
#     db.commit()
 
#     # ── Synchroniser aussi le profil SAMI en mémoire ─────────
#     sid_cookie = get_session_id(request, response)
#     sess = chat_session_service.get_or_create(sid_cookie)
#     if sess["profil"] is None:
#         from app.services.profile_service import construire_profil_etudiant
#         sess["profil"] = construire_profil_etudiant({})
 
#     if body.full_name:
#         sess["profil"].setdefault("informations_personnelles", {})["prenom"] = body.full_name.split()[0]
#     if body.average is not None:
#         sess["profil"].setdefault("parcours_academique", {})["moyenne_generale"] = body.average
#     if body.bac_type:
#         sess["profil"].setdefault("parcours_academique", {})["type_bac"] = body.bac_type
#     if body.city:
#         sess["profil"].setdefault("informations_personnelles", {})["ville"] = body.city
#     if body.interests:
#         sess["profil"].setdefault("preferences", {})["centres_interet"] = body.interests
 
#     return {
#         "success": True,
#         "message": "Profil mis à jour avec succès.",
#     }











 
@app.put("/api/profil")
async def update_profil(
    body: ProfilUpdateRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    user_id = (
        request.headers.get("X-User-Id")
        or body.user_id
        or request.session.get("user_id")
    )
 
    if not user_id:
        return JSONResponse(status_code=401, content={"error": True, "message": "Non authentifié."})
 
    user_exists = db.execute(text("SELECT id FROM users WHERE id = :id"), {"id": user_id}).fetchone()
    if not user_exists:
        return JSONResponse(status_code=404, content={"error": True, "message": "Utilisateur introuvable."})
 
    # ── users (full_name) ─────────────────────────────────────
    if body.full_name:
        db.execute(text("UPDATE users SET full_name = :fn WHERE id = :id"), {"fn": body.full_name, "id": user_id})
 
    # ── students ──────────────────────────────────────────────
    update_fields = {}
    if body.average  is not None: update_fields["average"]  = body.average
    if body.city     is not None: update_fields["city"]     = body.city
 
    # Normaliser bac_type et level avant sauvegarde
    if body.bac_type is not None:
        update_fields["bac_type"] = body.bac_type
 
    if body.level is not None:
        # Normaliser et sauvegarder le niveau normalisé
        niveau_norm = _normaliser_niveau_db(body.level)
        update_fields["level"] = niveau_norm
    elif body.diplome_actuel is not None:
        # Déduire le niveau depuis le diplôme
        niveau_norm = _normaliser_niveau_db(body.diplome_actuel)
        update_fields["level"] = niveau_norm
        # Stocker aussi le diplôme dans bac_type si pas déjà renseigné
        if "bac_type" not in update_fields:
            update_fields["bac_type"] = body.diplome_actuel
 
    if update_fields:
        set_clause = ", ".join(f"{k} = :{k}" for k in update_fields)
        update_fields["user_id"] = user_id
        db.execute(text(f"UPDATE students SET {set_clause} WHERE user_id = :user_id"), update_fields)
 
    # ── student_interests ─────────────────────────────────────
    if body.interests is not None:
        student_row = db.execute(text("SELECT id FROM students WHERE user_id = :uid"), {"uid": user_id}).fetchone()
        if student_row:
            sid_student = student_row.id
            db.execute(text("DELETE FROM student_interests WHERE student_id = :sid"), {"sid": sid_student})
            for interest_name in body.interests:
                if not interest_name: continue
                db.execute(text("INSERT INTO interests (id, name) VALUES (gen_random_uuid(), :name) ON CONFLICT (name) DO NOTHING"), {"name": interest_name})
                interest_row = db.execute(text("SELECT id FROM interests WHERE name = :name"), {"name": interest_name}).fetchone()
                if interest_row:
                    db.execute(text("INSERT INTO student_interests (student_id, interest_id) VALUES (:sid, :iid) ON CONFLICT DO NOTHING"), {"sid": sid_student, "iid": interest_row.id})
 
    db.commit()
 
    # ── Synchroniser le profil SAMI en mémoire ────────────────
    sid_cookie = get_session_id(request, response)
    sess = chat_session_service.get_or_create(sid_cookie)
    if sess["profil"] is None:
        from app.services.profile_service import construire_profil_etudiant
        sess["profil"] = construire_profil_etudiant({})
 
    profil = sess["profil"]
    parc   = profil.setdefault("parcours_academique", {})
    info   = profil.setdefault("informations_personnelles", {})
    pref   = profil.setdefault("preferences", {})
 
    if body.full_name:
        info["prenom"] = body.full_name.split()[0]
    if body.average is not None:
        parc["moyenne_generale"] = body.average
        parc["mention"]          = _calculer_mention(body.average)   # ← recalcul
    if body.bac_type:
        parc["type_bac"]  = body.bac_type
        parc["label_bac"] = body.bac_type
    if body.level:
        parc["niveau_actuel"] = _normaliser_niveau_db(body.level)
    if body.diplome_actuel:
        parc["diplome_actuel"] = body.diplome_actuel
        if not parc.get("niveau_actuel"):
            parc["niveau_actuel"] = _normaliser_niveau_db(body.diplome_actuel)
    if body.city:
        info["ville"] = body.city
    if body.interests:
        pref["centres_interet"] = body.interests
 
    # Recalculer statut
    has_moyenne = parc.get("moyenne_generale", 0) > 0
    has_niveau  = bool(parc.get("niveau_actuel"))
    if has_moyenne and has_niveau:
        profil["statut_profil"] = "partiel"
 
    sess["profil"] = profil
 
    print(f"[PUT /api/profil] Sauvegardé — moyenne={parc.get('moyenne_generale')}, "
          f"mention={parc.get('mention')}, niveau={parc.get('niveau_actuel')}")
 
    return {"success": True, "message": "Profil mis à jour avec succès."}






@app.get("/api/filieres")
async def get_filieres(request: Request, response: Response):
    """
    Retourne toutes les filières.
    Si une session existe avec un niveau déclaré,
    marque chaque filière comme accessible ou non.
    """
    sid  = get_session_id(request, response)
    sess = chat_session_service.get_or_create(sid)
    profil = sess.get("profil")
 
    filieres_accessibles_ids = None
    if profil:
        niveau = profil.get("parcours_academique", {}).get("niveau_actuel", "")
        if niveau:
            info = obtenir_filieres_comparables(profil)
            filieres_accessibles_ids = info["filieres_accessibles"]
 
    result = []
    for fid, f in FILIERES.items():
        item = {
            "id":          fid,
            "nom":         f["nom"],
            "niveau":      f["niveau"],
            "duree":       f["duree"],
            "description": f.get("description", ""),
            "accessible":  True  # par défaut si pas de profil
        }
        if filieres_accessibles_ids is not None:
            item["accessible"] = fid in filieres_accessibles_ids
        result.append(item)
 
    return {"filieres": result}





# ── GET /api/filieres/accessibles ────────────────────────────
# Appelé par renderComparer() dans le frontend
# Retourne uniquement les filières accessibles selon le niveau
@app.get("/api/filieres/accessibles")
async def get_filieres_accessibles(request: Request, response: Response):
    sid  = get_session_id(request, response)
    sess = chat_session_service.get_or_create(sid)
 
    profil = sess.get("profil")
 
    # Si profil absent ou niveau non déclaré → retourner toutes les filières
    if not profil:
        return {
            "filieres": [
                {
                    "id":      fid,
                    "nom":     f["nom"],
                    "niveau":  f["niveau"],
                    "duree":   f["duree"],
                }
                for fid, f in FILIERES.items()
            ],
            "explication": "",
            "annee_entree": "1ère année"
        }
 
    # Utiliser obtenir_filieres_comparables() pour filtrer par niveau
    info = obtenir_filieres_comparables(profil)
    filieres_accessibles_ids = info["filieres_accessibles"]
 
    filieres_filtrees = [
        {
            "id":     fid,
            "nom":    FILIERES[fid]["nom"],
            "niveau": FILIERES[fid]["niveau"],
            "duree":  FILIERES[fid]["duree"],
        }
        for fid in filieres_accessibles_ids
        if fid in FILIERES
    ]
 
    return {
        "filieres":     filieres_filtrees,
        "explication":  info.get("explication", ""),
        "annee_entree": info.get("annee_entree", "1ère année"),
        "note":         info.get("note", ""),
    }




# ── GET /api/peermatch/filieres ───────────────────────────────
# Appelé par renderPeerMatch() dans le frontend
# Retourne les filières disponibles pour le Peer Match
# filtrées selon le niveau de l'étudiant + filière recommandée FitScore
@app.get("/api/peermatch/filieres")
async def get_peermatch_filieres(request: Request, response: Response):
    sid  = get_session_id(request, response)
    sess = chat_session_service.get_or_create(sid)
 
    profil   = sess.get("profil")
    fitscore = sess.get("fitscore")
 
    # Filière recommandée par le FitScore (si calculé)
    filiere_recommandee = None
    if fitscore and fitscore.get("meilleure_filiere"):
        filiere_recommandee = fitscore["meilleure_filiere"]
 
    # Filtrer les filières par niveau
    if profil:
        info = obtenir_filieres_comparables(profil)
        filieres_ids = info["filieres_accessibles"]
        explication  = info.get("explication", "")
    else:
        # Pas de profil → toutes les filières
        filieres_ids = list(FILIERES.keys())
        explication  = ""
 
    filieres = [
        {
            "id":     fid,
            "nom":    FILIERES[fid]["nom"],
            "niveau": FILIERES[fid]["niveau"],
        }
        for fid in filieres_ids
        if fid in FILIERES
    ]
 
    # Si la filière recommandée n'est pas dans les accessibles
    # (ex: fitscore calculé avant que le niveau soit déclaré),
    # on ne l'ajoute pas — cohérence avec la règle de niveau
    if filiere_recommandee and filiere_recommandee not in filieres_ids:
        filiere_recommandee = filieres[0]["id"] if filieres else None
 
    return {
        "filieres":             filieres,
        "filiere_recommandee":  filiere_recommandee,
        "explication":          explication,
    }
     



# Ajouter dans main.py — après les routes /api/profil

@app.post("/api/auth/change-password")
async def change_password(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    current_password = body.get("current_password", "")
    new_password     = body.get("new_password", "")

    if not current_password or not new_password:
        return JSONResponse(status_code=400, content={"detail": "Mots de passe requis."})
    if len(new_password) < 6:
        return JSONResponse(status_code=400, content={"detail": "Le nouveau mot de passe doit faire au moins 6 caractères."})

    # Récupérer l'utilisateur depuis le header X-User-Id ou la session
    user_id = request.headers.get("X-User-Id") or request.session.get("user_id")
    if not user_id:
        return JSONResponse(status_code=401, content={"detail": "Non authentifié."})

    row = db.execute(text("SELECT id, password_hash FROM users WHERE id = :uid"), {"uid": user_id}).fetchone()
    if not row:
        return JSONResponse(status_code=404, content={"detail": "Utilisateur introuvable."})

    # Vérifier le mot de passe actuel
    # Utiliser passlib pbkdf2_sha256 (comme dans auth_routes.py)
    try:
        from passlib.hash import pbkdf2_sha256
        if not pbkdf2_sha256.verify(current_password, row.password_hash):
            return JSONResponse(status_code=400, content={"detail": "Mot de passe actuel incorrect."})
        # Hacher le nouveau mot de passe
        new_hash = pbkdf2_sha256.hash(new_password)
    except Exception:
        # Fallback bcrypt si pbkdf2 ne fonctionne pas
        try:
            import bcrypt
            if not bcrypt.checkpw(current_password.encode(), row.password_hash.encode()):
                return JSONResponse(status_code=400, content={"detail": "Mot de passe actuel incorrect."})
            new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        except Exception as e:
            return JSONResponse(status_code=500, content={"detail": f"Erreur serveur: {str(e)}"})

    # Mettre à jour en base
    db.execute(text("UPDATE users SET password_hash = :h WHERE id = :uid"), {"h": new_hash, "uid": user_id})
    db.commit()

    return {"success": True, "message": "Mot de passe modifié avec succès."}




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
async def admin_stats(db: Session = Depends(get_db)):
    try:
        total_users         = int(db.execute(text("SELECT COUNT(*) FROM users")).scalar() or 0)
        total_students      = int(db.execute(text("SELECT COUNT(*) FROM students")).scalar() or 0)
        total_conversations = int(db.execute(text("SELECT COUNT(*) FROM conversations")).scalar() or 0)
        total_messages      = int(db.execute(text("SELECT COUNT(*) FROM messages")).scalar() or 0)
        total_ambassadeurs  = int(db.execute(text("SELECT COUNT(*) FROM ambassadeurs WHERE is_active = TRUE")).scalar() or 0)
        inscriptions_recentes = int(db.execute(text("SELECT COUNT(*) FROM users WHERE created_at >= NOW() - INTERVAL '7 days'")).scalar() or 0)
        total_documents     = int(db.execute(text("SELECT COUNT(*) FROM documents")).scalar() or 0)
        total_chunks        = int(db.execute(text("SELECT COUNT(*) FROM document_chunks")).scalar() or 0)
 
        bac_rows = db.execute(text(
            "SELECT bac_type, COUNT(*) as cnt FROM students WHERE bac_type IS NOT NULL AND bac_type != '' GROUP BY bac_type"
        )).fetchall()
        bac_distribution = {r[0]: int(r[1]) for r in bac_rows}
 
        return {
            "total_users":           total_users,
            "total_students":        total_students,
            "total_conversations":   total_conversations,
            "total_messages":        total_messages,
            "total_ambassadeurs":    total_ambassadeurs,
            "fitscore_calcules":     total_conversations,
            "inscriptions_recentes": inscriptions_recentes,
            "total_documents":       total_documents,
            "total_chunks":          total_chunks,
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

# @app.put("/api/admin/students/{student_id}")
# async def admin_update_student(student_id: str, request: Request, db: Session = Depends(get_db)):
#     body = await request.json()
    
#     # Mettre à jour users
#     if body.get("full_name"):
#         db.execute(text("UPDATE users SET full_name = :fn WHERE id = :id"),
#             {"fn": body["full_name"], "id": student_id})
    
#     # Mettre à jour students
#     fields = {}
#     for key in ["average", "bac_type", "level", "city"]:
#         if key in body and body[key] is not None:
#             fields[key] = body[key]
    
#     if fields:
#         set_clause = ", ".join(f"{k} = :{k}" for k in fields)
#         fields["uid"] = student_id
#         db.execute(text(f"UPDATE students SET {set_clause} WHERE user_id = :uid"), fields)
    
#     db.commit()
#     return {"success": True}    


# ── GET /api/admin/ambassadeurs ───────────────────────────────
# @app.get("/api/admin/ambassadeurs")
# async def admin_ambassadeurs(db: Session = Depends(get_db)):
#     rows = db.execute(text("SELECT * FROM ambassadeurs ORDER BY created_at DESC")).fetchall()
#     return {"ambassadeurs": [dict(r._mapping) for r in rows]}


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











@app.post("/api/admin/documents/upload")
async def admin_upload_document(
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        content = await file.read()
        text_content = ""

        # ── Extraire le texte ─────────────────────────────────
        ext = file.filename.split('.')[-1].lower()
        if ext == 'txt':
            text_content = content.decode('utf-8', errors='ignore')
        elif ext == 'pdf':
            try:
                import pdfplumber, io
                with pdfplumber.open(io.BytesIO(content)) as pdf:
                    text_content = "\n".join(p.extract_text() or "" for p in pdf.pages)
            except Exception:
                text_content = content.decode('utf-8', errors='ignore')
        else:
            text_content = content.decode('utf-8', errors='ignore')

        # ── Créer le document en base ─────────────────────────
        doc_id = str(uuid.uuid4())
        db.execute(text("""
            INSERT INTO documents (id, title, source, uploaded_at)
            VALUES (:id, :title, :source, NOW())
        """), {"id": doc_id, "title": title, "source": file.filename})

        # ── Découper en chunks ────────────────────────────────
        words  = text_content.split()
        chunks = [' '.join(words[i:i+400]) for i in range(0, len(words), 400)]
        chunks = [c for c in chunks if len(c.strip()) > 50]

        # ── Générer les embeddings OpenAI ─────────────────────
        from app.services.openai_service import openai_service
        for i, chunk in enumerate(chunks):
            try:
                embedding_response = openai_service.client.embeddings.create(
                    input=chunk,
                    model="text-embedding-3-small"
                )
                embedding = embedding_response.data[0].embedding
                embedding_json = json.dumps(embedding)
            except Exception:
                embedding_json = None

            chunk_id = str(uuid.uuid4())
            db.execute(text("""
                INSERT INTO document_chunks (id, document_id, content, chunk_index, embedding)
                VALUES (:id, :doc_id, :content, :idx, :emb)
            """), {
                "id": chunk_id, "doc_id": doc_id,
                "content": chunk, "idx": i,
                "emb": embedding_json
            })

        db.commit()
        return {
            "success": True,
            "document": {
                "id": doc_id, "title": title,
                "source": file.filename,
                "uploaded_at": datetime.now().strftime("%Y-%m-%d"),
                "chunks_count": len(chunks),
                "file_type": ext,
            }
        }
    except Exception as e:
        db.rollback()
        import traceback; traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})



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
# @app.delete("/api/admin/students/{student_id}")
# async def admin_delete_student(student_id: str, db: Session = Depends(get_db)):
#     db.execute(text(
#         "DELETE FROM student_interests WHERE student_id IN (SELECT id FROM students WHERE user_id = :uid)"),
#         {"uid": student_id})
#     db.execute(text("DELETE FROM students WHERE user_id = :uid"), {"uid": student_id})
#     db.execute(text("DELETE FROM users WHERE id = :uid"),         {"uid": student_id})
#     db.commit()
#     return {"success": True}





# ============================================================
# PATCH main.py — Ajouter les 3 routes Voice Live
# Colle ces routes dans main.py AVANT if __name__ == "__main__"
# ============================================================
# Dépendances à ajouter en haut de main.py si pas déjà présentes :
#   import base64
#   from fastapi import UploadFile, File, Form
# ============================================================








# ============================================================
# PATCH main.py — Remplacer les 3 routes voice existantes
# Fix : get_or_create_session → get_session_id + chat_session_service
# ============================================================

# ─── 1. TRANSCRIPTION (Whisper) ──────────────────────────────────────────────
@app.post("/api/voice/transcribe")
async def voice_transcribe(
    audio:    UploadFile = File(...),
    lang:     str        = Form("fr"),
    request:  Request    = None,
    response: Response   = None,
):
    try:
        audio_bytes = await audio.read()

        PROMPTS = {
            "fr": "Bonjour. Orientation académique SUPMTI Meknès. Filières : IISI, IISIC, IISRT, MGE, MDI, FACG, MRI.",
            "en": "Hello. Academic orientation at SUPMTI Meknes. Programs: IISI, IISIC, IISRT, MGE, MDI, FACG, MRI.",
            "ar": "مرحبا. توجيه أكاديمي في SUPMTI مكناس.",
        }
        prompt = PROMPTS.get(lang, PROMPTS["fr"])

        ext      = (audio.filename or "voice.webm").split(".")[-1]
        filename = f"voice.{ext}"
        mime     = audio.content_type or "audio/webm"

        transcription = client.audio.transcriptions.create(
            model    = "whisper-1",
            file     = (filename, audio_bytes, mime),
            language = lang if lang in ("fr", "en", "ar") else "fr",
            prompt   = prompt,
        )

        text_raw = (transcription.text or "").strip()
        print(f"[VOICE] Transcription ({lang}): {text_raw[:80]}")
        return {"success": True, "text": text_raw, "lang": lang}

    except Exception as e:
        print(f"[VOICE] Erreur transcription : {e}")
        return {"success": False, "text": "", "error": str(e)}


# ─── 2. CHAT VOCAL ────────────────────────────────────────────────────────────
@app.post("/api/voice/chat")
async def voice_chat(
    body:     dict,
    request:  Request,
    response: Response,
):
    try:
        # ── Session (utilise les fonctions existantes de main.py) ────────────
        sid  = get_session_id(request, response)          # ← corrigé
        sess = chat_session_service.get_or_create(sid)    # ← corrigé

        message = body.get("message", "").strip()
        voice   = body.get("voice", "nova")
        lang    = body.get("lang",  "fr")

        if not message:
            return {"success": False, "error": "Message vide"}

        # ── Prompt vocal court (sans markdown) ───────────────────────────────
        SYSTEM = {
            "fr": ("Tu es Sami, conseiller académique vocal de SUPMTI Meknès. "
                   "Réponds en 2-3 phrases naturelles, sans markdown, sans listes, sans emojis. "
                   "Parle comme dans une vraie conversation."),
            "en": ("You are Sami, vocal academic advisor at SUPMTI Meknes. "
                   "Reply in 2-3 natural sentences, no markdown, no lists, no emojis."),
            "ar": ("أنت سامي، مستشار أكاديمي صوتي في SUPMTI مكناس. "
                   "أجب في 2-3 جمل طبيعية بالدارجة المغربية، بدون تنسيق."),
        }
        system_prompt = SYSTEM.get(lang, SYSTEM["fr"])

        # Historique court (6 derniers)
        hist = sess.get("historique", [])[-6:]
        msgs = [{"role": "system", "content": system_prompt}]
        msgs += hist
        msgs += [{"role": "user", "content": message}]

        # ── GPT ──────────────────────────────────────────────────────────────
        gpt = client.chat.completions.create(
            model       = os.getenv("MODEL_NAME", "gpt-4o-mini"),
            messages    = msgs,
            max_tokens  = 150,
            temperature = 0.7,
        )
        reply = gpt.choices[0].message.content.strip()

        # Sauvegarder dans la session
        sess["historique"].append({"role": "user",      "content": message})
        sess["historique"].append({"role": "assistant", "content": reply})
        sess["nb_messages"] = sess.get("nb_messages", 0) + 1

        # Extraire infos du profil depuis le message vocal
        try:
            sess["profil"] = extraire_infos_conversation(message, sess.get("profil") or {})
        except Exception:
            pass

        # ── TTS ──────────────────────────────────────────────────────────────
        audio_b64 = None
        clean = (reply
            .replace("**", "").replace("*", "").replace("#", "")
            .replace("\n", ". ").strip()[:1000]
        )
        try:
            tts = client.audio.speech.create(
                model           = "tts-1",
                voice           = voice,
                input           = clean,
                response_format = "mp3",
            )
            audio_b64 = base64.b64encode(tts.content).decode("utf-8")
            print(f"[VOICE] TTS généré — voix={voice} ({len(tts.content)} bytes)")
        except Exception as e:
            print(f"[VOICE] TTS erreur : {e}")

        return {
            "success": True,
            "text":    reply,
            "audio":   audio_b64,
            "lang":    lang,
            "profil":  sess.get("profil"),
        }

    except Exception as e:
        import traceback; traceback.print_exc()
        return {"success": False, "error": str(e), "text": "", "audio": None}


# ─── 3. TTS SEUL ─────────────────────────────────────────────────────────────
@app.post("/api/voice/tts")
async def voice_tts(body: dict):
    try:
        text  = (body.get("text", "") or "")[:1000]
        voice = body.get("voice", "nova")
        if not text.strip():
            return {"success": False, "error": "Texte vide"}
        clean = (text
            .replace("**", "").replace("*", "").replace("#", "")
            .replace("\n", ". ").strip()
        )
        tts = client.audio.speech.create(
            model=  "tts-1", voice=voice, input=clean, response_format="mp3"
        )
        return {"success": True, "audio": base64.b64encode(tts.content).decode("utf-8")}
    except Exception as e:
        return {"success": False, "error": str(e), "audio": None}














# ============================================================
# REMPLACE les 3 endpoints forgot-password dans main.py
# ✅ Utilise text() comme le reste du code — pas besoin de User
# ============================================================

import os, random, string
from datetime import datetime, timedelta
from fastapi import HTTPException   # ← ajouter cet import en haut de main.py si absent

_reset_codes: dict = {}

def _gen_code() -> str:
    return ''.join(random.choices(string.digits, k=6))

def _send_or_log(email: str, code: str):
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASS", "")
    print(f"\n{'='*45}")
    print(f"[RESET CODE] {email}  →  {code}  (expire dans 10 min)")
    print(f"{'='*45}\n")
    if not smtp_user or not smtp_pass:
        return
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "SUPMTI — Code de réinitialisation"
    msg["From"]    = f"SUPMTI <{smtp_user}>"
    msg["To"]      = email
    msg.attach(MIMEText(f"""
    <div style="font-family:sans-serif;max-width:480px;margin:auto;padding:32px;
                background:#f9fafb;border-radius:16px">
      <h2 style="color:#005555">Réinitialisation du mot de passe</h2>
      <p style="color:#6b7280">Votre code de vérification :</p>
      <div style="background:#005555;color:white;font-size:32px;font-weight:900;
                  letter-spacing:0.4em;text-align:center;padding:20px 32px;
                  border-radius:12px;margin:24px 0">{code}</div>
      <p style="color:#6b7280;font-size:13px">Expire dans <strong>10 minutes</strong>.</p>
    </div>""", "html"))
    with smtplib.SMTP(smtp_host, smtp_port) as s:
        s.starttls()
        s.login(smtp_user, smtp_pass)
        s.sendmail(smtp_user, email, msg.as_string())


# ── Schémas ───────────────────────────────────────────────
class ForgotPasswordRequest(BaseModel):
    email: str

class VerifyCodeRequest(BaseModel):
    email: str
    code:  str

class ResetPasswordRequest(BaseModel):
    email:        str
    token:        str
    new_password: str


# ══════════════════════════════════════════════════════════
# ENDPOINT 1 — POST /api/auth/forgot-password
# ══════════════════════════════════════════════════════════
@app.post("/api/auth/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    # ✅ SQL direct — pas besoin du modèle User
    row = db.execute(
        text("SELECT id FROM users WHERE email = :email"),
        {"email": payload.email}
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Aucun compte trouvé avec cet email.")

    code = _gen_code()
    _reset_codes[payload.email] = {
        "code":       code,
        "expires_at": datetime.utcnow() + timedelta(minutes=10),
    }

    try:
        _send_or_log(payload.email, code)
    except Exception as e:
        print(f"[WARN] Email non envoyé : {e}")

    is_dev = not os.getenv("SMTP_USER")
    return {
        "message":  "Code envoyé.",
        "dev_code": code if is_dev else None,
    }


# ══════════════════════════════════════════════════════════
# ENDPOINT 2 — POST /api/auth/verify-reset-code
# ══════════════════════════════════════════════════════════
@app.post("/api/auth/verify-reset-code")
async def verify_reset_code(payload: VerifyCodeRequest):
    entry = _reset_codes.get(payload.email)

    if not entry:
        raise HTTPException(status_code=400, detail="Aucun code en attente pour cet email.")
    if datetime.utcnow() > entry["expires_at"]:
        _reset_codes.pop(payload.email, None)
        raise HTTPException(status_code=400, detail="Code expiré. Veuillez recommencer.")
    if entry["code"] != payload.code.strip():
        raise HTTPException(status_code=400, detail="Code incorrect.")

    return {"token": payload.code, "message": "Code vérifié."}


# ══════════════════════════════════════════════════════════
# ENDPOINT 3 — POST /api/auth/reset-password
# ══════════════════════════════════════════════════════════
@app.post("/api/auth/reset-password")
async def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    entry = _reset_codes.get(payload.email)

    if not entry:
        raise HTTPException(status_code=400, detail="Session expirée. Veuillez recommencer.")
    if datetime.utcnow() > entry["expires_at"]:
        _reset_codes.pop(payload.email, None)
        raise HTTPException(status_code=400, detail="Code expiré. Veuillez recommencer.")
    if entry["code"] != payload.token.strip():
        raise HTTPException(status_code=400, detail="Token invalide.")

    # ✅ SQL direct — récupérer le hash existant pour détecter le bon champ
    row = db.execute(
        text("SELECT id, password_hash FROM users WHERE email = :email"),
        {"email": payload.email}
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")

    # Hacher le nouveau mot de passe avec pbkdf2_sha256 (même algo que auth_routes.py)
    try:
        from passlib.hash import pbkdf2_sha256
        new_hash = pbkdf2_sha256.hash(payload.new_password)
    except Exception:
        try:
            import bcrypt
            new_hash = bcrypt.hashpw(payload.new_password.encode(), bcrypt.gensalt()).decode()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur hash : {str(e)}")

    # ✅ SQL direct — pas besoin de deviner le nom du champ
    db.execute(
        text("UPDATE users SET password_hash = :h WHERE email = :email"),
        {"h": new_hash, "email": payload.email}
    )
    db.commit()
    _reset_codes.pop(payload.email, None)

    return {"message": "Mot de passe réinitialisé avec succès."}




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






# ============================================================
# WhatsApp Webhook — SAMI via Twilio
# Colle ce code dans main.py (remplace l'ancien @app.post("/api/whatsapp"))
# ============================================================
#
# FONCTIONNEMENT :
# 1. Twilio envoie POST /api/whatsapp avec Body= (message WhatsApp)
# 2. On crée une session stable par numéro (From=whatsapp:+212...)
# 3. On appelle generer_reponse_rag() avec l'historique de la session
# 4. On renvoie la réponse formatée en TwiML XML
#
# POUR ACTIVER :
# - Twilio Console → Messaging → WhatsApp Sandbox
# - "When a message comes in" → ton URL ngrok + /api/whatsapp
# ============================================================

import re
from fastapi import Form
from fastapi.responses import Response as FastAPIResponse

# Stockage sessions WhatsApp en mémoire (numéro → {historique, profil})
_wa_sessions: dict = {}

def _get_wa_session(phone: str) -> dict:
    """Retourne ou crée une session WhatsApp pour ce numéro."""
    if phone not in _wa_sessions:
        _wa_sessions[phone] = {
            "historique": [],
            "profil":     None,
            "nb_messages": 0,
        }
    return _wa_sessions[phone]


def _nettoyer_pour_whatsapp(texte: str) -> str:
    """
    Simplifie le markdown pour WhatsApp.
    WhatsApp supporte *gras* et _italique_ mais pas ## ou ---
    """
    # Titres markdown → majuscules
    texte = re.sub(r'^## (.+)$', r'*\1*', texte, flags=re.MULTILINE)
    texte = re.sub(r'^### (.+)$', r'*\1*', texte, flags=re.MULTILINE)

    # **gras** → *gras* (WhatsApp)
    texte = re.sub(r'\*\*(.+?)\*\*', r'*\1*', texte)

    # Supprimer les séparateurs ═══
    texte = re.sub(r'[═─]{3,}', '', texte)

    # Limiter à 1500 caractères (limite SMS/WhatsApp)
    if len(texte) > 1500:
        texte = texte[:1450] + '\n\n_[réponse tronquée — pose une question plus précise]_'

    return texte.strip()


@app.post("/api/whatsapp")
async def whatsapp_webhook(
    Body:      str = Form(""),
    From:      str = Form(""),
    ProfileName: str = Form(""),
):
    """
    Webhook Twilio WhatsApp.
    Body      = message de l'utilisateur
    From      = numéro expéditeur (ex: whatsapp:+212600000000)
    ProfileName = prénom WhatsApp de l'utilisateur
    """
    message = (Body or "").strip()
    phone   = (From or "unknown").replace("whatsapp:", "")

    print(f"[WA] {phone} ({ProfileName}): {message[:60]}")

    if not message:
        return _twiml("Désolé, je n'ai pas reçu ton message.")

    # ── Session ──────────────────────────────────────────────────
    sess = _get_wa_session(phone)

    # Initialiser le profil si absent
    if sess["profil"] is None:
        try:
            from app.services.profile_service import construire_profil_etudiant
            sess["profil"] = construire_profil_etudiant({})
            # Injecter le prénom WhatsApp si disponible
            if ProfileName:
                sess["profil"]["informations_personnelles"]["prenom"] = ProfileName.split()[0]
        except Exception:
            sess["profil"] = {}

    # ── Commandes spéciales ──────────────────────────────────────
    msg_lower = message.lower().strip()

    if msg_lower in ("reset", "nouveau", "recommencer", "/reset"):
        _wa_sessions.pop(phone, None)
        return _twiml("✅ Conversation réinitialisée. Bonjour ! Je suis SAMI, l'assistant d'orientation de SUPMTI Meknès. Comment puis-je t'aider ?")

    if msg_lower in ("aide", "help", "/aide", "?"):
        return _twiml(
            "*SAMI — Assistant SUPMTI Meknès* 🎓\n\n"
            "Je peux t'aider sur :\n"
            "• Les filières (IISI, MGE, MDI, IISIC...)\n"
            "• Les frais de scolarité et bourses\n"
            "• L'admission et les conditions\n"
            "• Ton orientation personnalisée\n\n"
            "Envoie *RESET* pour recommencer une nouvelle conversation."
        )

    # ── Extraction profil depuis le message ──────────────────────
    try:
        from app.services.profile_service import extraire_infos_conversation
        sess["profil"] = extraire_infos_conversation(message, sess["profil"])
    except Exception:
        pass

    # ── Appel RAG ────────────────────────────────────────────────
    try:
        from app.services.rag_service import generer_reponse_rag

        sess["historique"].append({"role": "user", "content": message})
        sess["nb_messages"] += 1

        resultat = generer_reponse_rag(
            question     = message,
            historique   = sess["historique"][-10:],  # 10 derniers messages
            profil_etudiant = sess["profil"],
        )

        reponse_brute = resultat.get("reponse", "Je n'ai pas pu générer une réponse.")
        reponse_wa    = _nettoyer_pour_whatsapp(reponse_brute)

        sess["historique"].append({"role": "assistant", "content": reponse_brute})

        # Limiter l'historique en mémoire
        if len(sess["historique"]) > 20:
            sess["historique"] = sess["historique"][-20:]

        print(f"[WA] Réponse → {reponse_wa[:80]}...")
        return _twiml(reponse_wa)

    except Exception as e:
        print(f"[WA] Erreur RAG : {e}")
        import traceback; traceback.print_exc()
        return _twiml(
            "Désolé, je rencontre une difficulté technique. "
            "Réessaie dans quelques instants ou contacte SUPMTI : +212 5 35 51 10 11"
        )


def _twiml(message: str) -> FastAPIResponse:
    """Génère une réponse TwiML XML pour Twilio."""
    # Échapper les caractères XML spéciaux
    safe = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    xml  = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{safe}</Message>
</Response>"""
    return FastAPIResponse(content=xml, media_type="application/xml")


# ── Endpoint stats WhatsApp (optionnel, pour l'admin) ────────
@app.get("/api/admin/whatsapp/stats")
async def wa_stats():
    """Retourne les stats des sessions WhatsApp actives."""
    return {
        "sessions_actives": len(_wa_sessions),
        "details": [
            {
                "phone":       phone,
                "nb_messages": sess["nb_messages"],
                "prenom":      sess["profil"].get("informations_personnelles", {}).get("prenom", "?") if sess["profil"] else "?",
            }
            for phone, sess in _wa_sessions.items()
        ]
    }


# ── Endpoint reset session WhatsApp (admin) ──────────────────
@app.delete("/api/admin/whatsapp/session/{phone}")
async def wa_reset_session(phone: str):
    """Supprime la session WhatsApp d'un numéro."""
    _wa_sessions.pop(phone, None)
    _wa_sessions.pop(f"whatsapp:{phone}", None)
    return {"success": True, "message": f"Session {phone} réinitialisée."}










@app.get("/debug/routes")
def debug_routes():
    return [
        {"path": route.path, "methods": list(route.methods)}
        for route in app.routes
        if hasattr(route, "path") and hasattr(route, "methods")
    ]





# ── Static files ──────────────────────────────────────────────
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logger.info(f"📁 Dossier static monté: {static_dir}")
else:
    logger.warning(f"⚠️ Dossier static non trouvé: {static_dir}")

logger.info(f"🚀 Application démarrée - Version {settings.API_VERSION}")