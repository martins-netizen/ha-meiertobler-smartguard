"""Short measurement names must not rename registered entities or their device."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from custom_components.meiertobler_smartguard.const import DOMAIN, MODEL
from custom_components.meiertobler_smartguard.diagnostics import (
    async_get_config_entry_diagnostics,
)
from custom_components.meiertobler_smartguard.entity import _circuit_display_name
from tests.ha_helpers import MockConfigEntry

from .conftest import TEST_GLOBAL_DEVICE_ID, TEST_SNAPSHOT
from .test_module_labels import LABELS
from .test_optional_measurements import EXTRA_VALUES


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        (None, "HK60"),
        ("HK60", "HK60"),
        ("HK 60", "HK60"),
        ("HK 60 Example floor circuit", "HK60: Example floor circuit"),
        ("hk60: Example floor circuit", "HK60: Example floor circuit"),
        ("HK60 - Example floor circuit", "HK60: Example floor circuit"),
        ("HK-60 · Example floor circuit", "HK60: Example floor circuit"),
        ("Example floor circuit", "HK60: Example floor circuit"),
        ("HK600 Example circuit", "HK60: HK600 Example circuit"),
        ("HK50 Example circuit", "HK60: HK50 Example circuit"),
    ],
)
def test_module_display_name(label: str | None, expected: str) -> None:
    assert _circuit_display_name("HK60", label) == expected


@pytest.mark.parametrize("language", ["en", "de"])
async def test_upgrade_retains_legacy_ids_device_custom_names_and_settings(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api: dict[str, AsyncMock],
    language: str,
) -> None:
    hass.config.language = language
    registry = er.async_get(hass)
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, TEST_GLOBAL_DEVICE_ID)},
        name=MODEL,
    )
    legacy = {
        (
            "sensor",
            "hk60_flow_temperature",
        ): "sensor.synthetic_old_long_circuit_vorlauf_ist",
        (
            "sensor",
            "hk60_flow_target_temperature",
        ): "sensor.synthetic_old_long_circuit_vorlauf_soll",
        (
            "select",
            "hk60_selected_mode_select",
        ): "select.synthetic_old_long_circuit_modus",
    }
    for (domain, key), eid in legacy.items():
        registry.async_get_or_create(
            domain,
            DOMAIN,
            f"{TEST_GLOBAL_DEVICE_ID}_{key}",
            suggested_object_id=eid.split(".", 1)[1],
            device_id=device.id,
            config_entry=config_entry,
            original_name="Legacy long configured name",
            has_entity_name=True,
        )
    actual = legacy[("sensor", "hk60_flow_temperature")]
    registry.async_update_entity(actual, name="Custom existing flow")
    registry.async_update_entity_options(actual, "sensor", {"display_precision": 3})
    snapshot = {
        **TEST_SNAPSHOT,
        **EXTRA_VALUES,
        **LABELS,
        "hk60_label": "HK 60 Example floor circuit",
    }
    mock_api["read_all"].return_value = snapshot
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    for (domain, key), eid in legacy.items():
        assert (
            registry.async_get_entity_id(
                domain, DOMAIN, f"{TEST_GLOBAL_DEVICE_ID}_{key}"
            )
            == eid
        )
        assert registry.async_get(eid).device_id == device.id
        assert (
            hass.states.get(eid).attributes["module_name"]
            == "HK 60 Example floor circuit"
        )
        assert (
            hass.states.get(eid).attributes["module_display_name"]
            == "HK60: Example floor circuit"
        )
    assert (
        hass.states.get(actual)
        .attributes["friendly_name"]
        .endswith("Custom existing flow")
    )
    assert registry.async_get(actual).options["sensor"]["display_precision"] == 3
    target = legacy[("sensor", "hk60_flow_target_temperature")]
    assert (
        hass.states.get(target)
        .attributes["friendly_name"]
        .endswith("Vorlauf SOLL · HK60" if language == "de" else "Flow target · HK60")
    )
    ambient = registry.async_get_entity_id(
        "sensor", DOMAIN, f"{TEST_GLOBAL_DEVICE_ID}_controller_outdoor_temperature"
    )
    assert ambient
    assert (
        hass.states.get(ambient)
        .attributes["friendly_name"]
        .endswith(
            "Aussentemperaturfühler"
            if language == "de"
            else "Outdoor temperature sensor"
        )
    )
    renamed = {**snapshot, "hk60_label": "Example renamed circuit"}
    mock_api["read_all"].return_value = renamed
    await config_entry.runtime_data.coordinator.async_request_refresh()
    await hass.async_block_till_done()
    assert (
        hass.states.get(target).attributes["module_display_name"]
        == "HK60: Example renamed circuit"
    )
    assert await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()
    for (domain, key), eid in legacy.items():
        assert (
            registry.async_get_entity_id(
                domain, DOMAIN, f"{TEST_GLOBAL_DEVICE_ID}_{key}"
            )
            == eid
        )
        assert registry.async_get(eid).device_id == device.id
    assert registry.async_get(actual).name == "Custom existing flow"
    for mock in mock_api.values():
        mock.reset_mock()
    diagnostics = await async_get_config_entry_diagnostics(hass, config_entry)
    assert "Example renamed circuit" not in str(diagnostics)
    assert "HK60: Example renamed circuit" not in str(diagnostics)
    for mock in mock_api.values():
        mock.assert_not_awaited()


@pytest.mark.parametrize("language", ["en", "de"])
def test_measurements_are_first_and_names_have_bounded_length(language: str) -> None:
    root = (
        Path(__file__).resolve().parents[1] / "custom_components/meiertobler_smartguard"
    )
    data = json.loads((root / "translations" / f"{language}.json").read_text())
    for platform in ("sensor", "select"):
        for key, description in data["entity"][platform].items():
            if key.startswith("hk60_") and not key.endswith("_label"):
                name = description["name"].format(module_suffix=" · HK60")
                assert name.endswith(" · HK60")
                assert not name.startswith("HK60")
                assert len(name) <= 29
                assert "{module_prefix}" not in description["name"]
