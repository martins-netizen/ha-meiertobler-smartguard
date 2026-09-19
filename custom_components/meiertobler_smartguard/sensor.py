"""Sensor entities for SmartGuard."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import SmartGuardValue
from .const import ENUM_STATES
from .data import SmartGuardConfigEntry
from .entity import SmartGuardEntity

ValueFormatter = Callable[[SmartGuardValue], str | float | int | None]


@dataclass(frozen=True, kw_only=True)
class SmartGuardSensorEntityDescription(SensorEntityDescription):
    """Describe a SmartGuard sensor."""

    value_formatter: ValueFormatter = lambda value: value


def _enum_formatter(key: str) -> ValueFormatter:
    states = ENUM_STATES[key]

    def formatter(value: SmartGuardValue) -> str | None:
        if isinstance(value, bool) or not isinstance(value, int):
            return None
        return states.get(value)

    return formatter


SENSOR_DESCRIPTIONS: tuple[SmartGuardSensorEntityDescription, ...] = (
    SmartGuardSensorEntityDescription(
        key="source_inlet_temperature",
        translation_key="source_inlet_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=2,
    ),
    SmartGuardSensorEntityDescription(
        key="condenser_inlet_temperature",
        translation_key="condenser_inlet_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=2,
    ),
    SmartGuardSensorEntityDescription(
        key="condenser_outlet_temperature",
        translation_key="condenser_outlet_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=2,
    ),
    SmartGuardSensorEntityDescription(
        key="hk60_flow_temperature",
        translation_key="hk60_flow_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=2,
    ),
    *(
        SmartGuardSensorEntityDescription(
            key=key,
            translation_key=key,
            device_class=SensorDeviceClass.ENUM,
            options=list(states.values()),
            value_formatter=_enum_formatter(key),
        )
        for key, states in ENUM_STATES.items()
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SmartGuardConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up SmartGuard sensors from a config entry."""
    async_add_entities(
        SmartGuardSensor(entry, description) for description in SENSOR_DESCRIPTIONS
    )


class SmartGuardSensor(SmartGuardEntity, SensorEntity):
    """Representation of one SmartGuard datapoint."""

    entity_description: SmartGuardSensorEntityDescription

    def __init__(
        self,
        entry: SmartGuardConfigEntry,
        description: SmartGuardSensorEntityDescription,
    ) -> None:
        super().__init__(entry, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> str | float | int | None:
        """Return the formatted value held in coordinator memory."""
        raw_value = self.coordinator.data.get(self.entity_description.key)
        if raw_value is None:
            return None
        return self.entity_description.value_formatter(
            cast("SmartGuardValue", raw_value)
        )

    @property
    def available(self) -> bool:
        """Mark an unknown future enum value unavailable instead of inventing a state."""
        return super().available and self.native_value is not None
