"""Select entities for SmartGuard."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import SmartGuardError, SmartGuardWriteVerificationError
from .const import (
    DOMAIN,
    HK60_SELECTED_MODE_DATA_POINT,
    HK60_SELECTED_MODE_OPTIONS,
    HK60_SELECTED_MODE_TO_VALUE,
)
from .data import SmartGuardConfigEntry
from .entity import SmartGuardEntity

_VALUE_TO_OPTION = {
    value: option for option, value in HK60_SELECTED_MODE_TO_VALUE.items()
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SmartGuardConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the verified HK60 operating-mode select."""
    async_add_entities([SmartGuardModeSelect(entry)])


class SmartGuardModeSelect(SmartGuardEntity, SelectEntity):
    """Select the requested HK60 operating mode with readback verification."""

    _attr_translation_key = "hk60_selected_mode"

    def __init__(self, entry: SmartGuardConfigEntry) -> None:
        super().__init__(entry, "hk60_selected_mode_select")
        self._attr_options = list(HK60_SELECTED_MODE_OPTIONS)
        self._client = entry.runtime_data.client
        self._serial_number = entry.runtime_data.identity.serial_number

    @property
    def current_option(self) -> str | None:
        """Return the current option held in coordinator memory."""
        value = self.coordinator.data.get(HK60_SELECTED_MODE_DATA_POINT.key)
        if isinstance(value, bool) or not isinstance(value, int):
            return None
        return _VALUE_TO_OPTION.get(value)

    @property
    def available(self) -> bool:
        """Require a known mode as well as a successful coordinator update."""
        return super().available and self.current_option is not None

    async def async_select_option(self, option: str) -> None:
        """Write an allowed option, verify it, and refresh all entities."""
        if option not in HK60_SELECTED_MODE_TO_VALUE:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_mode",
                translation_placeholders={"option": option},
            )

        value = HK60_SELECTED_MODE_TO_VALUE[option]
        if self.current_option == option:
            await self.coordinator.async_request_refresh()
            return

        try:
            await self._client.async_set_hk60_selected_mode(
                self._serial_number,
                value,
            )
        except SmartGuardWriteVerificationError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="write_not_confirmed",
            ) from err
        except SmartGuardError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="write_failed",
            ) from err

        await self.coordinator.async_request_refresh()
