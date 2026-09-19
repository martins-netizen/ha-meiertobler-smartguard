"""Tests for redacted SmartGuard diagnostics."""

from __future__ import annotations

from homeassistant.components.diagnostics import REDACTED
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.meiertobler_smartguard.const import CONF_HOST
from custom_components.meiertobler_smartguard.diagnostics import (
    async_get_config_entry_diagnostics,
)

from .conftest import (
    TEST_GLOBAL_DEVICE_ID,
    TEST_HOST,
    TEST_IDENTITY,
    TEST_SERIAL_NUMBER,
    TEST_SNAPSHOT,
)


async def test_config_entry_diagnostics_redact_identifiers(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api: object,
) -> None:
    """Diagnostics expose useful state without host or device identifiers."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    diagnostics = await async_get_config_entry_diagnostics(hass, config_entry)

    assert diagnostics == {
        "config_entry": {"data": {CONF_HOST: REDACTED}},
        "identity": {
            "global_device_id": REDACTED,
            "serial_number": REDACTED,
            "device_type": TEST_IDENTITY.device_type,
        },
        "coordinator": {
            "last_update_success": True,
            "data": TEST_SNAPSHOT,
        },
    }
    assert config_entry.data[CONF_HOST] == TEST_HOST
    assert TEST_HOST not in str(diagnostics)
    assert TEST_GLOBAL_DEVICE_ID not in str(diagnostics)
    assert TEST_SERIAL_NUMBER not in str(diagnostics)
