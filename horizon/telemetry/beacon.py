"""Compatibility shim for the retired upload-beacon module.

The upload beacon was retired from Horizon; ``horizon.telemetry.session``
still imports a few names from this module, so they resolve here to the
local telemetry toggles. Those stay off unless ``HORIZON_TELEMETRY`` is
explicitly enabled, and nothing here ships data anywhere.
"""

from horizon.telemetry.toggles import (
    _OFF_VALUES,
    _ON_VALUES,
    is_telemetry_enabled as is_beacon_enabled,
)

__all__ = ["_OFF_VALUES", "_ON_VALUES", "is_beacon_enabled"]
