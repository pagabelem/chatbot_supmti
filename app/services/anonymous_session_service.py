# ============================================================
# app/services/anonymous_session_service.py
# ============================================================

import uuid
import json
from datetime import datetime
from typing   import Optional
from sqlalchemy import text


class AnonymousSessionService:

    def sauvegarder_message_anonyme(
        self,
        session_id: str,
        conv_id:    str,
        sess:       dict,
        db,
        ip_address: Optional[str] = None,
    ) -> None:
        if not db or not session_id:
            return

        try:
            # ── 1. Créer la conversation si elle n'existe pas ───────
            existing = db.execute(
                text("SELECT id FROM anonymous_conversations WHERE id = :cid"),
                {"cid": conv_id}
            ).fetchone()

            profil_json = _extraire_profil_simplifie(sess.get("profil"))
            langue      = _detecter_langue(sess)

            if not existing:
                # Fix : cast ::jsonb via CAST() au lieu de :param::jsonb
                db.execute(text("""
                    INSERT INTO anonymous_conversations
                        (id, session_id, started_at, profil_extrait, ip_address, langue)
                    VALUES
                        (:id, :sid, NOW(), CAST(:profil AS jsonb), :ip, :lang)
                """), {
                    "id":     conv_id,
                    "sid":    session_id,
                    "profil": profil_json,
                    "ip":     ip_address or "",
                    "lang":   langue,
                })
                db.commit()
                sess["conv_db_creee"] = True

            else:
                # Mettre à jour le profil extrait
                db.execute(text("""
                    UPDATE anonymous_conversations
                    SET profil_extrait = CAST(:profil AS jsonb)
                    WHERE id = :cid
                """), {
                    "profil": profil_json,
                    "cid":    conv_id,
                })

            # ── 2. Insérer seulement les nouveaux messages ──────────
            existing_count = db.execute(
                text("SELECT COUNT(*) FROM anonymous_messages WHERE conversation_id = :cid"),
                {"cid": conv_id}
            ).scalar() or 0

            nouveaux = sess["historique"][existing_count:]
            for msg in nouveaux:
                db.execute(text("""
                    INSERT INTO anonymous_messages
                        (id, conversation_id, content, sender, created_at)
                    VALUES
                        (gen_random_uuid(), :cid, :content, :sender, NOW())
                """), {
                    "cid":     conv_id,
                    "content": msg.get("content", ""),
                    "sender":  msg.get("role", "user"),
                })

            if nouveaux:
                db.commit()
                print(
                    f"[ANON] ✅ {len(nouveaux)} msg(s) — "
                    f"conv {conv_id[:8]}… (session {session_id[:12]}…)"
                )

        except Exception as e:
            print(f"[ANON] ❌ Erreur sauvegarde anonyme : {e}")
            try:
                db.rollback()
            except Exception:
                pass

    def get_conversations_admin(self, db, limit: int = 200, offset: int = 0) -> list:
        try:
            rows = db.execute(text("""
                SELECT
                    ac.id,
                    ac.session_id,
                    ac.started_at,
                    ac.profil_extrait,
                    ac.ip_address,
                    ac.langue,
                    COUNT(am.id)                                          AS nb_messages,
                    MIN(CASE WHEN am.sender = 'user' THEN am.content END) AS premier_message
                FROM anonymous_conversations ac
                LEFT JOIN anonymous_messages am ON am.conversation_id = ac.id
                GROUP BY ac.id, ac.session_id, ac.started_at,
                         ac.profil_extrait, ac.ip_address, ac.langue
                HAVING COUNT(am.id) > 0
                ORDER BY ac.started_at DESC
                LIMIT :limit OFFSET :offset
            """), {"limit": limit, "offset": offset}).fetchall()

            result = []
            for r in rows:
                profil  = r.profil_extrait or {}
                premier = r.premier_message or ""
                titre   = (premier[:60] + "…") if len(premier) > 60 else premier

                result.append({
                    "id":          str(r.id),
                    "session_id":  (r.session_id or "")[:16] + "…",
                    "started_at":  r.started_at.strftime("%d/%m/%Y %H:%M") if r.started_at else "",
                    "nb_messages": int(r.nb_messages or 0),
                    "titre":       titre or "Conversation anonyme",
                    "langue":      r.langue or "fr",
                    "ip_address":  r.ip_address or "",
                    "prenom":      profil.get("prenom", "—"),
                    "bac":         profil.get("bac",    "—"),
                    "moyenne":     profil.get("moyenne", "—"),
                    "niveau":      profil.get("niveau", "—"),
                    "interets":    profil.get("interets", []),
                    "est_anonyme": True,
                })

            return result

        except Exception as e:
            print(f"[ANON] ❌ get_conversations_admin error: {e}")
            return []

    def get_messages_par_id(self, conv_id: str, db) -> list:
        try:
            rows = db.execute(text("""
                SELECT sender, content, created_at
                FROM anonymous_messages
                WHERE conversation_id = :cid
                ORDER BY created_at ASC
            """), {"cid": conv_id}).fetchall()

            return [
                {
                    "role":       r.sender,
                    "content":    r.content,
                    "created_at": r.created_at.strftime("%H:%M") if r.created_at else "",
                }
                for r in rows
            ]
        except Exception as e:
            print(f"[ANON] ❌ get_messages_par_id error: {e}")
            return []

    def compter_total(self, db) -> int:
        try:
            return db.execute(text("""
                SELECT COUNT(DISTINCT ac.id)
                FROM anonymous_conversations ac
                JOIN anonymous_messages am ON am.conversation_id = ac.id
            """)).scalar() or 0
        except Exception:
            return 0


# ── Helpers ───────────────────────────────────────────────────

def _extraire_profil_simplifie(profil: Optional[dict]) -> str:
    """Retourne un JSON string du profil simplifié."""
    if not profil:
        return "{}"

    parc = profil.get("parcours_academique", {})
    info = profil.get("informations_personnelles", {})
    pref = profil.get("preferences", {})

    simplifie: dict = {}

    prenom = info.get("prenom", "")
    if prenom and prenom != "Étudiant":
        simplifie["prenom"] = prenom

    bac = parc.get("type_bac", "")
    if bac and bac != "AUTRE":
        simplifie["bac"] = bac

    moyenne = parc.get("moyenne_generale", 0)
    if moyenne and float(moyenne) > 0:
        simplifie["moyenne"] = float(moyenne)

    niveau = parc.get("niveau_actuel", "")
    if niveau:
        simplifie["niveau"] = niveau

    interets = pref.get("centres_interet", [])
    if interets:
        simplifie["interets"] = interets[:5]

    ambition = pref.get("ambition_professionnelle", "")
    if ambition:
        simplifie["ambition"] = ambition[:100]

    ville = info.get("ville", "")
    if ville:
        simplifie["ville"] = ville

    pays = info.get("pays", "")
    if pays and pays != "Maroc":
        simplifie["pays"] = pays

    return json.dumps(simplifie, ensure_ascii=False)


def _detecter_langue(sess: dict) -> str:
    historique = sess.get("historique", [])
    if not historique:
        return "fr"
    for msg in historique[:3]:
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if any('\u0600' <= c <= '\u06FF' for c in content):
                return "ar"
            en_words = ["what", "how", "tell me", "i want", "hello", "hi ", "can you"]
            if any(w in content.lower() for w in en_words):
                return "en"
    return "fr"


# ── Singleton ─────────────────────────────────────────────────
anonymous_session_service = AnonymousSessionService()