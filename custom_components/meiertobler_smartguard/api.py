"""Async client for the local Meier Tobler SmartGuard REST API."""

from __future__ import annotations

import asyncio
import ipaddress
import json
import logging
import math
import re
import time
import unicodedata
from dataclasses import dataclass
from typing import Any, Final, cast

import aiohttp
from yarl import URL

from .const import (
    DATA_POINTS,
    DEFAULT_REQUEST_TIMEOUT_SECONDS,
    EXPECTED_DEVICE_TYPE,
    HK60_SELECTED_MODE_DATA_POINT,
    HK60_SELECTED_MODE_TO_VALUE,
    MODULE_LABEL_KEYS,
    OPTIONAL_DATA_POINTS,
    SmartGuardDataPoint,
)
from .holiday import HolidayPeriod, HolidayState, holiday_write_plan

type SmartGuardValue = float | int | bool | str
type SmartGuardSnapshot = dict[str, SmartGuardValue]
_HOSTNAME_RE: Final = re.compile(
    r"(?=^.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)*"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.?$"
)
_LOGGER = logging.getLogger(__name__)


class SmartGuardError(Exception):
    """Base exception for the SmartGuard client."""


class SmartGuardConnectionError(SmartGuardError):
    """The gateway could not be reached or returned a transient HTTP error."""


class SmartGuardTimeoutError(SmartGuardConnectionError):
    """The gateway request timed out."""


class SmartGuardInvalidResponseError(SmartGuardError):
    """The gateway returned an unexpected response."""


class SmartGuardUnsupportedDeviceError(SmartGuardError):
    """The endpoint is not a supported SmartGuard gateway."""


class SmartGuardWriteVerificationError(SmartGuardError):
    """The gateway did not confirm a requested write."""


class SmartGuardHolidayChangedError(SmartGuardError):
    """The target or source state no longer matches the confirmation."""


class SmartGuardHolidayConfirmationError(SmartGuardError):
    """The confirmation expired before a holiday write could start."""


class SmartGuardHolidayWriteError(SmartGuardError):
    """A holiday write may be partial; never silently retry or roll it back."""

    def __init__(self, actual: HolidayState | None) -> None:
        super().__init__("holiday write not fully confirmed")
        self.actual = actual


@dataclass(frozen=True, slots=True)
class SmartGuardIdentity:
    """Stable identity values returned by the gateway."""

    global_device_id: str
    serial_number: str
    device_type: str


def normalize_host(value: str) -> str:
    """Validate and normalize a host without scheme, path, port, or credentials."""
    host = value.strip()
    if not host or any(character.isspace() for character in host):
        raise ValueError("invalid host")
    if any(marker in host for marker in ("://", "/", "?", "#", "@")):
        raise ValueError("invalid host")

    candidate = host[1:-1] if host.startswith("[") and host.endswith("]") else host
    try:
        return str(ipaddress.ip_address(candidate))
    except ValueError:
        pass

    if ":" in host or not _HOSTNAME_RE.fullmatch(host):
        raise ValueError("invalid host")
    return host.rstrip(".").lower()


class SmartGuardApiClient:
    """Minimal async API client using an injected Home Assistant web session."""

    def __init__(
        self,
        host: str,
        session: aiohttp.ClientSession,
        *,
        request_timeout: int = DEFAULT_REQUEST_TIMEOUT_SECONDS,
    ) -> None:
        self.host = normalize_host(host)
        self._session = session
        self._base_url = URL.build(scheme="http", host=self.host)
        self._timeout = aiohttp.ClientTimeout(total=request_timeout)
        self._write_lock = asyncio.Lock()

    async def async_get_identity(self) -> SmartGuardIdentity:
        """Read and validate the gateway identity."""
        payload = await self._async_get_json("/api/v1/system/device/identity")
        device_type = _identifier(payload.get("deviceType"))
        global_device_id = _identifier(payload.get("globalDeviceId"))
        serial_number = _identifier(payload.get("serialNumber"))

        if device_type != EXPECTED_DEVICE_TYPE:
            raise SmartGuardUnsupportedDeviceError("unsupported device type")
        if global_device_id is None or serial_number is None:
            raise SmartGuardInvalidResponseError("identity fields missing")

        return SmartGuardIdentity(
            global_device_id=global_device_id,
            serial_number=serial_number,
            device_type=device_type,
        )

    async def async_read_all(self, serial_number: str) -> SmartGuardSnapshot:
        """Read core values and independently collect available optional values."""
        snapshot: SmartGuardSnapshot = {}
        for datapoint in DATA_POINTS:
            snapshot[datapoint.key] = await self.async_read_datapoint(
                serial_number,
                datapoint,
            )
        snapshot.update(await self._async_read_optional(serial_number))
        return snapshot

    async def _async_read_optional(self, serial_number: str) -> SmartGuardSnapshot:
        """Read enabled optional modules without failing the core update."""
        snapshot: SmartGuardSnapshot = {}
        for subsystem_path in dict.fromkeys(
            (
                *[point.subsystem_path for point in OPTIONAL_DATA_POINTS],
                *MODULE_LABEL_KEYS,
            )
        ):
            path = f"/api/v1/{EXPECTED_DEVICE_TYPE}/{serial_number}"
            if subsystem_path is not None:
                group, unit = subsystem_path
                path = f"{path}/{group}/{unit}"
            try:
                config = await self._async_get_json(f"{path}/config")
            except SmartGuardError:
                _LOGGER.debug(
                    "Optional SmartGuard module %s unavailable", subsystem_path
                )
                continue
            if config.get("enabled") is not True:
                continue
            label = normalize_module_label(config.get("label"))
            if label is not None:
                snapshot[MODULE_LABEL_KEYS[subsystem_path]] = label
            for datapoint in OPTIONAL_DATA_POINTS:
                if datapoint.subsystem_path != subsystem_path:
                    continue
                try:
                    snapshot[datapoint.key] = await self.async_read_datapoint(
                        serial_number, datapoint
                    )
                except SmartGuardError:
                    _LOGGER.debug(
                        "Optional SmartGuard value %s unavailable", datapoint.key
                    )
        return snapshot

    async def async_read_datapoint(
        self,
        serial_number: str,
        datapoint: SmartGuardDataPoint,
    ) -> SmartGuardValue:
        """Read and validate one datapoint value."""
        payload = await self._async_get_json(datapoint.path(serial_number))
        if "value" not in payload:
            raise SmartGuardInvalidResponseError("datapoint value missing")

        value = payload["value"]
        if datapoint.kind == "boolean":
            if not isinstance(value, bool):
                raise SmartGuardInvalidResponseError("invalid boolean value")
            return value
        numeric: float | int
        if datapoint.kind in ("enum", "counter", "timestamp"):
            if isinstance(value, bool) or not isinstance(value, int):
                raise SmartGuardInvalidResponseError("invalid integer value")
            numeric = value
        else:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise SmartGuardInvalidResponseError("invalid numeric value")
            try:
                numeric = float(value)
            except OverflowError as err:
                raise SmartGuardInvalidResponseError("numeric value overflow") from err
            if not math.isfinite(numeric):
                raise SmartGuardInvalidResponseError("non-finite numeric value")
        if (datapoint.minimum is not None and numeric < datapoint.minimum) or (
            datapoint.maximum is not None and numeric > datapoint.maximum
        ):
            raise SmartGuardInvalidResponseError("datapoint outside documented range")
        return numeric

    async def async_set_hk60_selected_mode(
        self,
        serial_number: str,
        value: int,
    ) -> int:
        """Write one allowed HK60 mode and verify it through an immediate readback."""
        if isinstance(value, bool) or value not in HK60_SELECTED_MODE_TO_VALUE.values():
            raise ValueError("unsupported HK60 mode")

        async with self._write_lock:
            await self._async_post_value(
                HK60_SELECTED_MODE_DATA_POINT.path(serial_number),
                value,
            )
            confirmed = await self.async_read_datapoint(
                serial_number,
                HK60_SELECTED_MODE_DATA_POINT,
            )

        if confirmed != value:
            raise SmartGuardWriteVerificationError("written mode was not confirmed")
        return value

    async def async_read_hk60_holiday_state(
        self, identity: SmartGuardIdentity
    ) -> HolidayState:
        """Verify the target and read a stable pair without changing any setting."""
        if await self.async_get_identity() != identity:
            raise SmartGuardHolidayChangedError("gateway identity changed")
        config = await self._async_get_json(
            f"/api/v1/{EXPECTED_DEVICE_TYPE}/{identity.serial_number}/1/2/config"
        )
        if config.get("enabled") is not True:
            raise SmartGuardInvalidResponseError("HK60 is not enabled")
        previous = await self._async_read_holiday_period(identity.serial_number)
        mode = await self.async_read_datapoint(
            identity.serial_number, HK60_SELECTED_MODE_DATA_POINT
        )
        if mode not in HK60_SELECTED_MODE_TO_VALUE.values():
            raise SmartGuardInvalidResponseError("unknown selected mode")
        period = await self._async_read_holiday_period(identity.serial_number)
        if period != previous:
            raise SmartGuardHolidayChangedError("holiday period changed while reading")
        return HolidayState(
            period, cast("int", mode), normalize_module_label(config.get("label"))
        )

    async def _async_read_holiday_period(self, serial_number: str) -> HolidayPeriod:
        """Read only the two observed date points; reject unknown unset markers."""
        values = [
            await self.async_read_datapoint(serial_number, point)
            for point in OPTIONAL_DATA_POINTS
            if point.key in ("hk60_holiday_start", "hk60_holiday_end")
        ]
        try:
            return HolidayPeriod(cast("int", values[0]), cast("int", values[1]))
        except ValueError as err:
            raise SmartGuardInvalidResponseError("invalid holiday period") from err

    async def async_set_hk60_holiday_period(
        self,
        identity: SmartGuardIdentity,
        expected: HolidayState,
        requested: HolidayPeriod,
        *,
        confirmation_deadline: float,
    ) -> HolidayState:
        """Apply a concretely confirmed pair with source guards and readbacks."""
        target = HolidayState(requested, expected.selected_mode, expected.label)
        async with self._write_lock:
            if time.monotonic() >= confirmation_deadline:
                raise SmartGuardHolidayConfirmationError("confirmation expired")
            if await self.async_read_hk60_holiday_state(identity) != expected:
                raise SmartGuardHolidayChangedError("confirmed source state changed")
            if time.monotonic() >= confirmation_deadline:
                raise SmartGuardHolidayConfirmationError("confirmation expired")
            if requested.end <= time.time():
                raise ValueError("holiday period has already ended")
            for key, value, intermediate in holiday_write_plan(
                expected.period, requested
            ):
                point = next(
                    point
                    for point in OPTIONAL_DATA_POINTS
                    if point.key == f"hk60_holiday_{key}"
                )
                expected_step = HolidayState(
                    intermediate, expected.selected_mode, expected.label
                )
                if await self._async_write_holiday_step(
                    identity, point, value, expected_step, target
                ):
                    break
            return target

    async def _async_write_holiday_step(
        self,
        identity: SmartGuardIdentity,
        point: SmartGuardDataPoint,
        value: int,
        expected: HolidayState,
        target: HolidayState,
    ) -> bool:
        """Verify one step; after an error, only a complete readback can succeed."""
        try:
            await self._async_post_value(point.path(identity.serial_number), value)
            actual = await self.async_read_hk60_holiday_state(identity)
        except SmartGuardError as err:
            try:
                actual = await self.async_read_hk60_holiday_state(identity)
            except SmartGuardError:
                actual = None
            if actual == target:
                return True
            raise SmartGuardHolidayWriteError(actual) from err
        if actual != expected:
            raise SmartGuardHolidayWriteError(actual)
        return False

    async def _async_post_value(self, path: str, value: int) -> None:
        """Write one integer value without exposing device details in errors."""
        url = self._base_url.with_path(path)
        body = json.dumps({"value": value}, separators=(",", ":"))
        try:
            async with self._session.post(
                url,
                data=body,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "text/plain",
                },
                timeout=self._timeout,
                allow_redirects=False,
            ) as response:
                if response.status >= 500:
                    raise SmartGuardConnectionError("gateway server error")
                if not 200 <= response.status < 300:
                    raise SmartGuardInvalidResponseError(
                        f"unexpected HTTP status {response.status}"
                    )
        except TimeoutError as err:
            raise SmartGuardTimeoutError("gateway request timed out") from err
        except aiohttp.ClientError as err:
            raise SmartGuardConnectionError("gateway connection failed") from err

    async def _async_get_json(self, path: str) -> dict[str, Any]:
        """Perform one GET and return a JSON object without logging private data."""
        url = self._base_url.with_path(path)
        try:
            async with self._session.get(
                url,
                headers={"Accept": "application/json"},
                timeout=self._timeout,
                allow_redirects=False,
            ) as response:
                if response.status >= 500:
                    raise SmartGuardConnectionError("gateway server error")
                if response.status != 200:
                    raise SmartGuardInvalidResponseError(
                        f"unexpected HTTP status {response.status}"
                    )
                try:
                    payload = await response.json(content_type=None)
                except (aiohttp.ContentTypeError, ValueError, TypeError) as err:
                    raise SmartGuardInvalidResponseError(
                        "invalid JSON response"
                    ) from err
        except TimeoutError as err:
            raise SmartGuardTimeoutError("gateway request timed out") from err
        except aiohttp.ClientError as err:
            raise SmartGuardConnectionError("gateway connection failed") from err

        if not isinstance(payload, dict):
            raise SmartGuardInvalidResponseError("JSON object expected")
        return cast("dict[str, Any]", payload)


def normalize_module_label(value: object) -> str | None:
    """Accept bounded printable metadata without coercing or logging it."""
    if not isinstance(value, str) or len(value) > 128:
        return None
    if any(unicodedata.category(character).startswith("C") for character in value):
        return None
    return value.strip() or None


def _identifier(value: object) -> str | None:
    """Return a conservative string representation of an API identifier."""
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        return None
    identifier = str(value).strip()
    if not identifier or not re.fullmatch(r"[A-Za-z0-9._-]+", identifier):
        return None
    return identifier
