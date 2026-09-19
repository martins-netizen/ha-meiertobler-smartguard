"""Tests for the Home-Assistant-independent SmartGuard API layer."""

from __future__ import annotations

import unittest
from collections.abc import Sequence
from types import TracebackType
from typing import Any, Self

import aiohttp

from custom_components.meiertobler_smartguard.api import (
    SmartGuardApiClient,
    SmartGuardConnectionError,
    SmartGuardInvalidResponseError,
    SmartGuardTimeoutError,
    SmartGuardUnsupportedDeviceError,
    SmartGuardWriteVerificationError,
    normalize_host,
)
from custom_components.meiertobler_smartguard.const import DATA_POINTS


class FakeResponse:
    """Minimal aiohttp response test double."""

    def __init__(self, status: int, payload: object) -> None:
        self.status = status
        self._payload = payload

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        return None

    async def json(self, *, content_type: str | None = None) -> object:
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


class FakeSession:
    """Queue deterministic responses for sequential GET requests."""

    def __init__(self, responses: Sequence[FakeResponse | Exception]) -> None:
        self.responses = list(responses)
        self.urls: list[str] = []
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def get(self, url: object, **kwargs: Any) -> FakeResponse:
        self.urls.append(str(url))
        self.calls.append(("GET", str(url), kwargs))
        return self._next_response()

    def post(self, url: object, **kwargs: Any) -> FakeResponse:
        self.urls.append(str(url))
        self.calls.append(("POST", str(url), kwargs))
        return self._next_response()

    def _next_response(self) -> FakeResponse:
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class NormalizeHostTests(unittest.TestCase):
    """Test strict host normalization."""

    def test_accepts_documentation_ip_and_hostname(self) -> None:
        self.assertEqual(normalize_host("192.0.2.10"), "192.0.2.10")
        self.assertEqual(normalize_host("SmartGuard.local"), "smartguard.local")
        self.assertEqual(normalize_host("[2001:db8::1]"), "2001:db8::1")
        self.assertEqual(normalize_host("smartguard.local."), "smartguard.local")

    def test_rejects_scheme_path_port_and_credentials(self) -> None:
        for value in (
            "http://192.0.2.10",
            "192.0.2.10/api",
            "192.0.2.10:80",
            "user@smartguard.local",
            "smart guard.local",
            "smartguard..local",
            "",
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize_host(value)


class ApiClientTests(unittest.IsolatedAsyncioTestCase):
    """Test response validation and verified endpoint construction."""

    async def test_identity_and_all_datapoints(self) -> None:
        identity = {
            "deviceType": 1001,
            "globalDeviceId": 123456,
            "serialNumber": 654321,
        }
        values = [10.5, 28.1, 29.0, 19.2, 2, 0, 0, 2]
        session = FakeSession(
            [FakeResponse(200, identity)]
            + [FakeResponse(200, {"value": value}) for value in values]
        )
        client = SmartGuardApiClient("192.0.2.10", session)

        parsed_identity = await client.async_get_identity()
        snapshot = await client.async_read_all(parsed_identity.serial_number)

        self.assertEqual(parsed_identity.global_device_id, "123456")
        self.assertEqual(parsed_identity.serial_number, "654321")
        self.assertEqual(list(snapshot), [point.key for point in DATA_POINTS])
        self.assertEqual(snapshot["hk60_operating_status"], 2)
        self.assertIn("/api/v1/1001/654321/1/2/datapoints/5009", session.urls[-1])

    async def test_rejects_unsupported_device(self) -> None:
        session = FakeSession(
            [
                FakeResponse(
                    200,
                    {
                        "deviceType": 9999,
                        "globalDeviceId": 1,
                        "serialNumber": 2,
                    },
                )
            ]
        )
        client = SmartGuardApiClient("192.0.2.10", session)
        with self.assertRaises(SmartGuardUnsupportedDeviceError):
            await client.async_get_identity()

    async def test_rejects_missing_or_invalid_identity(self) -> None:
        for payload in (
            {"deviceType": 1001, "globalDeviceId": None, "serialNumber": 2},
            {"deviceType": 1001, "globalDeviceId": "bad value", "serialNumber": 2},
            {"deviceType": 1001, "globalDeviceId": 1, "serialNumber": True},
            {"deviceType": 1001, "globalDeviceId": 1, "serialNumber": ""},
        ):
            session = FakeSession([FakeResponse(200, payload)])
            client = SmartGuardApiClient("192.0.2.10", session)
            with (
                self.subTest(payload=payload),
                self.assertRaises(SmartGuardInvalidResponseError),
            ):
                await client.async_get_identity()

    async def test_rejects_missing_and_boolean_datapoint_values(self) -> None:
        for payload in ({}, {"value": True}):
            session = FakeSession([FakeResponse(200, payload)])
            client = SmartGuardApiClient("192.0.2.10", session)
            with (
                self.subTest(payload=payload),
                self.assertRaises(SmartGuardInvalidResponseError),
            ):
                await client.async_read_datapoint("654321", DATA_POINTS[0])

    async def test_rejects_invalid_enum_values(self) -> None:
        enum_point = DATA_POINTS[4]
        for value in (True, 1.5, "1"):
            session = FakeSession([FakeResponse(200, {"value": value})])
            client = SmartGuardApiClient("192.0.2.10", session)
            with self.subTest(value=value), self.assertRaises(
                SmartGuardInvalidResponseError
            ):
                await client.async_read_datapoint("654321", enum_point)

    async def test_rejects_invalid_numeric_values(self) -> None:
        for value in ("12", float("nan"), float("inf")):
            session = FakeSession([FakeResponse(200, {"value": value})])
            client = SmartGuardApiClient("192.0.2.10", session)
            with self.subTest(value=value), self.assertRaises(
                SmartGuardInvalidResponseError
            ):
                await client.async_read_datapoint("654321", DATA_POINTS[0])

    async def test_maps_timeout_without_exposing_host(self) -> None:
        session = FakeSession([TimeoutError()])
        client = SmartGuardApiClient("192.0.2.10", session)
        with self.assertRaises(SmartGuardTimeoutError) as raised:
            await client.async_get_identity()
        self.assertNotIn("192.0.2.10", str(raised.exception))

    async def test_maps_get_http_and_payload_errors(self) -> None:
        cases: tuple[tuple[FakeResponse | Exception, type[Exception]], ...] = (
            (FakeResponse(503, None), SmartGuardConnectionError),
            (FakeResponse(404, None), SmartGuardInvalidResponseError),
            (FakeResponse(200, ValueError()), SmartGuardInvalidResponseError),
            (FakeResponse(200, []), SmartGuardInvalidResponseError),
            (aiohttp.ClientConnectionError(), SmartGuardConnectionError),
        )
        for response, expected in cases:
            session = FakeSession([response])
            client = SmartGuardApiClient("192.0.2.10", session)
            with self.subTest(response=response), self.assertRaises(expected):
                await client.async_get_identity()

    async def test_writes_allowed_mode_and_confirms_readback(self) -> None:
        session = FakeSession(
            [
                FakeResponse(204, None),
                FakeResponse(200, {"value": 4}),
            ]
        )
        client = SmartGuardApiClient("192.0.2.10", session)

        confirmed = await client.async_set_hk60_selected_mode("654321", 4)

        self.assertEqual(confirmed, 4)
        self.assertEqual([call[0] for call in session.calls], ["POST", "GET"])
        method, url, kwargs = session.calls[0]
        self.assertEqual(method, "POST")
        self.assertIn("/api/v1/1001/654321/1/2/datapoints/5004", url)
        self.assertEqual(kwargs["data"], '{"value":4}')
        self.assertEqual(kwargs["headers"]["Content-Type"], "text/plain")

    async def test_rejects_mode_outside_allowlist_without_request(self) -> None:
        for value in (True, 6):
            session = FakeSession([])
            client = SmartGuardApiClient(
                "192.0.2.10",
                session,
            )

            with self.subTest(value=value), self.assertRaises(ValueError):
                await client.async_set_hk60_selected_mode("654321", value)

            self.assertEqual(session.calls, [])

    async def test_rejects_write_not_confirmed_by_readback(self) -> None:
        session = FakeSession(
            [
                FakeResponse(200, None),
                FakeResponse(200, {"value": 0}),
            ]
        )
        client = SmartGuardApiClient("192.0.2.10", session)

        with self.assertRaises(SmartGuardWriteVerificationError):
            await client.async_set_hk60_selected_mode("654321", 1)

    async def test_maps_write_server_error_to_connection_error(self) -> None:
        session = FakeSession([FakeResponse(503, None)])
        client = SmartGuardApiClient("192.0.2.10", session)

        with self.assertRaises(SmartGuardConnectionError):
            await client.async_set_hk60_selected_mode("654321", 0)

    async def test_rejects_write_http_client_error(self) -> None:
        session = FakeSession([FakeResponse(403, None)])
        client = SmartGuardApiClient("192.0.2.10", session)

        with self.assertRaises(SmartGuardInvalidResponseError):
            await client.async_set_hk60_selected_mode("654321", 0)

    async def test_maps_write_timeout(self) -> None:
        session = FakeSession([TimeoutError()])
        client = SmartGuardApiClient("192.0.2.10", session)

        with self.assertRaises(SmartGuardTimeoutError):
            await client.async_set_hk60_selected_mode("654321", 0)

    async def test_maps_write_client_error(self) -> None:
        session = FakeSession([aiohttp.ClientConnectionError()])
        client = SmartGuardApiClient("192.0.2.10", session)

        with self.assertRaises(SmartGuardConnectionError):
            await client.async_set_hk60_selected_mode("654321", 0)


if __name__ == "__main__":
    unittest.main()
