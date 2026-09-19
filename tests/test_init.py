"""Tests for SmartGuard config-entry setup and unloading."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.meiertobler_smartguard import (
    _async_update_listener,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.meiertobler_smartguard.api import SmartGuardConnectionError
from custom_components.meiertobler_smartguard.const import CONF_HOST

from .conftest import (
    TEST_GLOBAL_DEVICE_ID,
    TEST_HOST,
    TEST_IDENTITY,
)


async def test_setup_entry_through_home_assistant(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api: dict[str, AsyncMock],
) -> None:
    """Home Assistant loads all nine entities from one mocked gateway snapshot."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED
    registry = er.async_get(hass)
    entry_entities = [
        entity
        for entity in registry.entities.values()
        if entity.config_entry_id == config_entry.entry_id
    ]
    assert len(entry_entities) == 9

    temperature_id = registry.async_get_entity_id(
        "sensor",
        config_entry.domain,
        f"{TEST_GLOBAL_DEVICE_ID}_source_inlet_temperature",
    )
    select_id = registry.async_get_entity_id(
        "select",
        config_entry.domain,
        f"{TEST_GLOBAL_DEVICE_ID}_hk60_selected_mode_select",
    )
    assert temperature_id is not None
    assert select_id is not None
    assert hass.states.get(temperature_id).state == "12.5"
    assert hass.states.get(select_id).state == "auto"
    mock_api["get_identity"].assert_awaited_once()
    mock_api["read_all"].assert_awaited_once_with(TEST_IDENTITY.serial_number)

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.NOT_LOADED


async def test_setup_entry_builds_runtime_and_forwards_platforms() -> None:
    """Successful setup owns runtime data and registers the reload listener."""
    hass = MagicMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock()
    entry = MagicMock()
    entry.data = {CONF_HOST: TEST_HOST}
    entry.add_update_listener.return_value = "listener-remover"

    with (
        patch(
            "homeassistant.helpers.aiohttp_client.async_get_clientsession",
            return_value="session",
        ),
        patch(
            "custom_components.meiertobler_smartguard.api.SmartGuardApiClient"
        ) as client_class,
        patch(
            "custom_components.meiertobler_smartguard.coordinator."
            "SmartGuardCoordinator"
        ) as coordinator_class,
    ):
        client = client_class.return_value
        client.async_get_identity = AsyncMock(return_value=TEST_IDENTITY)
        coordinator = coordinator_class.return_value
        coordinator.async_config_entry_first_refresh = AsyncMock()

        assert await async_setup_entry(hass, entry)

    assert entry.runtime_data.client is client
    assert entry.runtime_data.coordinator is coordinator
    assert entry.runtime_data.identity is TEST_IDENTITY
    entry.async_on_unload.assert_called_once_with("listener-remover")
    entry.add_update_listener.assert_called_once_with(_async_update_listener)
    hass.config_entries.async_forward_entry_setups.assert_awaited_once()


async def test_setup_entry_defers_when_identity_is_unavailable() -> None:
    """Identity failures request Home Assistant's config-entry retry handling."""
    hass = MagicMock()
    entry = MagicMock()
    entry.data = {CONF_HOST: TEST_HOST}

    with (
        patch(
            "homeassistant.helpers.aiohttp_client.async_get_clientsession",
            return_value="session",
        ),
        patch(
            "custom_components.meiertobler_smartguard.api.SmartGuardApiClient"
        ) as client_class,
    ):
        client_class.return_value.async_get_identity = AsyncMock(
            side_effect=SmartGuardConnectionError()
        )
        with pytest.raises(ConfigEntryNotReady):
            await async_setup_entry(hass, entry)


async def test_unload_entry() -> None:
    """Unload delegates both integration platforms to Home Assistant."""
    hass = MagicMock()
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    entry = MagicMock()

    assert await async_unload_entry(hass, entry)
    hass.config_entries.async_unload_platforms.assert_awaited_once()


async def test_update_listener_reloads_entry() -> None:
    """Changing entry data reloads the integration."""
    hass = MagicMock()
    hass.config_entries.async_reload = AsyncMock()
    entry = MagicMock()
    entry.entry_id = "entry-123"

    await _async_update_listener(hass, entry)

    hass.config_entries.async_reload.assert_awaited_once_with("entry-123")
