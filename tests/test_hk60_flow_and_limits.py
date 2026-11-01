"""UI-derived HK60 fields: exact API contracts and native read-only entities."""

from __future__ import annotations

from unittest.mock import AsyncMock
from urllib.parse import urlsplit

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.translation import async_get_translations
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.meiertobler_smartguard.api import SmartGuardApiClient
from custom_components.meiertobler_smartguard.const import DOMAIN
from custom_components.meiertobler_smartguard.sensor import (
    OPTIONAL_SENSOR_DESCRIPTIONS,
    SENSOR_DESCRIPTIONS,
)

from .conftest import TEST_GLOBAL_DEVICE_ID, TEST_HOST, TEST_SNAPSHOT
from .test_api import FakeResponse
from .test_operating_readings import PREFIX, RoutedSession
from .test_optional_measurements import EXTRA_VALUES

# Explicit UI bindings; synthetic values in EXTRA_VALUES are not field settings.
HK60_IDS = {
    "hk60_flow_target_temperature": 52204,
    "hk60_design_outdoor_temperature": 5221,
    "hk60_heating_on_temperature": 5271,
    "hk60_heating_off_temperature": 5272,
    "hk60_heating_on_damping": 5273,
    "hk60_heating_off_damping": 5274,
    "hk60_cooling_on_temperature": 5276,
    "hk60_cooling_off_temperature": 5277,
    "hk60_cooling_on_damping": 5278,
    "hk60_cooling_off_damping": 5279,
}


async def test_all_ten_hk60_fields_share_one_config_check_and_use_gets() -> None:
    """The new endpoints must not become controls or per-entity refreshes."""
    session = RoutedSession()
    data = await SmartGuardApiClient(TEST_HOST, session).async_read_all("654321")
    paths = [urlsplit(url).path for url in session.urls]
    for key, point_id in HK60_IDS.items():
        assert paths.count(f"{PREFIX}/1/2/datapoints/{point_id}") == 1
        assert data[key] == EXTRA_VALUES[key]
    assert paths.count(f"{PREFIX}/1/2/config") == 1
    assert len(session.calls) == 36
    assert all(method == "GET" for method, _, _ in session.calls)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("hk60_flow_target_temperature", -273.15),
        ("hk60_flow_target_temperature", -50.1),
        ("hk60_flow_target_temperature", 125.1),
        ("hk60_flow_target_temperature", True),
        ("hk60_flow_target_temperature", "35"),
        ("hk60_flow_target_temperature", float("nan")),
        ("hk60_flow_target_temperature", float("inf")),
        ("hk60_design_outdoor_temperature", -60.1),
        ("hk60_design_outdoor_temperature", 60.1),
        ("hk60_heating_on_temperature", 4.9),
        ("hk60_heating_off_temperature", 30.1),
        ("hk60_cooling_on_temperature", False),
        ("hk60_cooling_off_temperature", "20"),
        ("hk60_heating_on_damping", 0),
        ("hk60_heating_off_damping", 48.1),
        ("hk60_cooling_on_damping", True),
        ("hk60_cooling_off_damping", "2"),
        ("hk60_cooling_off_damping", float("nan")),
    ],
)
async def test_invalid_hk60_value_is_isolated(key: str, value: object) -> None:
    """An invalid optional value cannot hide actual flow or healthy parameters."""
    session = RoutedSession()
    session.routes[f"{PREFIX}/1/2/datapoints/{HK60_IDS[key]}"] = FakeResponse(
        200, {"value": value}
    )
    expected = {**TEST_SNAPSHOT, **EXTRA_VALUES}
    del expected[key]
    assert (
        await SmartGuardApiClient(TEST_HOST, session).async_read_all("654321")
        == expected
    )


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("hk60_flow_target_temperature", -50),
        ("hk60_flow_target_temperature", 125),
        ("hk60_design_outdoor_temperature", -60),
        ("hk60_design_outdoor_temperature", 60),
        ("hk60_heating_on_temperature", 5),
        ("hk60_heating_off_temperature", 30),
        ("hk60_cooling_on_temperature", 5),
        ("hk60_cooling_off_temperature", 30),
        ("hk60_heating_on_damping", 1),
        ("hk60_heating_off_damping", 48),
        ("hk60_cooling_on_damping", 1.5),
        ("hk60_cooling_off_damping", 48.0),
    ],
)
async def test_valid_hk60_boundaries_and_decimal_durations(
    key: str, value: float
) -> None:
    """Preserve numeric duration/temperature precision without integer coercion."""
    session = RoutedSession()
    session.routes[f"{PREFIX}/1/2/datapoints/{HK60_IDS[key]}"] = FakeResponse(
        200, {"value": value}
    )
    result = await SmartGuardApiClient(TEST_HOST, session).async_read_all("654321")
    assert result[key] == value


@pytest.mark.parametrize(
    "response",
    [FakeResponse(404, None), FakeResponse(416, None), FakeResponse(503, None),
     FakeResponse(200, {}), TimeoutError()],
)
async def test_missing_flow_target_recovers_without_disturbing_actual_flow(
    response: FakeResponse | Exception,
) -> None:
    session = RoutedSession()
    path = f"{PREFIX}/1/2/datapoints/52204"
    session.routes[path] = response
    client = SmartGuardApiClient(TEST_HOST, session)
    missing = await client.async_read_all("654321")
    assert "hk60_flow_target_temperature" not in missing
    assert missing["hk60_flow_temperature"] == TEST_SNAPSHOT["hk60_flow_temperature"]
    assert missing["hk60_heating_on_damping"] == EXTRA_VALUES["hk60_heating_on_damping"]
    session.routes[path] = FakeResponse(200, {"value": 36.125})
    assert (await client.async_read_all("654321"))["hk60_flow_target_temperature"] == 36.125


async def test_hk60_sensors_have_distinct_names_units_and_setting_semantics(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api: dict[str, AsyncMock],
) -> None:
    """Current target is a measurement; thresholds/timers are reported settings."""
    snapshot = {**TEST_SNAPSHOT, **EXTRA_VALUES}
    mock_api["read_all"].return_value = snapshot
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    registry = er.async_get(hass)
    descriptions = {d.key: d for d in (*SENSOR_DESCRIPTIONS, *OPTIONAL_SENSOR_DESCRIPTIONS)}
    ids = {}
    for key in HK60_IDS:
        eid = registry.async_get_entity_id("sensor", DOMAIN, f"{TEST_GLOBAL_DEVICE_ID}_{key}")
        assert eid is not None
        ids[key] = eid
        state = hass.states.get(eid)
        assert float(state.state) == EXTRA_VALUES[key]
        duration = key.endswith("_damping")
        assert state.attributes["unit_of_measurement"] == ("h" if duration else "°C")
        assert state.attributes["device_class"] == ("duration" if duration else "temperature")
        assert descriptions[key].suggested_display_precision == (0 if duration else 1)
        if key == "hk60_flow_target_temperature":
            assert state.attributes["state_class"] == "measurement"
        else:
            assert "state_class" not in state.attributes
    assert len(set(ids.values())) == 10
    assert descriptions["hk60_flow_temperature"].suggested_display_precision == 1

    # Late discovery/failure/recovery is exercised for all optional keys by the
    # shared native tests; here preserve user customizations on both flow sensors.
    actual = registry.async_get_entity_id(
        "sensor", DOMAIN, f"{TEST_GLOBAL_DEVICE_ID}_hk60_flow_temperature"
    )
    assert actual is not None
    for eid in (actual, ids["hk60_flow_target_temperature"]):
        registry.async_update_entity(eid, name="Custom flow label")
        registry.async_update_entity_options(eid, "sensor", {"display_precision": 3})
    await hass.async_block_till_done()
    assert await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()
    for key, eid in ids.items():
        assert registry.async_get_entity_id("sensor", DOMAIN, f"{TEST_GLOBAL_DEVICE_ID}_{key}") == eid
    for eid in (actual, ids["hk60_flow_target_temperature"]):
        entry = registry.async_get(eid)
        assert entry.name == "Custom flow label"
        assert entry.options["sensor"]["display_precision"] == 3
    assert float(hass.states.get(ids["hk60_flow_target_temperature"]).state) == 34.75
    mock_api["set_mode"].assert_not_awaited()


@pytest.mark.parametrize("language", ["en", "de"])
async def test_hk60_names_use_native_translations(
    hass: HomeAssistant, language: str
) -> None:
    translations = await async_get_translations(hass, language, "entity", {DOMAIN})
    for key in HK60_IDS:
        assert translations[f"component.{DOMAIN}.entity.sensor.{key}.name"]
    assert translations[f"component.{DOMAIN}.entity.sensor.hk60_flow_target_temperature.name"] == (
        "HK60 Vorlauf SOLL" if language == "de" else "HK60 flow target temperature"
    )
