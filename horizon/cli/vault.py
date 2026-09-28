"""``horizon vault`` — manage the forwarder credential in the OS key store.

Stores the remote per-user ``hz_...`` key (Windows Credential Manager /
macOS Keychain) so the local forwarder can attach it without the key
appearing in any plaintext config file.
"""

from __future__ import annotations

import getpass
import sys

import click

from horizon.cli.main import main
from horizon.vault import VaultError, clear_credential, get_credential, set_credential


@main.group()
def vault() -> None:
    """Manage the remote credential in the OS key store (set / get / clear)."""


@vault.command("set")
def vault_set() -> None:
    """Prompt for the remote ``hz_...`` key and store it (input hidden)."""
    value = getpass.getpass("Remote Horizon key (hz_...): ")
    try:
        set_credential(value)
    except VaultError as exc:
        click.echo(f"error: {exc}", err=True)
        sys.exit(2)
    click.echo("credential stored")


@vault.command("get")
def vault_get() -> None:
    """Print the stored key (for piping; use with care)."""
    try:
        click.echo(get_credential())
    except VaultError as exc:
        click.echo(f"error: {exc}", err=True)
        sys.exit(2)


@vault.command("clear")
def vault_clear() -> None:
    """Delete the stored credential."""
    clear_credential()
    click.echo("credential cleared (if it existed)")
