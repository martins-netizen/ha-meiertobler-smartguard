# HK60 heating-curve diagnostics

Status: **published in 0.7.0**. These four optional read-only settings extend
the 0.6.0 readings. See the [0.7.0 release notes](RELEASE_NOTES_0.7.0.md).

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
adding an absolute-temperature offset. The complete suite exercises this
behavior on the current minimum Core 2026.11.0. See the
[development checks](TECHNICAL_REFERENCE.md#development-checks).
The four diagnostic sensors have no measurement or operating-hour state class.
Full values are retained; suggested display precision is one decimal place.

Each value requires the existing HK60 configuration to report `enabled: true`.
The first valid reading creates its entity. A missing, out-of-range, incorrectly
typed or non-finite response affects only that value; subsequent valid data can
restore it. Zero is a valid boost. Existing entity IDs and user names are retained.

No additional module discovery or per-entity refresh is added. Together with
the two holiday timestamp readings, the complete 0.7.0 release uses **44 GETs**
per 60-second refresh: eight core values, six shared module configurations and
30 optional numeric/boolean/timestamp values. Its maximum is **45 entities**:
32 numeric/enum/timestamp sensors, six label sensors, six binary sensors and
the existing HK60 mode select. Disabling a sensor alone does not change the poll.

These four settings remain read-only. The release's separate confirmed
[holiday editor](HOLIDAY_MODE_PLAN.md) does not edit them. The exact controller
curve, its filtering and a direct wind input have not been verified. The
reported heating on/off damping settings do not establish a curve-averaging
window. Do not infer a fault solely from a model/target difference.

For future additions, names must explicitly distinguish an **electric heater
target** in a hot-water tank/buffer from a heat-pump hot-water target and an HK60
flow target. A displayed heater target does not prove that the heater is running.
No electric-heater target is added by this change.
