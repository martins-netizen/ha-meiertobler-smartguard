"""Read-only discovery of SmartGuard write capabilities."""

from __future__ import annotations

import probatio
from homeassistant.auth.permissions.const import POLICY_READ
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_CONFIG_ENTRY_ID
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
from homeassistant.exceptions import ServiceValidationError, Unauthorized, UnknownUser
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, HK60_MODE_SELECT_KEY, HK60_SELECTED_MODE_OPTIONS
from .data import SmartGuardConfigEntry

_SERVICE_GET_WRITE_CAPABILITIES = "get_write_capabilities"
_CATALOGUE_SCHEMA = probatio.Schema(
    {probatio.Required(ATTR_CONFIG_ENTRY_ID): cv.string}
)


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Register the response-only capability action."""
    hass.services.async_register(
        DOMAIN,
        _SERVICE_GET_WRITE_CAPABILITIES,
        _async_get_write_capabilities,
        schema=_CATALOGUE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )


async def _async_get_write_capabilities(call: ServiceCall) -> ServiceResponse:
    """Describe the registered HK60 control using Home Assistant's local state."""
    hass = call.hass
    user = None
    if (user_id := call.context.user_id) is not None:
        user = await hass.auth.async_get_user(user_id)
        if user is None:
            raise UnknownUser(context=call.context, user_id=user_id)
        if not user.is_active:
            raise Unauthorized(context=call.context, permission=POLICY_READ)

    entry: SmartGuardConfigEntry | None = hass.config_entries.async_get_entry(
        call.data[ATTR_CONFIG_ENTRY_ID]
    )
    if (
        entry is None
        or entry.domain != DOMAIN
        or entry.state is not ConfigEntryState.LOADED
    ):
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="write_capabilities_target_unavailable",
        )
    registry = er.async_get(hass)
    unique_id = entry.runtime_data.entity_unique_id(HK60_MODE_SELECT_KEY)
    select = next(
        (
            record
            for record in er.async_entries_for_config_entry(registry, entry.entry_id)
            if record.domain == "select"
            and record.platform == DOMAIN
            and record.unique_id == unique_id
            and not record.disabled
        ),
        None,
    )
    if select is None:
        return {"parameters": {}}

    entity_id = select.entity_id
    if user is not None and not user.permissions.check_entity(entity_id, POLICY_READ):
        raise Unauthorized(
            context=call.context, entity_id=entity_id, permission=POLICY_READ
        )

    state = hass.states.get(entity_id)
    return {
        "parameters": {
            "hk60.operating_mode": {
                "type": "select",
                "available": state is not None
                and state.state in HK60_SELECTED_MODE_OPTIONS,
                "options": list(HK60_SELECTED_MODE_OPTIONS),
                "action": "select.select_option",
                "target": {"entity_id": entity_id},
                "value_field": "option",
            }
        }
    }
