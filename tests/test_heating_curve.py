"""Heating-curve settings stay read-only and preserve temperature-delta semantics."""

from __future__ import annotations

from unittest.mock import AsyncMock
from urllib.parse import urlsplit

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.meiertobler_smartguard.api import SmartGuardApiClient
from custom_components.meiertobler_smartguard.const import DOMAIN
from tests.ha_helpers import MockConfigEntry

from .conftest import TEST_GLOBAL_DEVICE_ID, TEST_HOST, TEST_SNAPSHOT
from .test_api import FakeResponse
from .test_operating_readings import PREFIX, RoutedSession
from .test_optional_measurements import EXTRA_VALUES

POINTS = {
    "hk60_heating_temperature_boost": 5071,
    "hk60_design_flow_temperature": 5222,
    "hk60_minimum_flow_normal": 5223,
    "hk60_minimum_flow_reduced": 5225,
}


async def test_four_exact_gets_share_the_existing_hk60_config() -> None:
    session = RoutedSession()
    data = await SmartGuardApiClient(TEST_HOST, session).async_read_all("654321")
    paths = [urlsplit(url).path for url in session.urls]
    assert len(session.calls) == 44
    assert paths.count(f"{PREFIX}/1/2/config") == 1
    for key, point in POINTS.items():
        assert paths.count(f"{PREFIX}/1/2/datapoints/{point}") == 1
        assert data[key] == EXTRA_VALUES[key]
    assert not any(path.endswith(f"/{point}") for path in paths for point in (5241,))
    assert all(method == "GET" for method, _, _ in session.calls)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("hk60_heating_temperature_boost", -0.1),
        ("hk60_heating_temperature_boost", 16.1),
        ("hk60_heating_temperature_boost", False),
        ("hk60_heating_temperature_boost", "0"),
        ("hk60_heating_temperature_boost", float("nan")),
        ("hk60_design_flow_temperature", 9.9),
        ("hk60_design_flow_temperature", 80.1),
        ("hk60_design_flow_temperature", -273.15),
        ("hk60_minimum_flow_normal", 19.9),
        ("hk60_minimum_flow_normal", 90.1),
        ("hk60_minimum_flow_normal", True),
        ("hk60_minimum_flow_reduced", 14.9),
        ("hk60_minimum_flow_reduced", 90.1),
        ("hk60_minimum_flow_reduced", float("inf")),
    ],
)
async def test_bad_curve_setting_isolated_and_recovers(key: str, value: object) -> None:
    session = RoutedSession()
    path = f"{PREFIX}/1/2/datapoints/{POINTS[key]}"
    session.routes[path] = FakeResponse(200, {"value": value})
    client = SmartGuardApiClient(TEST_HOST, session)
    data = await client.async_read_all("654321")
    assert key not in data
    assert data["hk60_flow_temperature"] == TEST_SNAPSHOT["hk60_flow_temperature"]
    assert data["hk60_room_target_heating"] == EXTRA_VALUES["hk60_room_target_heating"]
    session.routes[path] = FakeResponse(200, {"value": EXTRA_VALUES[key]})
    assert (await client.async_read_all("654321"))[key] == EXTRA_VALUES[key]


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("hk60_heating_temperature_boost", 0),
        ("hk60_heating_temperature_boost", 16),
        ("hk60_heating_temperature_boost", 1.25),
        ("hk60_design_flow_temperature", 10),
        ("hk60_design_flow_temperature", 80),
        ("hk60_design_flow_temperature", 38.125),
        ("hk60_minimum_flow_normal", 20),
        ("hk60_minimum_flow_normal", 90),
        ("hk60_minimum_flow_reduced", 15),
        ("hk60_minimum_flow_reduced", 90),
    ],
)
async def test_numeric_boundaries_zero_and_precision(key: str, value: float) -> None:
    session = RoutedSession()
    session.routes[f"{PREFIX}/1/2/datapoints/{POINTS[key]}"] = FakeResponse(200, {"value": value})
    data = await SmartGuardApiClient(TEST_HOST, session).async_read_all("654321")
    assert data[key] == value


@pytest.mark.parametrize("language", ["en", "de"])
async def test_native_diagnostics_and_delta_conversion(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api: dict[str, AsyncMock],
    language: str,
) -> None:
    hass.config.language = language
    snapshot = {**TEST_SNAPSHOT, **EXTRA_VALUES}
    mock_api["read_all"].return_value = snapshot
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    registry = er.async_get(hass)
    ids = {}
    for key in POINTS:
        eid = registry.async_get_entity_id("sensor", DOMAIN, f"{TEST_GLOBAL_DEVICE_ID}_{key}")
        assert eid
        ids[key] = eid
        state = hass.states.get(eid)
        assert float(state.state) == EXTRA_VALUES[key]
        assert "state_class" not in state.attributes
        assert state.attributes["friendly_name"].endswith(" · HK60")
        assert registry.async_get(eid).entity_category == "diagnostic"
        assert registry.async_get(eid).platform == DOMAIN
    boost = ids["hk60_heating_temperature_boost"]
    state = hass.states.get(boost)
    assert state.attributes["unit_of_measurement"] == "K"
    assert state.attributes["device_class"] == "temperature_delta"
    assert float(state.state) == 0  # Never -273.15 degrees Celsius.
    expected = "Überhöhung Heizen · HK60" if language == "de" else "Heating boost · HK60"
    assert state.attributes["friendly_name"].endswith(expected)
    for key in POINTS.keys() - {"hk60_heating_temperature_boost"}:
        state = hass.states.get(ids[key])
        assert state.attributes["device_class"] == "temperature"
        assert state.attributes["unit_of_measurement"] == "°C"

    registry.async_update_entity(boost, name="Custom boost")
    registry.async_update_entity_options(boost, "sensor", {"unit_of_measurement": "°F", "display_precision": 2})
    mock_api["read_all"].return_value = {**snapshot, "hk60_heating_temperature_boost": 1.25}
    assert await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()
    assert float(hass.states.get(boost).state) == pytest.approx(2.25)  # 1.25 K -> 2.25 F, no offset.
    assert hass.states.get(boost).attributes["unit_of_measurement"] == "°F"
    assert registry.async_get(boost).name == "Custom boost"
    assert registry.async_get(boost).options["sensor"]["display_precision"] == 2
    assert all(registry.async_get_entity_id("sensor", DOMAIN, f"{TEST_GLOBAL_DEVICE_ID}_{key}") == eid for key, eid in ids.items())
    mock_api["set_mode"].assert_not_awaited()
