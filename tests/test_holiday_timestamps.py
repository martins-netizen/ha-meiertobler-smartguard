"""Reported holiday instants stay read-only, timezone-aware and private in diagnostics."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock
from zoneinfo import ZoneInfo

import pytest
from homeassistant.components.diagnostics import REDACTED
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.meiertobler_smartguard.api import SmartGuardApiClient
from custom_components.meiertobler_smartguard.const import (
    DOMAIN,
    HOLIDAY_TIMESTAMP_KEYS,
    MAX_TIMESTAMP_SECONDS,
)
from custom_components.meiertobler_smartguard.diagnostics import (
    async_get_config_entry_diagnostics,
)
from custom_components.meiertobler_smartguard.sensor import (
    OPTIONAL_SENSOR_DESCRIPTIONS,
    SmartGuardSensor,
)
from tests.ha_helpers import MockConfigEntry

from .conftest import TEST_GLOBAL_DEVICE_ID, TEST_HOST, TEST_SNAPSHOT
from .test_api import FakeResponse
from .test_operating_readings import PREFIX, RoutedSession
from .test_optional_measurements import EXTRA_VALUES

POINTS = {"hk60_holiday_start": 5226, "hk60_holiday_end": 5227}
DESCRIPTIONS = {d.key: d for d in OPTIONAL_SENSOR_DESCRIPTIONS if d.key in POINTS}


async def test_two_exact_gets_share_hk60_config_and_do_not_read_adjustment() -> None:
    session = RoutedSession()
    data = await SmartGuardApiClient(TEST_HOST, session).async_read_all("654321")
    paths = [call[1].split("654321", 1)[1] for call in session.calls]
    assert len(paths) == 44
    assert paths.count("/1/2/config") == 1
    for key, point in POINTS.items():
        assert paths.count(f"/1/2/datapoints/{point}") == 1
        assert type(data[key]) is int
        assert data[key] == EXTRA_VALUES[key]
    assert not any(path.endswith("/5241") for path in paths)
    assert all(method == "GET" for method, _, _ in session.calls)


@pytest.mark.parametrize("key", HOLIDAY_TIMESTAMP_KEYS)
@pytest.mark.parametrize("value", [None, True, False, "1893499200", 1893499200.0, float("nan"), float("inf"), {}, [], 0, -1, MAX_TIMESTAMP_SECONDS + 1, 10**400])
async def test_invalid_timestamp_isolated_and_recovers(key: str, value: object) -> None:
    session = RoutedSession()
    path = f"{PREFIX}/1/2/datapoints/{POINTS[key]}"
    session.routes[path] = FakeResponse(200, {"value": value})
    client = SmartGuardApiClient(TEST_HOST, session)
    data = await client.async_read_all("654321")
    assert key not in data
    assert data["hk60_flow_temperature"] == TEST_SNAPSHOT["hk60_flow_temperature"]
    other = next(item for item in POINTS if item != key)
    assert data[other] == EXTRA_VALUES[other]
    session.routes[path] = FakeResponse(200, {"value": EXTRA_VALUES[key]})
    assert (await client.async_read_all("654321"))[key] == EXTRA_VALUES[key]
    assert all(method == "GET" for method, _, _ in session.calls)


@pytest.mark.parametrize("response", [FakeResponse(404, {}), FakeResponse(416, {}), FakeResponse(200, {})])
async def test_missing_timestamp_does_not_suppress_other_readings(response: FakeResponse) -> None:
    session = RoutedSession()
    session.routes[f"{PREFIX}/1/2/datapoints/5226"] = response
    data = await SmartGuardApiClient(TEST_HOST, session).async_read_all("654321")
    assert "hk60_holiday_start" not in data
    assert data["hk60_holiday_end"] == EXTRA_VALUES["hk60_holiday_end"]
    assert data["hk60_selected_mode"] == 0


async def test_disabled_hk60_never_reads_holiday_points_of_any_circuit() -> None:
    session = RoutedSession()
    session.routes[f"{PREFIX}/1/2/config"] = FakeResponse(200, {"enabled": False})
    data = await SmartGuardApiClient(TEST_HOST, session).async_read_all("654321")
    assert not set(POINTS) & data.keys()
    assert not any(url.endswith(("/5226", "/5227")) for url in session.urls)


@pytest.mark.parametrize("seconds", [1, 2**31, MAX_TIMESTAMP_SECONDS])
async def test_integer_conversion_guards_are_not_a_2038_firmware_claim(seconds: int) -> None:
    session = RoutedSession()
    session.routes[f"{PREFIX}/1/2/datapoints/5226"] = FakeResponse(200, {"value": seconds})
    data = await SmartGuardApiClient(TEST_HOST, session).async_read_all("654321")
    assert data["hk60_holiday_start"] == seconds
    native = DESCRIPTIONS["hk60_holiday_start"].value_formatter(seconds)
    assert isinstance(native, datetime)
    assert native.tzinfo is UTC
    assert int(native.timestamp()) == seconds


@pytest.mark.parametrize(("utc", "local"), [
    ("2026-01-15T11:00:00+00:00", "2026-01-15T12:00"),
    ("2026-07-15T10:00:00+00:00", "2026-07-15T12:00"),
    ("2026-03-29T00:30:00+00:00", "2026-03-29T01:30"),
    ("2026-03-29T01:30:00+00:00", "2026-03-29T03:30"),
    ("2026-10-24T23:30:00+00:00", "2026-10-25T01:30"),
    ("2026-10-25T00:30:00+00:00", "2026-10-25T02:30"),
    ("2026-10-25T01:30:00+00:00", "2026-10-25T02:30"),
    ("2026-12-31T23:30:00+00:00", "2027-01-01T00:30"),
])
def test_synthetic_utc_instants_survive_dst_without_offset_reapplication(utc: str, local: str) -> None:
    expected = datetime.fromisoformat(utc)
    for description in DESCRIPTIONS.values():
        native = description.value_formatter(int(expected.timestamp()))
        assert native == expected
        assert native.tzinfo is UTC
        assert native.astimezone(ZoneInfo("Europe/Zurich")).strftime("%Y-%m-%dT%H:%M") == local


@pytest.mark.parametrize("language", ["en", "de"])
async def test_native_timestamp_metadata_privacy_and_preserved_customization(hass: HomeAssistant, config_entry: MockConfigEntry, mock_api: dict[str, AsyncMock], language: str) -> None:
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
        assert datetime.fromisoformat(state.state).tzinfo is not None
        assert state.attributes["device_class"] == "timestamp"
        assert "unit_of_measurement" not in state.attributes
        assert "state_class" not in state.attributes
        assert state.attributes["module_id"] == "1/2"
        assert registry.async_get(eid).entity_category.value == "diagnostic"
        entity = SmartGuardSensor(config_entry, DESCRIPTIONS[key])
        assert entity.native_value == datetime.fromtimestamp(EXTRA_VALUES[key], tz=UTC)
        expected = ("Ferienbeginn" if key.endswith("start") else "Ferienende") if language == "de" else ("Holiday start" if key.endswith("start") else "Holiday end")
        assert state.attributes["friendly_name"].endswith(expected + " · HK60")

    for mock in mock_api.values():
        mock.reset_mock()
    diagnostics = await async_get_config_entry_diagnostics(hass, config_entry)
    for key in POINTS:
        assert diagnostics["coordinator"]["data"][key] == REDACTED
        assert str(EXTRA_VALUES[key]) not in json.dumps(diagnostics)
        assert config_entry.runtime_data.coordinator.data[key] == EXTRA_VALUES[key]
    assert diagnostics["coordinator"]["data"]["hk60_flow_temperature"] == snapshot["hk60_flow_temperature"]
    for mock in mock_api.values():
        mock.assert_not_awaited()

    start = ids["hk60_holiday_start"]
    registry.async_update_entity(start, new_entity_id="sensor.preserved_holiday_start", name="My reported start")
    assert await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()
    assert registry.async_get_entity_id("sensor", DOMAIN, f"{TEST_GLOBAL_DEVICE_ID}_hk60_holiday_start") == "sensor.preserved_holiday_start"
    assert registry.async_get("sensor.preserved_holiday_start").name == "My reported start"
    assert registry.async_get_entity_id("sensor", DOMAIN, f"{TEST_GLOBAL_DEVICE_ID}_hk60_holiday_end") == ids["hk60_holiday_end"]
    mock_api["set_mode"].assert_not_awaited()


async def test_late_discovery_and_invalid_cached_values_stay_unavailable(hass: HomeAssistant, config_entry: MockConfigEntry, mock_api: dict[str, AsyncMock]) -> None:
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    registry = er.async_get(hass)
    assert registry.async_get_entity_id("sensor", DOMAIN, f"{TEST_GLOBAL_DEVICE_ID}_hk60_holiday_start") is None
    coordinator = config_entry.runtime_data.coordinator
    snapshot = {**TEST_SNAPSHOT, **EXTRA_VALUES}
    coordinator.async_set_updated_data(snapshot)
    await hass.async_block_till_done()
    eid = registry.async_get_entity_id("sensor", DOMAIN, f"{TEST_GLOBAL_DEVICE_ID}_hk60_holiday_start")
    assert eid
    expected = hass.states.get(eid).state
    for invalid in (None, False, 1.0, "1893499200", 0, -1, MAX_TIMESTAMP_SECONDS + 1):
        coordinator.async_set_updated_data({**snapshot, "hk60_holiday_start": invalid})
        await hass.async_block_till_done()
        assert hass.states.get(eid).state == "unavailable"
        assert hass.states.get(registry.async_get_entity_id("sensor", DOMAIN, f"{TEST_GLOBAL_DEVICE_ID}_hk60_holiday_end")).state != "unavailable"
    coordinator.async_set_updated_data(snapshot)
    await hass.async_block_till_done()
    assert hass.states.get(eid).state == expected
    assert registry.async_get_entity_id("sensor", DOMAIN, f"{TEST_GLOBAL_DEVICE_ID}_hk60_holiday_start") == eid
    mock_api["set_mode"].assert_not_awaited()
