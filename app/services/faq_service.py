# # app/services/faq_service.py
# """
# Service FAQ — Questions sans réponse.

# Responsabilités :
#   1. Détecter si une réponse SAMI est un "fallback" (info manquante)
#   2. Logger la question en base sans bloquer le chat
#   3. Regrouper les questions similaires (deduplication par hash)
#   4. Injecter la réponse admin dans la base RAG (Documents + Chunks)
# """

# import os
# import re
# import uuid
# import hashlib
# from datetime import datetime
# from sqlalchemy import text
# from sqlalchemy.orm import Session


# # ── Phrases de fallback à détecter ───────────────────────────
# # Corresponds exactement à ce que SAMI retourne quand il ne sait pas.
# _FALLBACK_PHRASES = [
#     "je n'ai pas cette information précise",
#     "je n'ai pas cette information",
#     "contacte supmti",
#     "contacter supmti",
#     "je ne dispose pas de cette information",
#     "cette information n'est pas disponible",
#     "i don't have this information",
#     "ما عنديش هاد المعلومة",
#     "مش عارف هاد الشي",
# ]

# # Questions à ignorer (trop courtes, salutations, etc.)
# _MIN_QUESTION_LENGTH = 10


# def est_fallback(reponse: str) -> bool:
#     """
#     Retourne True si la réponse contient une phrase de fallback.
#     Insensible à la casse et aux accents.
#     """
#     if not reponse:
#         return False
#     reponse_lower = reponse.lower()
#     return any(phrase in reponse_lower for phrase in _FALLBACK_PHRASES)


# def _normaliser_question(question: str) -> str:
#     """Normalise la question pour la déduplication."""
#     q = question.lower().strip()
#     q = re.sub(r'\s+', ' ', q)
#     q = re.sub(r'[?!.,;:]+$', '', q)
#     return q


# def _hash_question(question: str) -> str:
#     """Hash MD5 court pour regrouper les questions similaires."""
#     normalise = _normaliser_question(question)
#     # Tronquer pour que des variantes proches aient le même hash
#     # (on prend les 60 premiers chars après normalisation)
#     cle = normalise[:60]
#     return hashlib.md5(cle.encode("utf-8")).hexdigest()[:16]


# def logguer_question_sans_reponse(
#     db: Session,
#     question: str,
#     session_id: str = None,
#     langue: str = "fr",
# ) -> None:
#     """
#     Enregistre la question en base.
#     - Si une question similaire existe déjà → incrémente nb_fois
#     - Sinon → crée une nouvelle entrée
#     Appel silencieux : ne lève jamais d'exception.
#     """
#     if not question or len(question.strip()) < _MIN_QUESTION_LENGTH:
#         return

#     try:
#         q_hash = _hash_question(question)

#         # Chercher une entrée existante avec le même hash
#         existing = db.execute(
#             text("""
#                 SELECT id, nb_fois FROM questions_sans_reponse
#                 WHERE question_hash = :h AND statut = 'non_traitee'
#                 LIMIT 1
#             """),
#             {"h": q_hash}
#         ).fetchone()

#         if existing:
#             # Incrémenter le compteur
#             db.execute(
#                 text("""
#                     UPDATE questions_sans_reponse
#                     SET nb_fois      = nb_fois + 1,
#                         derniere_vue = NOW()
#                     WHERE id = :id
#                 """),
#                 {"id": str(existing.id)}
#             )
#         else:
#             # Nouvelle question
#             db.execute(
#                 text("""
#                     INSERT INTO questions_sans_reponse
#                         (id, question, session_id, langue, nb_fois,
#                          premiere_vue, derniere_vue, statut, question_hash)
#                     VALUES
#                         (:id, :q, :sid, :lang, 1,
#                          NOW(), NOW(), 'non_traitee', :hash)
#                 """),
#                 {
#                     "id":   str(uuid.uuid4()),
#                     "q":    question.strip()[:1000],
#                     "sid":  (session_id or "")[:255],
#                     "lang": langue[:10],
#                     "hash": q_hash,
#                 }
#             )

#         db.commit()
#         print(f"[FAQ] ✅ Question sans réponse loggée : {question[:60]}…")

#     except Exception as e:
#         print(f"[FAQ] ⚠️ Impossible de logger la question : {e}")
#         try:
#             db.rollback()
#         except Exception:
#             pass


# def get_questions_sans_reponse(
#     db: Session,
#     statut: str = None,
#     limit:  int = 100,
#     offset: int = 0,
# ) -> list:
#     """
#     Récupère les questions sans réponse pour le back office.
#     Triées par nb_fois DESC (les plus demandées en premier).
#     """
#     where = "WHERE 1=1"
#     params: dict = {"limit": limit, "offset": offset}

#     if statut:
#         where += " AND statut = :statut"
#         params["statut"] = statut

#     rows = db.execute(
#         text(f"""
#             SELECT id, question, langue, nb_fois, statut,
#                    reponse_admin, premiere_vue, derniere_vue
#             FROM questions_sans_reponse
#             {where}
#             ORDER BY nb_fois DESC, derniere_vue DESC
#             LIMIT :limit OFFSET :offset
#         """),
#         params
#     ).fetchall()

#     return [
#         {
#             "id":            str(r.id),
#             "question":      r.question,
#             "langue":        r.langue,
#             "nb_fois":       r.nb_fois,
#             "statut":        r.statut,
#             "reponse_admin": r.reponse_admin,
#             "premiere_vue":  r.premiere_vue.strftime("%d/%m/%Y %H:%M") if r.premiere_vue else "",
#             "derniere_vue":  r.derniere_vue.strftime("%d/%m/%Y %H:%M") if r.derniere_vue else "",
#         }
#         for r in rows
#     ]


# def get_stats_faq(db: Session) -> dict:
#     """Statistiques rapides pour le dashboard admin."""
#     try:
#         total     = db.execute(text("SELECT COUNT(*) FROM questions_sans_reponse")).scalar() or 0
#         non_trait = db.execute(text("SELECT COUNT(*) FROM questions_sans_reponse WHERE statut = 'non_traitee'")).scalar() or 0
#         traitees  = db.execute(text("SELECT COUNT(*) FROM questions_sans_reponse WHERE statut = 'reponse_ajoutee'")).scalar() or 0
#         top5      = db.execute(text("""
#             SELECT question, nb_fois FROM questions_sans_reponse
#             ORDER BY nb_fois DESC LIMIT 5
#         """)).fetchall()
#         return {
#             "total":             int(total),
#             "non_traitees":      int(non_trait),
#             "traitees":          int(traitees),
#             "top5_questions":    [{"question": r.question[:80], "nb_fois": r.nb_fois} for r in top5],
#         }
#     except Exception as e:
#         print(f"[FAQ] get_stats_faq error: {e}")
#         return {"total": 0, "non_traitees": 0, "traitees": 0, "top5_questions": []}


# def ajouter_reponse_admin(
#     db:           Session,
#     question_id:  str,
#     reponse:      str,
#     injecter_rag: bool = True,
# ) -> dict:
#     """
#     Enregistre la réponse de l'admin et l'injecte dans la base RAG.

#     Si injecter_rag=True :
#       - Crée un nouveau Document "FAQ — <question>"
#       - Crée le DocumentChunk correspondant
#       - Met à jour le statut → 'reponse_ajoutee'
#       - Invalide le cache hardcode pour que la prochaine requête
#         utilise la nouvelle info
#     """
#     try:
#         # Récupérer la question
#         row = db.execute(
#             text("SELECT question, langue FROM questions_sans_reponse WHERE id = :id"),
#             {"id": question_id}
#         ).fetchone()

#         if not row:
#             return {"success": False, "error": "Question introuvable"}

#         question = row.question
#         langue   = row.langue or "fr"

#         # Mettre à jour le statut et la réponse
#         db.execute(
#             text("""
#                 UPDATE questions_sans_reponse
#                 SET reponse_admin = :rep, statut = 'reponse_ajoutee',
#                     derniere_vue  = NOW()
#                 WHERE id = :id
#             """),
#             {"rep": reponse.strip(), "id": question_id}
#         )

#         doc_id    = None
#         chunk_id  = None

#         if injecter_rag:
#             # ── Créer le document RAG ─────────────────────────────
#             doc_id    = str(uuid.uuid4())
#             titre_doc = f"FAQ — {question[:80]}"
#             contenu   = f"Question fréquente : {question}\n\nRéponse : {reponse}"

#             db.execute(
#                 text("""
#                     INSERT INTO documents (id, title, source, uploaded_at)
#                     VALUES (:id, :title, 'FAQ Admin', NOW())
#                 """),
#                 {"id": doc_id, "title": titre_doc}
#             )

#             # ── Créer le chunk ────────────────────────────────────
#             chunk_id = str(uuid.uuid4())
#             db.execute(
#                 text("""
#                     INSERT INTO document_chunks
#                         (id, document_id, content, embedding, created_at)
#                     VALUES (:id, :doc_id, :content, NULL, NOW())
#                 """),
#                 {"id": chunk_id, "doc_id": doc_id, "content": contenu}
#             )

#             # ── Aussi écrire dans un fichier .txt pour le RAG FAISS ──
#             _ecrire_faq_dans_fichier(question, reponse)

#         db.commit()

#         # ── Invalider le cache hardcode ───────────────────────────
#         if injecter_rag:
#             _invalider_cache_rag()

#         return {
#             "success":   True,
#             "doc_id":    doc_id,
#             "chunk_id":  chunk_id,
#             "rag_injecte": injecter_rag,
#             "message":   "Réponse enregistrée" + (" et injectée dans la RAG." if injecter_rag else "."),
#         }

#     except Exception as e:
#         print(f"[FAQ] ajouter_reponse_admin error: {e}")
#         try:
#             db.rollback()
#         except Exception:
#             pass
#         return {"success": False, "error": str(e)}


# def ignorer_question(db: Session, question_id: str) -> dict:
#     """Marque une question comme ignorée (hors périmètre)."""
#     try:
#         db.execute(
#             text("""
#                 UPDATE questions_sans_reponse
#                 SET statut = 'ignoree', derniere_vue = NOW()
#                 WHERE id = :id
#             """),
#             {"id": question_id}
#         )
#         db.commit()
#         return {"success": True}
#     except Exception as e:
#         return {"success": False, "error": str(e)}


# def supprimer_question(db: Session, question_id: str) -> dict:
#     """Supprime définitivement une entrée."""
#     try:
#         db.execute(
#             text("DELETE FROM questions_sans_reponse WHERE id = :id"),
#             {"id": question_id}
#         )
#         db.commit()
#         return {"success": True}
#     except Exception as e:
#         return {"success": False, "error": str(e)}


# # ── Helpers internes ─────────────────────────────────────────

# def _ecrire_faq_dans_fichier(question: str, reponse: str) -> None:
#     """
#     Ajoute la paire Q/R dans ./data/documents/faq_admin.txt
#     pour que le prochain rebuild FAISS intègre ces infos.
#     """
#     try:
#         documents_path = os.getenv("DOCUMENTS_PATH", "./data/documents")
#         os.makedirs(documents_path, exist_ok=True)
#         chemin = os.path.join(documents_path, "faq_admin.txt")

#         entree = (
#             f"\n\n=== FAQ ADMIN — {datetime.now().strftime('%d/%m/%Y')} ===\n"
#             f"Question : {question}\n"
#             f"Réponse : {reponse}\n"
#         )

#         with open(chemin, "a", encoding="utf-8") as f:
#             f.write(entree)

#         print(f"[FAQ] ✅ Réponse écrite dans {chemin}")
#     except Exception as e:
#         print(f"[FAQ] ⚠️ Impossible d'écrire dans faq_admin.txt : {e}")


# def _invalider_cache_rag() -> None:
#     """
#     Invalide le cache mémoire du RAG service pour forcer
#     la prise en compte immédiate de la nouvelle FAQ.
#     """
#     try:
#         from app.services import rag_service
#         rag_service._HARDCODE_CACHE = None
#         rag_service.construire_prompt_systeme.cache_clear()
#         print("[FAQ] ✅ Cache RAG invalidé — prochaine requête rechargera les données.")
#     except Exception as e:
#         print(f"[FAQ] ⚠️ Impossible d'invalider le cache RAG : {e}")



# app/services/faq_service.py
"""
Service FAQ — Questions sans réponse.

Responsabilités :
  1. Détecter si une réponse SAMI est un "fallback" (info manquante)
  2. Logger la question en base sans bloquer le chat
  3. Regrouper les questions similaires (deduplication par hash)
  4. Injecter la réponse admin dans la base RAG (Documents + Chunks)
"""

import os
import re
import uuid
import hashlib
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session


# ── Phrases de fallback à détecter ───────────────────────────
# Corresponds exactement à ce que SAMI retourne quand il ne sait pas.
_FALLBACK_PHRASES = [
    "je n'ai pas cette information précise",
    "je n'ai pas cette information",
    # "contacte supmti",  # ← SUPPRIMÉ - bug: trop large
    # "contacter supmti", # ← SUPPRIMÉ - bug: trop large
    "je ne dispose pas de cette information",
    "cette information n'est pas disponible",
    "i don't have this information",
    "ما عنديش هاد المعلومة",
    "مش عارف هاد الشي",
]

# Questions à ignorer (trop courtes, salutations, etc.)
_MIN_QUESTION_LENGTH = 10


def est_fallback(reponse: str) -> bool:
    """
    Retourne True si la réponse contient une phrase de fallback.
    Insensible à la casse et aux accents.
    """
    if not reponse:
        return False
    reponse_lower = reponse.lower()
    return any(phrase in reponse_lower for phrase in _FALLBACK_PHRASES)


def _normaliser_question(question: str) -> str:
    """Normalise la question pour la déduplication."""
    q = question.lower().strip()
    q = re.sub(r'\s+', ' ', q)
    q = re.sub(r'[?!.,;:]+$', '', q)
    return q


def _hash_question(question: str) -> str:
    """Hash MD5 court pour regrouper les questions similaires."""
    normalise = _normaliser_question(question)
    # Tronquer pour que des variantes proches aient le même hash
    # (on prend les 60 premiers chars après normalisation)
    cle = normalise[:60]
    return hashlib.md5(cle.encode("utf-8")).hexdigest()[:16]


def logguer_question_sans_reponse(
    db: Session,
    question: str,
    session_id: str = None,
    langue: str = "fr",
    reponse_sami: str = None,  # ← NOUVEAU paramètre
) -> None:
    """
    Enregistre la question en base UNIQUEMENT si c'est une vraie question sans réponse.
    - Si une question similaire existe déjà → incrémente nb_fois
    - Sinon → crée une nouvelle entrée
    Appel silencieux : ne lève jamais d'exception.
    
    MAIN CHANGE: On ne logge que si reponse_sami est un fallback
    """
    # ← NOUVEAU FILTRE : ne logger que si c'est un vrai fallback
    if reponse_sami is not None and not est_fallback(reponse_sami):
        print(f"[FAQ] ℹ️ Question avec réponse trouvée, pas de log : {question[:60]}…")
        return
    
    if not question or len(question.strip()) < _MIN_QUESTION_LENGTH:
        return

    try:
        q_hash = _hash_question(question)

        # Chercher une entrée existante avec le même hash
        existing = db.execute(
            text("""
                SELECT id, nb_fois FROM questions_sans_reponse
                WHERE question_hash = :h AND statut = 'non_traitee'
                LIMIT 1
            """),
            {"h": q_hash}
        ).fetchone()

        if existing:
            # Incrémenter le compteur
            db.execute(
                text("""
                    UPDATE questions_sans_reponse
                    SET nb_fois      = nb_fois + 1,
                        derniere_vue = NOW()
                    WHERE id = :id
                """),
                {"id": str(existing.id)}
            )
        else:
            # Nouvelle question
            db.execute(
                text("""
                    INSERT INTO questions_sans_reponse
                        (id, question, session_id, langue, nb_fois,
                         premiere_vue, derniere_vue, statut, question_hash)
                    VALUES
                        (:id, :q, :sid, :lang, 1,
                         NOW(), NOW(), 'non_traitee', :hash)
                """),
                {
                    "id":   str(uuid.uuid4()),
                    "q":    question.strip()[:1000],
                    "sid":  (session_id or "")[:255],
                    "lang": langue[:10],
                    "hash": q_hash,
                }
            )

        db.commit()
        print(f"[FAQ] ✅ Question sans réponse loggée : {question[:60]}…")

    except Exception as e:
        print(f"[FAQ] ⚠️ Impossible de logger la question : {e}")
        try:
            db.rollback()
        except Exception:
            pass


def get_questions_sans_reponse(
    db: Session,
    statut: str = None,
    limit:  int = 100,
    offset: int = 0,
) -> list:
    """
    Récupère les questions sans réponse pour le back office.
    Triées par nb_fois DESC (les plus demandées en premier).
    """
    where = "WHERE 1=1"
    params: dict = {"limit": limit, "offset": offset}

    if statut:
        where += " AND statut = :statut"
        params["statut"] = statut

    rows = db.execute(
        text(f"""
            SELECT id, question, langue, nb_fois, statut,
                   reponse_admin, premiere_vue, derniere_vue
            FROM questions_sans_reponse
            {where}
            ORDER BY nb_fois DESC, derniere_vue DESC
            LIMIT :limit OFFSET :offset
        """),
        params
    ).fetchall()

    return [
        {
            "id":            str(r.id),
            "question":      r.question,
            "langue":        r.langue,
            "nb_fois":       r.nb_fois,
            "statut":        r.statut,
            "reponse_admin": r.reponse_admin,
            "premiere_vue":  r.premiere_vue.strftime("%d/%m/%Y %H:%M") if r.premiere_vue else "",
            "derniere_vue":  r.derniere_vue.strftime("%d/%m/%Y %H:%M") if r.derniere_vue else "",
        }
        for r in rows
    ]


def get_stats_faq(db: Session) -> dict:
    """Statistiques rapides pour le dashboard admin."""
    try:
        total     = db.execute(text("SELECT COUNT(*) FROM questions_sans_reponse")).scalar() or 0
        non_trait = db.execute(text("SELECT COUNT(*) FROM questions_sans_reponse WHERE statut = 'non_traitee'")).scalar() or 0
        traitees  = db.execute(text("SELECT COUNT(*) FROM questions_sans_reponse WHERE statut = 'reponse_ajoutee'")).scalar() or 0
        top5      = db.execute(text("""
            SELECT question, nb_fois FROM questions_sans_reponse
            ORDER BY nb_fois DESC LIMIT 5
        """)).fetchall()
        return {
            "total":             int(total),
            "non_traitees":      int(non_trait),
            "traitees":          int(traitees),
            "top5_questions":    [{"question": r.question[:80], "nb_fois": r.nb_fois} for r in top5],
        }
    except Exception as e:
        print(f"[FAQ] get_stats_faq error: {e}")
        return {"total": 0, "non_traitees": 0, "traitees": 0, "top5_questions": []}


def ajouter_reponse_admin(
    db:           Session,
    question_id:  str,
    reponse:      str,
    injecter_rag: bool = True,
) -> dict:
    """
    Enregistre la réponse de l'admin et l'injecte dans la base RAG.

    Si injecter_rag=True :
      - Crée un nouveau Document "FAQ — <question>"
      - Crée le DocumentChunk correspondant
      - Met à jour le statut → 'reponse_ajoutee'
      - Invalide le cache hardcode pour que la prochaine requête
        utilise la nouvelle info
    """
    try:
        # Récupérer la question
        row = db.execute(
            text("SELECT question, langue FROM questions_sans_reponse WHERE id = :id"),
            {"id": question_id}
        ).fetchone()

        if not row:
            return {"success": False, "error": "Question introuvable"}

        question = row.question
        langue   = row.langue or "fr"

        # Mettre à jour le statut et la réponse
        db.execute(
            text("""
                UPDATE questions_sans_reponse
                SET reponse_admin = :rep, statut = 'reponse_ajoutee',
                    derniere_vue  = NOW()
                WHERE id = :id
            """),
            {"rep": reponse.strip(), "id": question_id}
        )

        doc_id    = None
        chunk_id  = None

        if injecter_rag:
            # ── Créer le document RAG ─────────────────────────────
            doc_id    = str(uuid.uuid4())
            titre_doc = f"FAQ — {question[:80]}"
            contenu   = f"Question fréquente : {question}\n\nRéponse : {reponse}"

            db.execute(
                text("""
                    INSERT INTO documents (id, title, source, uploaded_at)
                    VALUES (:id, :title, 'FAQ Admin', NOW())
                """),
                {"id": doc_id, "title": titre_doc}
            )

            # ── Créer le chunk ────────────────────────────────────
            chunk_id = str(uuid.uuid4())
            db.execute(
                text("""
                    INSERT INTO document_chunks
                        (id, document_id, content, embedding, created_at)
                    VALUES (:id, :doc_id, :content, NULL, NOW())
                """),
                {"id": chunk_id, "doc_id": doc_id, "content": contenu}
            )

            # ── Aussi écrire dans un fichier .txt pour le RAG FAISS ──
            _ecrire_faq_dans_fichier(question, reponse)

        db.commit()

        # ── Invalider le cache hardcode ───────────────────────────
        if injecter_rag:
            _invalider_cache_rag()

        return {
            "success":   True,
            "doc_id":    doc_id,
            "chunk_id":  chunk_id,
            "rag_injecte": injecter_rag,
            "message":   "Réponse enregistrée" + (" et injectée dans la RAG." if injecter_rag else "."),
        }

    except Exception as e:
        print(f"[FAQ] ajouter_reponse_admin error: {e}")
        try:
            db.rollback()
        except Exception:
            pass
        return {"success": False, "error": str(e)}


def ignorer_question(db: Session, question_id: str) -> dict:
    """Marque une question comme ignorée (hors périmètre)."""
    try:
        db.execute(
            text("""
                UPDATE questions_sans_reponse
                SET statut = 'ignoree', derniere_vue = NOW()
                WHERE id = :id
            """),
            {"id": question_id}
        )
        db.commit()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def supprimer_question(db: Session, question_id: str) -> dict:
    """Supprime définitivement une entrée."""
    try:
        db.execute(
            text("DELETE FROM questions_sans_reponse WHERE id = :id"),
            {"id": question_id}
        )
        db.commit()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Helpers internes ─────────────────────────────────────────

def _ecrire_faq_dans_fichier(question: str, reponse: str) -> None:
    """
    Ajoute la paire Q/R dans ./data/documents/faq_admin.txt
    pour que le prochain rebuild FAISS intègre ces infos.
    """
    try:
        documents_path = os.getenv("DOCUMENTS_PATH", "./data/documents")
        os.makedirs(documents_path, exist_ok=True)
        chemin = os.path.join(documents_path, "faq_admin.txt")

        entree = (
            f"\n\n=== FAQ ADMIN — {datetime.now().strftime('%d/%m/%Y')} ===\n"
            f"Question : {question}\n"
            f"Réponse : {reponse}\n"
        )

        with open(chemin, "a", encoding="utf-8") as f:
            f.write(entree)

        print(f"[FAQ] ✅ Réponse écrite dans {chemin}")
    except Exception as e:
        print(f"[FAQ] ⚠️ Impossible d'écrire dans faq_admin.txt : {e}")


def _invalider_cache_rag() -> None:
    """
    Invalide le cache mémoire du RAG service pour forcer
    la prise en compte immédiate de la nouvelle FAQ.
    """
    try:
        from app.services import rag_service
        rag_service._HARDCODE_CACHE = None
        rag_service.construire_prompt_systeme.cache_clear()
        print("[FAQ] ✅ Cache RAG invalidé — prochaine requête rechargera les données.")
    except Exception as e:
        print(f"[FAQ] ⚠️ Impossible d'invalider le cache RAG : {e}")

