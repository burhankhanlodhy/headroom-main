"""OS credential-store access for the local forwarder.

The PC-side forwarder relays loopback traffic to a remote Horizon proxy and
attaches the caller's per-user ``hz_...`` key. Storing that key in a
plaintext config file would defeat the point of per-user keys, so it lives
in the OS credential store instead (Windows Credential Manager, macOS
Keychain, Secret Service on Linux) via ``keyring``.

``keyring`` is an optional dependency (``pip install horizon-ai[vault]``);
every function raises :class:`VaultError` with an actionable message when it
is missing or the platform backend misbehaves.
"""

from __future__ import annotations

SERVICE_NAME = "horizon"
CREDENTIAL_NAME = "remote-api-key"


class VaultError(RuntimeError):
    """Raised when the credential store is unavailable or the entry is absent."""


def _load_keyring():
    try:
        import keyring
    except ImportError as exc:
        raise VaultError(
            "keyring is not installed - install it with: pip install horizon-ai[vault]"
        ) from exc
    backend = keyring.get_keyring()
    if "fail" in type(backend).__module__:
        raise VaultError(
            "no usable OS credential-store backend found (keyring backend: "
            f"{type(backend).__name__})"
        )
    return keyring


def set_credential(value: str) -> None:
    """Store the remote per-user key in the OS credential store."""

    if not value or not value.strip():
        raise VaultError("credential value must be non-empty")
    keyring = _load_keyring()
    keyring.set_password(SERVICE_NAME, CREDENTIAL_NAME, value.strip())


def get_credential() -> str:
    """Return the stored per-user key, raising :class:`VaultError` if absent."""

    keyring = _load_keyring()
    value = keyring.get_password(SERVICE_NAME, CREDENTIAL_NAME)
    if not value:
        raise VaultError(
            "no Horizon credential stored - set one with: horizon vault set"
        )
    return value


def has_credential() -> bool:
    """Return True when a credential is stored (without revealing it)."""

    try:
        keyring = _load_keyring()
    except VaultError:
        return False
    return bool(keyring.get_password(SERVICE_NAME, CREDENTIAL_NAME))


def clear_credential() -> None:
    """Delete the stored credential. Absent entries are tolerated."""

    keyring = _load_keyring()
    try:
        keyring.delete_password(SERVICE_NAME, CREDENTIAL_NAME)
    except Exception:  # noqa: BLE001 - deleting a missing entry is fine
        pass
