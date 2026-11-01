# HK60 heating-curve diagnostics

Status: **unreleased**. These four optional read-only settings extend the
published 0.6.0 readings; they are not a release or a new control interface.

| Reading | HK60 datapoint | Native unit | Accepted range |
|---|---:|---|---|
| Heating temperature boost | 5071 | K, temperature difference | 0–16 |
| Design flow temperature | 5222 | °C | 10–80 |
| Minimum normal flow | 5223 | °C | 20–90 |
| Minimum reduced flow | 5225 | °C | 15–90 |

All paths are relative to `/api/v1/1001/<serial>/1/2/datapoints/`.
These values were confirmed by an earlier read-only gateway check and appear
in the supplied frontend. Ranges follow the manufacturer's documented contract,
not a recommendation to select such temperatures for a floor circuit.

Design flow is the configured heating-curve value at the design outdoor
temperature. It differs from the current requested flow (`52204`) and actual
flow (`1001`). The two minima are reported settings, not measured temperatures.
No measured room temperature or exact hydraulic/priority behavior is inferred.

The boost uses Home Assistant's **temperature_delta** device class with native
and suggested unit K. An override to Fahrenheit converts an interval without
adding an absolute-temperature offset. This class is present in the declared
minimum Core 2026.9.0; native tests run against the pinned Core 2026.10.4.
The four diagnostic sensors have no measurement or operating-hour state class.
Full values are retained; suggested display precision is one decimal place.

Each value requires the existing HK60 configuration to report `enabled: true`.
The first valid reading creates its entity. A missing, out-of-range, incorrectly
typed or non-finite response affects only that value; subsequent valid data can
restore it. Zero is a valid boost. Existing entity IDs and user names are retained.

No additional module discovery or per-entity refresh is added. With all supported
modules and readings available, the unreleased scope uses **42 GETs** per complete
60-second refresh: eight core values, six shared module configurations and
28 optional numeric/boolean values. Maximum entity count is **43**: 30 numeric/enum
sensors, six label sensors, six binary sensors and the existing HK60 mode select.
This is four extra GETs and four sensors compared with published 0.6.0. Disabling
a sensor in the entity registry does not by itself change the coordinated poll.

Only the existing HK60 mode write remains supported. These diagnostics do not
write setpoints, alter heater functions or implement holiday control.

For future additions, names must explicitly distinguish an **electric heater
target** in a hot-water tank/buffer from a heat-pump hot-water target and an HK60
flow target. A displayed heater target does not prove that the heater is running.
No electric-heater target is added by this change.
