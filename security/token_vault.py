# -*- coding: utf-8 -*-
"""
================================================================================
          COFFRE-FORT DE JETONS HACHÉS — RATISS CYPHER ODV V2
================================================================================
Stockage des clés API en hachage SHA-256 dans SQLite.
Les valeurs claires ne sont JAMAIS persistées. La vérification d'une clé
fournie se fait par comparaison de hachage. Les clés réelles vivent
uniquement en mémoire, via les variables d'environnement, pour la durée
du processus, et ne transitent jamais dans les logs ou les réponses.
================================================================================
"""
import hashlib
import os
import sqlite3
import threading

DB_PATH = os.environ.get("TOKEN_VAULT_DB_PATH", "data/tokens.db")


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class TokenVault:
    """Coffre-fort de jetons : enregistrement par hachage SHA-256 seulement."""

    _local = threading.local()

    @classmethod
    def _conn(cls):
        if not hasattr(cls._local, "conn") or cls._local.conn is None:
            cls._local.conn = sqlite3.connect(DB_PATH, timeout=10)
            cls._local.conn.row_factory = sqlite3.Row
            cls._local.conn.execute("PRAGMA journal_mode=WAL")
        return cls._local.conn

    @classmethod
    def _init_db(cls):
        cls._conn().execute(
            """CREATE TABLE IF NOT EXISTS token_hashes (
                service TEXT PRIMARY KEY,
                hash_sha256 TEXT NOT NULL,
                registered_at REAL NOT NULL
            )"""
        )
        cls._conn().commit()

    @classmethod
    def register(cls, service: str, plaintext_value: str):
        """Enregistre le hachage d'un jeton. La valeur claire n'est PAS stockée."""
        import time
        cls._init_db()
        cls._conn().execute(
            "INSERT OR REPLACE INTO token_hashes VALUES (?, ?, ?)",
            (service, sha256(plaintext_value), time.time()),
        )
        cls._conn().commit()

    @classmethod
    def verify(cls, service: str, plaintext_value: str) -> bool:
        """Vérifie qu'un jeton correspond au hachage enregistré."""
        cls._init_db()
        row = cls._conn().execute(
            "SELECT hash_sha256 FROM token_hashes WHERE service=?", (service,)
        ).fetchone()
        return row is not None and row["hash_sha256"] == sha256(plaintext_value)

    @classmethod
    def registered_services(cls) -> list:
        cls._init_db()
        return [r["service"] for r in cls._conn().execute(
            "SELECT service FROM token_hashes"
        ).fetchall()]

    @classmethod
    def forget(cls, service: str):
        cls._init_db()
        cls._conn().execute("DELETE FROM token_hashes WHERE service=?", (service,))
        cls._conn().commit()


def mask_token(token: str) -> str:
    """Masque un jeton pour affichage sécurisé (ex: sk-or...3b0a)."""
    if not token or len(token) < 12:
        return "****"
    return f"{token[:6]}...{token[-4:]}"


if __name__ == "__main__":
    # Exemple d'usage : enregistrer uniquement le hachage
    TokenVault.register("openrouter", "sk-or-test-secret")
    print("Services enregistrés:", TokenVault.registered_services())
    print("Vérification correcte:", TokenVault.verify("openrouter", "sk-or-test-secret"))
    print("Vérification incorrecte:", TokenVault.verify("openrouter", "mauvaise_cle"))
    TokenVault.forget("openrouter")
