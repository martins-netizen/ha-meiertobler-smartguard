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

DataPointKind = Literal["temperature", "enum"]


@dataclass(frozen=True, slots=True)
class SmartGuardDataPoint:
    """Describe one verified SmartGuard datapoint."""

    key: str
    datapoint_id: int
    kind: DataPointKind
    subsystem_path: tuple[int, int] | None = None

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
}

HK60_SELECTED_MODE_TO_VALUE: dict[str, int] = {
    option: value
    for value, option in ENUM_STATES[HK60_SELECTED_MODE_DATA_POINT.key].items()
}
HK60_SELECTED_MODE_OPTIONS: tuple[str, ...] = tuple(HK60_SELECTED_MODE_TO_VALUE)
