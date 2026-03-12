"""
chat_session_service.py
=======================
Service dédié à la gestion des sessions de chat et de l'historique
des conversations pour SUPMTI SAMI.

Usage dans main.py :
    from app.services.chat_session_service import ChatSessionService
    service = ChatSessionService()
"""

import uuid
from datetime import datetime
from typing import Optional


# ════════════════════════════════════════════════════════════════
# STOCKAGE EN MÉMOIRE (remplaçable par Redis / DB sans changer l'API)
# ════════════════════════════════════════════════════════════════

_sessions:    dict = {}   # sid → session_data
_historiques: dict = {}   # sid → [ chat_snapshot, ... ]


# ════════════════════════════════════════════════════════════════
# MODÈLE D'UNE SESSION VIDE
# ════════════════════════════════════════════════════════════════

def _session_vide() -> dict:
    """Retourne une session fraîche avec tous les champs attendus."""
    return {
        # Profil étudiant extrait par le RAG
        "profil":               None,

        # Services complémentaires
        "suivi_coach":          None,
        "fitscore":             None,

        # Test psychométrique
        "etat_test_psycho":     None,
        "test_psycho_en_cours": False,

        # Messages de la conversation courante
        "historique":           [],
        "nb_messages":          0,

        # PeerMatch
        "peer_match_declenche": False,

        # Métadonnées du chat courant
        "chat_actuel_id":    str(uuid.uuid4()),
        "chat_actuel_titre": "Nouvelle conversation",
        "debut": datetime.now().strftime("%d/%m/%Y %H:%M"),
    }


# ════════════════════════════════════════════════════════════════
# CLASSE SERVICE
# ════════════════════════════════════════════════════════════════

class ChatSessionService:
    """
    Centralise toutes les opérations sur les sessions :
    - création / récupération
    - nouveau chat (archivage + reset)
    - chargement d'un chat passé
    - liste de l'historique
    """

    # ── Récupération / création ──────────────────────────────────

    def get_or_create(self, sid: str) -> dict:
        """Retourne la session existante ou en crée une nouvelle."""
        if sid not in _sessions:
            _sessions[sid] = _session_vide()
        return _sessions[sid]

    def get_session(self, sid: str) -> Optional[dict]:
        """Retourne la session ou None si elle n'existe pas."""
        return _sessions.get(sid)

    # ── Auto-titre ───────────────────────────────────────────────

    def auto_titre(self, sess: dict, premier_message: str) -> None:
        """Génère le titre à partir du 1er message si pas encore fait."""
        if sess["nb_messages"] == 0:
            titre = premier_message.strip()
            sess["chat_actuel_titre"] = (titre[:45] + "…") if len(titre) > 45 else titre

    # ── Nouveau chat ─────────────────────────────────────────────

    def nouveau_chat(self, sid: str) -> dict:
        """
        Archive la conversation courante (si non vide)
        puis crée une session fraîche.

        Retourne un dict de réponse pour l'endpoint /api/new_chat.
        """
        sess = self.get_or_create(sid)

        # ── 1. Archiver si la conversation contient des messages ──
        if sess["nb_messages"] > 0:
            self._archiver_conversation(sid, sess)

        # ── 2. Créer une session fraîche (conserver le profil si souhaité) ──
        nouvelle_sess = _session_vide()

        # Option : conserver le profil entre les conversations
        # (décommente la ligne suivante si tu veux)
        # nouvelle_sess["profil"] = sess.get("profil")

        _sessions[sid] = nouvelle_sess

        return {
            "success":       True,
            "message":       "Nouvelle conversation créée",
            "nouveau_id":    nouvelle_sess["chat_actuel_id"],
            "nb_historique": len(_historiques.get(sid, [])),
        }

    # ── Historique ───────────────────────────────────────────────

    def get_historique_liste(self, sid: str) -> list:
        """
        Retourne la liste des conversations archivées
        + la conversation courante si elle a des messages,
        triées du plus récent au plus ancien.
        """
        archivees = list(_historiques.get(sid, []))

        # Ajouter la conversation courante si elle a des messages
        sess = _sessions.get(sid)
        if sess and sess["nb_messages"] > 0:
            courante = {
                "id":          sess["chat_actuel_id"],
                "titre":       sess["chat_actuel_titre"],
                "date":        sess.get("debut", "Aujourd'hui"),
                "nb_messages": sess["nb_messages"],
                "en_cours":    True,
            }
            archivees = archivees + [courante]

        # Plus récente en premier
        return list(reversed(archivees))

    def get_chat_par_id(self, sid: str, chat_id: str) -> Optional[dict]:
        """
        Retourne les messages d'une conversation archivée.
        Vérifie aussi si c'est la conversation courante.
        """
        sess = _sessions.get(sid)

        # Vérifier si c'est la conversation courante
        if sess and sess["chat_actuel_id"] == chat_id:
            return {
                "id":          sess["chat_actuel_id"],
                "titre":       sess["chat_actuel_titre"],
                "date":        sess.get("debut", "Aujourd'hui"),
                "nb_messages": sess["nb_messages"],
                "messages":    list(sess["historique"]),
                "en_cours":    True,
            }

        # Chercher dans l'historique archivé
        chats = _historiques.get(sid, [])
        chat  = next((c for c in chats if c["id"] == chat_id), None)
        return chat

    def charger_chat(self, sid: str, chat_id: str) -> dict:
        """
        Charge une conversation passée comme conversation active.
        Archive d'abord la conversation courante si elle a des messages.
        """
        sess = self.get_or_create(sid)

        # Récupérer le chat à charger
        chat = self.get_chat_par_id(sid, chat_id)
        if not chat:
            return {"success": False, "error": "Conversation non trouvée"}

        # Si c'est déjà la conversation courante, ne rien faire
        if chat.get("en_cours"):
            return {
                "success":   True,
                "messages":  chat["messages"],
                "titre":     chat["titre"],
                "chat_id":   chat_id,
                "en_cours":  True,
            }

        # Archiver la conversation courante si elle a des messages
        if sess["nb_messages"] > 0:
            self._archiver_conversation(sid, sess)

        # Restaurer l'ancienne conversation comme session courante
        nouvelle_sess = _session_vide()
        nouvelle_sess["chat_actuel_id"]    = chat["id"]
        nouvelle_sess["chat_actuel_titre"] = chat["titre"]
        nouvelle_sess["debut"]             = chat["date"]
        nouvelle_sess["historique"]        = list(chat.get("messages", []))
        nouvelle_sess["nb_messages"]       = chat["nb_messages"]
        # Restaurer le profil si disponible dans le snapshot
        if chat.get("profil"):
            nouvelle_sess["profil"] = chat["profil"]

        _sessions[sid] = nouvelle_sess

        return {
            "success":   True,
            "messages":  nouvelle_sess["historique"],
            "titre":     nouvelle_sess["chat_actuel_titre"],
            "chat_id":   chat_id,
            "en_cours":  False,
        }

    def supprimer_chat(self, sid: str, chat_id: str) -> dict:
        """Supprime une conversation archivée de l'historique."""
        if sid not in _historiques:
            return {"success": False, "error": "Aucun historique"}

        avant = len(_historiques[sid])
        _historiques[sid] = [c for c in _historiques[sid] if c["id"] != chat_id]
        apres = len(_historiques[sid])

        if avant == apres:
            return {"success": False, "error": "Conversation non trouvée"}
        return {"success": True, "message": "Conversation supprimée"}

    def reset_complet(self, sid: str) -> dict:
        """Supprime toute la session et l'historique (logout / reset)."""
        _sessions.pop(sid, None)
        _historiques.pop(sid, None)
        return {"success": True, "message": "Session réinitialisée"}

    # ── Interne ──────────────────────────────────────────────────

    def _archiver_conversation(self, sid: str, sess: dict) -> None:
        """Archive la session courante dans l'historique du sid."""
        if sid not in _historiques:
            _historiques[sid] = []

        snapshot = {
            "id":          sess["chat_actuel_id"],
            "titre":       sess["chat_actuel_titre"],
            "date":        sess.get("debut", datetime.now().strftime("%d/%m/%Y %H:%M")),
            "nb_messages": sess["nb_messages"],
            "messages":    list(sess["historique"]),
            # Conserver le profil pour restauration future
            "profil":      sess.get("profil"),
        }
        _historiques[sid].append(snapshot)


# ── Instance singleton ────────────────────────────────────────
chat_session_service = ChatSessionService()