"""SQLite-backed API-key store.

Design notes:

- Stdlib ``sqlite3`` only — no new dependencies on the proxy image.
- One connection per operation. The store is written by the operator CLI and
  read by the proxy server process (typically different processes, possibly
  different containers sharing a volume), so short-lived connections in WAL
  mode are the robust cross-process shape; no lock state is carried between
  calls.
- Only SHA-256 hashes of keys are stored. Timing side channels on a hash
  lookup of a 36-hex-character random secret are not practical; the proxy
  still compares the *master* token with ``hmac.compare_digest`` as before.
"""

from __future__ import annotations

import hashlib
import os
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from horizon import paths

KEY_PREFIX_TAG = "hz_"
_KEYS_PATH_ENV = "HORIZON_KEYS_PATH"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    key_hash TEXT NOT NULL UNIQUE,
    prefix TEXT NOT NULL,
    created_at TEXT NOT NULL,
    revoked_at TEXT,
    last_used_at TEXT
)
"""


def key_store_path(explicit: str | os.PathLike[str] | None = None) -> Path:
    """Resolve the key-store database path.

    Precedence: ``explicit`` argument > ``$HORIZON_KEYS_PATH`` >
    ``<workspace>/keys.db``.
    """

    if explicit is not None and str(explicit) != "":
        return Path(explicit).expanduser()
    env_value = os.environ.get(_KEYS_PATH_ENV, "").strip()
    if env_value:
        return Path(env_value).expanduser()
    return paths.workspace_dir() / "keys.db"


@dataclass(frozen=True)
class KeyRecord:
    name: str
    prefix: str
    created_at: str
    revoked_at: str | None
    last_used_at: str | None


def _hash_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _row_to_record(row: sqlite3.Row) -> KeyRecord:
    return KeyRecord(
        name=row["name"],
        prefix=row["prefix"],
        created_at=row["created_at"],
        revoked_at=row["revoked_at"],
        last_used_at=row["last_used_at"],
    )


class KeyStore:
    """Issue, list, authenticate, and revoke per-user API keys."""

    def __init__(self, path: str | os.PathLike[str] | None = None) -> None:
        self.path = key_store_path(path)

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=10000")
        return conn

    def _ensure_schema(self, conn: sqlite3.Connection) -> None:
        conn.execute(_SCHEMA)

    def issue(self, name: str) -> tuple[str, KeyRecord]:
        """Generate a new key for ``name``. Returns ``(plaintext_key, record)``.

        The plaintext key is returned exactly once and is not persisted.
        Raises ``ValueError`` when the name is already in use (active or
        revoked) — re-issue requires an explicit revoke-then-issue or a
        different name, so an operator cannot silently overwrite a
        credential that may still be deployed.
        """

        if not name or not name.strip():
            raise ValueError("key name must be non-empty")
        name = name.strip()
        key = KEY_PREFIX_TAG + secrets.token_hex(18)
        key_hash = _hash_key(key)
        prefix = key[: len(KEY_PREFIX_TAG) + 8]
        created_at = _now()
        with self._connect() as conn:
            self._ensure_schema(conn)
            existing = conn.execute(
                "SELECT 1 FROM api_keys WHERE name = ?", (name,)
            ).fetchone()
            if existing is not None:
                raise ValueError(f"key name already in use: {name!r}")
            conn.execute(
                "INSERT INTO api_keys (name, key_hash, prefix, created_at)"
                " VALUES (?, ?, ?, ?)",
                (name, key_hash, prefix, created_at),
            )
        return key, KeyRecord(
            name=name,
            prefix=prefix,
            created_at=created_at,
            revoked_at=None,
            last_used_at=None,
        )

    def authenticate(self, key: str) -> KeyRecord | None:
        """Return the active key record for ``key``, or ``None``.

        Revoked keys authenticate as ``None``. Successful authentication
        stamps ``last_used_at`` — a write per authenticated request, which is
        acceptable for a small team on WAL SQLite; move to a sampled stamp if
        that ever shows up in profiling. The record is re-fetched after the
        UPDATE so the returned stamp reflects the write, matching ``revoke``.
        """

        if not key:
            return None
        key_hash = _hash_key(key)
        with self._connect() as conn:
            self._ensure_schema(conn)
            row = conn.execute(
                "SELECT * FROM api_keys WHERE key_hash = ? AND revoked_at IS NULL",
                (key_hash,),
            ).fetchone()
            if row is None:
                return None
            conn.execute(
                "UPDATE api_keys SET last_used_at = ? WHERE id = ?",
                (_now(), row["id"]),
            )
            fresh = conn.execute(
                "SELECT * FROM api_keys WHERE id = ?", (row["id"],)
            ).fetchone()
            return _row_to_record(fresh)

    def list_keys(self) -> list[KeyRecord]:
        with self._connect() as conn:
            self._ensure_schema(conn)
            rows = conn.execute(
                "SELECT * FROM api_keys ORDER BY created_at"
            ).fetchall()
            return [_row_to_record(row) for row in rows]

    def revoke(self, name_or_prefix: str) -> KeyRecord | None:
        """Revoke by name or display prefix. Returns the record, or ``None``
        when nothing matched. Revocation is idempotent."""

        if not name_or_prefix or not name_or_prefix.strip():
            return None
        needle = name_or_prefix.strip()
        now = _now()
        with self._connect() as conn:
            self._ensure_schema(conn)
            row = conn.execute(
                "SELECT * FROM api_keys WHERE name = ? OR (prefix = ? AND revoked_at IS NULL)",
                (needle, needle),
            ).fetchone()
            if row is None:
                return None
            conn.execute(
                "UPDATE api_keys SET revoked_at = ? WHERE id = ? AND revoked_at IS NULL",
                (now, row["id"]),
            )
            fresh = conn.execute(
                "SELECT * FROM api_keys WHERE id = ?", (row["id"],)
            ).fetchone()
            return _row_to_record(fresh)
