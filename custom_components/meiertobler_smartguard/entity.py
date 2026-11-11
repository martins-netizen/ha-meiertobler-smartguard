"""Base entity for SmartGuard."""

from __future__ import annotations

import re
from collections.abc import Mapping

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import normalize_module_label
from .const import (
    CIRCUIT_MODULE_NAMES,
    DOMAIN,
    ENTITY_MODULE_LABEL_KEYS,
    LABEL_MODULE_IDS,
    MANUFACTURER,
    MODEL,
    MODULE_LABEL_DEFAULT_NAMES,
)
from .coordinator import SmartGuardCoordinator
from .data import SmartGuardConfigEntry


def _circuit_display_name(circuit: str, label: str | None) -> str:
    """Keep the technical assignment and configured name out of measurement names."""
    if label is None:
        return circuit
    number = circuit.removeprefix("HK")
    name = re.sub(
        rf"^HK[ _-]*{number}(?:\s*[:·\u2013\u2014-]\s*|\s+|$)",
        "",
        label,
        count=1,
        flags=re.IGNORECASE,
    ).strip()
    return f"{circuit}: {name}" if name else circuit


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
        runtime = entry.runtime_data
        super().__init__(runtime.coordinator, context=key)
        identity = runtime.identity
        self._attr_unique_id = runtime.entity_unique_id(key)
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
        circuit = CIRCUIT_MODULE_NAMES.get(key or "")
        self._attr_translation_placeholders = {
            "module_prefix": f"{label} " if label else "",
            "module_suffix": f" · {circuit}" if circuit else "",
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
        if key in CIRCUIT_MODULE_NAMES:
            attributes["module_display_name"] = _circuit_display_name(
                CIRCUIT_MODULE_NAMES[key], label
            )
        return attributes

    @callback
    def _handle_coordinator_update(self) -> None:
        """Refresh translated names when only a module label changes."""
        self._update_module_name()
        super()._handle_coordinator_update()
