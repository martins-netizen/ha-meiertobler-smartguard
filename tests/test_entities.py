"""Tests for SmartGuard sensor and select entities."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.meiertobler_smartguard.api import (
    SmartGuardApiClient,
    SmartGuardConnectionError,
    SmartGuardWriteVerificationError,
)
from custom_components.meiertobler_smartguard.coordinator import SmartGuardCoordinator
from custom_components.meiertobler_smartguard.data import SmartGuardRuntimeData
from custom_components.meiertobler_smartguard.select import (
    SmartGuardModeSelect,
)
from custom_components.meiertobler_smartguard.select import (
    async_setup_entry as async_setup_select,
)
from custom_components.meiertobler_smartguard.sensor import (
    SENSOR_DESCRIPTIONS,
    SmartGuardSensor,
)
from custom_components.meiertobler_smartguard.sensor import (
    async_setup_entry as async_setup_sensor,
)

from .conftest import TEST_IDENTITY, TEST_SERIAL_NUMBER, TEST_SNAPSHOT


def _runtime_entry(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> tuple[MockConfigEntry, MagicMock, SmartGuardCoordinator]:
    """Attach deterministic runtime data to a config entry."""
    client = MagicMock(spec=SmartGuardApiClient)
    client.async_set_hk60_selected_mode = AsyncMock(return_value=0)
    coordinator = SmartGuardCoordinator(
        hass,
        config_entry,
        client,
        TEST_SERIAL_NUMBER,
    )
    coordinator.async_set_updated_data(TEST_SNAPSHOT.copy())
    config_entry.runtime_data = SmartGuardRuntimeData(
        client,
        coordinator,
        TEST_IDENTITY,
    )
    return config_entry, client, coordinator


async def test_platform_setup_adds_all_entities(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> None:
    """Platform setup creates eight sensors and one select."""
    entry, _, _ = _runtime_entry(hass, config_entry)
    entities: list[object] = []

    await async_setup_sensor(hass, entry, entities.extend)
    await async_setup_select(hass, entry, entities.extend)

    assert len(entities) == len(SENSOR_DESCRIPTIONS) + 1
    assert isinstance(entities[-1], SmartGuardModeSelect)


def test_sensor_values_and_device_info(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> None:
    """Sensors format coordinator data and share stable device metadata."""
    entry, _, coordinator = _runtime_entry(hass, config_entry)
    temperature = SmartGuardSensor(entry, SENSOR_DESCRIPTIONS[0])
    enum_sensor = SmartGuardSensor(entry, SENSOR_DESCRIPTIONS[4])

    assert temperature.native_value == 12.5
    assert temperature.available
    assert enum_sensor.native_value == "heating"
    assert enum_sensor.available
    assert temperature.unique_id == f"{TEST_IDENTITY.global_device_id}_source_inlet_temperature"
    assert temperature.device_info["serial_number"] == TEST_SERIAL_NUMBER

    coordinator.async_set_updated_data(
        {
            **TEST_SNAPSHOT,
            "source_inlet_temperature": None,
            "hk60_operating_status": 99,
        }
    )
    assert temperature.native_value is None
    assert not temperature.available
    assert enum_sensor.native_value is None
    assert not enum_sensor.available


@pytest.mark.parametrize("raw_value", [True, 1.5])
def test_enum_sensor_rejects_non_integer_value(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    raw_value: bool | float,
) -> None:
    """Unexpected enum value types are unavailable."""
    entry, _, coordinator = _runtime_entry(hass, config_entry)
    sensor = SmartGuardSensor(entry, SENSOR_DESCRIPTIONS[4])
    coordinator.async_set_updated_data(
        {**TEST_SNAPSHOT, "hk60_operating_status": raw_value}
    )

    assert sensor.native_value is None
    assert not sensor.available


@pytest.mark.parametrize("raw_value", [True, 1.5, 99])
def test_select_rejects_unknown_coordinator_value(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    raw_value: bool | float | int,
) -> None:
    """The select is unavailable for malformed or future mode values."""
    entry, _, coordinator = _runtime_entry(hass, config_entry)
    select = SmartGuardModeSelect(entry)
    coordinator.async_set_updated_data(
        {**TEST_SNAPSHOT, "hk60_selected_mode": raw_value}
    )

    assert select.current_option is None
    assert not select.available


async def test_select_writes_and_refreshes(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> None:
    """Changing the option writes the mapped value and refreshes all entities."""
    entry, client, coordinator = _runtime_entry(hass, config_entry)
    coordinator.async_request_refresh = AsyncMock()
    select = SmartGuardModeSelect(entry)

    assert select.current_option == "auto"
    assert select.available
    await select.async_select_option("heating")

    client.async_set_hk60_selected_mode.assert_awaited_once_with(
        TEST_SERIAL_NUMBER,
        4,
    )
    coordinator.async_request_refresh.assert_awaited_once_with()


async def test_select_same_option_only_refreshes(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> None:
    """Selecting the current option avoids an unnecessary gateway write."""
    entry, client, coordinator = _runtime_entry(hass, config_entry)
    coordinator.async_request_refresh = AsyncMock()
    select = SmartGuardModeSelect(entry)

    await select.async_select_option("auto")

    client.async_set_hk60_selected_mode.assert_not_awaited()
    coordinator.async_request_refresh.assert_awaited_once_with()


async def test_select_rejects_invalid_option(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> None:
    """Options outside the allowlist are rejected before any gateway write."""
    entry, client, _ = _runtime_entry(hass, config_entry)
    select = SmartGuardModeSelect(entry)

    with pytest.raises(ServiceValidationError):
        await select.async_select_option("unsupported")
    client.async_set_hk60_selected_mode.assert_not_awaited()


@pytest.mark.parametrize(
    ("error", "translation_key"),
    [
        (SmartGuardWriteVerificationError(), "write_not_confirmed"),
        (SmartGuardConnectionError(), "write_failed"),
    ],
)
async def test_select_maps_write_errors(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    error: Exception,
    translation_key: str,
) -> None:
    """Gateway write failures become translated Home Assistant errors."""
    entry, client, coordinator = _runtime_entry(hass, config_entry)
    client.async_set_hk60_selected_mode.side_effect = error
    coordinator.async_request_refresh = AsyncMock()
    select = SmartGuardModeSelect(entry)

    with pytest.raises(HomeAssistantError) as raised:
        await select.async_select_option("normal")

    assert raised.value.translation_key == translation_key
    coordinator.async_request_refresh.assert_not_awaited()
