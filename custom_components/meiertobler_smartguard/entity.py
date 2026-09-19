"""Base entity for SmartGuard."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import SmartGuardCoordinator
from .data import SmartGuardConfigEntry


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
