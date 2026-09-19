"""Shared fixtures for SmartGuard integration tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.meiertobler_smartguard.api import SmartGuardIdentity
from custom_components.meiertobler_smartguard.const import CONF_HOST, DOMAIN, MODEL

TEST_HOST = "192.0.2.10"
TEST_GLOBAL_DEVICE_ID = "global-123"
TEST_SERIAL_NUMBER = "serial-456"
TEST_IDENTITY = SmartGuardIdentity(
    global_device_id=TEST_GLOBAL_DEVICE_ID,
    serial_number=TEST_SERIAL_NUMBER,
    device_type="1001",
)
TEST_SNAPSHOT = {
    "source_inlet_temperature": 12.5,
    "condenser_inlet_temperature": 26.5,
    "condenser_outlet_temperature": 27.0,
    "hk60_flow_temperature": 25.0,
    "hk60_operating_status": 1,
    "hk60_selected_mode": 0,
    "hk60_effective_mode": 0,
    "hk60_season_status": 1,
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable loading integrations from custom_components."""


@pytest.fixture
def config_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Return a configured SmartGuard entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=MODEL,
        data={CONF_HOST: TEST_HOST},
        unique_id=TEST_GLOBAL_DEVICE_ID,
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def mock_api() -> dict[str, AsyncMock]:
    """Mock all gateway I/O used during integration setup."""
    with (
        patch(
            "custom_components.meiertobler_smartguard.api."
            "SmartGuardApiClient.async_get_identity",
            new=AsyncMock(return_value=TEST_IDENTITY),
        ) as get_identity,
        patch(
            "custom_components.meiertobler_smartguard.api."
            "SmartGuardApiClient.async_read_all",
            new=AsyncMock(return_value=TEST_SNAPSHOT.copy()),
        ) as read_all,
        patch(
            "custom_components.meiertobler_smartguard.api."
            "SmartGuardApiClient.async_set_hk60_selected_mode",
            new=AsyncMock(return_value=0),
        ) as set_mode,
    ):
        yield {
            "get_identity": get_identity,
            "read_all": read_all,
            "set_mode": set_mode,
        }
