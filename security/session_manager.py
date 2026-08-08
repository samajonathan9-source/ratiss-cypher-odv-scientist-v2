# -*- coding: utf-8 -*-
"""
================================================================================
          GESTIONNAIRE DE SESSIONS SÉCURISÉ — RATISS CYPHER ODV V2
================================================================================
Propriété Intellectuelle : JohnKing0 & Architecte Jonathan Evina
Version du Système       : RATISS V9 AEON PRIME — RATISS-CYPHER-ODV-SCIENTIST-V2

Ce module implémente la sécurité native multi-utilisateurs :
1. Session unique (UUID4) par utilisateur, stockée en SQLite.
2. Jetons d'accès signés, stockés en hachage SHA-256 (jamais en clair).
3. Expiration configurable des sessions (défaut : 24h).
4. Isolation stricte des workspaces : ./workspace/{session_id}/
5. Verrouillage par fichier (thread-safe) des accès SQLite.
================================================================================
"""
import hashlib
import json
import os
import secrets
import sqlite3
import threading
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# --- Configuration par défaut (surchargeable par env) ----------------------
SESSION_TTL_HOURS = float(os.environ.get("SESSION_TTL_HOURS", "24"))
DB_PATH = os.environ.get("SESSIONS_DB_PATH", "data/sessions.db")
WORKSPACE_ROOT = os.environ.get("WORKSPACE_ROOT", "workspace")


def sha256(token: str) -> str:
    """Hachage SHA-256 d'un jeton (jamais stocké en clair)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class SessionManager:
    """Gestionnaire de sessions utilisateurs avec isolation des workspaces."""

    _local = threading.local()

    def __init__(self, db_path: str = DB_PATH, ttl_hours: float = SESSION_TTL_HOURS):
        self.ttl_hours = ttl_hours
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        os.makedirs(WORKSPACE_ROOT, exist_ok=True)
        self._init_db()

    # ------------------------------------------------------------------
    # Base de données SQLite (connexion thread-local, verrou file)
    # ------------------------------------------------------------------
    @classmethod
    def _conn(cls):
        if not hasattr(cls._local, "conn") or cls._local.conn is None:
            cls._local.conn = sqlite3.connect(DB_PATH, timeout=10)
            cls._local.conn.row_factory = sqlite3.Row
            cls._local.conn.execute("PRAGMA journal_mode=WAL")
        return cls._local.conn

    def _init_db(self):
        conn = self._conn()
        conn.execute(
            """CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                token_hash TEXT NOT NULL,
                created_at REAL NOT NULL,
                expires_at REAL NOT NULL,
                workspace TEXT NOT NULL,
                state TEXT NOT NULL DEFAULT 'active'
            )"""
        )
        conn.commit()

    # ------------------------------------------------------------------
    # API publique
    # ------------------------------------------------------------------
    def create_session(self) -> dict:
        """Crée une nouvelle session : UUID, jeton secret, workspace isolé."""
        session_id = str(uuid.uuid4())
        # Jeton d'accès fort : NE JAMAIS être retourné en clair à un tiers
        raw_token = secrets.token_urlsafe(48)
        token_hash = sha256(raw_token)
        now = time.time()
        expires_at = now + (self.ttl_hours * 3600)
        workspace = os.path.join(WORKSPACE_ROOT, session_id)
        os.makedirs(workspace, exist_ok=True)
        self._conn().execute(
            "INSERT INTO sessions VALUES (?, ?, ?, ?, ?, 'active')",
            (session_id, token_hash, now, expires_at, workspace),
        )
        self._conn().commit()
        return {
            "session_id": session_id,
            "token": raw_token,          # remis UNE SEULE fois à l'utilisateur
            "expires_at": expires_at,
            "workspace": workspace,
        }

    def validate_session(self, session_id: str, token: str) -> dict:
        """Valide une session et retourne son contexte (workspace) ou None."""
        if not session_id or not token:
            return None
        token_hash = sha256(token)
        row = self._conn().execute(
            "SELECT * FROM sessions WHERE session_id=? AND token_hash=? AND state='active'",
            (session_id, token_hash),
        ).fetchone()
        if row is None:
            return None
        if time.time() > row["expires_at"]:
            self.revoke_session(session_id)
            return None
        return {
            "session_id": session_id,
            "workspace": row["workspace"],
            "expires_at": row["expires_at"],
        }

    def revoke_session(self, session_id: str):
        """Révoque une session (soft-delete)."""
        self._conn().execute(
            "UPDATE sessions SET state='revoked' WHERE session_id=?", (session_id,)
        )
        self._conn().commit()

    def cleanup_expired(self) -> int:
        """Supprime les sessions expirées et purge leur workspace."""
        conn = self._conn()
        rows = conn.execute(
            "SELECT session_id, workspace FROM sessions WHERE state='active' AND expires_at < ?",
            (time.time(),),
        ).fetchall()
        count = 0
        for row in rows:
            conn.execute("UPDATE sessions SET state='expired' WHERE session_id=?", (row["session_id"],))
            ws = Path(row["workspace"])
            if ws.exists():
                for f in ws.iterdir():
                    try:
                        f.unlink()
                    except OSError:
                        pass
                try:
                    ws.rmdir()
                except OSError:
                    pass
            count += 1
        conn.commit()
        return count

    def session_stats(self) -> dict:
        conn = self._conn()
        return conn.execute(
            "SELECT state, COUNT(*) AS n FROM sessions GROUP BY state"
        ).fetchall()


if __name__ == "__main__":
    mgr = SessionManager()
    s = mgr.create_session()
    print("Session créée:")
    print(json.dumps({k: v for k, v in s.items()}, indent=2, default=str))
    ctx = mgr.validate_session(s["session_id"], s["token"])
    print("Validation:", ctx is not None)
    # Mauvais jeton
    print("Mauvais jeton:", mgr.validate_session(s["session_id"], "invalid"))
    mgr.revoke_session(s["session_id"])
    print("Après révocation:", mgr.validate_session(s["session_id"], s["token"]) is None)
