# HK60 flow target and heating/cooling limits

[Back to the overview](../README.md) · [Operating readings](OPERATING_READINGS.md)

Included since published **0.6.0**: ten optional read-only HK60 sensors and
configured module names, retained in the current stable **0.7.1**.
See the [versioned release notes](RELEASE_NOTES_0.6.0.md) and
[GitHub Releases](https://github.com/martins-netizen/ha-meiertobler-smartguard/releases)
for the publication record. No editable temperature or duration controls are added.

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

Use a target/actual comparison from the **same HK60 circuit**. Heat-pump
condenser temperatures can belong to a different hydraulic point and can rise
during hot-water production. A brief target/actual gap is not a fault diagnosis:
account for startup, operating status, hot-water production and defrost before
turning a sustained deviation into an operational warning. This release exposes
the measurements; it does not install a fault-monitoring automation.

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

The 60-second coordinated sequential polling interval is retained. In the
**0.6.0 release**, with every supported module enabled and valid, a complete
refresh uses **38 GET requests**:
eight core readings, six configuration checks and 24 optional numeric readings.
There are no per-entity network requests and no new gateway writes. This
version can provide **26 numeric/enum sensors, six binary sensors and one
HK60 mode select**, plus up to six diagnostic label sensors (39 entities in
total). Unsupported readings or missing labels can reduce that count.

These are historical 0.6.0 totals. The current 0.7.1 release also includes
heating-curve and holiday readings, for up to **45 supported entities and
44 GET requests** per refresh. See the [technical reference](TECHNICAL_REFERENCE.md).

## Configured module names

The module `/config` responses provide `label` and `enabled`, as described on
page 9 of the manufacturer's
[network and data-access documentation](https://dokumente.meiertobler.ch/files/product-assets/90355/lvxlo.pdf).
Labels are read from the controller root, HK50 (`1/1`), HK60 (`1/2`), HK70
(`1/3`), heating buffer (`2/1`) and hot-water storage (`3/1`). A module must
report boolean `enabled: true` before its label is used.

In published **0.6.0**, a configured label **Floor heating** replaces the technical
HK60 prefix in display names, producing **Floor heating flow target temperature**.
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

### Shorter names since 0.7.0

The naming refinement **published in 0.7.0** puts the measurement first and keeps
only a short circuit suffix, such as **Flow target · HK60** or
**Heating on threshold · HK60**. Long configured circuit labels no longer
hide the measurement in narrow device views. German examples are **Vorlauf
SOLL · HK60**, **Heizgrenze ein · HK60** and **Heizen ein: Dämpfung · HK60**.
The controller's reported outdoor reading becomes **Outdoor temperature sensor**
(**Aussentemperaturfühler**), without suggesting a controller temperature.

The configured assignment remains separate in `module_display_name`, for
example **HK60: Example floor circuit**. A matching leading `HK 60` or `HK60:`
in the label is not repeated in that display attribute. The raw `module_name`
attribute and diagnostic label-sensor value are unchanged. HK50/HK70 retain
label-only discovery and also expose their formatted assignment.

Storage labels keep their current naming behavior. Existing gateway device
assignment, entity/unique IDs, user names and display settings are preserved;
no logical device migration or automation rewrite is performed. A later
label change updates module metadata while the short HK60 measurement names
stay readable. Integration diagnostics still redact every free-text label.
The naming refinement itself adds no requests or gateway writes. The full
[0.7.0 release](RELEASE_NOTES_0.7.0.md) separately adds heating-curve/holiday
readings and confirmed holiday editing; the historical 0.6.0 tag is unchanged.

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
installation or rendered-UI acceptance by themselves. Versioned release notes
retain the corresponding publication and field-verification records.

Storage electric-heater targets/hysteresis and further module controls remain
outside this integration. A UI save button alone does not establish safe write
support. Supported writes are the verified HK60 operating-mode selection
(`5004`) and the separately confirmed [whole-period holiday editor](HOLIDAY_MODE_PLAN.md)
for `5226`/`5227`. The temperature and damping sensors in this guide remain read-only.
