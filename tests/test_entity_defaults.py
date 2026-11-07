"""Real HA registry tests for optional diagnostic counter defaults."""

from __future__ import annotations

from importlib.metadata import version
from unittest.mock import AsyncMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.meiertobler_smartguard.const import DOMAIN, MODEL
from tests.ha_helpers import MockConfigEntry

from .conftest import TEST_GLOBAL_DEVICE_ID, TEST_SNAPSHOT

COUNTER_VALUES = {
    "buffer_heater_operating_hours": 0,
    "dhw_heater_operating_hours": 12,
}
STORAGE_VALUES = {
    **COUNTER_VALUES,
    "buffer_temperature": 28.25,
    "dhw_temperature": 48.5,
    "buffer_heater_status": False,
    "dhw_heater_status": True,
}


def _counter_id(registry: er.EntityRegistry, key: str) -> str:
    entity_id = registry.async_get_entity_id(
        "sensor", DOMAIN, f"{TEST_GLOBAL_DEVICE_ID}_{key}"
    )
    assert entity_id is not None
    return entity_id


@pytest.mark.parametrize("late_discovery", [False, True])
async def test_only_new_operating_hour_counters_default_to_disabled(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api: dict[str, AsyncMock],
    late_discovery: bool,
) -> None:
    """Discover disabled counters at startup or later without hiding core data."""
    if not late_discovery:
        mock_api["read_all"].return_value = {**TEST_SNAPSHOT, **STORAGE_VALUES}
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    registry = er.async_get(hass)
    if late_discovery:
        assert all(
            registry.async_get_entity_id("sensor", DOMAIN, f"{TEST_GLOBAL_DEVICE_ID}_{key}")
            is None
            for key in COUNTER_VALUES
        )
        config_entry.runtime_data.coordinator.async_set_updated_data(
            {**TEST_SNAPSHOT, **STORAGE_VALUES}
        )
        await hass.async_block_till_done()

    entries = [
        entry for entry in registry.entities.values()
        if entry.config_entry_id == config_entry.entry_id
    ]
    assert len(entries) == 15
    counter_ids = {_counter_id(registry, key) for key in COUNTER_VALUES}
    for entry in entries:
        if entry.entity_id in counter_ids:
            assert entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION
            assert hass.states.get(entry.entity_id) is None
        else:
            assert entry.disabled_by is None
            assert hass.states.get(entry.entity_id) is not None
    mock_api["set_mode"].assert_not_awaited()


@pytest.mark.parametrize("key", list(COUNTER_VALUES))
@pytest.mark.parametrize(
    "disabled_by", [None, er.RegistryEntryDisabler.USER, er.RegistryEntryDisabler.INTEGRATION]
)
async def test_existing_counter_activation_names_and_ids_survive_reload(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api: dict[str, AsyncMock],
    key: str,
    disabled_by: er.RegistryEntryDisabler | None,
) -> None:
    """A default change must not alter a pre-existing user's registry choices."""
    registry = er.async_get(hass)
    saved = registry.async_get_or_create(
        "sensor", DOMAIN, f"{TEST_GLOBAL_DEVICE_ID}_{key}",
        config_entry=config_entry, suggested_object_id=f"custom_{key}",
        disabled_by=disabled_by,
    )
    registry.async_update_entity(saved.entity_id, name="Custom runtime counter")
    mock_api["read_all"].return_value = {**TEST_SNAPSHOT, **STORAGE_VALUES}
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    for reload_entry in [False, True]:
        if reload_entry:
            assert await hass.config_entries.async_reload(config_entry.entry_id)
            await hass.async_block_till_done()
        assert _counter_id(registry, key) == saved.entity_id
        current = registry.async_get(saved.entity_id)
        assert current is not None
        assert current.name == "Custom runtime counter"
        assert current.disabled_by is disabled_by
        state = hass.states.get(saved.entity_id)
        if disabled_by is None:
            assert state is not None
            assert state.state == str(COUNTER_VALUES[key])
            expected_name = (
                f"{MODEL} Custom runtime counter"
                if tuple(map(int, version("homeassistant").split(".")[:2])) >= (2026, 11)
                else "Custom runtime counter"
            )
            assert state.attributes["friendly_name"] == expected_name
        else:
            assert state is None
    mock_api["set_mode"].assert_not_awaited()


@pytest.mark.parametrize("key", list(COUNTER_VALUES))
async def test_user_can_enable_a_new_counter_and_keep_it_enabled(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api: dict[str, AsyncMock],
    key: str,
) -> None:
    """Explicit activation exposes real values, including zero, across reload."""
    mock_api["read_all"].return_value = {**TEST_SNAPSHOT, **STORAGE_VALUES}
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    registry = er.async_get(hass)
    entity_id = _counter_id(registry, key)
    registry.async_update_entity(entity_id, disabled_by=None)
    assert await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()

    assert _counter_id(registry, key) == entity_id
    assert registry.async_get(entity_id).disabled_by is None
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == str(COUNTER_VALUES[key])
    assert state.attributes["unit_of_measurement"] == "h"
    assert state.attributes["state_class"] == "total_increasing"
    other_key = next(candidate for candidate in COUNTER_VALUES if candidate != key)
    assert registry.async_get(_counter_id(registry, other_key)).disabled_by is er.RegistryEntryDisabler.INTEGRATION
    assert hass.states.get(_counter_id(registry, other_key)) is None
    mock_api["set_mode"].assert_not_awaited()
