"""Diagnostics support for Meier Tobler SmartGuard."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Final

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from .const import CONF_HOST
from .data import SmartGuardConfigEntry

_CONFIG_KEYS_TO_REDACT: Final = frozenset({CONF_HOST})
_IDENTITY_KEYS_TO_REDACT: Final = frozenset(
    {
        "global_device_id",
        "serial_number",
    }
)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: SmartGuardConfigEntry,
) -> dict[str, Any]:
    """Return redacted config-entry diagnostics from coordinator memory."""
    runtime_data = entry.runtime_data
    return {
        "config_entry": {
            "data": async_redact_data(dict(entry.data), _CONFIG_KEYS_TO_REDACT),
        },
        "identity": async_redact_data(
            asdict(runtime_data.identity),
            _IDENTITY_KEYS_TO_REDACT,
        ),
        "coordinator": {
            "last_update_success": runtime_data.coordinator.last_update_success,
            "data": dict(runtime_data.coordinator.data),
        },
    }
