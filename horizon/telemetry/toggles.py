"""Local telemetry toggles (``HORIZON_TELEMETRY`` / ``HORIZON_TELEMETRY_WARN``).

These helpers were rescued from the retired upload-beacon module. They govern
LOCAL aggregate statistics only — the in-process collector and the ``/stats``
endpoint. Nothing here ships data anywhere; there is no separate upload
beacon in Horizon.
"""

from __future__ import annotations

import os

_OFF_VALUES = frozenset(("off", "false", "0", "no", "disable", "disabled"))
_ON_VALUES = frozenset(("on", "true", "1", "yes", "enable", "enabled"))


def is_telemetry_enabled() -> bool:
    """Check if local telemetry collection is enabled (off by default, opt-in).

    Fail-closed: only enabled when HORIZON_TELEMETRY is set to an explicit
    on-value (on/true/1/yes/enable/enabled). Anything else — including unset,
    empty, or an unrecognized value — leaves it disabled.
    """
    from horizon.offline import is_offline

    if is_offline():
        return False
    val = os.environ.get("HORIZON_TELEMETRY", "").lower().strip()
    return val in _ON_VALUES


def is_telemetry_warn_enabled() -> bool:
    """Check if telemetry warnings are enabled (feature flag, on by default).

    Set HORIZON_TELEMETRY_WARN=off to suppress startup/wrap notices.
    This is a build/pack-time feature flag intended for operators who want
    to disable the notice without disabling telemetry itself.
    """
    val = os.environ.get("HORIZON_TELEMETRY_WARN", "on").lower().strip()
    return val not in _OFF_VALUES


def format_telemetry_notice(*, prefix: str = "") -> str:
    """Return a single-line local-telemetry notice suitable for CLI output.

    Returns an empty string when telemetry or warnings are disabled so callers
    can unconditionally include the result in their output.
    """
    if not is_telemetry_warn_enabled():
        return ""
    if not is_telemetry_enabled():
        return ""
    return (
        f"{prefix}Telemetry:    ENABLED (local aggregate stats only — nothing sent externally) | "
        "Disable: HORIZON_TELEMETRY=off or --no-telemetry"
    )
