"""Sensor entities for SmartGuard."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import SmartGuardValue
from .const import (
    DATA_POINTS,
    ENUM_STATES,
    HOLIDAY_TIMESTAMP_KEYS,
    MAX_TIMESTAMP_SECONDS,
    MODULE_LABEL_KEYS,
)
from .data import SmartGuardConfigEntry
from .entity import SmartGuardEntity, async_add_optional_entities

ValueFormatter = Callable[[SmartGuardValue], str | float | int | datetime | None]


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


def _timestamp_formatter(value: SmartGuardValue) -> datetime | None:
    """Expose positive whole Unix seconds as UTC, without local offset arithmetic."""
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    if not 1 <= value <= MAX_TIMESTAMP_SECONDS:
        return None
    return datetime(1970, 1, 1, tzinfo=UTC) + timedelta(seconds=value)


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
        suggested_display_precision=1,
    ),
    *(
        SmartGuardSensorEntityDescription(
            key=point.key,
            translation_key=point.key,
            device_class=SensorDeviceClass.ENUM,
            options=list(ENUM_STATES[point.key].values()),
            value_formatter=_enum_formatter(point.key),
        )
        for point in DATA_POINTS
        if point.kind == "enum"
    ),
)

OPTIONAL_SENSOR_DESCRIPTIONS: tuple[SmartGuardSensorEntityDescription, ...] = (
    *(
        SmartGuardSensorEntityDescription(
            key=key,
            translation_key=key,
            device_class=SensorDeviceClass.TIMESTAMP,
            entity_category=EntityCategory.DIAGNOSTIC,
            value_formatter=_timestamp_formatter,
        )
        for key in HOLIDAY_TIMESTAMP_KEYS
    ),
    SmartGuardSensorEntityDescription(
        key="hk60_heating_temperature_boost",
        translation_key="hk60_heating_temperature_boost",
        device_class=SensorDeviceClass.TEMPERATURE_DELTA,
        native_unit_of_measurement=UnitOfTemperature.KELVIN,
        suggested_unit_of_measurement=UnitOfTemperature.KELVIN,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
    ),
    *(
        SmartGuardSensorEntityDescription(
            key=key,
            translation_key=key,
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            entity_category=EntityCategory.DIAGNOSTIC,
            suggested_display_precision=1,
        )
        for key in (
            "hk60_design_flow_temperature",
            "hk60_minimum_flow_normal",
            "hk60_minimum_flow_reduced",
        )
    ),
    *(
        SmartGuardSensorEntityDescription(
            key=key,
            translation_key=key,
            entity_category=EntityCategory.DIAGNOSTIC,
            icon="mdi:label-outline",
        )
        for key in MODULE_LABEL_KEYS.values()
    ),
    SmartGuardSensorEntityDescription(
        key="hk60_flow_target_temperature",
        translation_key="hk60_flow_target_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
    ),
    *(
        SmartGuardSensorEntityDescription(
            key=key,
            translation_key=key,
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            suggested_display_precision=1,
        )
        for key in (
            "hk60_design_outdoor_temperature",
            "hk60_heating_on_temperature",
            "hk60_heating_off_temperature",
            "hk60_cooling_on_temperature",
            "hk60_cooling_off_temperature",
        )
    ),
    *(
        SmartGuardSensorEntityDescription(
            key=key,
            translation_key=key,
            device_class=SensorDeviceClass.DURATION,
            native_unit_of_measurement=UnitOfTime.HOURS,
            suggested_display_precision=0,
        )
        for key in (
            "hk60_heating_on_damping",
            "hk60_heating_off_damping",
            "hk60_cooling_on_damping",
            "hk60_cooling_off_damping",
        )
    ),
    *(
        SmartGuardSensorEntityDescription(
            key=key,
            translation_key=key,
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            suggested_display_precision=1,
        )
        for key in ("hk60_room_target_heating", "hk60_room_target_cooling")
    ),
    SmartGuardSensorEntityDescription(
        key="controller_outdoor_temperature",
        translation_key="controller_outdoor_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=2,
    ),
    SmartGuardSensorEntityDescription(
        key="controller_smart_grid_status",
        translation_key="controller_smart_grid_status",
        device_class=SensorDeviceClass.ENUM,
        options=list(ENUM_STATES["controller_smart_grid_status"].values()),
        value_formatter=_enum_formatter("controller_smart_grid_status"),
    ),
    *(
        SmartGuardSensorEntityDescription(
            key=key,
            translation_key=key,
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            suggested_display_precision=2,
        )
        for key in ("buffer_temperature", "dhw_temperature")
    ),
    *(
        SmartGuardSensorEntityDescription(
            key=key,
            translation_key=key,
            device_class=SensorDeviceClass.DURATION,
            state_class=SensorStateClass.TOTAL_INCREASING,
            native_unit_of_measurement=UnitOfTime.HOURS,
            entity_category=EntityCategory.DIAGNOSTIC,
            suggested_display_precision=0,
        )
        for key in ("buffer_heater_operating_hours", "dhw_heater_operating_hours")
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
    async_add_optional_entities(
        entry,
        {
            description.key: SmartGuardSensor(entry, description)
            for description in OPTIONAL_SENSOR_DESCRIPTIONS
        },
        async_add_entities,
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
    def native_value(self) -> str | float | int | datetime | None:
        """Return the formatted value held in coordinator memory."""
        raw_value = self.coordinator.data.get(self.entity_description.key)
        if raw_value is None:
            return None
        return self.entity_description.value_formatter(raw_value)

    @property
    def available(self) -> bool:
        """Mark an invalid value unavailable instead of inventing a state."""
        return super().available and self.native_value is not None
