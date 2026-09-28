"""``horizon keys`` — issue, list, and revoke per-user proxy API keys.

Operator tooling for the VPS deployment: each user gets a ``hz_...`` key
accepted by the proxy security gate alongside the master
``HORIZON_PROXY_TOKEN``. Plaintext keys are shown exactly once at issue
time; only SHA-256 hashes live in the store.
"""

from __future__ import annotations

import sys

import click

from horizon.cli.main import main
from horizon.keys import KeyStore


@main.group()
def keys() -> None:
    """Manage per-user proxy API keys (issue / list / revoke)."""


@keys.command("issue")
@click.argument("name")
@click.option(
    "--store",
    "store_path",
    type=click.Path(file_okay=True, dir_okay=False, resolve_path=True),
    default=None,
    help="Key store database path (default: $HORIZON_KEYS_PATH or <workspace>/keys.db).",
)
def keys_issue(name: str, store_path: str | None) -> None:
    """Issue a new API key named NAME. The key is printed once."""
    store = KeyStore(store_path) if store_path else KeyStore()
    try:
        key, record = store.issue(name)
    except ValueError as exc:
        click.echo(f"error: {exc}", err=True)
        sys.exit(2)
    click.echo(f"key name:   {record.name}")
    click.echo(f"prefix:     {record.prefix}...")
    click.echo(f"created:    {record.created_at}")
    click.echo()
    click.secho(key, bold=True)
    click.echo()
    click.echo("Store this value now - it is not shown again and cannot be recovered.")
    click.echo("Use it as:  Authorization: Bearer <key>   or   x-horizon-proxy-token: <key>")


@keys.command("list")
@click.option(
    "--store",
    "store_path",
    type=click.Path(file_okay=True, dir_okay=False, resolve_path=True),
    default=None,
    help="Key store database path (default: $HORIZON_KEYS_PATH or <workspace>/keys.db).",
)
def keys_list(store_path: str | None) -> None:
    """List all API keys (prefixes only - plaintext is never stored)."""
    store = KeyStore(store_path) if store_path else KeyStore()
    records = store.list_keys()
    if not records:
        click.echo("no keys issued")
        return
    width = max(len(r.name) for r in records)
    click.echo(f"{'name'.ljust(width)}  prefix        status    last_used             created")
    for r in records:
        status = "REVOKED" if r.revoked_at else "active"
        click.echo(
            f"{r.name.ljust(width)}  {r.prefix}...  {status.ljust(8)}  "
            f"{r.last_used_at or '-':<20}  {r.created_at}"
        )


@keys.command("revoke")
@click.argument("name_or_prefix")
@click.option(
    "--store",
    "store_path",
    type=click.Path(file_okay=True, dir_okay=False, resolve_path=True),
    default=None,
    help="Key store database path (default: $HORIZON_KEYS_PATH or <workspace>/keys.db).",
)
def keys_revoke(name_or_prefix: str, store_path: str | None) -> None:
    """Revoke the key named NAME_OR_PREFIX (name or display prefix)."""
    store = KeyStore(store_path) if store_path else KeyStore()
    record = store.revoke(name_or_prefix)
    if record is None:
        click.echo(f"error: no key matches {name_or_prefix!r}", err=True)
        sys.exit(2)
    click.echo(f"revoked: {record.name} ({record.prefix}...) at {record.revoked_at}")
