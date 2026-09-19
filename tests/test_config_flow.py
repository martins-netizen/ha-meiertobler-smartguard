"""Tests for the SmartGuard configuration flows."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.meiertobler_smartguard.api import (
    SmartGuardConnectionError,
    SmartGuardIdentity,
    SmartGuardInvalidResponseError,
    SmartGuardTimeoutError,
    SmartGuardUnsupportedDeviceError,
)
from custom_components.meiertobler_smartguard.const import CONF_HOST, DOMAIN, MODEL

from .conftest import TEST_GLOBAL_DEVICE_ID, TEST_HOST, TEST_IDENTITY


async def test_user_flow_success(hass: HomeAssistant) -> None:
    """A valid gateway creates one normalized config entry."""
    with patch(
        "custom_components.meiertobler_smartguard.config_flow."
        "SmartGuardApiClient"
    ) as client_class:
        client = client_class.return_value
        client.async_get_identity = AsyncMock(return_value=TEST_IDENTITY)
        client.async_read_all = AsyncMock(return_value={})

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
        assert result["type"] is FlowResultType.FORM

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "  SMARTGUARD.LOCAL.  "},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == MODEL
    assert result["data"] == {CONF_HOST: "smartguard.local"}
    assert result["result"].unique_id == TEST_GLOBAL_DEVICE_ID
    client.async_read_all.assert_awaited_once_with(TEST_IDENTITY.serial_number)


@pytest.mark.parametrize(
    ("error", "field", "expected"),
    [
        (SmartGuardTimeoutError(), "base", "cannot_connect"),
        (SmartGuardConnectionError(), "base", "cannot_connect"),
        (SmartGuardUnsupportedDeviceError(), "base", "unsupported_device"),
        (SmartGuardInvalidResponseError(), "base", "invalid_response"),
        (RuntimeError(), "base", "unknown"),
    ],
)
async def test_user_flow_maps_validation_errors(
    hass: HomeAssistant,
    error: Exception,
    field: str,
    expected: str,
) -> None:
    """Validation failures are exposed as stable config-flow errors."""
    with patch(
        "custom_components.meiertobler_smartguard.config_flow."
        "SmartGuardConfigFlow._async_validate",
        new=AsyncMock(side_effect=error),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={CONF_HOST: TEST_HOST},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {field: expected}


async def test_user_flow_rejects_invalid_host(hass: HomeAssistant) -> None:
    """Invalid host syntax is rejected before network access."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={CONF_HOST: "http://smartguard.local"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_HOST: "invalid_host"}


async def test_user_flow_aborts_duplicate(hass: HomeAssistant) -> None:
    """The stable gateway identifier prevents duplicate entries."""
    existing = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: TEST_HOST},
        unique_id=TEST_GLOBAL_DEVICE_ID,
    )
    existing.add_to_hass(hass)

    with patch(
        "custom_components.meiertobler_smartguard.config_flow."
        "SmartGuardConfigFlow._async_validate",
        new=AsyncMock(return_value=TEST_IDENTITY),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={CONF_HOST: TEST_HOST},
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reconfigure_success(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> None:
    """Reconfiguration updates the host while preserving the device identity."""
    with patch(
        "custom_components.meiertobler_smartguard.config_flow."
        "SmartGuardConfigFlow._async_validate",
        new=AsyncMock(return_value=TEST_IDENTITY),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_RECONFIGURE,
                "entry_id": config_entry.entry_id,
            },
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "reconfigure"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "smartguard-new.local"},
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert config_entry.data == {CONF_HOST: "smartguard-new.local"}


async def test_reconfigure_rejects_wrong_device(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> None:
    """A host belonging to another gateway cannot replace the current entry."""
    other_identity = SmartGuardIdentity("other-device", "serial-999", "1001")
    with patch(
        "custom_components.meiertobler_smartguard.config_flow."
        "SmartGuardConfigFlow._async_validate",
        new=AsyncMock(return_value=other_identity),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_RECONFIGURE,
                "entry_id": config_entry.entry_id,
            },
            data={CONF_HOST: "other.local"},
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "wrong_device"
    assert config_entry.data == {CONF_HOST: TEST_HOST}


@pytest.mark.parametrize(
    ("host", "error", "field", "expected"),
    [
        ("bad/path", None, CONF_HOST, "invalid_host"),
        (TEST_HOST, SmartGuardConnectionError(), "base", "cannot_connect"),
        (TEST_HOST, SmartGuardTimeoutError(), "base", "cannot_connect"),
        (TEST_HOST, SmartGuardUnsupportedDeviceError(), "base", "unsupported_device"),
        (TEST_HOST, SmartGuardInvalidResponseError(), "base", "invalid_response"),
        (TEST_HOST, RuntimeError(), "base", "unknown"),
    ],
)
async def test_reconfigure_maps_errors(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    host: str,
    error: Exception | None,
    field: str,
    expected: str,
) -> None:
    """Reconfiguration exposes validation failures without changing the entry."""
    validate = AsyncMock(side_effect=error)
    with patch(
        "custom_components.meiertobler_smartguard.config_flow."
        "SmartGuardConfigFlow._async_validate",
        new=validate,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_RECONFIGURE,
                "entry_id": config_entry.entry_id,
            },
            data={CONF_HOST: host},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {field: expected}
    assert config_entry.data == {CONF_HOST: TEST_HOST}
    if error is None:
        validate.assert_not_awaited()
