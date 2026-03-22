"""
chat_session_service.py
========================
- 1 conversation = 1 entrée DB persistée tout au long du chat
- _sauvegarder_messages() : upsert en continu à chaque message
- _archiver_conversation() : appelé seulement au nouveau_chat()
- get_historique_liste()   : lit depuis DB, groupé par conversation
"""

import uuid
from datetime import datetime
from typing   import Optional
from sqlalchemy import text


_sessions: dict = {}


def _session_vide() -> dict:
    return {
        "profil":               None,
        "suivi_coach":          None,
        "fitscore":             None,
        "etat_test_psycho":     None,
        "test_psycho_en_cours": False,
        "historique":           [],
        "nb_messages":          0,
        "peer_match_declenche": False,
        "chat_actuel_id":       str(uuid.uuid4()),
        "chat_actuel_titre":    "Nouvelle conversation",
        "debut":                datetime.now().strftime("%d/%m/%Y %H:%M"),
        "profil_db_charge":     False,
        "conv_db_creee":        False,   # flag : conversation insérée en DB
    }


class ChatSessionService:

    def get_or_create(self, sid: str) -> dict:
        if sid not in _sessions:
            _sessions[sid] = _session_vide()
        return _sessions[sid]

    def get_session(self, sid: str) -> Optional[dict]:
        return _sessions.get(sid)

    def auto_titre(self, sess: dict, premier_message: str) -> None:
        if sess["nb_messages"] == 0:
            titre = premier_message.strip()
            sess["chat_actuel_titre"] = (titre[:45] + "…") if len(titre) > 45 else titre

    # ── Nouveau chat ─────────────────────────────────────────────

    def nouveau_chat(self, sid: str, db=None, user_id: str = None) -> dict:
        sess = self.get_or_create(sid)

        # Finaliser la conversation courante si elle a des messages
        if sess["nb_messages"] > 0 and db and user_id:
            self._sauvegarder_messages(sid, sess, db=db, user_id=user_id)

        nouvelle_sess = _session_vide()
        nouvelle_sess["profil"]           = sess.get("profil")
        nouvelle_sess["profil_db_charge"] = sess.get("profil_db_charge", False)
        _sessions[sid] = nouvelle_sess

        return {
            "success":    True,
            "message":    "Nouvelle conversation créée",
            "nouveau_id": nouvelle_sess["chat_actuel_id"],
        }

    # ── Historique ───────────────────────────────────────────────

    def get_historique_liste(self, sid: str, db=None, user_id: str = None) -> list:
        archivees = []

        if db and user_id:
            try:
                student_row = db.execute(
                    text("SELECT id FROM students WHERE user_id = :uid"),
                    {"uid": user_id}
                ).fetchone()

                if student_row:
                    rows = db.execute(text("""
                        SELECT
                            c.id,
                            c.started_at,
                            COUNT(m.id)  AS nb_msg,
                            MIN(CASE WHEN m.sender = 'user' THEN m.content END) AS premier_msg
                        FROM conversations c
                        LEFT JOIN messages m ON m.conversation_id = c.id
                        WHERE c.student_id = :sid
                        GROUP BY c.id, c.started_at
                        HAVING COUNT(m.id) > 0
                        ORDER BY c.started_at DESC
                        LIMIT 50
                    """), {"sid": str(student_row.id)}).fetchall()

                    for r in rows:
                        titre = "Conversation"
                        if r.premier_msg:
                            t = r.premier_msg
                            titre = t[:47] + "…" if len(t) > 47 else t

                        archivees.append({
                            "id":          str(r.id),
                            "titre":       titre,
                            "date":        r.started_at.strftime("%d/%m/%Y %H:%M") if r.started_at else "",
                            "nb_messages": int(r.nb_msg or 0),
                            "en_cours":    False,
                        })

            except Exception as e:
                print(f"[WARN] get_historique_liste DB error: {e}")

        # Ajouter la conversation courante en RAM si elle a des messages
        sess = _sessions.get(sid)
        if sess and sess["nb_messages"] > 0:
            ids_db = {c["id"] for c in archivees}
            if sess["chat_actuel_id"] not in ids_db:
                archivees.insert(0, {
                    "id":          sess["chat_actuel_id"],
                    "titre":       sess["chat_actuel_titre"],
                    "date":        sess.get("debut", "Aujourd'hui"),
                    "nb_messages": sess["nb_messages"],
                    "en_cours":    True,
                })
            else:
                # Mettre à jour le statut en_cours
                for c in archivees:
                    if c["id"] == sess["chat_actuel_id"]:
                        c["en_cours"] = True
                        break

        return archivees

    def get_chat_par_id(self, sid: str, chat_id: str, db=None) -> Optional[dict]:
        sess = _sessions.get(sid)

        # Conversation courante en RAM
        if sess and sess["chat_actuel_id"] == chat_id:
            return {
                "id":          sess["chat_actuel_id"],
                "titre":       sess["chat_actuel_titre"],
                "date":        sess.get("debut", "Aujourd'hui"),
                "nb_messages": sess["nb_messages"],
                "messages":    list(sess["historique"]),
                "en_cours":    True,
            }

        # Chercher en DB
        if db:
            try:
                conv = db.execute(
                    text("SELECT id, started_at FROM conversations WHERE id = :cid"),
                    {"cid": chat_id}
                ).fetchone()

                if conv:
                    msgs = db.execute(text("""
                        SELECT sender, content
                        FROM messages
                        WHERE conversation_id = :cid
                        ORDER BY created_at ASC
                    """), {"cid": chat_id}).fetchall()

                    msgs_list = [{"role": m.sender, "content": m.content} for m in msgs]

                    titre = "Conversation"
                    user_msgs = [m for m in msgs_list if m["role"] == "user"]
                    if user_msgs:
                        t = user_msgs[0]["content"]
                        titre = t[:47] + "…" if len(t) > 47 else t

                    return {
                        "id":          str(conv.id),
                        "titre":       titre,
                        "date":        conv.started_at.strftime("%d/%m/%Y %H:%M") if conv.started_at else "",
                        "nb_messages": len(msgs_list),
                        "messages":    msgs_list,
                        "en_cours":    False,
                    }
            except Exception as e:
                print(f"[WARN] get_chat_par_id DB error: {e}")

        return None

    def supprimer_chat(self, sid: str, chat_id: str, db=None) -> dict:
        if db:
            try:
                db.execute(text("DELETE FROM messages     WHERE conversation_id = :cid"), {"cid": chat_id})
                db.execute(text("DELETE FROM conversations WHERE id = :cid"),             {"cid": chat_id})
                db.commit()
            except Exception as e:
                print(f"[WARN] supprimer_chat DB error: {e}")
        return {"success": True, "message": "Conversation supprimée"}

    def reset_complet(self, sid: str, db=None, user_id: str = None) -> dict:
        _sessions.pop(sid, None)
        return {"success": True, "message": "Session réinitialisée"}

    # ── Sauvegarde continue (appelée à chaque message) ───────────

    def _sauvegarder_messages(self, sid: str, sess: dict, db=None, user_id: str = None) -> None:
        """
        Crée la conversation en DB si elle n'existe pas encore,
        puis insère uniquement les nouveaux messages.
        1 conversation = 1 entrée, mise à jour en continu.
        """
        if not db or not user_id:
            return

        conv_id = sess["chat_actuel_id"]

        try:
            # Récupérer student_id
            student_row = db.execute(
                text("SELECT id FROM students WHERE user_id = :uid"),
                {"uid": user_id}
            ).fetchone()

            if not student_row:
                print(f"[WARN] Pas de student pour user_id={user_id}")
                return

            student_id = str(student_row.id)

            # Créer la conversation si elle n'existe pas encore
            if not sess.get("conv_db_creee"):
                existing = db.execute(
                    text("SELECT id FROM conversations WHERE id = :cid"),
                    {"cid": conv_id}
                ).fetchone()

                if not existing:
                    db.execute(text("""
                        INSERT INTO conversations (id, student_id, started_at)
                        VALUES (:id, :sid, NOW())
                    """), {"id": conv_id, "sid": student_id})
                    db.commit()

                sess["conv_db_creee"] = True

            # Compter les messages déjà en DB pour cette conversation
            existing_count = db.execute(
                text("SELECT COUNT(*) FROM messages WHERE conversation_id = :cid"),
                {"cid": conv_id}
            ).scalar() or 0

            # Insérer seulement les nouveaux messages
            nouveaux = sess["historique"][existing_count:]
            for msg in nouveaux:
                db.execute(text("""
                    INSERT INTO messages (id, conversation_id, content, sender, created_at)
                    VALUES (gen_random_uuid(), :cid, :content, :sender, NOW())
                """), {
                    "cid":     conv_id,
                    "content": msg.get("content", ""),
                    "sender":  msg.get("role", "user"),
                })

            if nouveaux:
                db.commit()
                print(f"[DB] ✅ {len(nouveaux)} nouveau(x) message(s) sauvegardé(s) — conv {conv_id[:8]}… ({sess['nb_messages']} total)")

        except Exception as e:
            print(f"[WARN] _sauvegarder_messages error: {e}")
            try:
                db.rollback()
            except Exception:
                pass

    # Alias pour compatibilité avec main.py
    _archiver_conversation = _sauvegarder_messages


# ── Instance singleton ────────────────────────────────────────
chat_session_service = ChatSessionService()