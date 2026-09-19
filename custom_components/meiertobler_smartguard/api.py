"""Async client for the local Meier Tobler SmartGuard REST API."""

from __future__ import annotations

import asyncio
import ipaddress
import json
import math
import re
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
    SmartGuardDataPoint,
)

type SmartGuardValue = float | int
type SmartGuardSnapshot = dict[str, SmartGuardValue]
_HOSTNAME_RE: Final = re.compile(
    r"(?=^.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)*"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.?$"
)


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
        """Read all verified datapoints sequentially."""
        snapshot: SmartGuardSnapshot = {}
        for datapoint in DATA_POINTS:
            snapshot[datapoint.key] = await self.async_read_datapoint(
                serial_number,
                datapoint,
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
        if datapoint.kind == "enum":
            if isinstance(value, bool) or not isinstance(value, int):
                raise SmartGuardInvalidResponseError("invalid enum value")
            return value

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise SmartGuardInvalidResponseError("invalid numeric value")
        numeric = float(value)
        if not math.isfinite(numeric):
            raise SmartGuardInvalidResponseError("non-finite numeric value")
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


def _identifier(value: object) -> str | None:
    """Return a conservative string representation of an API identifier."""
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        return None
    identifier = str(value).strip()
    if not identifier or not re.fullmatch(r"[A-Za-z0-9._-]+", identifier):
        return None
    return identifier
