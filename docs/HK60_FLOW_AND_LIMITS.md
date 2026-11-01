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
supported module enabled and valid, a complete refresh uses **38 GET requests**:
eight core readings, six configuration checks and 24 optional numeric readings.
There are no per-entity network requests and no new gateway writes. This
development version can provide **26 sensors, six binary sensors and one
HK60 mode select**, plus up to six diagnostic label sensors (39 entities in
total). Unsupported readings or missing labels can reduce that count.

## Configured module names

The module `/config` responses provide `label` and `enabled`, as described on
page 9 of the manufacturer's
[network and data-access documentation](https://dokumente.meiertobler.ch/files/product-assets/90355/lvxlo.pdf).
Labels are read from the controller root, HK50 (`1/1`), HK60 (`1/2`), HK70
(`1/3`), heating buffer (`2/1`) and hot-water storage (`3/1`). A module must
report boolean `enabled: true` before its label is used.

For example, a configured label **Floor heating** replaces the technical HK60
prefix in display names, producing **Floor heating flow target temperature**.
Storage entities use their corresponding configured labels. Technical module
IDs remain in the `module_id` attribute, with the configured text in
`module_name`. The labels are also separate diagnostic sensors, making the
HK50/HK60/HK70 assignments visible even though numeric readings and mode control
currently cover HK60 only. HK50/HK70 discovery reads their config only; it
does not query their datapoints or create additional mode controls.

Existing unique IDs, registered entity IDs, device assignment, custom names
and precision overrides are preserved. A later label change updates the
default display name without renaming existing IDs. Fresh installations may
derive their initial entity IDs from their configured labels. Missing/invalid
labels use the existing translated default names; existing label sensors
become unavailable and can recover later. Numeric readings remain independent.
Labels are plain text, trimmed and limited to 128 characters; non-text and
control-character values are ignored. They are never used in endpoint paths.

HK60, buffer, hot-water and controller labels reuse the four existing config
reads. HK50/HK70 add **two config GETs**, giving the 38-request budget above.
No raw label is logged by the API client. Free-text labels may be personal;
integration diagnostics redact all six label fields while retaining validated
numeric readings. This redaction does not remove labels from local HA names.

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
