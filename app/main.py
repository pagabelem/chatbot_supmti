# ============================================================
# FASTAPI — SUPMTI Chatbot
# Toutes les routes sur http://127.0.0.1:8000
# ============================================================

import os
import uuid
from datetime import datetime
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="SUPMTI Smart Orientation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Import des services ──────────────────────────────────────
from app.services.chat_session_service import chat_session_service   # ← UNIQUE store
from app.services.openai_service import openai_service
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
from app.services.fit_score_service import (
    calculer_fitscore_complet,
    generer_rapport_fitscore,
)
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
from app.academic_config import FILIERES

# ============================================================
# COOKIE
# ============================================================

COOKIE_NAME = "supmti_sid"

def get_session_id(request: Request, response: Response) -> str:
    sid = request.cookies.get(COOKIE_NAME)
    if not sid:
        sid = str(uuid.uuid4())
    response.set_cookie(
        key=COOKIE_NAME,
        value=sid,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
    )
    return sid

# ============================================================
# DÉMARRAGE RAG
# ============================================================

print("🚀 Démarrage du système RAG...")
demarrer_rag()
print("✅ Système prêt !")

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


# ============================================================
# HELPER CHAT — utilise UNIQUEMENT chat_session_service
# ============================================================

async def _process_chat(user_message: str, request: Request, response: Response) -> dict:
    sid  = get_session_id(request, response)
    sess = chat_session_service.get_or_create(sid)          # ← service unique

    if sess["profil"] is None:
        sess["profil"] = construire_profil_etudiant({})

    sess["profil"] = extraire_infos_conversation(user_message, sess["profil"])

    if sess["profil"].get("statut_profil") == "complet" and sess["suivi_coach"] is None:
        sess["suivi_coach"] = initialiser_suivi_coach(sess["profil"])

    # Auto-titre depuis le 1er message
    chat_session_service.auto_titre(sess, user_message)     # ← délégué au service

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

    return {
        "response":   reponse_finale,   # compatibilité ancienne
        "reponse":    reponse_finale,   # champ principal frontend
        "profil":     sess["profil"],
        "peer_match": peer_match_info,
    }


# ============================================================
# ROUTES
# ============================================================

@app.get("/")
def read_root():
    return {"message": "API SUPMTI SAMI — port 8000"}

@app.post("/chat")
async def chat_endpoint(body: ChatRequest, request: Request, response: Response):
    return await _process_chat(body.user_message, request, response)

@app.post("/api/chat")
async def api_chat(body: ChatV2Request, request: Request, response: Response):
    return await _process_chat(body.message, request, response)


# ── GET /api/session ──────────────────────────────────────────
@app.get("/api/session")
async def get_session(request: Request, response: Response):
    sid  = get_session_id(request, response)
    sess = chat_session_service.get_or_create(sid)
    return {
        "session_id":           sid,
        "profil":               sess["profil"],
        "fitscore":             sess["fitscore"],
        "test_psycho_en_cours": sess["test_psycho_en_cours"],
        "historique_chats":     chat_session_service.get_historique_liste(sid),
        "chat_actuel_id":       sess["chat_actuel_id"],
        "chat_actuel_titre":    sess["chat_actuel_titre"],
        "nb_messages":          sess["nb_messages"],
    }


# ── POST /api/new_chat ────────────────────────────────────────
@app.post("/api/new_chat")
async def new_chat(request: Request, response: Response):
    sid = get_session_id(request, response)
    return chat_session_service.nouveau_chat(sid)


# ── GET /api/historique/{chat_id} — charger les messages ──────
@app.get("/api/historique/{chat_id}")
async def get_historique_chat(chat_id: str, request: Request, response: Response):
    sid  = get_session_id(request, response)
    chat = chat_session_service.get_chat_par_id(sid, chat_id)
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
async def delete_historique_chat(chat_id: str, request: Request, response: Response):
    sid = get_session_id(request, response)
    return chat_session_service.supprimer_chat(sid, chat_id)


# ── POST /api/fitscore ────────────────────────────────────────
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
    return {"rapport": rapport, "classement": result.get("classement", []), "meilleure_filiere": result.get("meilleure_filiere"), "profil": sess["profil"]}


# ── POST /api/admission ───────────────────────────────────────
@app.post("/api/admission")
async def admission(request: Request, response: Response):
    sid  = get_session_id(request, response)
    sess = chat_session_service.get_or_create(sid)
    if not sess["profil"]:
        return JSONResponse(status_code=400, content={"error": True, "message": "Dis-moi ton BAC et ta moyenne d'abord !"})
    rapport = generer_rapport_admission(sess["profil"], sess["fitscore"])
    return {"rapport": rapport, "profil": sess["profil"]}


# ── POST /api/carriere ────────────────────────────────────────
@app.post("/api/carriere")
async def carriere(body: CarriereRequest, request: Request, response: Response):
    sid  = get_session_id(request, response)
    sess = chat_session_service.get_or_create(sid)
    if not sess["profil"]:
        sess["profil"] = construire_profil_etudiant({})
    filiere_id = (body.filiere_id or "").upper()
    if not filiere_id:
        info = obtenir_filieres_comparables(sess["profil"])
        return {"filieres_disponibles": info["filieres_accessibles"], "explication": info["explication"], "annee_entree": info["annee_entree"]}
    simulation = simuler_carriere(sess["profil"], filiere_id)
    return {"scenario": simulation["scenario"], "filiere_nom": simulation["filiere_nom"], "donnees_cles": simulation["donnees_cles"]}


# ── POST /api/comparer ────────────────────────────────────────
@app.post("/api/comparer")
async def comparer(body: ComparerRequest, request: Request, response: Response):
    sid  = get_session_id(request, response)
    sess = chat_session_service.get_or_create(sid)
    if not sess["profil"]:
        return JSONResponse(status_code=400, content={"error": True, "message": "Dis-moi ton profil d'abord !"})
    return comparer_carrieres_intelligent(sess["profil"], (body.filiere_1 or "").upper() or None, (body.filiere_2 or "").upper() or None)


# ── POST /api/psycho/start ────────────────────────────────────
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


# ── POST /api/psycho/answer ───────────────────────────────────
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
        return {"complete": True, "rapport": rapport, "scores": profil_psycho["scores"], "points_forts": profil_psycho["points_forts"]}
    return {"complete": False, "message": msg, "question_actuelle": nouvel_etat["question_actuelle"], "total_questions": 10}


# ── POST /api/coach ───────────────────────────────────────────
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


# ── GET /api/profil ───────────────────────────────────────────
@app.get("/api/profil")
async def get_profil(request: Request, response: Response):
    sid  = get_session_id(request, response)
    sess = chat_session_service.get_or_create(sid)
    return {"profil": sess["profil"]}


# ── GET /api/filieres ─────────────────────────────────────────
@app.get("/api/filieres")
def get_filieres():
    return {"filieres": [
        {"id": fid, "nom": f["nom"], "niveau": f["niveau"], "duree": f["duree"], "description": f.get("description", "")}
        for fid, f in FILIERES.items()
    ]}


# ── POST /api/reset ───────────────────────────────────────────
@app.post("/api/reset")
async def reset_session(request: Request, response: Response):
    sid = get_session_id(request, response)
    return chat_session_service.reset_complet(sid)