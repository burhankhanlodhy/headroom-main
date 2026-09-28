"""Tests for the per-user API-key store (horizon.keys)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from horizon.keys import KeyStore, key_store_path


@pytest.fixture()
def store(tmp_path: Path) -> KeyStore:
    return KeyStore(tmp_path / "keys.db")


def test_issue_returns_plaintext_once_and_stores_prefix_only(store: KeyStore) -> None:
    key, record = store.issue("alice")

    assert key.startswith("hz_")
    assert len(key) > 20
    assert record.name == "alice"
    assert record.prefix == key[:11]
    assert record.revoked_at is None
    assert record.last_used_at is None

    # Only the hash lives in the database.
    with sqlite3.connect(store.path) as conn:
        rows = conn.execute("SELECT name, key_hash, prefix FROM api_keys").fetchall()
    assert len(rows) == 1
    name, key_hash, prefix = rows[0]
    assert name == "alice"
    assert key not in key_hash
    assert prefix == record.prefix


def test_authenticate_roundtrip(store: KeyStore) -> None:
    key, record = store.issue("bob")

    authed = store.authenticate(key)
    assert authed is not None
    assert authed.name == record.name
    assert authed.last_used_at is not None


def test_authenticate_rejects_wrong_key(store: KeyStore) -> None:
    store.issue("carol")
    assert store.authenticate("hz_" + "0" * 36) is None
    assert store.authenticate("") is None
    assert store.authenticate("not-a-key") is None


def test_revoke_by_name_blocks_authentication(store: KeyStore) -> None:
    key, _ = store.issue("dave")
    assert store.authenticate(key) is not None

    revoked = store.revoke("dave")
    assert revoked is not None
    assert revoked.revoked_at is not None

    assert store.authenticate(key) is None
    # Idempotent: revoking again does not resurrect or error.
    assert store.revoke("dave") is not None


def test_revoke_by_prefix(store: KeyStore) -> None:
    key, record = store.issue("erin")
    revoked = store.revoke(record.prefix)
    assert revoked is not None
    assert revoked.name == "erin"
    assert store.authenticate(key) is None


def test_revoke_unknown_returns_none(store: KeyStore) -> None:
    assert store.revoke("nobody") is None
    assert store.revoke("") is None


def test_duplicate_name_rejected(store: KeyStore) -> None:
    store.issue("frank")
    with pytest.raises(ValueError, match="already in use"):
        store.issue("frank")


def test_list_keys_reports_revocation(store: KeyStore) -> None:
    store.issue("grace")
    store.issue("heidi")
    store.revoke("heidi")

    records = {r.name: r for r in store.list_keys()}
    assert set(records) == {"grace", "heidi"}
    assert records["grace"].revoked_at is None
    assert records["heidi"].revoked_at is not None


def test_key_store_path_precedence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HORIZON_KEYS_PATH", raising=False)
    explicit = tmp_path / "explicit.db"
    assert key_store_path(explicit) == explicit

    from horizon import paths

    monkeypatch.setenv("HORIZON_KEYS_PATH", str(tmp_path / "env.db"))
    assert key_store_path() == tmp_path / "env.db"

    monkeypatch.delenv("HORIZON_KEYS_PATH", raising=False)
    assert key_store_path() == paths.workspace_dir() / "keys.db"
