"""Config flow for Meier Tobler SmartGuard."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import TextSelector

from .api import (
    SmartGuardApiClient,
    SmartGuardConnectionError,
    SmartGuardIdentity,
    SmartGuardInvalidResponseError,
    SmartGuardTimeoutError,
    SmartGuardUnsupportedDeviceError,
    normalize_host,
)
from .const import CONF_HOST, DOMAIN, MODEL

_LOGGER = logging.getLogger(__name__)
_HOST_SCHEMA = vol.Schema({vol.Required(CONF_HOST): TextSelector()})


class SmartGuardConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a SmartGuard config flow."""

    VERSION = 1
    MINOR_VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Set up a SmartGuard gateway."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                host = normalize_host(user_input[CONF_HOST])
                identity = await self._async_validate(host)
            except ValueError:
                errors[CONF_HOST] = "invalid_host"
            except SmartGuardTimeoutError:
                errors["base"] = "cannot_connect"
            except SmartGuardConnectionError:
                errors["base"] = "cannot_connect"
            except SmartGuardUnsupportedDeviceError:
                errors["base"] = "unsupported_device"
            except SmartGuardInvalidResponseError:
                errors["base"] = "invalid_response"
            except Exception:
                _LOGGER.exception("Unexpected exception during SmartGuard setup")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(identity.global_device_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=MODEL,
                    data={CONF_HOST: host},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_HOST_SCHEMA,
            errors=errors,
        )

    async def async_step_reconfigure(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Change the gateway host while preserving device identity."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                host = normalize_host(user_input[CONF_HOST])
                identity = await self._async_validate(host)
            except ValueError:
                errors[CONF_HOST] = "invalid_host"
            except (SmartGuardConnectionError, SmartGuardTimeoutError):
                errors["base"] = "cannot_connect"
            except SmartGuardUnsupportedDeviceError:
                errors["base"] = "unsupported_device"
            except SmartGuardInvalidResponseError:
                errors["base"] = "invalid_response"
            except Exception:
                _LOGGER.exception(
                    "Unexpected exception during SmartGuard reconfiguration"
                )
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(identity.global_device_id)
                self._abort_if_unique_id_mismatch(reason="wrong_device")
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={CONF_HOST: host},
                )

        schema = self.add_suggested_values_to_schema(
            _HOST_SCHEMA,
            {CONF_HOST: entry.data[CONF_HOST]},
        )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=schema,
            errors=errors,
        )

    async def _async_validate(self, host: str) -> SmartGuardIdentity:
        """Validate identity and all read-only datapoints before saving."""
        client = SmartGuardApiClient(host, async_get_clientsession(self.hass))
        identity = await client.async_get_identity()
        await client.async_read_all(identity.serial_number)
        return identity
