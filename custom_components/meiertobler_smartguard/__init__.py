"""Meier Tobler SmartGuard integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import SmartGuardConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SmartGuardConfigEntry,
) -> bool:
    """Set up SmartGuard from a config entry."""
    from homeassistant.const import Platform
    from homeassistant.exceptions import ConfigEntryNotReady
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    from .api import SmartGuardApiClient, SmartGuardError
    from .const import CONF_HOST
    from .coordinator import SmartGuardCoordinator
    from .data import SmartGuardRuntimeData

    client = SmartGuardApiClient(
        entry.data[CONF_HOST],
        async_get_clientsession(hass),
    )
    try:
        identity = await client.async_get_identity()
    except SmartGuardError as err:
        raise ConfigEntryNotReady("SmartGuard identity is unavailable") from err
    coordinator = SmartGuardCoordinator(
        hass,
        entry,
        client,
        identity.serial_number,
    )
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = SmartGuardRuntimeData(client, coordinator, identity)
    await hass.config_entries.async_forward_entry_setups(
        entry,
        [Platform.SENSOR, Platform.SELECT],
    )
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: SmartGuardConfigEntry,
) -> bool:
    """Unload a SmartGuard config entry."""
    from homeassistant.const import Platform

    return await hass.config_entries.async_unload_platforms(
        entry,
        [Platform.SENSOR, Platform.SELECT],
    )


async def _async_update_listener(
    hass: HomeAssistant,
    entry: SmartGuardConfigEntry,
) -> None:
    """Reload after config-entry data changes."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Allow Home Assistant to load the integration package."""
    return True
