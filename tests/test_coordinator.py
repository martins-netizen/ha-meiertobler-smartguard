"""Tests for the SmartGuard data coordinator."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.meiertobler_smartguard.api import (
    SmartGuardApiClient,
    SmartGuardConnectionError,
)
from custom_components.meiertobler_smartguard.coordinator import SmartGuardCoordinator

from .conftest import TEST_SERIAL_NUMBER, TEST_SNAPSHOT


async def test_coordinator_reads_snapshot(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> None:
    """The coordinator returns the complete client snapshot."""
    client = MagicMock(spec=SmartGuardApiClient)
    client.async_read_all = AsyncMock(return_value=TEST_SNAPSHOT.copy())
    coordinator = SmartGuardCoordinator(
        hass,
        config_entry,
        client,
        TEST_SERIAL_NUMBER,
    )

    assert await coordinator._async_update_data() == TEST_SNAPSHOT
    client.async_read_all.assert_awaited_once_with(TEST_SERIAL_NUMBER)


async def test_coordinator_maps_client_error(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> None:
    """Client failures become Home Assistant update failures."""
    client = MagicMock(spec=SmartGuardApiClient)
    client.async_read_all = AsyncMock(side_effect=SmartGuardConnectionError())
    coordinator = SmartGuardCoordinator(
        hass,
        config_entry,
        client,
        TEST_SERIAL_NUMBER,
    )

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()
