"""Meier Tobler SmartGuard integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import SmartGuardConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SmartGuardConfigEntry,
) -> bool:
    """Set up SmartGuard from a config entry."""
    from homeassistant.const import Platform
    from homeassistant.exceptions import ConfigEntryError, ConfigEntryNotReady
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    from .api import (
        SmartGuardApiClient,
        SmartGuardError,
        SmartGuardUnsupportedDeviceError,
    )
    from .const import CONF_HOST, DOMAIN
    from .coordinator import SmartGuardCoordinator
    from .data import SmartGuardRuntimeData
    from .issues import (
        async_clear_configuration_issues,
        async_create_configuration_issue,
    )

    try:
        client = SmartGuardApiClient(
            entry.data[CONF_HOST],
            async_get_clientsession(hass),
        )
    except ValueError as err:
        async_create_configuration_issue(hass, entry, "invalid_host")
        raise ConfigEntryError(
            translation_domain=DOMAIN, translation_key="invalid_host"
        ) from err
    try:
        identity = await client.async_get_identity()
    except SmartGuardUnsupportedDeviceError as err:
        async_create_configuration_issue(hass, entry, "unsupported_device")
        raise ConfigEntryError(
            translation_domain=DOMAIN, translation_key="unsupported_device"
        ) from err
    except SmartGuardError as err:
        raise ConfigEntryNotReady("SmartGuard identity is unavailable") from err
    if entry.unique_id is not None and identity.global_device_id != entry.unique_id:
        async_create_configuration_issue(hass, entry, "wrong_device")
        raise ConfigEntryError(
            translation_domain=DOMAIN, translation_key="wrong_device"
        )
    async_clear_configuration_issues(hass, entry.entry_id)
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
        [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.SELECT],
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
        [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.SELECT],
    )


async def _async_update_listener(
    hass: HomeAssistant,
    entry: SmartGuardConfigEntry,
) -> None:
    """Reload after config-entry data changes."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_remove_entry(
    hass: HomeAssistant,
    entry: SmartGuardConfigEntry,
) -> None:
    """Remove persistent repair notices when their configuration is removed."""
    from .issues import async_clear_configuration_issues

    async_clear_configuration_issues(hass, entry.entry_id)
