"""Actionable, entry-specific SmartGuard configuration issues."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import issue_registry as ir

from .const import DOMAIN

if TYPE_CHECKING:
    from .data import SmartGuardConfigEntry

type ConfigurationIssue = Literal["invalid_host", "unsupported_device", "wrong_device"]
_CONFIGURATION_ISSUES: tuple[ConfigurationIssue, ...] = (
    "invalid_host",
    "unsupported_device",
    "wrong_device",
)


@callback
def async_create_configuration_issue(
    hass: HomeAssistant,
    entry: SmartGuardConfigEntry,
    issue: ConfigurationIssue,
) -> None:
    """Keep one actionable issue per entry without storing gateway identifiers."""
    for other in _CONFIGURATION_ISSUES:
        if other != issue:
            ir.async_delete_issue(hass, DOMAIN, f"{entry.entry_id}_{other}")
    ir.async_create_issue(
        hass,
        DOMAIN,
        f"{entry.entry_id}_{issue}",
        is_fixable=False,
        is_persistent=True,
        severity=ir.IssueSeverity.ERROR,
        translation_key=issue,
        translation_placeholders={
            "entry_title": entry.title,
            "integration_url": f"/config/integrations/integration/{DOMAIN}",
        },
    )


@callback
def async_clear_configuration_issues(hass: HomeAssistant, entry_id: str) -> None:
    """Remove only the known configuration issues belonging to this entry."""
    for issue in _CONFIGURATION_ISSUES:
        ir.async_delete_issue(hass, DOMAIN, f"{entry_id}_{issue}")
