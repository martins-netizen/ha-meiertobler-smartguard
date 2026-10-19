"""Read-only heater status indicators reported by SmartGuard."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .data import SmartGuardConfigEntry
from .entity import SmartGuardEntity, async_add_optional_entities

DESCRIPTIONS = tuple(
    BinarySensorEntityDescription(
        key=key,
        translation_key=key,
        icon="mdi:radiator",
    )
    for key in ("buffer_heater_status", "dhw_heater_status")
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SmartGuardConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Discover indicators only after a valid boolean is returned."""
    async_add_optional_entities(
        entry,
        {
            description.key: SmartGuardBinarySensor(entry, description)
            for description in DESCRIPTIONS
        },
        async_add_entities,
    )


class SmartGuardBinarySensor(SmartGuardEntity, BinarySensorEntity):
    """Expose the gateway indicator without claiming measured heater power."""

    def __init__(
        self,
        entry: SmartGuardConfigEntry,
        description: BinarySensorEntityDescription,
    ) -> None:
        super().__init__(entry, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return the actual boolean; a missing reading is unknown, not off."""
        value = self.coordinator.data.get(self.entity_description.key)
        return value if isinstance(value, bool) else None

    @property
    def available(self) -> bool:
        """Unavailable indicators never silently become off."""
        return super().available and self.is_on is not None
