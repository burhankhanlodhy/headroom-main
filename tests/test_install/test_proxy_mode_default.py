"""`horizon install` must default to cache mode, like `horizon proxy` does.

#1893 shipped the coding/cache posture as Horizon's out-of-box default, but it
only touched `cli/proxy.py` and `proxy/server.py` — the install path kept the
older `token` default from #1404. Since `planner.py` writes `HORIZON_MODE` into
the install env, an installed Horizon actively *overrode* the good server default
with the cache-busting one.

Cache mode freezes prior turns and compresses only the newest delta ("~0
prefix-cache busts"); token mode rewrites frozen history, which moves the cached
prefix bytes and forces a full cold re-write. These tests pin the agreement so the
two entry points cannot drift apart again.
"""

from __future__ import annotations

from horizon.install.models import DeploymentManifest
from horizon.proxy.proxy_mode_policy import PROXY_MODE_CACHE


def _mode_option_default(command) -> str:
    """The declared default of a command's ``--mode`` option."""
    for param in command.params:
        if param.name == "proxy_mode":
            return str(param.default)
    raise AssertionError(f"{command.name} has no --mode/proxy_mode option")


def test_install_apply_defaults_to_cache_mode() -> None:
    from horizon.cli.install import install_apply

    assert _mode_option_default(install_apply) == PROXY_MODE_CACHE


def test_deploy_defaults_to_cache_mode() -> None:
    from horizon.cli.install import deploy

    assert _mode_option_default(deploy) == PROXY_MODE_CACHE


def test_manifest_default_is_cache_mode() -> None:
    """A manifest that omits proxy_mode must not fall back to token."""
    assert DeploymentManifest.__dataclass_fields__["proxy_mode"].default == PROXY_MODE_CACHE


def test_install_and_proxy_agree_on_the_default() -> None:
    """The whole point: both entry points land on the same posture.

    `horizon proxy` resolves `mode or HORIZON_MODE or PROXY_MODE_CACHE`, so its
    default is PROXY_MODE_CACHE. Install must match, or installing Horizon
    silently changes the compression posture versus running it directly.
    """
    from horizon.cli.install import deploy, install_apply

    assert _mode_option_default(install_apply) == _mode_option_default(deploy) == PROXY_MODE_CACHE


def test_token_mode_is_still_reachable() -> None:
    """Changing the default must not take the choice away.

    The option carries no restrictive ``type``, and the normalizer still accepts
    token (plus its aliases), so `--mode token` remains available to anyone who
    wants maximum compression and accepts the prefix-cache busts.
    """
    from horizon.cli.install import deploy, install_apply
    from horizon.proxy.proxy_mode_policy import (
        PROXY_MODE_TOKEN,
        normalize_proxy_mode_value,
    )

    for command in (install_apply, deploy):
        param = next(p for p in command.params if p.name == "proxy_mode")
        assert param.type.name == "text", f"{command.name} --mode became restrictive"

    assert normalize_proxy_mode_value("token") == PROXY_MODE_TOKEN
    assert normalize_proxy_mode_value("token_horizon") == PROXY_MODE_TOKEN
