"""Tests for optional storage measurements and independent failure handling."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.meiertobler_smartguard.api import (
    SmartGuardApiClient,
    SmartGuardInvalidResponseError,
)
from custom_components.meiertobler_smartguard.const import (
    DATA_POINTS,
    DOMAIN,
    OPTIONAL_DATA_POINTS,
)

from .conftest import TEST_GLOBAL_DEVICE_ID, TEST_SNAPSHOT
from .test_api import FakeResponse, FakeSession

EXTRA_VALUES = {
    "buffer_temperature": 28.25,
    "buffer_heater_status": False,
    "buffer_heater_operating_hours": 0,
    "dhw_temperature": 48.5,
    "dhw_heater_status": True,
    "dhw_heater_operating_hours": 12,
}


def _core_responses() -> list[FakeResponse]:
    return [
        FakeResponse(200, {"value": TEST_SNAPSHOT[point.key]}) for point in DATA_POINTS
    ]


async def test_enabled_storage_modules_use_documented_read_only_paths() -> None:
    """Optional values retain their exact types and never invoke a write."""
    responses = _core_responses()
    for group in (2, 3):
        responses.append(FakeResponse(200, {"enabled": True, "label": "Private label"}))
        responses.extend(
            FakeResponse(200, {"value": EXTRA_VALUES[point.key]})
            for point in OPTIONAL_DATA_POINTS
            if point.subsystem_path == (group, 1)
        )
    session = FakeSession(responses)
    client = SmartGuardApiClient("192.0.2.10", session)

    snapshot = await client.async_read_all("654321")

    assert snapshot == {**TEST_SNAPSHOT, **EXTRA_VALUES}
    assert snapshot["buffer_heater_status"] is False
    assert type(snapshot["buffer_heater_operating_hours"]) is int
    assert all(method == "GET" for method, _, _ in session.calls)
    assert {url.split("/654321/", 1)[1] for url in session.urls[8:]} == {
        "2/1/config",
        "2/1/datapoints/1001",
        "2/1/datapoints/3191",
        "2/1/datapoints/3192",
        "3/1/config",
        "3/1/datapoints/1001",
        "3/1/datapoints/4191",
        "3/1/datapoints/4192",
    }


@pytest.mark.parametrize(
    "config", [{"enabled": False}, {}, {"enabled": "true"}, {"enabled": 1}]
)
async def test_disabled_or_unconfirmed_modules_are_not_polled(
    config: dict[str, object],
) -> None:
    """Only the actual boolean true can enable optional module reads."""
    session = FakeSession(
        _core_responses() + [FakeResponse(200, config) for _ in range(2)]
    )
    client = SmartGuardApiClient("192.0.2.10", session)

    assert await client.async_read_all("654321") == TEST_SNAPSHOT
    assert len(session.urls) == 10


async def test_missing_and_transient_optional_modules_retry_on_next_update() -> None:
    """A 404 or timeout never breaks core values or permanently hides a module."""
    session = FakeSession(
        _core_responses()
        + [FakeResponse(404, None), TimeoutError()]
        + _core_responses()
        + [FakeResponse(200, {"enabled": True})]
        + [FakeResponse(200, {"value": value}) for value in (30.0, False, 0)]
        + [FakeResponse(200, {"enabled": False})]
    )
    client = SmartGuardApiClient("192.0.2.10", session)

    assert await client.async_read_all("654321") == TEST_SNAPSHOT
    updated = await client.async_read_all("654321")
    assert updated["buffer_temperature"] == 30.0
    assert updated["buffer_heater_status"] is False
    assert updated["buffer_heater_operating_hours"] == 0


async def test_one_missing_optional_value_does_not_hide_other_readings() -> None:
    """An unavailable temperature is omitted while status and hours stay valid."""
    session = FakeSession(
        [
            *_core_responses(),
            FakeResponse(200, {"enabled": True}),
            FakeResponse(503, None),
            FakeResponse(200, {"value": False}),
            FakeResponse(200, {"value": 0}),
            FakeResponse(200, {"enabled": False}),
        ]
    )
    snapshot = await SmartGuardApiClient("192.0.2.10", session).async_read_all("654321")

    assert "buffer_temperature" not in snapshot
    assert snapshot == {
        **TEST_SNAPSHOT,
        "buffer_heater_status": False,
        "buffer_heater_operating_hours": 0,
    }


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("buffer_temperature", -273.15),
        ("buffer_temperature", -50.1),
        ("dhw_temperature", 125.1),
        ("dhw_temperature", True),
        ("dhw_temperature", "25"),
        ("dhw_temperature", float("nan")),
        ("dhw_temperature", float("inf")),
        ("dhw_temperature", 10**400),
        ("buffer_heater_status", 0),
        ("buffer_heater_status", 1),
        ("dhw_heater_status", "false"),
        ("buffer_heater_operating_hours", -1),
        ("buffer_heater_operating_hours", 0.5),
        ("dhw_heater_operating_hours", False),
        ("dhw_heater_operating_hours", 2**31),
    ],
)
async def test_invalid_optional_values_are_rejected(key: str, value: object) -> None:
    """Reject sentinel temperatures, coercions and invalid counter values."""
    point = next(point for point in OPTIONAL_DATA_POINTS if point.key == key)
    session = FakeSession([FakeResponse(200, {"value": value})])
    client = SmartGuardApiClient("192.0.2.10", session)

    with pytest.raises(SmartGuardInvalidResponseError):
        await client.async_read_datapoint("654321", point)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("buffer_temperature", -50),
        ("dhw_temperature", 125),
        ("buffer_heater_operating_hours", 0),
        ("dhw_heater_operating_hours", 2**31 - 1),
        ("buffer_heater_status", False),
    ],
)
async def test_documented_boundary_values_remain_valid(key: str, value: object) -> None:
    """Off and zero are valid data, including documented numeric boundaries."""
    point = next(point for point in OPTIONAL_DATA_POINTS if point.key == key)
    session = FakeSession([FakeResponse(200, {"value": value})])
    assert (
        await SmartGuardApiClient("192.0.2.10", session).async_read_datapoint(
            "654321", point
        )
        == value
    )


async def test_optional_entities_appear_recover_and_unload(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api: dict[str, AsyncMock],
) -> None:
    """Late discovery, valid off/zero, unavailability and recovery work in HA."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    registry = er.async_get(hass)
    coordinator = config_entry.runtime_data.coordinator

    def entity_id(key: str) -> str | None:
        platform = "binary_sensor" if key.endswith("_status") else "sensor"
        return registry.async_get_entity_id(
            platform, DOMAIN, f"{TEST_GLOBAL_DEVICE_ID}_{key}"
        )

    assert all(entity_id(key) is None for key in EXTRA_VALUES)
    coordinator.async_set_updated_data({**TEST_SNAPSHOT, **EXTRA_VALUES})
    await hass.async_block_till_done()
    ids = {key: entity_id(key) for key in EXTRA_VALUES}
    assert all(ids.values())
    assert hass.states.get(ids["buffer_heater_status"]).state == "off"
    assert hass.states.get(ids["dhw_heater_status"]).state == "on"
    hours = hass.states.get(ids["buffer_heater_operating_hours"])
    assert hours.state == "0"
    assert hours.attributes["unit_of_measurement"] == "h"
    assert hours.attributes["state_class"] == "total_increasing"
    assert (
        hass.states.get(ids["dhw_temperature"]).attributes["unit_of_measurement"]
        == "°C"
    )

    coordinator.async_set_updated_data(TEST_SNAPSHOT.copy())
    await hass.async_block_till_done()
    assert all(hass.states.get(eid).state == "unavailable" for eid in ids.values())
    coordinator.async_set_updated_data({**TEST_SNAPSHOT, **EXTRA_VALUES})
    await hass.async_block_till_done()
    assert hass.states.get(ids["buffer_heater_status"]).state == "off"
    assert (
        sum(
            entity.config_entry_id == config_entry.entry_id
            for entity in registry.entities.values()
        )
        == 15
    )
    mock_api["set_mode"].assert_not_awaited()

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
    assert all(
        (state := hass.states.get(eid)) is None or state.state == "unavailable"
        for eid in ids.values()
    )
    coordinator.async_set_updated_data({**TEST_SNAPSHOT, **EXTRA_VALUES})
    await hass.async_block_till_done()
    assert all(
        (state := hass.states.get(eid)) is None or state.state == "unavailable"
        for eid in ids.values()
    )
