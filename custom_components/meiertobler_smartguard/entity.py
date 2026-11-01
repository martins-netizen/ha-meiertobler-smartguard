"""Base entity for SmartGuard."""

from __future__ import annotations

from collections.abc import Mapping

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import normalize_module_label
from .const import (
    DOMAIN,
    ENTITY_MODULE_LABEL_KEYS,
    LABEL_MODULE_IDS,
    MANUFACTURER,
    MODEL,
    MODULE_LABEL_DEFAULT_NAMES,
)
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
        self._module_label_key = ENTITY_MODULE_LABEL_KEYS.get(key)
        self._update_module_name()
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, identity.global_device_id)},
            manufacturer=MANUFACTURER,
            model=MODEL,
            name=MODEL,
            serial_number=identity.serial_number,
        )

    def _update_module_name(self) -> None:
        """Use local configured labels while retaining translated fallbacks."""
        key = self._module_label_key
        label = normalize_module_label(self.coordinator.data.get(key)) if key else None
        if label is None:
            language = self.coordinator.hass.config.language
            names = MODULE_LABEL_DEFAULT_NAMES.get(key or "", ("", ""))
            label = names[1 if language == "de" else 0]
        self._attr_translation_placeholders = {
            "module_prefix": f"{label} " if label else ""
        }
        self.__dict__.pop("translation_placeholders", None)
        self.__dict__.pop("name", None)

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        """Keep the technical module assignment available alongside its label."""
        key = self._module_label_key
        if key is None:
            return None
        attributes = {"module_id": LABEL_MODULE_IDS[key]}
        label = normalize_module_label(self.coordinator.data.get(key))
        if label is not None:
            attributes["module_name"] = label
        return attributes

    @callback
    def _handle_coordinator_update(self) -> None:
        """Refresh translated names when only a module label changes."""
        self._update_module_name()
        super()._handle_coordinator_update()
