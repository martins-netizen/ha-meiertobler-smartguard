"""Runtime data types for SmartGuard config entries."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry

from .api import SmartGuardApiClient, SmartGuardIdentity
from .coordinator import SmartGuardCoordinator


@dataclass(slots=True)
class SmartGuardRuntimeData:
    """Runtime objects owned by one config entry."""

    client: SmartGuardApiClient
    coordinator: SmartGuardCoordinator
    identity: SmartGuardIdentity

    def entity_unique_id(self, key: str) -> str:
        """Return the registry identifier for this gateway and entity key."""
        return f"{self.identity.global_device_id}_{key}"


type SmartGuardConfigEntry = ConfigEntry[SmartGuardRuntimeData]
