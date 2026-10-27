"""Native Home Assistant repair lifecycle and gateway identity protection."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.translation import async_get_translations
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.meiertobler_smartguard.api import (
    SmartGuardConnectionError,
    SmartGuardIdentity,
    SmartGuardInvalidResponseError,
    SmartGuardTimeoutError,
    SmartGuardUnsupportedDeviceError,
)
from custom_components.meiertobler_smartguard.const import DOMAIN
from custom_components.meiertobler_smartguard.issues import (
    async_create_configuration_issue,
)

from .conftest import (
    TEST_GLOBAL_DEVICE_ID,
    TEST_HOST,
    TEST_IDENTITY,
    TEST_SERIAL_NUMBER,
)


def _issues(registry: ir.IssueRegistry) -> list[ir.IssueEntry]:
    return [issue for issue in registry.issues.values() if issue.domain == DOMAIN]


@pytest.mark.parametrize(
    "reason", ["invalid_host", "unsupported_device", "wrong_device"]
)
async def test_permanent_configuration_error_creates_private_repair(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api: dict[str, AsyncMock],
    issue_registry: ir.IssueRegistry,
    reason: str,
) -> None:
    """Reject a known bad configuration before reading or controlling a gateway."""
    if reason == "invalid_host":
        hass.config_entries.async_update_entry(
            config_entry, data={CONF_HOST: "http://invalid.local/path"}
        )
    elif reason == "unsupported_device":
        mock_api["get_identity"].side_effect = SmartGuardUnsupportedDeviceError()
    else:
        mock_api["get_identity"].return_value = SmartGuardIdentity(
            "other-device", "other-serial", "1001"
        )
    saved_data = dict(config_entry.data)

    assert not await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.SETUP_ERROR
    assert config_entry.unique_id == TEST_GLOBAL_DEVICE_ID
    assert dict(config_entry.data) == saved_data
    mock_api["read_all"].assert_not_awaited()
    mock_api["set_mode"].assert_not_awaited()
    assert len(_issues(issue_registry)) == 1
    issue = issue_registry.async_get_issue(DOMAIN, f"{config_entry.entry_id}_{reason}")
    assert issue is not None
    assert issue.active and issue.is_persistent and not issue.is_fixable
    assert issue.severity is ir.IssueSeverity.ERROR
    assert issue.translation_key == reason
    assert issue.translation_placeholders == {
        "entry_title": config_entry.title,
        "integration_url": f"/config/integrations/integration/{DOMAIN}",
    }
    serialized = json.dumps(issue.to_json())
    for private in [
        TEST_HOST,
        TEST_GLOBAL_DEVICE_ID,
        TEST_SERIAL_NUMBER,
        "other-device",
    ]:
        assert private not in serialized


@pytest.mark.parametrize(
    "error",
    [
        SmartGuardConnectionError(),
        SmartGuardTimeoutError(),
        SmartGuardInvalidResponseError(),
    ],
)
async def test_uncertain_identity_failure_keeps_retry_without_repair(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api: dict[str, AsyncMock],
    issue_registry: ir.IssueRegistry,
    error: Exception,
) -> None:
    """A temporary or ambiguous response is not labelled a permanent problem."""
    mock_api["get_identity"].side_effect = error

    assert not await hass.config_entries.async_setup(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.SETUP_RETRY
    assert not _issues(issue_registry)


async def test_reload_deduplicates_and_success_clears_repair(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api: dict[str, AsyncMock],
    issue_registry: ir.IssueRegistry,
) -> None:
    """Repeated failures retain one issue; verified recovery removes it."""
    mock_api["get_identity"].side_effect = SmartGuardUnsupportedDeviceError()
    assert not await hass.config_entries.async_setup(config_entry.entry_id)
    first = _issues(issue_registry)[0]
    assert not await hass.config_entries.async_reload(config_entry.entry_id)
    assert len(_issues(issue_registry)) == 1
    assert _issues(issue_registry)[0].created == first.created

    mock_api["get_identity"].side_effect = None
    assert await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.LOADED
    assert not _issues(issue_registry)
    mock_api["set_mode"].assert_not_awaited()


async def test_new_permanent_reason_replaces_only_its_entry_issue(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api: dict[str, AsyncMock],
    issue_registry: ir.IssueRegistry,
) -> None:
    """A changed cause replaces obsolete advice instead of stacking notices."""
    mock_api["get_identity"].side_effect = SmartGuardUnsupportedDeviceError()
    assert not await hass.config_entries.async_setup(config_entry.entry_id)
    mock_api["get_identity"].side_effect = None
    mock_api["get_identity"].return_value = SmartGuardIdentity(
        "other", "serial", "1001"
    )
    assert not await hass.config_entries.async_reload(config_entry.entry_id)
    assert [issue.translation_key for issue in _issues(issue_registry)] == [
        "wrong_device"
    ]


async def test_transient_retry_does_not_erase_last_confirmed_problem(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api: dict[str, AsyncMock],
    issue_registry: ir.IssueRegistry,
) -> None:
    """A timeout cannot confirm that a known gateway mismatch has been resolved."""
    async_create_configuration_issue(hass, config_entry, "wrong_device")
    mock_api["get_identity"].side_effect = SmartGuardTimeoutError()
    assert not await hass.config_entries.async_setup(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.SETUP_RETRY
    assert [issue.translation_key for issue in _issues(issue_registry)] == [
        "wrong_device"
    ]


async def test_valid_identity_clears_repair_even_if_snapshot_is_temporarily_unavailable(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api: dict[str, AsyncMock],
    issue_registry: ir.IssueRegistry,
) -> None:
    """Identity recovery and temporary measurement failures are separate facts."""
    async_create_configuration_issue(hass, config_entry, "wrong_device")
    mock_api["read_all"].side_effect = SmartGuardConnectionError()
    assert not await hass.config_entries.async_setup(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.SETUP_RETRY
    assert not _issues(issue_registry)


async def test_reconfigure_preserves_registry_and_clears_issue_after_reload(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api: dict[str, AsyncMock],
    issue_registry: ir.IssueRegistry,
) -> None:
    """The existing reconfigure flow recovers the original device without writes."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    registry = er.async_get(hass)
    before = {
        entity.entity_id: entity.unique_id
        for entity in registry.entities.values()
        if entity.config_entry_id == config_entry.entry_id
    }
    mock_api["get_identity"].return_value = SmartGuardIdentity(
        "other", "serial", "1001"
    )
    assert not await hass.config_entries.async_reload(config_entry.entry_id)
    assert _issues(issue_registry)

    context = {"source": "reconfigure", "entry_id": config_entry.entry_id}
    rejected = await hass.config_entries.flow.async_init(
        DOMAIN, context=context.copy(), data={CONF_HOST: "other.local"}
    )
    assert rejected["type"] is FlowResultType.ABORT
    assert rejected["reason"] == "wrong_device"
    assert config_entry.data[CONF_HOST] == TEST_HOST
    assert _issues(issue_registry)

    mock_api["get_identity"].return_value = TEST_IDENTITY
    recovered = await hass.config_entries.flow.async_init(
        DOMAIN, context=context.copy(), data={CONF_HOST: "recovered.local"}
    )
    assert recovered["type"] is FlowResultType.ABORT
    assert recovered["reason"] == "reconfigure_successful"
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.LOADED
    assert config_entry.data[CONF_HOST] == "recovered.local"
    assert config_entry.unique_id == TEST_GLOBAL_DEVICE_ID
    assert not _issues(issue_registry)
    after = {
        entity.entity_id: entity.unique_id
        for entity in registry.entities.values()
        if entity.config_entry_id == config_entry.entry_id
    }
    assert after == before
    mock_api["set_mode"].assert_not_awaited()


async def test_removing_failed_entry_keeps_other_entries_and_unrelated_issues(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api: dict[str, AsyncMock],
    issue_registry: ir.IssueRegistry,
) -> None:
    """Removal cleans persistent notices only for the removed configuration."""
    other = MockConfigEntry(
        domain=DOMAIN,
        title="Second gateway",
        data={CONF_HOST: "192.0.2.20"},
        unique_id="second",
    )
    mock_api["get_identity"].side_effect = SmartGuardUnsupportedDeviceError()
    assert not await hass.config_entries.async_setup(config_entry.entry_id)
    other.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(other.entry_id)
    ir.async_create_issue(
        hass,
        DOMAIN,
        "unrelated",
        is_fixable=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key="wrong_device",
        translation_placeholders={
            "entry_title": "Example",
            "integration_url": "/config/integrations",
        },
    )
    assert len(_issues(issue_registry)) == 3
    assert await hass.config_entries.async_remove(config_entry.entry_id) == {
        "require_restart": False
    }
    assert (
        issue_registry.async_get_issue(
            DOMAIN, f"{config_entry.entry_id}_unsupported_device"
        )
        is None
    )
    assert (
        issue_registry.async_get_issue(DOMAIN, f"{other.entry_id}_unsupported_device")
        is not None
    )
    assert issue_registry.async_get_issue(DOMAIN, "unrelated") is not None


async def test_legacy_entry_without_unique_id_remains_loadable(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api: dict[str, AsyncMock],
    issue_registry: ir.IssueRegistry,
) -> None:
    """Do not invent an identity mismatch when no saved identity exists."""
    hass.config_entries.async_update_entry(config_entry, unique_id=None)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.LOADED
    assert not _issues(issue_registry)


@pytest.mark.parametrize("language", ["de", "en"])
async def test_native_repair_translations_resolve(
    hass: HomeAssistant, language: str
) -> None:
    """HA can render each supported repair without unresolved placeholders."""
    translations = await async_get_translations(hass, language, "issues", {DOMAIN})
    for reason in ["invalid_host", "unsupported_device", "wrong_device"]:
        prefix = f"component.{DOMAIN}.issues.{reason}"
        assert translations[f"{prefix}.title"]
        description = translations[f"{prefix}.description"].format(
            entry_title="Example SmartGuard",
            integration_url=f"/config/integrations/integration/{DOMAIN}",
        )
        assert "Example SmartGuard" in description
        assert f"/config/integrations/integration/{DOMAIN}" in description
