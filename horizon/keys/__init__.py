"""Per-user API keys for the Horizon proxy.

Keys are issued by the operator (``horizon keys issue``), stored as SHA-256
hashes in a SQLite database under the Horizon workspace, and accepted by the
proxy security gate as an alternative to the single operator token. The
plaintext key is shown exactly once at issue time and never persisted.
"""

from .store import KeyRecord, KeyStore, key_store_path

__all__ = ["KeyRecord", "KeyStore", "key_store_path"]
