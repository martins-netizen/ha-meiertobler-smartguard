"""Holiday editing guards, real client requests and native HA options flow."""

from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime
from unittest.mock import AsyncMock, patch
from zoneinfo import ZoneInfo

import pytest
from homeassistant.data_entry_flow import FlowResultType

from custom_components.meiertobler_smartguard.api import (
    SmartGuardApiClient,
    SmartGuardConnectionError,
    SmartGuardHolidayChangedError,
    SmartGuardHolidayConfirmationError,
    SmartGuardHolidayWriteError,
    SmartGuardInvalidResponseError,
)
from custom_components.meiertobler_smartguard.const import (
    CONF_HOST,
    MAX_TIMESTAMP_SECONDS,
)
from custom_components.meiertobler_smartguard.holiday import (
    HolidayPeriod,
    HolidayState,
    format_holiday_timestamp,
    holiday_write_plan,
    parse_holiday_timestamp,
)
from custom_components.meiertobler_smartguard.holiday_flow import (
    SmartGuardHolidayOptionsFlow,
)

from .conftest import TEST_HOST, TEST_IDENTITY
from .test_api import FakeResponse, FakeSession

ZONE = ZoneInfo("Europe/Zurich")
PREFIX = "custom_components.meiertobler_smartguard."


def ts(text):
    return int(datetime.fromisoformat(text).timestamp())


OLD = HolidayPeriod(ts("2030-01-01T10:00:00+00:00"), ts("2030-01-10T10:00:00+00:00"))
NEW = HolidayPeriod(ts("2031-01-01T10:00:00+00:00"), ts("2031-01-10T10:00:00+00:00"))
SOURCE = HolidayState(OLD, 0, "Floor heating")
TARGET = HolidayState(NEW, 0, "Floor heating")
INPUT = {"start": "2031-01-01T11:00:00", "end": "2031-01-10T11:00:00"}


def responses(period=OLD, *, mode=0, enabled=True, label="Floor heating", final=None):
    identity = {
        "deviceType": "1001",
        "globalDeviceId": TEST_IDENTITY.global_device_id,
        "serialNumber": TEST_IDENTITY.serial_number,
    }
    final = final or period
    return [
        FakeResponse(200, value)
        for value in [
            identity,
            {"enabled": enabled, "label": label},
            {"value": period.start},
            {"value": period.end},
            {"value": mode},
            {"value": final.start},
            {"value": final.end},
        ]
    ]


def posts(session):
    return [call for call in session.calls if call[0] == "POST"]


async def save(client, requested=NEW, expected=SOURCE, deadline=None):
    return await client.async_set_hk60_holiday_period(
        TEST_IDENTITY,
        expected,
        requested,
        confirmation_deadline=time.monotonic() + 300 if deadline is None else deadline,
    )


@pytest.mark.parametrize(
    "start,end",
    [
        (True, 2),
        (1, False),
        (1.0, 2),
        ("1", 2),
        (0, 2),
        (-1, 2),
        (1, MAX_TIMESTAMP_SECONDS + 1),
        (2, 2),
        (3, 2),
    ],
)
def test_period_rejects_invalid_pairs(start, end):
    with pytest.raises(ValueError):
        HolidayPeriod(start, end)


@pytest.mark.parametrize(
    "text,expected",
    [
        ("2031-01-01T11:00:00", NEW.start),
        ("2031-01-01T10:00:00Z", NEW.start),
        ("2027-07-01T12:00:00", ts("2027-07-01T10:00:00Z")),
        ("2027-10-31T02:30:00+02:00", ts("2027-10-31T00:30:00Z")),
        ("2027-10-31T02:30:00+01:00", ts("2027-10-31T01:30:00Z")),
    ],
)
def test_timestamp_conversion_handles_explicit_offsets_and_seasons(text, expected):
    assert parse_holiday_timestamp(text, ZONE) == expected


@pytest.mark.parametrize(
    "text",
    [
        None,
        True,
        1,
        "bad",
        "2027-03-28T02:30:00",
        "2027-10-31T02:30:00",
        "2031-01-01T10:00:00.1",
        "1970-01-01T00:00:00Z",
        "9999-12-31T23:59:59Z",
    ],
)
def test_invalid_or_ambiguous_local_time_is_never_guessed(text):
    with pytest.raises((ValueError, OverflowError)):
        parse_holiday_timestamp(text, ZONE)


def test_display_retains_utc_offset_and_handles_upper_boundary():
    assert "CET (UTC+0100)" in format_holiday_timestamp(NEW.start, ZONE)
    assert "UTC (UTC+0000)" in format_holiday_timestamp(MAX_TIMESTAMP_SECONDS, ZONE)


@pytest.mark.parametrize(
    "previous,requested,keys",
    [
        (OLD, NEW, ["end", "start"]),
        (NEW, OLD, ["start", "end"]),
        (OLD, HolidayPeriod(OLD.start + 60, OLD.end + 60), ["start", "end"]),
        (OLD, HolidayPeriod(OLD.start, OLD.end + 60), ["end"]),
        (OLD, HolidayPeriod(OLD.start + 60, OLD.end), ["start"]),
        (OLD, OLD, []),
    ],
)
def test_write_order_preserves_ordered_intermediates(previous, requested, keys):
    plan = holiday_write_plan(previous, requested)
    assert [item[0] for item in plan] == keys
    assert all(item[2].start < item[2].end for item in plan)
    if plan:
        assert plan[-1][2] == requested


async def test_client_reads_verified_stable_source():
    session = FakeSession(responses())
    client = SmartGuardApiClient(TEST_HOST, session)
    assert await client.async_read_hk60_holiday_state(TEST_IDENTITY) == SOURCE
    assert not posts(session)
    assert all(call[2]["allow_redirects"] is False for call in session.calls)


@pytest.mark.parametrize(
    "case", ["identity", "disabled", "invalid_pair", "changed", "invalid_mode"]
)
async def test_client_rejects_unverified_sources(case):
    replies = responses()
    expected = SmartGuardInvalidResponseError
    if case == "identity":
        replies[0] = FakeResponse(
            200,
            {"deviceType": 1001, "globalDeviceId": "other", "serialNumber": "other"},
        )
        expected = SmartGuardHolidayChangedError
    elif case == "disabled":
        replies = responses(enabled=False)
    elif case == "invalid_pair":
        replies[3] = FakeResponse(200, {"value": OLD.start - 1})
    elif case == "changed":
        replies = responses(final=NEW)
        expected = SmartGuardHolidayChangedError
    else:
        replies = responses(mode=99)
    session = FakeSession(replies)
    with pytest.raises(expected):
        await SmartGuardApiClient(TEST_HOST, session).async_read_hk60_holiday_state(
            TEST_IDENTITY
        )
    assert not posts(session)


async def test_two_posts_use_known_paths_numeric_body_and_full_readback():
    intermediate = HolidayPeriod(OLD.start, NEW.end)
    session = FakeSession(
        [
            *responses(),
            FakeResponse(200, {}),
            *responses(intermediate),
            FakeResponse(200, {}),
            *responses(NEW),
        ]
    )
    assert await save(SmartGuardApiClient(TEST_HOST, session)) == TARGET
    calls = posts(session)
    assert [call[1].rsplit("/", 1)[-1] for call in calls] == ["5227", "5226"]
    assert [json.loads(call[2]["data"]) for call in calls] == [
        {"value": NEW.end},
        {"value": NEW.start},
    ]
    assert all(
        f"/1001/{TEST_IDENTITY.serial_number}/1/2/datapoints/" in call[1]
        for call in calls
    )
    assert all(call[2]["headers"]["Content-Type"] == "text/plain" for call in calls)
    assert all(call[2]["allow_redirects"] is False for call in calls)
    assert not session.responses


@pytest.mark.parametrize("requested", [OLD, HolidayPeriod(OLD.start, OLD.end + 60)])
async def test_skip_unchanged_endpoints(requested):
    replies = responses()
    if requested != OLD:
        replies += [FakeResponse(200, {}), *responses(requested)]
    session = FakeSession(replies)
    assert await save(
        SmartGuardApiClient(TEST_HOST, session), requested=requested
    ) == HolidayState(requested, 0, SOURCE.label)
    assert len(posts(session)) == int(requested != OLD)


@pytest.mark.parametrize(
    "changed",
    [
        HolidayState(NEW, 0, SOURCE.label),
        HolidayState(OLD, 1, SOURCE.label),
        HolidayState(OLD, 0, "Other label"),
    ],
)
async def test_no_write_if_period_mode_or_label_changed(changed):
    session = FakeSession(
        responses(changed.period, mode=changed.selected_mode, label=changed.label)
    )
    with pytest.raises(SmartGuardHolidayChangedError):
        await save(SmartGuardApiClient(TEST_HOST, session))
    assert not posts(session)


@pytest.mark.parametrize("stage", ["before_lock", "during_read"])
async def test_confirmation_expiry_is_checked_inside_write_lock(stage):
    session = FakeSession(responses())
    client = SmartGuardApiClient(TEST_HOST, session)
    if stage == "before_lock":
        with pytest.raises(SmartGuardHolidayConfirmationError):
            await save(client, deadline=0)
        assert not session.calls
    else:
        with (
            patch(PREFIX + "api.time") as clock,
            pytest.raises(SmartGuardHolidayConfirmationError),
        ):
            clock.monotonic.side_effect = [100, 400]
            await save(client, deadline=300)
        assert len(session.calls) == 7
    assert not posts(session)


async def test_queued_writer_waits_for_existing_lock_then_rejects_expired_confirmation():
    session = FakeSession([])
    client = SmartGuardApiClient(TEST_HOST, session)
    async with client._write_lock:
        task = asyncio.create_task(save(client, deadline=0))
        await asyncio.sleep(0)
        assert not task.done()
        assert not session.calls
    with pytest.raises(SmartGuardHolidayConfirmationError):
        await task
    assert not session.calls


async def test_ended_period_is_not_written():
    session = FakeSession(responses())
    with pytest.raises(ValueError):
        await save(
            SmartGuardApiClient(TEST_HOST, session), requested=HolidayPeriod(1, 2)
        )
    assert not posts(session)


@pytest.mark.parametrize(
    "failure,known",
    [
        (FakeResponse(400, {}), SOURCE),
        (
            TimeoutError(),
            HolidayState(HolidayPeriod(OLD.start, NEW.end), 0, SOURCE.label),
        ),
        (SmartGuardConnectionError(), None),
    ],
)
async def test_first_write_failure_stops_and_reports_observed_state(failure, known):
    recovery = responses(known.period) if known else [SmartGuardConnectionError()]
    session = FakeSession([*responses(), failure, *recovery])
    with pytest.raises(SmartGuardHolidayWriteError) as caught:
        await save(SmartGuardApiClient(TEST_HOST, session))
    assert caught.value.actual == known
    assert len(posts(session)) == 1
    assert str(NEW.start) not in str(caught.value)


async def test_lost_final_reply_is_success_only_after_full_independent_readback():
    intermediate = HolidayPeriod(OLD.start, NEW.end)
    session = FakeSession(
        [
            *responses(),
            FakeResponse(200, {}),
            *responses(intermediate),
            TimeoutError(),
            *responses(NEW),
        ]
    )
    assert await save(SmartGuardApiClient(TEST_HOST, session)) == TARGET
    assert len(posts(session)) == 2


async def test_different_successful_readback_stops_without_second_post_or_rollback():
    session = FakeSession(
        [*responses(), FakeResponse(200, {}), *responses(OLD, mode=1)]
    )
    with pytest.raises(SmartGuardHolidayWriteError) as caught:
        await save(SmartGuardApiClient(TEST_HOST, session))
    assert caught.value.actual == HolidayState(OLD, 1, SOURCE.label)
    assert len(posts(session)) == 1


async def test_failed_readback_attempts_one_read_only_recovery():
    session = FakeSession(
        [*responses(), FakeResponse(200, {}), TimeoutError(), *responses()]
    )
    with pytest.raises(SmartGuardHolidayWriteError) as caught:
        await save(SmartGuardApiClient(TEST_HOST, session))
    assert caught.value.actual == SOURCE
    assert len(posts(session)) == 1


@pytest.fixture
async def editor(hass, config_entry, mock_api, request):
    options = getattr(request, "param", {})
    hass.config_entries.async_update_entry(config_entry, options=options)
    await hass.config.async_set_time_zone("Europe/Zurich")
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    client = config_entry.runtime_data.client
    with (
        patch.object(
            client, "async_read_hk60_holiday_state", new=AsyncMock(return_value=SOURCE)
        ) as read,
        patch.object(
            client, "async_set_hk60_holiday_period", new=AsyncMock(return_value=TARGET)
        ) as write,
    ):
        yield {"read": read, "write": write, "options": options}


async def stage(hass, entry):
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    return await hass.config_entries.options.async_configure(result["flow_id"], INPUT)


@pytest.mark.parametrize("editor", [{}, {"retained": True}], indirect=True)
async def test_native_editor_requires_explicit_confirmation_and_keeps_options_private(
    hass, config_entry, editor
):
    result = await stage(hass, config_entry)
    assert result["step_id"] == "confirm"
    warning = result["description_placeholders"]
    assert warning["circuit"] == "HK60: Floor heating"
    assert warning["writes"] == "2"
    assert "2030-01-01 11:00:00 CET (UTC+0100)" in warning["intermediate"]
    assert "2031-01-01 11:00:00 CET (UTC+0100)" in warning["requested"]
    editor["write"].assert_not_awaited()
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"confirm": False}
    )
    assert result["errors"] == {"base": "confirmation_required"}
    editor["write"].assert_not_awaited()
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"confirm": True}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == editor["options"]
    args = editor["write"].await_args
    assert args.args == (TEST_IDENTITY, SOURCE, NEW)
    assert args.kwargs["confirmation_deadline"] > time.monotonic()
    assert editor["write"].await_count == 1
    assert config_entry.options == editor["options"]
    assert config_entry.data == {CONF_HOST: TEST_HOST}


async def test_unloaded_entry_cannot_edit(hass, config_entry):
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["reason"] == "not_loaded"


@pytest.mark.parametrize("case", ["gateway", "unrepresentable"])
async def test_editor_needs_readable_current_period(hass, config_entry, editor, case):
    if case == "gateway":
        editor["read"].side_effect = SmartGuardConnectionError()
    else:
        editor["read"].return_value = HolidayState(
            HolidayPeriod(NEW.start, MAX_TIMESTAMP_SECONDS), 0, None
        )
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["reason"] == "period_unavailable"
    editor["write"].assert_not_awaited()


@pytest.mark.parametrize(
    "data",
    [
        {"start": "2031-01-10T11:00:00", "end": "2031-01-01T11:00:00"},
        {"start": "2027-03-28T02:30:00", "end": "2031-01-01T11:00:00"},
        {"start": "2027-10-31T02:30:00", "end": "2031-01-01T11:00:00"},
        {"start": "1970-01-01T00:00:01Z", "end": "1970-01-01T00:00:02Z"},
    ],
)
async def test_native_editor_rejects_invalid_period(hass, config_entry, editor, data):
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], data)
    assert result["errors"] == {"base": "invalid_period"}
    editor["write"].assert_not_awaited()


async def test_same_period_does_not_write(hass, config_entry, editor):
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"start": "2030-01-01T11:00:00", "end": "2030-01-10T11:00:00"},
    )
    assert result["reason"] == "no_changes"
    editor["write"].assert_not_awaited()


@pytest.mark.parametrize("cause", ["expired", "reloaded", "host"])
async def test_pending_confirmation_is_bound_to_loaded_runtime_and_host(
    hass, config_entry, editor, cause
):
    result = await stage(hass, config_entry)
    flow = hass.config_entries.options._progress[result["flow_id"]]
    if cause == "expired":
        flow._expires = 0
        expected = "confirmation_expired"
    elif cause == "reloaded":
        flow._runtime = None
        expected = "source_changed"
    else:
        flow._host = "192.0.2.99"
        expected = "source_changed"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"confirm": True}
    )
    assert result["reason"] == expected
    editor["write"].assert_not_awaited()


async def test_direct_confirm_step_without_staged_period_never_writes():
    result = await SmartGuardHolidayOptionsFlow().async_step_confirm({"confirm": True})
    assert result["reason"] == "confirmation_expired"


async def test_cancelling_native_confirmation_never_writes(hass, config_entry, editor):
    result = await stage(hass, config_entry)
    hass.config_entries.options.async_abort(result["flow_id"])
    editor["write"].assert_not_awaited()


@pytest.mark.parametrize(
    "failure,reason",
    [
        (SmartGuardHolidayConfirmationError(), "confirmation_expired"),
        (SmartGuardHolidayChangedError(), "source_changed"),
        (SmartGuardHolidayWriteError(SOURCE), "write_incomplete"),
        (SmartGuardHolidayWriteError(None), "write_unknown"),
        (SmartGuardConnectionError(), "read_failed"),
        (ValueError(), "period_ended"),
    ],
)
async def test_native_editor_reports_failure_without_retry(
    hass, config_entry, editor, failure, reason
):
    editor["write"].side_effect = failure
    result = await stage(hass, config_entry)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"confirm": True}
    )
    assert result["reason"] == reason
    assert editor["write"].await_count == 1
    assert config_entry.options == editor["options"]
