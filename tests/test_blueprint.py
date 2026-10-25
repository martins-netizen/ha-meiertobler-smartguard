"""Tests for the guarded SmartGuard automation blueprint."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.components.automation.config import (
    AUTOMATION_BLUEPRINT_SCHEMA,
    ValidationStatus,
    async_validate_config_item,
)
from homeassistant.components.blueprint.errors import MissingInput
from homeassistant.components.blueprint.importer import fetch_blueprint_from_url
from homeassistant.components.blueprint.models import Blueprint, BlueprintInputs
from homeassistant.core import HomeAssistant, ServiceCall, State
from homeassistant.exceptions import HomeAssistantError
from homeassistant.setup import async_setup_component
from homeassistant.util.yaml import load_yaml_dict
from pytest_homeassistant_custom_component.common import (
    async_fire_time_changed,
    mock_restore_cache,
)
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT_PATH = (
    ROOT
    / "blueprints"
    / "automation"
    / "martins_netizen"
    / "smartguard_guarded_night_heating.yaml"
)
BLUEPRINT_INPUTS: dict[str, Any] = {
    "mode_select": "select.smartguard_mode",
    "operating_status": "sensor.smartguard_operating_status",
    "enable_helper": "input_boolean.smartguard_night_heating",
    "override_helper": "input_boolean.smartguard_night_heating_owned",
    "indoor_temperature": "sensor.indoor_temperature_maximum",
    "maximum_indoor_temperature": 25.0,
    "heating_time": "23:00:00",
    "auto_time": "06:00:00",
}
PUBLIC_URL = (
    "https://github.com/martins-netizen/ha-meiertobler-smartguard/blob/main/"
    "blueprints/automation/martins_netizen/smartguard_guarded_night_heating.yaml"
)
RAW_URL = PUBLIC_URL.replace("github.com/", "raw.githubusercontent.com/").replace(
    "/blob/", "/"
)


@pytest.fixture(autouse=True)
async def _unload_test_automation(hass: HomeAssistant) -> AsyncIterator[None]:
    """Detach the real time/state listeners before each isolated HA is stopped."""
    yield
    if hass.services.has_service("automation", "turn_off"):
        await hass.services.async_call(
            "automation",
            "turn_off",
            {"entity_id": "automation.smartguard_blueprint_test", "stop_actions": True},
            blocking=True,
        )
        await hass.async_block_till_done()


def _load_blueprint() -> Blueprint:
    """Load the repository blueprint through Home Assistant's schema."""
    return Blueprint(
        load_yaml_dict(BLUEPRINT_PATH),
        path=BLUEPRINT_PATH.name,
        expected_domain="automation",
        schema=AUTOMATION_BLUEPRINT_SCHEMA,
    )


def _substitute_blueprint(
    input_values: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Substitute representative synthetic inputs into the blueprint."""
    blueprint = _load_blueprint()
    inputs = BlueprintInputs(
        blueprint,
        {
            "use_blueprint": {
                "path": f"martins-netizen/{BLUEPRINT_PATH.name}",
                "input": BLUEPRINT_INPUTS if input_values is None else input_values,
            }
        },
    )
    inputs.validate()
    return inputs.async_substitute()


def test_blueprint_schema_and_substitution() -> None:
    """Home Assistant accepts the metadata, selectors, inputs, and defaults."""
    blueprint = _load_blueprint()
    assert blueprint.validate() is None
    assert set(blueprint.inputs) == set(BLUEPRINT_INPUTS)

    automation = _substitute_blueprint()
    assert automation["triggers"][0]["at"] == "23:00:00"
    assert automation["triggers"][1]["at"] == "06:00:00"
    assert automation["mode"] == "queued"
    assert automation["max"] == 10


async def test_substituted_blueprint_is_valid_automation(
    hass: HomeAssistant,
) -> None:
    """The substituted blueprint passes Home Assistant automation validation."""
    validated = await async_validate_config_item(
        hass,
        "smartguard_guarded_night_heating",
        _substitute_blueprint(),
    )
    assert validated is not None
    assert validated.validation_status is ValidationStatus.OK


async def test_public_github_import_and_required_ownership_input(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Import the documented URL through HA, with HTTP content mocked locally."""
    aioclient_mock.get(RAW_URL, text=BLUEPRINT_PATH.read_text(encoding="utf-8"))
    imported = await fetch_blueprint_from_url(hass, PUBLIC_URL)
    assert imported.suggested_filename == (
        "martins-netizen/smartguard_guarded_night_heating"
    )
    assert imported.blueprint.metadata["source_url"] == PUBLIC_URL

    blueprint = Blueprint(
        imported.blueprint.data,
        expected_domain="automation",
        schema=AUTOMATION_BLUEPRINT_SCHEMA,
    )
    old_inputs = {k: v for k, v in BLUEPRINT_INPUTS.items() if k != "override_helper"}
    with pytest.raises(MissingInput):
        BlueprintInputs(
            blueprint, {"use_blueprint": {"path": "example.yaml", "input": old_inputs}}
        ).validate()
    inputs = BlueprintInputs(
        blueprint,
        {"use_blueprint": {"path": "example.yaml", "input": BLUEPRINT_INPUTS}},
    )
    inputs.validate()
    validated = await async_validate_config_item(
        hass, "imported_smartguard_blueprint", inputs.async_substitute()
    )
    assert validated is not None
    assert validated.validation_status is ValidationStatus.OK


async def _setup_automation(
    hass: HomeAssistant,
    *,
    mode: str = "auto",
    owned: bool = False,
    restore_owned: bool = False,
    fail_write: bool = False,
    confirm_write: bool = True,
    same_helper: bool = False,
) -> list[ServiceCall]:
    """Run real HA helpers/automations with a synthetic, isolated select service."""
    await hass.config.async_set_time_zone("UTC")
    await hass.async_start()
    if restore_owned:
        mock_restore_cache(hass, [State(BLUEPRINT_INPUTS["override_helper"], "on")])
    owner_config: dict[str, Any] = {} if restore_owned else {"initial": owned}
    assert await async_setup_component(
        hass,
        "input_boolean",
        {
            "input_boolean": {
                "smartguard_night_heating": {"initial": True},
                "smartguard_night_heating_owned": owner_config,
            }
        },
    )
    hass.states.async_set(BLUEPRINT_INPUTS["mode_select"], mode)
    hass.states.async_set(BLUEPRINT_INPUTS["operating_status"], "cooling")
    hass.states.async_set(
        BLUEPRINT_INPUTS["indoor_temperature"], "25.0", {"unit_of_measurement": "°C"}
    )
    writes: list[ServiceCall] = []

    async def select_option(call: ServiceCall) -> None:
        writes.append(call)
        if fail_write:
            raise HomeAssistantError("Synthetic write failure")
        if confirm_write:
            hass.states.async_set(
                BLUEPRINT_INPUTS["mode_select"], call.data["option"], context=call.context
            )

    hass.services.async_register("select", "select_option", select_option)
    input_values = BLUEPRINT_INPUTS.copy()
    if same_helper:
        input_values["override_helper"] = input_values["enable_helper"]
    automation = _substitute_blueprint(input_values)
    automation.update(alias="SmartGuard blueprint test", id="smartguard_blueprint_test")
    assert await async_setup_component(hass, "automation", {"automation": [automation]})
    await hass.async_block_till_done()
    return writes


async def _trigger(hass: HomeAssistant, trigger_id: str) -> None:
    """Exercise blueprint actions without bypassing the top-level condition."""
    automation = hass.data["automation"].get_entity("automation.smartguard_blueprint_test")
    assert automation is not None
    await automation.async_trigger(
        {"trigger": {"id": trigger_id}}, skip_condition=False
    )
    await hass.async_block_till_done()


async def _at(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, instant: str
) -> None:
    freezer.move_to(instant)
    async_fire_time_changed(hass, datetime.fromisoformat(instant))
    await hass.async_block_till_done()


async def test_scheduled_night_and_morning_cycle(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Real time triggers select heating, persist ownership, then return auto."""
    freezer.move_to("2026-10-25T22:59:00+00:00")
    writes = await _setup_automation(hass)
    await _at(hass, freezer, "2026-10-25T23:00:00+00:00")
    assert [call.data["option"] for call in writes] == ["heating"]
    assert hass.states.is_state(BLUEPRINT_INPUTS["override_helper"], "on")
    await _at(hass, freezer, "2026-10-26T06:00:00+00:00")
    assert [call.data["option"] for call in writes] == ["heating", "auto"]
    assert hass.states.is_state(BLUEPRINT_INPUTS["override_helper"], "off")


@pytest.mark.parametrize(
    ("entity", "state", "unit"),
    [
        ("enable_helper", "off", None),
        ("enable_helper", "unavailable", None),
        ("override_helper", "unavailable", None),
        ("mode_select", "normal", None),
        ("mode_select", "unavailable", None),
        ("operating_status", "heating", None),
        ("operating_status", "unknown", None),
        ("indoor_temperature", "25.1", "°C"),
        ("indoor_temperature", "unknown", "°C"),
        ("indoor_temperature", "unavailable", "°C"),
        ("indoor_temperature", "nan", "°C"),
        ("indoor_temperature", "inf", "°C"),
        ("indoor_temperature", "-inf", "°C"),
        ("indoor_temperature", "20", "°F"),
        ("indoor_temperature", "20", None),
    ],
)
async def test_night_safeguards_block_writes(
    hass: HomeAssistant, entity: str, state: str, unit: str | None
) -> None:
    """Missing, invalid and incompatible inputs never start an override."""
    writes = await _setup_automation(hass)
    attributes = {"unit_of_measurement": unit} if unit else {}
    hass.states.async_set(BLUEPRINT_INPUTS[entity], state, attributes)
    await hass.async_block_till_done()
    await _trigger(hass, "select_heating")
    assert writes == []


async def test_manual_heating_is_not_reset(hass: HomeAssistant) -> None:
    """Morning never owns an existing manually selected heating mode."""
    writes = await _setup_automation(hass, mode="heating")
    await _trigger(hass, "return_auto")
    assert writes == []
    assert hass.states.is_state(BLUEPRINT_INPUTS["mode_select"], "heating")


async def test_manual_mode_change_cancels_ownership(hass: HomeAssistant) -> None:
    """A mode change and even an immediate switch back relinquish ownership."""
    writes = await _setup_automation(hass)
    await _trigger(hass, "select_heating")
    hass.states.async_set(BLUEPRINT_INPUTS["mode_select"], "normal")
    hass.states.async_set(BLUEPRINT_INPUTS["mode_select"], "heating")
    await hass.async_block_till_done()
    assert hass.states.is_state(BLUEPRINT_INPUTS["override_helper"], "off")
    await _trigger(hass, "return_auto")
    assert [call.data["option"] for call in writes] == ["heating"]


async def test_disabled_enable_does_not_block_owned_morning_return(
    hass: HomeAssistant,
) -> None:
    """Disabling new overrides does not strand an already owned heating mode."""
    writes = await _setup_automation(hass, mode="heating", owned=True)
    hass.states.async_set(BLUEPRINT_INPUTS["enable_helper"], "off")
    await _trigger(hass, "return_auto")
    assert [call.data["option"] for call in writes] == ["auto"]
    assert hass.states.is_state(BLUEPRINT_INPUTS["override_helper"], "off")


async def test_restored_marker_allows_scheduled_morning_return(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """A restored real input_boolean retains ownership across a restart."""
    freezer.move_to("2026-10-26T05:59:00+00:00")
    writes = await _setup_automation(hass, mode="heating", restore_owned=True)
    assert hass.states.is_state(BLUEPRINT_INPUTS["override_helper"], "on")
    await _at(hass, freezer, "2026-10-26T06:00:00+00:00")
    assert [call.data["option"] for call in writes] == ["auto"]
    assert hass.states.is_state(BLUEPRINT_INPUTS["override_helper"], "off")


async def test_unavailable_mode_preserves_marker(hass: HomeAssistant) -> None:
    """A transient missing state does not claim successful morning recovery."""
    writes = await _setup_automation(hass, mode="heating", owned=True)
    hass.states.async_set(BLUEPRINT_INPUTS["mode_select"], "unavailable")
    await hass.async_block_till_done()
    await _trigger(hass, "return_auto")
    assert writes == []
    assert hass.states.is_state(BLUEPRINT_INPUTS["override_helper"], "on")


@pytest.mark.parametrize("confirm_write", [False, True])
async def test_failed_or_unconfirmed_write_never_creates_ownership(
    hass: HomeAssistant, confirm_write: bool
) -> None:
    """Neither a raised write failure nor missing readback creates ownership."""
    writes = await _setup_automation(
        hass, fail_write=confirm_write, confirm_write=confirm_write
    )
    await _trigger(hass, "select_heating")
    assert len(writes) == 1
    assert hass.states.is_state(BLUEPRINT_INPUTS["override_helper"], "off")


async def test_shared_enable_and_owner_helper_blocks_actions(
    hass: HomeAssistant,
) -> None:
    """Misconfiguring both inputs with one helper cannot reset manual heating."""
    writes = await _setup_automation(hass, mode="heating", same_helper=True)
    await _trigger(hass, "return_auto")
    await _trigger(hass, "select_heating")
    assert writes == []


@pytest.mark.parametrize("confirm_write", [False, True])
async def test_failed_morning_return_keeps_ownership(
    hass: HomeAssistant, confirm_write: bool
) -> None:
    """A failed or unconfirmed return cannot falsely clear the persistent marker."""
    writes = await _setup_automation(
        hass,
        mode="heating",
        owned=True,
        fail_write=confirm_write,
        confirm_write=confirm_write,
    )
    await _trigger(hass, "return_auto")
    assert len(writes) == 1
    assert hass.states.is_state(BLUEPRINT_INPUTS["override_helper"], "on")


async def test_existing_ownership_blocks_another_night_override(
    hass: HomeAssistant,
) -> None:
    """An unresolved previous override cannot silently acquire new ownership."""
    writes = await _setup_automation(hass, owned=True)
    await _trigger(hass, "select_heating")
    assert writes == []
