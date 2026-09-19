"""Data update coordinator for SmartGuard."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SmartGuardApiClient, SmartGuardError, SmartGuardSnapshot
from .const import DEFAULT_UPDATE_INTERVAL_SECONDS, DOMAIN

if TYPE_CHECKING:
    from .data import SmartGuardConfigEntry

_LOGGER = logging.getLogger(__name__)


class SmartGuardCoordinator(DataUpdateCoordinator[SmartGuardSnapshot]):
    """Coordinate one sequential SmartGuard refresh for all entities."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: SmartGuardConfigEntry,
        client: SmartGuardApiClient,
        serial_number: str,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=config_entry,
            update_interval=timedelta(seconds=DEFAULT_UPDATE_INTERVAL_SECONDS),
            always_update=False,
        )
        self.client = client
        self.serial_number = serial_number

    async def _async_update_data(self) -> SmartGuardSnapshot:
        """Fetch the latest verified datapoints."""
        try:
            return await self.client.async_read_all(self.serial_number)
        except SmartGuardError as err:
            raise UpdateFailed("SmartGuard communication failed") from err
