"""Validated holiday periods and timezone conversion, without gateway I/O."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, tzinfo

from .const import MAX_TIMESTAMP_SECONDS


@dataclass(frozen=True, slots=True)
class HolidayPeriod:
    """A complete, ordered pair of whole UTC Unix seconds."""

    start: int
    end: int

    def __post_init__(self) -> None:
        for value in (self.start, self.end):
            if type(value) is not int or not 1 <= value <= MAX_TIMESTAMP_SECONDS:
                raise ValueError("invalid holiday timestamp")
        if self.start >= self.end:
            raise ValueError("holiday end must follow start")


@dataclass(frozen=True, slots=True)
class HolidayState:
    """The source period, selected mode and circuit label shown for confirmation."""

    period: HolidayPeriod
    selected_mode: int
    label: str | None


def holiday_write_plan(
    previous: HolidayPeriod, requested: HolidayPeriod
) -> tuple[tuple[str, int, HolidayPeriod], ...]:
    """Keep each intermediate pair ordered; the gateway has no atomic pair write."""
    changes = []
    current = previous
    order = ("start", "end") if requested.start < previous.end else ("end", "start")
    for key in order:
        value = getattr(requested, key)
        if getattr(current, key) == value:
            continue
        current = HolidayPeriod(
            value if key == "start" else current.start,
            value if key == "end" else current.end,
        )
        changes.append((key, value, current))
    return tuple(changes)


def parse_holiday_timestamp(value: object, zone: tzinfo) -> int:
    """Reject guessed, nonexistent or repeated local times without an offset."""
    if not isinstance(value, str):
        raise ValueError("date/time text required")
    parsed = datetime.fromisoformat(value)
    if parsed.microsecond:
        raise ValueError("whole seconds required")
    if parsed.tzinfo is not None:
        candidates = {parsed.astimezone(UTC)}
    else:
        candidates = {
            aware.astimezone(UTC)
            for fold in (0, 1)
            if (aware := parsed.replace(tzinfo=zone, fold=fold))
            .astimezone(UTC)
            .astimezone(zone)
            .replace(tzinfo=None)
            == parsed
        }
    if len(candidates) != 1:
        raise ValueError("ambiguous or nonexistent local date/time")
    timestamp = int(candidates.pop().timestamp())
    if not 1 <= timestamp <= MAX_TIMESTAMP_SECONDS:
        raise ValueError("date/time outside serialization range")
    datetime.fromtimestamp(timestamp, UTC).astimezone(zone)
    return timestamp


def format_holiday_timestamp(value: int, zone: tzinfo) -> str:
    """Show an exact local instant and offset in the confirmation, not in logs."""
    instant = datetime.fromtimestamp(value, UTC)
    try:
        local = instant.astimezone(zone)
    except OverflowError:
        local = instant
    return local.strftime("%Y-%m-%d %H:%M:%S %Z (UTC%z)")
