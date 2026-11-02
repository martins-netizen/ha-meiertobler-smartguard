"""Guided, explicitly confirmed holiday editing through native HA options."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any, cast
from zoneinfo import ZoneInfo

import probatio
from homeassistant.config_entries import ConfigEntryState, ConfigFlowResult, OptionsFlow
from homeassistant.helpers.selector import BooleanSelector, DateTimeSelector

from .api import (
    SmartGuardError,
    SmartGuardHolidayChangedError,
    SmartGuardHolidayConfirmationError,
    SmartGuardHolidayWriteError,
)
from .const import CONF_HOST, HK60_SELECTED_MODE_TO_VALUE
from .data import SmartGuardConfigEntry, SmartGuardRuntimeData
from .entity import _circuit_display_name
from .holiday import (
    HolidayPeriod,
    HolidayState,
    format_holiday_timestamp,
    holiday_write_plan,
    parse_holiday_timestamp,
)

_PERIOD_SCHEMA = probatio.Schema(
    {
        probatio.Required("start"): DateTimeSelector(),
        probatio.Required("end"): DateTimeSelector(),
    }
)
_CONFIRM_SCHEMA = probatio.Schema(
    {
        probatio.Required("confirm", default=False): BooleanSelector(),
    }
)
_CONFIRM_SECONDS = 300


class SmartGuardHolidayOptionsFlow(OptionsFlow):
    """Keep dates in flow memory and never expose an unconfirmed write action."""

    def __init__(self) -> None:
        self._source: HolidayState | None = None
        self._requested: HolidayPeriod | None = None
        self._runtime: SmartGuardRuntimeData | None = None
        self._host: str | None = None
        self._expires = 0.0

    @property
    def _entry(self) -> SmartGuardConfigEntry:
        return cast("SmartGuardConfigEntry", self.config_entry)

    @property
    def _zone(self) -> ZoneInfo:
        return ZoneInfo(self.hass.config.time_zone)

    def _period_text(self, period: HolidayPeriod) -> str:
        return " / ".join(
            format_holiday_timestamp(value, self._zone)
            for value in (period.start, period.end)
        )

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Read the original period and collect both proposed local dates."""
        if self._entry.state is not ConfigEntryState.LOADED:
            return self.async_abort(reason="not_loaded")
        if self._source is None:
            self._runtime = self._entry.runtime_data
            self._host = self._entry.data[CONF_HOST]
            try:
                self._source = await self._runtime.client.async_read_hk60_holiday_state(
                    self._runtime.identity
                )
            except SmartGuardError:
                return self.async_abort(reason="period_unavailable")
        errors = {}
        if user_input is not None:
            try:
                requested = HolidayPeriod(
                    parse_holiday_timestamp(user_input.get("start"), self._zone),
                    parse_holiday_timestamp(user_input.get("end"), self._zone),
                )
                if requested.end <= time.time():
                    raise ValueError("period already ended")
            except (ValueError, OverflowError):
                errors["base"] = "invalid_period"
            else:
                if requested == self._source.period:
                    return self.async_abort(reason="no_changes")
                self._requested = requested
                self._expires = time.monotonic() + _CONFIRM_SECONDS
                return await self.async_step_confirm()
        try:
            # HA's DateTimeSelector splits its suggested value at a space.
            suggested = {
                key: datetime.fromtimestamp(value, UTC)
                .astimezone(self._zone)
                .replace(tzinfo=None)
                .isoformat(sep=" ")
                for key, value in (
                    ("start", self._source.period.start),
                    ("end", self._source.period.end),
                )
            }
        except OverflowError:
            return self.async_abort(reason="period_unavailable")
        schema = self.add_suggested_values_to_schema(
            _PERIOD_SCHEMA, user_input or suggested
        )
        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
            description_placeholders={"timezone": self.hass.config.time_zone},
        )

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Require a new confirmation for this target, exact pair and source state."""
        if (
            self._source is None
            or self._requested is None
            or time.monotonic() >= self._expires
        ):
            return self.async_abort(reason="confirmation_expired")
        if (
            self._entry.state is not ConfigEntryState.LOADED
            or self._entry.runtime_data is not self._runtime
            or self._entry.data[CONF_HOST] != self._host
        ):
            return self.async_abort(reason="source_changed")
        errors = {}
        if user_input is not None:
            if user_input.get("confirm") is not True:
                errors["base"] = "confirmation_required"
            else:
                return await self._async_apply_period(
                    self._entry.runtime_data, self._source, self._requested
                )
        plan = holiday_write_plan(self._source.period, self._requested)
        mode = next(
            key
            for key, value in HK60_SELECTED_MODE_TO_VALUE.items()
            if value == self._source.selected_mode
        )
        return self.async_show_form(
            step_id="confirm",
            data_schema=_CONFIRM_SCHEMA,
            errors=errors,
            description_placeholders={
                "circuit": _circuit_display_name("HK60", self._source.label),
                "previous": self._period_text(self._source.period),
                "requested": self._period_text(self._requested),
                "intermediate": self._period_text(plan[0][2]),
                "mode": mode,
                "writes": str(len(plan)),
            },
        )

    async def _async_apply_period(
        self,
        runtime: SmartGuardRuntimeData,
        source: HolidayState,
        requested: HolidayPeriod,
    ) -> ConfigFlowResult:
        """Consume this confirmation once and report the observed outcome."""
        deadline = self._expires
        self._expires = 0
        try:
            await runtime.client.async_set_hk60_holiday_period(
                runtime.identity, source, requested, confirmation_deadline=deadline
            )
        except SmartGuardHolidayConfirmationError:
            return self.async_abort(reason="confirmation_expired")
        except SmartGuardHolidayChangedError:
            return self.async_abort(reason="source_changed")
        except SmartGuardHolidayWriteError as err:
            await runtime.coordinator.async_request_refresh()
            if err.actual is None:
                return self.async_abort(reason="write_unknown")
            return self.async_abort(
                reason="write_incomplete",
                description_placeholders={
                    "actual": self._period_text(err.actual.period)
                },
            )
        except SmartGuardError:
            return self.async_abort(reason="read_failed")
        except ValueError:
            return self.async_abort(reason="period_ended")
        await runtime.coordinator.async_request_refresh()
        return self.async_create_entry(title="", data=dict(self._entry.options))
