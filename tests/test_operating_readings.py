"""Read-only operating values: isolation, exact paths and native HA behavior."""

from __future__ import annotations

from unittest.mock import AsyncMock
from urllib.parse import urlsplit

import pytest
from homeassistant.components.diagnostics import REDACTED
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.translation import async_get_translations
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.meiertobler_smartguard.api import SmartGuardApiClient
from custom_components.meiertobler_smartguard.const import (
    DATA_POINTS,
    DOMAIN,
    OPTIONAL_DATA_POINTS,
)
from custom_components.meiertobler_smartguard.diagnostics import (
    async_get_config_entry_diagnostics,
)

from .conftest import TEST_GLOBAL_DEVICE_ID, TEST_HOST, TEST_SNAPSHOT
from .test_api import FakeResponse, FakeSession
from .test_optional_measurements import EXTRA_VALUES

PREFIX = "/api/v1/1001/654321"
NEW_PATHS = {
    "hk60_room_target_heating": "/1/2/datapoints/5201",
    "hk60_room_target_cooling": "/1/2/datapoints/5202",
    "controller_outdoor_temperature": "/datapoints/1115",
    "controller_smart_grid_status": "/datapoints/2703",
    "controller_generator_fault": "/datapoints/1004",
    "controller_priority1_fault": "/datapoints/1005",
    "controller_priority2_fault": "/datapoints/1006",
    "buffer_heating_request": "/2/1/datapoints/1004",
}
BINARY_KEYS = {
    "controller_generator_fault",
    "controller_priority1_fault",
    "controller_priority2_fault",
    "buffer_heating_request",
}


class RoutedSession(FakeSession):
    """Respond by path so one missing endpoint cannot shift later responses."""

    def __init__(self) -> None:
        super().__init__([])
        self.routes: dict[str, FakeResponse | Exception] = {
            PREFIX + suffix: FakeResponse(200, {"enabled": True, "label": "Private"})
            for suffix in ("/config", "/1/2/config", "/2/1/config", "/3/1/config")
        }
        values = {**TEST_SNAPSHOT, **EXTRA_VALUES}
        self.routes.update(
            {
                point.path("654321"): FakeResponse(200, {"value": values[point.key]})
                for point in (*DATA_POINTS, *OPTIONAL_DATA_POINTS)
            }
        )

    def get(self, url: object, **kwargs: object) -> FakeResponse:
        self.urls.append(str(url))
        self.calls.append(("GET", str(url), kwargs))
        response = self.routes[urlsplit(str(url)).path]
        if isinstance(response, Exception):
            raise response
        return response


async def test_eight_new_readings_use_exact_get_paths_and_shared_module_config() -> (
    None
):
    """No additional controller commands, retries or duplicate buffer config read."""
    session = RoutedSession()
    snapshot = await SmartGuardApiClient(TEST_HOST, session).async_read_all("654321")

    assert all(snapshot[key] == EXTRA_VALUES[key] for key in NEW_PATHS)
    assert len(session.calls) == 26
    assert all(method == "GET" for method, _, _ in session.calls)
    paths = [urlsplit(url).path for url in session.urls]
    for suffix in NEW_PATHS.values():
        assert paths.count(PREFIX + suffix) == 1
    for suffix in ("/config", "/1/2/config", "/2/1/config", "/3/1/config"):
        assert paths.count(PREFIX + suffix) == 1
    assert not any(
        path.endswith(suffix)
        for path in paths
        for suffix in ("/1106", "/2053", "/1002", "/3106")
    )
    assert snapshot["controller_smart_grid_status"] == 0
    assert snapshot["controller_generator_fault"] is False


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("hk60_room_target_heating", 4.9),
        ("hk60_room_target_cooling", 30.1),
        ("hk60_room_target_heating", -273.15),
        ("hk60_room_target_cooling", True),
        ("controller_outdoor_temperature", -273.15),
        ("controller_outdoor_temperature", 126),
        ("controller_outdoor_temperature", float("nan")),
        ("controller_smart_grid_status", 5),
        ("controller_smart_grid_status", -1),
        ("controller_smart_grid_status", 1.0),
        ("controller_smart_grid_status", True),
        ("controller_generator_fault", 0),
        ("controller_priority1_fault", 1),
        ("controller_priority2_fault", "false"),
        ("buffer_heating_request", "true"),
    ],
)
async def test_one_invalid_operating_value_never_removes_healthy_readings(
    key: str, value: object
) -> None:
    """Do not coerce wrong types or silently turn an invalid fault into off."""
    session = RoutedSession()
    session.routes[PREFIX + NEW_PATHS[key]] = FakeResponse(200, {"value": value})
    expected = {**TEST_SNAPSHOT, **EXTRA_VALUES}
    del expected[key]

    assert (
        await SmartGuardApiClient(TEST_HOST, session).async_read_all("654321")
        == expected
    )


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("hk60_room_target_heating", 5),
        ("hk60_room_target_cooling", 30),
        ("controller_outdoor_temperature", -50),
        ("controller_outdoor_temperature", 125),
        ("controller_smart_grid_status", 0),
        ("controller_smart_grid_status", 4),
        ("controller_generator_fault", False),
        ("controller_priority1_fault", True),
        ("buffer_heating_request", False),
    ],
)
async def test_new_reading_boundaries_off_and_zero_are_valid(
    key: str, value: object
) -> None:
    session = RoutedSession()
    session.routes[PREFIX + NEW_PATHS[key]] = FakeResponse(200, {"value": value})
    snapshot = await SmartGuardApiClient(TEST_HOST, session).async_read_all("654321")
    assert snapshot[key] == value


@pytest.mark.parametrize(
    "response",
    [
        FakeResponse(404, None),
        FakeResponse(416, None),
        FakeResponse(503, None),
        FakeResponse(200, {}),
        TimeoutError(),
    ],
)
async def test_optional_fault_input_recovers_without_breaking_original_entities(
    response: FakeResponse | Exception,
) -> None:
    """Fault unavailability and recovery must not be interpreted as a clear fault."""
    session = RoutedSession()
    key = "controller_generator_fault"
    path = PREFIX + NEW_PATHS[key]
    session.routes[path] = response
    client = SmartGuardApiClient(TEST_HOST, session)

    first = await client.async_read_all("654321")
    assert key not in first
    assert first["hk60_selected_mode"] == TEST_SNAPSHOT["hk60_selected_mode"]
    assert first["buffer_temperature"] == EXTRA_VALUES["buffer_temperature"]
    session.routes[path] = FakeResponse(200, {"value": True})
    assert (await client.async_read_all("654321"))[key] is True
    session.routes[path] = FakeResponse(200, {"value": False})
    assert (await client.async_read_all("654321"))[key] is False


@pytest.mark.parametrize("module", ["", "/1/2", "/2/1"])
async def test_disabled_operating_module_issues_no_datapoint_gets(module: str) -> None:
    """Shared config checks gate all optional reads belonging to that module."""
    session = RoutedSession()
    session.routes[PREFIX + module + "/config"] = FakeResponse(200, {"enabled": False})
    snapshot = await SmartGuardApiClient(TEST_HOST, session).async_read_all("654321")
    expected_missing = {
        point.key
        for point in OPTIONAL_DATA_POINTS
        if point.subsystem_path == {"": None, "/1/2": (1, 2), "/2/1": (2, 1)}[module]
    }
    assert all(key not in snapshot for key in expected_missing)
    assert all(snapshot[key] == value for key, value in TEST_SNAPSHOT.items())
    paths = [urlsplit(url).path for url in session.urls]
    for point in OPTIONAL_DATA_POINTS:
        if point.key in expected_missing:
            assert point.path("654321") not in paths


async def test_native_operating_entities_have_correct_units_semantics_and_recovery(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api: dict[str, AsyncMock],
) -> None:
    """Expose 16 sensors, six binary sensors and the single existing mode select."""
    snapshot = {**TEST_SNAPSHOT, **EXTRA_VALUES}
    mock_api["read_all"].return_value = snapshot
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    registry = er.async_get(hass)
    coordinator = config_entry.runtime_data.coordinator

    def entity_id(key: str) -> str:
        domain = "binary_sensor" if key in BINARY_KEYS else "sensor"
        result = registry.async_get_entity_id(
            domain, DOMAIN, f"{TEST_GLOBAL_DEVICE_ID}_{key}"
        )
        assert result is not None
        return result

    ids = {key: entity_id(key) for key in NEW_PATHS}
    for key in ("hk60_room_target_heating", "hk60_room_target_cooling"):
        state = hass.states.get(ids[key])
        assert float(state.state) == EXTRA_VALUES[key]
        assert state.attributes["device_class"] == "temperature"
        assert state.attributes["unit_of_measurement"] == "°C"
        assert "state_class" not in state.attributes
    outdoor = hass.states.get(ids["controller_outdoor_temperature"])
    assert outdoor.attributes["unit_of_measurement"] == "°C"
    assert outdoor.attributes["state_class"] == "measurement"
    grid = hass.states.get(ids["controller_smart_grid_status"])
    assert grid.state == "none"
    assert grid.attributes["options"] == ["none", "normal", "push", "eco", "forced"]
    for value, state in enumerate(("none", "normal", "push", "eco", "forced")):
        coordinator.async_set_updated_data(
            {**snapshot, "controller_smart_grid_status": value}
        )
        await hass.async_block_till_done()
        assert hass.states.get(ids["controller_smart_grid_status"]).state == state
    for key in BINARY_KEYS - {"buffer_heating_request"}:
        assert hass.states.get(ids[key]).attributes["device_class"] == "problem"
    assert hass.states.get(ids["controller_generator_fault"]).state == "off"
    assert hass.states.get(ids["controller_priority1_fault"]).state == "on"
    request = hass.states.get(ids["buffer_heating_request"])
    assert request.state == "off"
    assert "device_class" not in request.attributes
    entries = [
        e
        for e in registry.entities.values()
        if e.config_entry_id == config_entry.entry_id
    ]
    assert len(entries) == 23
    assert sum(e.domain == "sensor" for e in entries) == 16
    assert sum(e.domain == "binary_sensor" for e in entries) == 6
    assert sum(e.domain == "select" for e in entries) == 1

    # A partial or complete outage must never produce a healthy fault default.
    coordinator.async_set_updated_data(TEST_SNAPSHOT.copy())
    await hass.async_block_till_done()
    assert all(hass.states.get(eid).state == "unavailable" for eid in ids.values())
    coordinator.async_set_updated_data(snapshot)
    await hass.async_block_till_done()
    assert hass.states.get(ids["controller_priority1_fault"]).state == "on"
    coordinator.async_set_update_error(UpdateFailed("test outage"))
    await hass.async_block_till_done()
    assert all(hass.states.get(eid).state == "unavailable" for eid in ids.values())
    coordinator.async_set_updated_data(snapshot)
    await hass.async_block_till_done()
    assert hass.states.get(ids["controller_generator_fault"]).state == "off"
    mock_api["set_mode"].assert_not_awaited()

    # Native entity customizations and all discovered IDs survive reload.
    flow_id = registry.async_get_entity_id(
        "sensor", DOMAIN, f"{TEST_GLOBAL_DEVICE_ID}_hk60_flow_temperature"
    )
    assert flow_id is not None
    registry.async_update_entity(
        flow_id, new_entity_id="sensor.preserved_flow", name="Existing flow name"
    )
    await hass.async_block_till_done()
    assert await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()
    assert all(entity_id(key) == eid for key, eid in ids.items())
    assert registry.async_get("sensor.preserved_flow").name == "Existing flow name"
    assert hass.states.get("sensor.preserved_flow").state != "unavailable"
    assert (
        len(
            [
                e
                for e in registry.entities.values()
                if e.config_entry_id == config_entry.entry_id
            ]
        )
        == 23
    )

    # Diagnostics include only validated values and do no additional I/O.
    mock_api["get_identity"].reset_mock()
    mock_api["read_all"].reset_mock()
    diagnostics = await async_get_config_entry_diagnostics(hass, config_entry)
    assert diagnostics["identity"]["global_device_id"] == REDACTED
    assert TEST_HOST not in str(diagnostics)
    assert TEST_GLOBAL_DEVICE_ID not in str(diagnostics)
    assert diagnostics["coordinator"]["data"] == snapshot
    mock_api["get_identity"].assert_not_awaited()
    mock_api["read_all"].assert_not_awaited()
    mock_api["set_mode"].assert_not_awaited()


@pytest.mark.parametrize("value", [True, 1.0, 99])
async def test_unknown_or_malformed_smart_grid_status_is_unavailable(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api: dict[str, AsyncMock],
    value: object,
) -> None:
    """Protect presentation even if coordinator data bypasses API validation."""
    mock_api["read_all"].return_value = {
        **TEST_SNAPSHOT,
        "controller_smart_grid_status": value,
    }
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    entity_id = er.async_get(hass).async_get_entity_id(
        "sensor", DOMAIN, f"{TEST_GLOBAL_DEVICE_ID}_controller_smart_grid_status"
    )
    assert entity_id is not None
    assert hass.states.get(entity_id).state == "unavailable"
    config_entry.runtime_data.coordinator.async_set_updated_data(
        {**TEST_SNAPSHOT, "controller_smart_grid_status": 3}
    )
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == "eco"


@pytest.mark.parametrize("language", ["de", "en"])
async def test_native_operating_names_and_smart_grid_states_are_translated(
    hass: HomeAssistant, language: str
) -> None:
    """Resolve every new name and enum label through HA's translation loader."""
    translations = await async_get_translations(hass, language, "entity", {DOMAIN})
    for key in NEW_PATHS:
        domain = "binary_sensor" if key in BINARY_KEYS else "sensor"
        assert translations[f"component.{DOMAIN}.entity.{domain}.{key}.name"]
    prefix = f"component.{DOMAIN}.entity.sensor.controller_smart_grid_status.state"
    assert translations[f"{prefix}.none"] == (
        "Keine Vorgabe" if language == "de" else "None"
    )
    for state in ("normal", "push", "eco", "forced"):
        assert translations[f"{prefix}.{state}"]
