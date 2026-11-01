"""Configured module labels: circuit assignment, naming, privacy and recovery."""

from __future__ import annotations

from unittest.mock import AsyncMock
from urllib.parse import urlsplit

import pytest
from homeassistant.components.diagnostics import REDACTED
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.meiertobler_smartguard.api import SmartGuardApiClient
from custom_components.meiertobler_smartguard.const import DOMAIN, MODULE_LABEL_KEYS
from custom_components.meiertobler_smartguard.diagnostics import (
    async_get_config_entry_diagnostics,
)
from custom_components.meiertobler_smartguard.entity import SmartGuardEntity

from .conftest import TEST_GLOBAL_DEVICE_ID, TEST_HOST, TEST_SNAPSHOT
from .test_api import FakeResponse
from .test_operating_readings import PREFIX, RoutedSession
from .test_optional_measurements import EXTRA_VALUES

LABELS = {
    "controller_label": "Example controller",
    "hk50_label": "Example radiators",
    "hk60_label": "Example floor circuit",
    "hk70_label": "Example secondary circuit",
    "buffer_label": "Example buffer",
    "dhw_label": "Example water storage",
}


def config_path(module: tuple[int, int] | None) -> str:
    suffix = "" if module is None else f"/{module[0]}/{module[1]}"
    return PREFIX + suffix + "/config"


async def test_labels_use_existing_configs_plus_only_hk50_and_hk70_configs() -> None:
    session = RoutedSession()
    for module, key in MODULE_LABEL_KEYS.items():
        session.routes[config_path(module)] = FakeResponse(200, {"enabled": True, "label": LABELS[key]})
    data = await SmartGuardApiClient(TEST_HOST, session).async_read_all("654321")
    assert data == {**TEST_SNAPSHOT, **EXTRA_VALUES, **LABELS}
    paths = [urlsplit(url).path for url in session.urls]
    assert len(paths) == 38
    for module in MODULE_LABEL_KEYS:
        assert paths.count(config_path(module)) == 1
    assert all(method == "GET" for method, _, _ in session.calls)
    assert not any("/1/1/datapoints/" in p or "/1/3/datapoints/" in p for p in paths)


@pytest.mark.parametrize("label", [None, True, 42, {}, [], "", "  ", "x" * 129,
                                   "name\x00", "name\nline", "name\u202e", "name\ud800"])
async def test_invalid_label_never_hides_numeric_values_or_leaks_to_logs(
    label: object, caplog: pytest.LogCaptureFixture,
) -> None:
    session = RoutedSession()
    session.routes[config_path((1, 2))] = FakeResponse(200, {"enabled": True, "label": label})
    data = await SmartGuardApiClient(TEST_HOST, session).async_read_all("654321")
    assert data == {**TEST_SNAPSHOT, **EXTRA_VALUES}
    assert "name" not in caplog.text


@pytest.mark.parametrize("label", ["  Example Ätage 2  ", "x" * 128, "Example {room} <north>"])
async def test_printable_labels_are_trimmed_and_kept_as_plain_text(label: str) -> None:
    session = RoutedSession()
    session.routes[config_path((1, 2))] = FakeResponse(200, {"enabled": True, "label": label})
    data = await SmartGuardApiClient(TEST_HOST, session).async_read_all("654321")
    assert data["hk60_label"] == label.strip()


@pytest.mark.parametrize("response", [FakeResponse(404, None), FakeResponse(503, None),
                                      FakeResponse(200, {"enabled": False, "label": "Disabled"}),
                                      FakeResponse(200, {"enabled": "true", "label": "Unconfirmed"}),
                                      TimeoutError()])
async def test_optional_circuit_label_recovers_without_affecting_hk60(
    response: FakeResponse | Exception,
) -> None:
    session = RoutedSession()
    path = config_path((1, 1))
    session.routes[path] = response
    client = SmartGuardApiClient(TEST_HOST, session)
    assert await client.async_read_all("654321") == {**TEST_SNAPSHOT, **EXTRA_VALUES}
    session.routes[path] = FakeResponse(200, {"enabled": True, "label": "Example radiators"})
    assert (await client.async_read_all("654321"))["hk50_label"] == "Example radiators"


@pytest.mark.parametrize("language", ["en", "de"])
async def test_native_names_follow_labels_preserving_ids_custom_names_and_privacy(
    hass: HomeAssistant, config_entry: MockConfigEntry,
    mock_api: dict[str, AsyncMock], language: str,
) -> None:
    hass.config.language = language
    snapshot = {**TEST_SNAPSHOT, **EXTRA_VALUES, **LABELS}
    mock_api["read_all"].return_value = snapshot
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    registry = er.async_get(hass)

    def entity_id(key: str, domain: str = "sensor") -> str:
        eid = registry.async_get_entity_id(domain, DOMAIN, f"{TEST_GLOBAL_DEVICE_ID}_{key}")
        assert eid is not None
        return eid

    label_ids = {key: entity_id(key) for key in LABELS}
    for key, eid in label_ids.items():
        assert hass.states.get(eid).state == LABELS[key]
        assert registry.async_get(eid).entity_category.value == "diagnostic"
        assert "state_class" not in hass.states.get(eid).attributes
        assert "unit_of_measurement" not in hass.states.get(eid).attributes
    actual = entity_id("hk60_flow_temperature")
    target = entity_id("hk60_flow_target_temperature")
    mode = entity_id("hk60_selected_mode_select", "select")
    for eid in (actual, target, mode):
        attrs = hass.states.get(eid).attributes
        assert attrs["friendly_name"].endswith(" · HK60")
        assert LABELS["hk60_label"] not in attrs["friendly_name"]
        assert attrs["module_display_name"] == "HK60: " + LABELS["hk60_label"]
        assert attrs["module_name"] == LABELS["hk60_label"]
        assert attrs["module_id"] == "1/2"
    for key, label in [("buffer_temperature", LABELS["buffer_label"]), ("dhw_temperature", LABELS["dhw_label"])]:
        assert label in hass.states.get(entity_id(key)).attributes["friendly_name"]
    assert hass.states.get(label_ids["hk50_label"]).attributes["module_id"] == "1/1"
    assert hass.states.get(label_ids["hk70_label"]).attributes["module_id"] == "1/3"
    assert len([e for e in registry.entities.values() if e.config_entry_id == config_entry.entry_id]) == 39

    registry.async_update_entity(actual, name="Personal flow name")
    registry.async_update_entity_options(actual, "sensor", {"display_precision": 3})
    await hass.async_block_till_done()
    coordinator = config_entry.runtime_data.coordinator
    # Only text changes; unchanged numeric readings must still update the name.
    renamed = {**snapshot, "hk60_label": "Example renamed circuit"}
    mock_api["read_all"].return_value = renamed
    await coordinator.async_request_refresh()
    await hass.async_block_till_done()
    assert "Example renamed circuit" not in hass.states.get(target).attributes["friendly_name"]
    assert hass.states.get(target).attributes["module_display_name"] == "HK60: Example renamed circuit"
    assert "Example renamed circuit" not in hass.states.get(mode).attributes["friendly_name"]
    assert hass.states.get(mode).attributes["module_display_name"] == "HK60: Example renamed circuit"
    assert hass.states.get(actual).attributes["friendly_name"].endswith("Personal flow name")
    assert registry.async_get(actual).options["sensor"]["display_precision"] == 3
    assert await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()
    assert entity_id("hk60_flow_temperature") == actual
    assert entity_id("hk60_flow_target_temperature") == target
    assert entity_id("hk60_selected_mode_select", "select") == mode
    assert {key: entity_id(key) for key in LABELS} == label_ids
    coordinator = config_entry.runtime_data.coordinator

    for mock in mock_api.values():
        mock.reset_mock()
    diagnostics = await async_get_config_entry_diagnostics(hass, config_entry)
    for key, value in renamed.items():
        assert diagnostics["coordinator"]["data"][key] == (REDACTED if key in LABELS else value)
    for label in renamed.values():
        if isinstance(label, str):
            assert label not in str(diagnostics)
    assert coordinator.data["hk60_label"] == "Example renamed circuit"
    for mock in mock_api.values():
        mock.assert_not_awaited()

    coordinator.async_set_updated_data({**TEST_SNAPSHOT, **EXTRA_VALUES})
    await hass.async_block_till_done()
    assert "HK60" in hass.states.get(target).attributes["friendly_name"]
    assert "module_name" not in hass.states.get(target).attributes
    assert hass.states.get(actual).attributes["friendly_name"].endswith("Personal flow name")
    assert all(hass.states.get(eid).state == "unavailable" for eid in label_ids.values())
    unknown = SmartGuardEntity(config_entry, "unmapped_future_key")
    assert unknown.extra_state_attributes is None
    assert unknown.translation_placeholders == {"module_prefix": "", "module_suffix": ""}
