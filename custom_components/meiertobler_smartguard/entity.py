"""Base entity for SmartGuard."""

from __future__ import annotations

from collections.abc import Mapping

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import SmartGuardCoordinator
from .data import SmartGuardConfigEntry


@callback
def async_add_optional_entities(
    entry: SmartGuardConfigEntry,
    entities: Mapping[str, Entity],
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add each optional entity once its first valid reading arrives."""
    pending = dict(entities)
    coordinator = entry.runtime_data.coordinator

    @callback
    def add_discovered_entities() -> None:
        keys = [key for key in pending if key in coordinator.data]
        if keys:
            async_add_entities([pending.pop(key) for key in keys])

    entry.async_on_unload(coordinator.async_add_listener(add_discovered_entities))
    add_discovered_entities()


class SmartGuardEntity(CoordinatorEntity[SmartGuardCoordinator]):
    """Base entity associated with one SmartGuard gateway."""

    _attr_has_entity_name = True

    def __init__(self, entry: SmartGuardConfigEntry, key: str) -> None:
        super().__init__(entry.runtime_data.coordinator, context=key)
        identity = entry.runtime_data.identity
        self._attr_unique_id = f"{identity.global_device_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, identity.global_device_id)},
            manufacturer=MANUFACTURER,
            model=MODEL,
            name=MODEL,
            serial_number=identity.serial_number,
        )
