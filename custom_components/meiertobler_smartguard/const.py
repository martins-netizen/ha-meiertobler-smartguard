"""Constants and verified datapoint definitions for SmartGuard."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

DOMAIN = "meiertobler_smartguard"
CONF_HOST = "host"
MANUFACTURER = "Meier Tobler"
MODEL = "SmartGuard 2.0"
EXPECTED_DEVICE_TYPE = "1001"
DEFAULT_UPDATE_INTERVAL_SECONDS = 60
DEFAULT_REQUEST_TIMEOUT_SECONDS = 10

DataPointKind = Literal["temperature", "enum", "counter", "boolean"]


@dataclass(frozen=True, slots=True)
class SmartGuardDataPoint:
    """Describe one verified SmartGuard datapoint."""

    key: str
    datapoint_id: int
    kind: DataPointKind
    subsystem_path: tuple[int, int] | None = None
    minimum: float | None = None
    maximum: float | None = None

    def path(self, serial_number: str) -> str:
        """Return the API path for this datapoint."""
        base = f"/api/v1/{EXPECTED_DEVICE_TYPE}/{serial_number}"
        if self.subsystem_path is not None:
            group, unit = self.subsystem_path
            base = f"{base}/{group}/{unit}"
        return f"{base}/datapoints/{self.datapoint_id}"


HK60_SELECTED_MODE_DATA_POINT = SmartGuardDataPoint(
    "hk60_selected_mode",
    5004,
    "enum",
    (1, 2),
)

DATA_POINTS: tuple[SmartGuardDataPoint, ...] = (
    SmartGuardDataPoint("source_inlet_temperature", 101001, "temperature"),
    SmartGuardDataPoint("condenser_inlet_temperature", 101008, "temperature"),
    SmartGuardDataPoint("condenser_outlet_temperature", 101009, "temperature"),
    SmartGuardDataPoint("hk60_flow_temperature", 1001, "temperature", (1, 2)),
    SmartGuardDataPoint("hk60_operating_status", 5003, "enum", (1, 2)),
    HK60_SELECTED_MODE_DATA_POINT,
    SmartGuardDataPoint("hk60_effective_mode", 5005, "enum", (1, 2)),
    SmartGuardDataPoint("hk60_season_status", 5009, "enum", (1, 2)),
)

# Manufacturer: SmartGuard, Netzwerk und Datenzugangspunkte, pages 9, 18-20.
# These modules are optional and must report enabled=true before polling.
OPTIONAL_DATA_POINTS: tuple[SmartGuardDataPoint, ...] = (
    SmartGuardDataPoint("buffer_temperature", 1001, "temperature", (2, 1), -50, 125),
    SmartGuardDataPoint("buffer_heater_status", 3191, "boolean", (2, 1)),
    SmartGuardDataPoint(
        "buffer_heater_operating_hours", 3192, "counter", (2, 1), 0, 2**31 - 1
    ),
    SmartGuardDataPoint("dhw_temperature", 1001, "temperature", (3, 1), -50, 125),
    SmartGuardDataPoint("dhw_heater_status", 4191, "boolean", (3, 1)),
    SmartGuardDataPoint(
        "dhw_heater_operating_hours", 4192, "counter", (3, 1), 0, 2**31 - 1
    ),
    SmartGuardDataPoint("hk60_room_target_heating", 5201, "temperature", (1, 2), 5, 30),
    SmartGuardDataPoint("hk60_room_target_cooling", 5202, "temperature", (1, 2), 5, 30),
    SmartGuardDataPoint(
        "controller_outdoor_temperature", 1115, "temperature", None, -50, 125
    ),
    SmartGuardDataPoint("controller_smart_grid_status", 2703, "enum", None, 0, 4),
    SmartGuardDataPoint("controller_generator_fault", 1004, "boolean"),
    SmartGuardDataPoint("controller_priority1_fault", 1005, "boolean"),
    SmartGuardDataPoint("controller_priority2_fault", 1006, "boolean"),
    SmartGuardDataPoint("buffer_heating_request", 1004, "boolean", (2, 1)),
)

ENUM_STATES: dict[str, dict[int, str]] = {
    "hk60_operating_status": {
        0: "standby",
        1: "heating",
        2: "cooling",
    },
    "hk60_selected_mode": {
        0: "auto",
        1: "normal",
        2: "reduced",
        3: "frost_protection",
        4: "heating",
        5: "cooling",
    },
    "hk60_effective_mode": {
        0: "normal",
        1: "reduced",
        2: "away",
        3: "frost_protection",
    },
    "hk60_season_status": {
        0: "transition",
        1: "heating_season",
        2: "cooling_season",
    },
    "controller_smart_grid_status": {
        0: "none",
        1: "normal",
        2: "push",
        3: "eco",
        4: "forced",
    },
}

HK60_SELECTED_MODE_TO_VALUE: dict[str, int] = {
    option: value
    for value, option in ENUM_STATES[HK60_SELECTED_MODE_DATA_POINT.key].items()
}
HK60_SELECTED_MODE_OPTIONS: tuple[str, ...] = tuple(HK60_SELECTED_MODE_TO_VALUE)
