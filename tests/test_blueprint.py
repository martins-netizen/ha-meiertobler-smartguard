"""Tests for the guarded SmartGuard automation blueprint."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from homeassistant.components.automation.config import (
    AUTOMATION_BLUEPRINT_SCHEMA,
    ValidationStatus,
    async_validate_config_item,
)
from homeassistant.components.blueprint.models import Blueprint, BlueprintInputs
from homeassistant.core import HomeAssistant
from homeassistant.util.yaml import load_yaml_dict

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
    "indoor_temperature": "sensor.indoor_temperature_maximum",
    "maximum_indoor_temperature": 25.0,
    "heating_time": "23:00:00",
    "auto_time": "06:00:00",
}


def _load_blueprint() -> Blueprint:
    """Load the repository blueprint through Home Assistant's schema."""
    return Blueprint(
        load_yaml_dict(BLUEPRINT_PATH),
        path=BLUEPRINT_PATH.name,
        expected_domain="automation",
        schema=AUTOMATION_BLUEPRINT_SCHEMA,
    )


def _substitute_blueprint() -> dict[str, Any]:
    """Substitute representative synthetic inputs into the blueprint."""
    blueprint = _load_blueprint()
    inputs = BlueprintInputs(
        blueprint,
        {
            "use_blueprint": {
                "path": f"martins_netizen/{BLUEPRINT_PATH.name}",
                "input": BLUEPRINT_INPUTS,
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
    assert automation["mode"] == "single"
    assert automation["max_exceeded"] == "silent"


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
