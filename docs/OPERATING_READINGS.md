# Additional operating readings

[Back to the overview](../README.md)

Status: **development only, not yet released**. These eight additional read-only
entities are not included in the published 0.4.1 release. This change does not
install anything in Home Assistant or add temperature controls.

## Readings

Paths are relative to `/api/v1/1001/<serial_number>`. The manufacturer's
[SmartGuard network and data access documentation](https://dokumente.meiertobler.ch/files/product-assets/90355/lvxlo.pdf)
describes module configuration on page 9 and the datapoints on pages 18 and 20.

| Entity | Module | Datapoint | Type / interpretation |
| --- | --- | --- | --- |
| HK60 room heating target | `1/2` | `5201` | Temperature setting, 5–30 °C |
| HK60 room cooling target | `1/2` | `5202` | Temperature setting, 5–30 °C |
| Controller outdoor temperature | Controller root | `1115` | Measured temperature, −50 to 125 °C |
| Smart Grid status | Controller root | `2703` | Enum: None, Normal, Push, Eco, Forced |
| Heat generator fault input | Controller root | `1004` | Boolean: true means a reported fault |
| Priority 1 collective fault input | Controller root | `1005` | Boolean: true means a reported fault |
| Priority 2 collective fault input | Controller root | `1006` | Boolean: true means a reported fault |
| Heating buffer heat request | `2/1` | `1004` | Boolean: true means a reported request |

HK60 paths use `/1/2/datapoints/<id>`, controller paths use
`/datapoints/<id>`, and the buffer request uses `/2/1/datapoints/1004`.
The two `1004` endpoints are different signals and have distinct entity IDs.

Room targets are **settings reported by the controller**, not measured room
temperatures. Their sensor entities have temperature units without a measurement
state class. The outdoor-temperature sensor has the measurement state class.
Fault inputs use Home Assistant's problem device class. The buffer request has
no heat/power device class: a request does not prove that heating or an electric
heater is running. The existing storage heater indicators remain unchanged.

The stable Smart Grid states are `none`, `normal`, `push`, `eco`, and `forced`;
English and German display labels are provided. Status zero is a valid `none`
state. A future or malformed value is unavailable, not guessed to be normal.

## Availability and polling

All new readings are optional. Each module must report the actual boolean
`enabled: true` at its `/config` endpoint before its optional datapoints are
queried. The controller root has its own `/config`; the buffer reuses the same
config check as its existing temperature, indicator and hours. Optional HK60
configuration does not change the original eight core readings.

Entities are discovered after their first valid reading, including a valid
false or zero. A later missing or invalid reading makes only that entity
unavailable; it does not become a zero temperature or a cleared fault. Optional
module or datapoint failures do not block the original readings. Subsequent
updates retry and can recover or discover readings without a new config entry.

The coordinator retains the 60-second interval and sequential requests. With
all optional modules enabled, one complete refresh performs **26 GET requests**:
eight original readings, four module configuration checks and 14 optional
readings. There are no per-entity network requests or new gateway writes.
With all readings available, the combined entity count is **16 sensors, six
binary sensors and the existing single HK60 mode select**.

## Verified scope and limits

A private read-only gateway inventory confirmed documented types and ranges
for the eight selected datapoints. Raw installation values, addresses, module
labels and device identifiers are not part of this guide or the test fixtures.
Automated tests cover exact GET paths, shared configuration checks, false/zero,
range/type rejection, independent failures and recovery, late discovery,
translation, units, unchanged IDs and custom names after reload, and diagnostics
without additional I/O. Installation and UI verification remain separate steps.

The same inventory did not provide a valid HK60 return temperature, rejected
the controller operating-mode endpoint, and returned an EVU-status Boolean
instead of the documented integer. Those three datapoints are not added here.
Other heating-curve/offset values and the heat-pump subsystem identification
also remain outside this eight-entity change.

The manufacturer marks the room targets as writable, but this change exposes
them as sensors only. It performs no write-capability test. Changing room
targets, heating curves, EVU/Smart Grid commands or heaters requires a separate
implementation and verification. Existing mode selection and the guarded night
automation keep their current behavior.
