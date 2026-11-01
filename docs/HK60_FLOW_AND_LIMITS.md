# HK60 flow target and heating/cooling limits

[Back to the overview](../README.md) · [Operating readings](OPERATING_READINGS.md)

This **unreleased** addition exposes ten optional read-only HK60 sensors.
It is not included in published 0.5.0 and requires a future release for HACS
installation. It adds no editable temperature or duration controls.

## Readings and interpretation

All paths are relative to `/api/v1/1001/<serial_number>/1/2/datapoints/`.

| Sensor | Datapoint | Unit | Validation |
| --- | --- | --- | --- |
| Current flow target temperature | `52204` | °C | −50 to 125; broad plausibility guard |
| Heating design outdoor temperature | `5221` | °C | −60 to 60; broad plausibility guard |
| Heating on outdoor threshold | `5271` | °C | 5–30; UI input bounds |
| Heating off outdoor threshold | `5272` | °C | 5–30; UI input bounds |
| Heating on damping duration | `5273` | h | 1–48; UI input bounds |
| Heating off damping duration | `5274` | h | 1–48; UI input bounds |
| Cooling on outdoor threshold | `5276` | °C | 5–30; UI input bounds |
| Cooling off outdoor threshold | `5277` | °C | 5–30; UI input bounds |
| Cooling on damping duration | `5278` | h | 1–48; UI input bounds |
| Cooling off damping duration | `5279` | h | 1–48; UI input bounds |

The **current flow target** is the controller's reported requested flow
temperature. Compare it with the existing actual flow temperature (`1001`),
for example in a Home Assistant history graph. It is distinct from the room
heating/cooling targets and from the design flow temperature (`5222`).
It is not a writable setpoint in this integration. Both flow sensors suggest
one decimal for display; stored numeric precision and user overrides remain
unchanged. The target has the measurement state class so its changing values
can be recorded in long-term statistics alongside actual flow readings.

The other nine values are **reported controller parameters**, not measured
room/outdoor temperatures or elapsed heating/cooling time. They have no
measurement or total-increasing state class. Damping values use hours and
the duration device class; they are not operating-hour counters. This guide
does not infer the controller's exact threshold/timer algorithm from their names.

## Discovery, failures and request budget

HK60 must return the actual boolean `enabled: true` at `/1/2/config` before
these optional values are queried. That check is shared with the existing
room-target sensors. The original eight core values remain unchanged.

Each new entity is discovered after its first valid numeric reading. Missing,
malformed, unsupported or out-of-range values affect only that reading;
existing entities become unavailable instead of receiving invented defaults.
Later polls can discover or recover them without a new config entry.
Boolean temperatures, numeric strings, non-finite values and the −273.15 °C
sentinel are rejected. Neither an unsupported field nor its later recovery
changes the existing HK60 mode select or night automation.

The 60-second coordinated sequential polling interval is retained. With every
supported module enabled and valid, a complete refresh uses **36 GET requests**:
eight core readings, four shared configuration checks and 24 optional readings.
There are no per-entity network requests and no new gateway writes. This
development version can provide **26 sensors, six binary sensors and one
HK60 mode select**; unsupported readings can reduce that count.

## Evidence and remaining verification

On 2026-11-01, the local HK60 UI explicitly associated `1_2_52204` with
`flow_temp_req` (the flow-temperature target). A separate identity-bound
read-only check then successfully read this endpoint twice and all nine
additional endpoints once. Saved gateway identity and the mode matched
before/after; no write, reload or restart was performed. Private addresses,
identifiers, raw HTML and installation-specific settings are not published.
This is a field observation from one gateway, not a universal firmware claim.

The manufacturer's published heating-circuit table did not establish the
current flow-target ID; this mapping comes from the UI and the successful
GETs. The two broad temperature guards above are not claimed as manufacturer
operating limits. Threshold/damping bounds come from the UI inputs.

Automated tests use synthetic values to cover exact GET paths, shared config,
range/type rejection, independent failures/recovery, late discovery, native
units/state classes, translations, IDs and customizations after reload, and
diagnostics without extra I/O. Those tests and the endpoint reads do not claim
installation or rendered-UI acceptance of this new integration source.

Storage electric-heater targets/hysteresis, holiday schedules and further
module controls are outside this addition. A UI save button alone does not
establish safe write support. The only gateway write remains the existing
verified HK60 operating-mode selection (`5004`).
