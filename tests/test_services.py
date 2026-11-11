"""Test SmartGuard capability discovery through the Home Assistant action."""

from __future__ import annotations

from dataclasses import replace
from unittest.mock import AsyncMock

import probatio
import pytest
from homeassistant.auth.const import GROUP_ID_ADMIN, GROUP_ID_READ_ONLY
from homeassistant.auth.permissions.const import POLICY_READ
from homeassistant.const import ATTR_CONFIG_ENTRY_ID
from homeassistant.core import Context, HomeAssistant, ServiceResponse
from homeassistant.exceptions import ServiceValidationError, Unauthorized, UnknownUser
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.service import async_get_all_descriptions

from custom_components.meiertobler_smartguard.api import SmartGuardConnectionError
from custom_components.meiertobler_smartguard.const import (
    CONF_HOST,
    DOMAIN,
    HK60_MODE_SELECT_KEY,
)
from tests.ha_helpers import MockConfigEntry

from .conftest import TEST_GLOBAL_DEVICE_ID, TEST_IDENTITY

ACTION = "get_write_capabilities"
MODE_CAPABILITY = "hk60.operating_mode"


async def _catalogue(
    hass: HomeAssistant, entry_id: str, context: Context | None = None
) -> ServiceResponse:
    response = await hass.services.async_call(
        DOMAIN,
        ACTION,
        {ATTR_CONFIG_ENTRY_ID: entry_id},
        blocking=True,
        return_response=True,
        context=context,
    )
    assert response is not None
    return response


def _select_id(hass: HomeAssistant, global_id: str = TEST_GLOBAL_DEVICE_ID) -> str:
    entity_id = er.async_get(hass).async_get_entity_id(
        "select", DOMAIN, f"{global_id}_{HK60_MODE_SELECT_KEY}"
    )
    assert entity_id is not None
    return entity_id


async def test_catalogue_returns_existing_mode_control_without_gateway_io(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api: dict[str, AsyncMock],
) -> None:
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    counts = {key: mock.await_count for key, mock in mock_api.items()}

    assert await _catalogue(hass, config_entry.entry_id) == {
        "parameters": {
            MODE_CAPABILITY: {
                "type": "select",
                "available": True,
                "options": [
                    "auto",
                    "normal",
                    "reduced",
                    "frost_protection",
                    "heating",
                    "cooling",
                ],
                "action": "select.select_option",
                "target": {"entity_id": _select_id(hass)},
                "value_field": "option",
            }
        }
    }
    assert {key: mock.await_count for key, mock in mock_api.items()} == counts


async def test_catalogue_tracks_entity_rename_and_gateway_unavailability(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api: dict[str, AsyncMock],
) -> None:
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    renamed = "select.downstairs_heating_mode"
    er.async_get(hass).async_update_entity(_select_id(hass), new_entity_id=renamed)
    await hass.async_block_till_done()

    capability = (await _catalogue(hass, config_entry.entry_id))["parameters"][
        MODE_CAPABILITY
    ]
    assert capability["target"] == {"entity_id": renamed}
    assert capability["available"] is True

    mock_api["read_all"].side_effect = SmartGuardConnectionError("gateway offline")
    await config_entry.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()
    reads = mock_api["read_all"].await_count
    offline = (await _catalogue(hass, config_entry.entry_id))["parameters"][
        MODE_CAPABILITY
    ]
    assert offline == {**capability, "available": False}
    assert mock_api["read_all"].await_count == reads
    mock_api["set_mode"].assert_not_awaited()


async def test_disabled_select_is_omitted(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api: dict[str, AsyncMock],
) -> None:
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    er.async_get(hass).async_update_entity(
        _select_id(hass), disabled_by=er.RegistryEntryDisabler.USER
    )
    await hass.async_block_till_done()

    assert await _catalogue(hass, config_entry.entry_id) == {"parameters": {}}
    mock_api["set_mode"].assert_not_awaited()


async def test_catalogue_checks_read_permission_without_granting_control(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api: dict[str, AsyncMock],
) -> None:
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    await hass.auth.async_create_user("Test administrator", group_ids=[GROUP_ID_ADMIN])
    reader = await hass.auth.async_create_user(
        "Test reader", group_ids=[GROUP_ID_READ_ONLY]
    )
    denied = await hass.auth.async_create_user("Test user without entity permissions")
    entity_id = _select_id(hass)
    reader_context = Context(user_id=reader.id)

    assert (await _catalogue(hass, config_entry.entry_id, reader_context))[
        "parameters"
    ][MODE_CAPABILITY]["target"] == {"entity_id": entity_id}
    with pytest.raises(Unauthorized):
        await hass.services.async_call(
            "select",
            "select_option",
            {"entity_id": entity_id, "option": "heating"},
            blocking=True,
            context=reader_context,
        )
    with pytest.raises(Unauthorized) as denied_error:
        await _catalogue(hass, config_entry.entry_id, Context(user_id=denied.id))
    assert denied_error.value.permission == POLICY_READ
    assert denied_error.value.entity_id == entity_id
    with pytest.raises(UnknownUser):
        await _catalogue(hass, config_entry.entry_id, Context(user_id="unknown-user"))
    await hass.auth.async_update_user(reader, is_active=False)
    with pytest.raises(Unauthorized):
        await _catalogue(hass, config_entry.entry_id, reader_context)
    mock_api["set_mode"].assert_not_awaited()


async def test_catalogue_scopes_results_to_the_explicit_gateway(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api: dict[str, AsyncMock],
) -> None:
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    other_identity = replace(
        TEST_IDENTITY,
        global_device_id="fixture-gateway-two",
        serial_number="fixture-serial-two",
    )
    other = MockConfigEntry(
        domain=DOMAIN,
        title="Second SmartGuard",
        data={CONF_HOST: "192.0.2.11"},
        unique_id=other_identity.global_device_id,
    )
    other.add_to_hass(hass)
    mock_api["get_identity"].return_value = other_identity
    assert await hass.config_entries.async_setup(other.entry_id)
    await hass.async_block_till_done()

    first_target = (await _catalogue(hass, config_entry.entry_id))["parameters"][
        MODE_CAPABILITY
    ]["target"]
    second_target = (await _catalogue(hass, other.entry_id))["parameters"][
        MODE_CAPABILITY
    ]["target"]
    assert first_target == {"entity_id": _select_id(hass)}
    assert second_target == {
        "entity_id": _select_id(hass, other_identity.global_device_id)
    }
    assert first_target != second_target


async def test_catalogue_requires_a_loaded_target_and_response(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api: dict[str, AsyncMock],
) -> None:
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    description = (await async_get_all_descriptions(hass))[DOMAIN][ACTION]
    assert description["response"] == {"optional": False}
    assert description["fields"][ATTR_CONFIG_ENTRY_ID] == {
        "required": True,
        "selector": {"config_entry": {"integration": DOMAIN}},
    }
    with pytest.raises(probatio.Invalid):
        await hass.services.async_call(
            DOMAIN, ACTION, {}, blocking=True, return_response=True
        )
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, ACTION, {ATTR_CONFIG_ENTRY_ID: config_entry.entry_id}, blocking=True
        )

    other = MockConfigEntry(domain="test", title="Unrelated integration")
    other.add_to_hass(hass)
    assert await hass.config_entries.async_unload(config_entry.entry_id)
    assert hass.services.has_service(DOMAIN, ACTION)
    for entry_id in ("missing-entry", other.entry_id, config_entry.entry_id):
        with pytest.raises(ServiceValidationError) as invalid:
            await _catalogue(hass, entry_id)
        assert invalid.value.translation_key == "write_capabilities_target_unavailable"
        assert not invalid.value.translation_placeholders
