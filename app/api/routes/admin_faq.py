# app/api/routes/admin_faq.py
"""
Routes back office — Questions sans réponse (FAQ manquante).
IMPORTANT : les routes fixes (/stats, /export) DOIVENT être déclarées
AVANT les routes avec paramètre (/{question_id}) pour éviter que FastAPI
n'interprète "stats" ou "export" comme un question_id.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import Response as FastAPIResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database.connection import get_db
from app.services.faq_service import (
    get_questions_sans_reponse,
    get_stats_faq,
    ajouter_reponse_admin,
    ignorer_question,
    supprimer_question,
)

router = APIRouter(
    prefix="/api/admin/faq",
    tags=["FAQ manquante"]
)


# ── Schémas ──────────────────────────────────────────────────
class ReponseAdminPayload(BaseModel):
    reponse:      str
    injecter_rag: bool = True


# ════════════════════════════════════════════════════════════
# ROUTES FIXES — déclarées EN PREMIER (avant /{question_id})
# ════════════════════════════════════════════════════════════

# ── GET /api/admin/faq/stats ──────────────────────────────────
@router.get("/stats", summary="Statistiques FAQ manquante")
def stats_faq(db: Session = Depends(get_db)):
    """
    Retourne :
    - total questions loggées
    - non traitées / traitées
    - top 5 des questions les plus posées
    """
    return get_stats_faq(db)


# ── GET /api/admin/faq/export ─────────────────────────────────
@router.get("/export", summary="Exporter les questions sans réponse en CSV")
def exporter_csv(db: Session = Depends(get_db)):
    """
    Télécharge un fichier CSV avec toutes les questions non traitées.
    """
    questions = get_questions_sans_reponse(db, statut="non_traitee", limit=1000)

    lines = ["Question,Nombre de fois posée,Langue,Première vue,Dernière vue"]
    for q in questions:
        lines.append(",".join([
            f'"{q["question"].replace(chr(34), chr(39))}"',
            str(q["nb_fois"]),
            q["langue"],
            q["premiere_vue"],
            q["derniere_vue"],
        ]))

    return FastAPIResponse(
        content="\n".join(lines),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=faq_manquante_supmti.csv"}
    )


# ── GET /api/admin/faq ────────────────────────────────────────
@router.get("", summary="Lister les questions sans réponse")
def lister_questions(
    statut: Optional[str] = Query(
        None,
        description="Filtrer par statut : non_traitee | reponse_ajoutee | ignoree"
    ),
    limit:  int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    db:     Session = Depends(get_db),
):
    """
    Retourne toutes les questions pour lesquelles SAMI a répondu
    "Je n'ai pas cette information précise".
    Triées par nb_fois DESC.
    """
    return {
        "questions":      get_questions_sans_reponse(db, statut=statut, limit=limit, offset=offset),
        "statut_filtre":  statut or "tous",
    }


# ════════════════════════════════════════════════════════════
# ROUTES AVEC PARAMÈTRE — déclarées EN DERNIER
# ════════════════════════════════════════════════════════════

# ── POST /api/admin/faq/{id}/reponse ─────────────────────────
@router.post("/{question_id}/reponse", summary="Ajouter une réponse + injecter dans la RAG")
def ajouter_reponse(
    question_id: str,
    body:        ReponseAdminPayload,
    db:          Session = Depends(get_db),
):
    """
    L'admin rédige la réponse manquante.
    Si injecter_rag=true : crée Document + Chunk, écrit dans faq_admin.txt,
    invalide le cache → SAMI utilise immédiatement cette nouvelle information.
    """
    if not body.reponse or len(body.reponse.strip()) < 10:
        raise HTTPException(status_code=400, detail="La réponse est trop courte (min 10 caractères).")

    return ajouter_reponse_admin(
        db           = db,
        question_id  = question_id,
        reponse      = body.reponse,
        injecter_rag = body.injecter_rag,
    )


# ── PATCH /api/admin/faq/{id}/ignorer ────────────────────────
@router.patch("/{question_id}/ignorer", summary="Ignorer une question")
def ignorer(question_id: str, db: Session = Depends(get_db)):
    """Marque la question comme ignorée (hors périmètre)."""
    return ignorer_question(db, question_id)


# ── PATCH /api/admin/faq/{id}/reouvrir ───────────────────────
@router.patch("/{question_id}/reouvrir", summary="Rouvrir une question ignorée")
def reouvrir(question_id: str, db: Session = Depends(get_db)):
    """Remet le statut à 'non_traitee' pour réévaluation."""
    from sqlalchemy import text
    try:
        db.execute(
            text("UPDATE questions_sans_reponse SET statut = 'non_traitee' WHERE id = :id"),
            {"id": question_id}
        )
        db.commit()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── DELETE /api/admin/faq/{id} ────────────────────────────────
@router.delete("/{question_id}", summary="Supprimer une question")
def supprimer(question_id: str, db: Session = Depends(get_db)):
    """Supprime définitivement l'entrée."""
    return supprimer_question(db, question_id)